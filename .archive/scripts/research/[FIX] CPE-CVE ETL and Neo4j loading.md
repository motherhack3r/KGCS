# Fixing CPE-CVE ETL and Neo4j loading pipeline: analysis and recommendations

## Findings & actions (concise)

- Schemas inspected:
  - cpe_api_json_2.0.schema — CPE JSON structure (cpe.cpeName, cpeNameId UUID, deprecated, created/lastModified, refs).
  - cpematch_api_json_2.0.schema — CPEMatch uses `matchCriteriaId`, `criteria`, `matches[]` (cpeName / cpeNameId) and version range fields.
  - cve_api_json_2.0.schema — CVE feed with `configurations` structures and `cpeMatch`/`matchCriteriaId` occurrences; supports CVSS variants.

- OWL inspection (key files):
  - core-ontology-extended-v1.0.owl — canonical core classes/properties. Important properties: `sec:CPEUri` (capitalized), `sec:cpeNameId`, `sec:Platform`, `sec:PlatformConfiguration`, `sec:affects` / `sec:affected_by`, `sec:matchesPlatform` / `sec:matchedBy`, etc.
  - SHACL bundles: core-shapes.ttl expects `sec:CPEUri` in places; cpematch-shapes.ttl refers to `sec:cpeUri` (lowercase) in other places — there is a naming/casing mismatch across ontology modules / shapes.

- ETL code analysis (intent vs output)
  - etl_cpe.py
    - Emits Platform nodes at `<https://example.org/platform/{cpeNameId|quotedName}>`.
    - Writes triples using predicate `<https://example.org/sec/core#cpeUri>` (lowercase `cpeUri`), plus `cpeNameId`, vendor/product/version, etc.
  - etl_cpematch.py
    - Emits PlatformConfiguration nodes at `<https://example.org/platformConfiguration/{matchCriteriaId}>`.
    - Emits platform inclusion triples using `<https://example.org/sec/core#includes>` (literal predicate `includes`), and also emits Platform triples for included platforms (with `<...#cpeUri>`).
    - Has option to include or exclude orphan configs (important for emitting only meaningful PlatformConfiguration nodes).
  - etl_cve.py
    - Emits Vulnerability nodes (subject is MITRE CVE URL), writes `<...#affects>` / `<...#affected_by>` triples linking CVE ↔ PlatformConfiguration using `matchCriteriaId`.
    - Builds optional mapping from criteria->matchCriteriaId by indexing CPEMatch JSON (used when matchCriteriaId absent in CVE feed entries).

- Loader / Neo4j interaction
  - load_to_neo4j.py expects RDF predicates defined in the `sec` namespace, and specifically reads `SEC.CPEUri` (note capitalization), `SEC.matchesPlatform` and `SEC.affected_by` when extracting edges.
  - Loader merges nodes by the external identifier properties: `(Platform {cpeUri})`, `(PlatformConfiguration {matchCriteriaId})`, `(Vulnerability {cveId})`, then creates relationships via UNWIND.

- Sample files (sizes — checked before sampling)
  - pipeline-stage1-cpe.ttl ≈ 2.6 GB
  - pipeline-stage2-cpematch.ttl ≈ 19.9 GB
  - pipeline-stage3-cve.ttl ≈ 1.9 GB
  - Smaller files available for quick inspection:
    - pipeline-stage1-cpe-rels.ttl ≈ 33.6 MB — sampled
    - Sampled first lines of `pipeline-stage2-cpematch-rels.ttl` and `pipeline-stage3-cve-rels.ttl` to confirm formats (they show PlatformConfiguration→Platform `includes` and PlatformConfiguration↔Vulnerability `affected_by` triples.)

## Problems / Incoherences found (critical)

- Predicate / identifier name mismatches between ETL, OWL, SHACL and loader:
  - Capitalization mismatch: OWL core uses `sec:CPEUri` (capitalized) while ETL writes `sec#cpeUri` (lowercase). SHACL core-shapes checks `sec:CPEUri`, but cpematch-shapes.ttl references `sec:cpeUri` (lowercase) — inconsistent across modules.
  - Relationship name mismatch: ETL writes `sec:includes` from PlatformConfiguration → Platform; the core OWL defines `sec:matchesPlatform` / `sec:configurationFor` / `sec:includesConfiguration` variants. The Neo4j extractor expects `SEC.matchesPlatform` (exact property), so it will miss relationships if ETL uses `includes`.
  - Loader expects to find platform link via `SEC.matchesPlatform`. ETL emits `includes` (and loader doesn't query `includes`) — this disconnect causes the loader to fail linking configs→platforms, losing cpeUri mapping required for fast Neo4j relationship creation.
- Because the core ontology is frozen (per repository policy), the source of truth must be the OWL/SHACL names — ETL should be adapted to emit the canonical URIs expected by OWL/SHACL/loader.

## Recommended fixes / improvements (practical & safe)

1. Canonicalize property names (must do first)
   - Align ETL outputs with the frozen core ontology:
     - Change ETL to write `https://example.org/sec/core#CPEUri` (capitalized) OR change loader & SHACL to accept `cpeUri` consistently — but since OWL core is frozen, preferred fix is to update ETL to emit the exact `sec:CPEUri` and `sec:matchesPlatform` (or whichever property the core OWL declares as canonical).
     - Change ETL `includes` → `matchesPlatform` (or emit both temporarily while migrating).
   - Update etl_cpematch.py to:
     - Emit `sec:matchesPlatform` (PlatformConfiguration → Platform) or `sec:configurationFor` as defined by OWL and the loader’s extractor.
     - Optionally emit inverse `sec:matchedBy`/`sec:configurationFor` if required by SHACL.

2. Keep identifiers canonical and indexed
   - Platforms: use `cpeNameId` (UUID) if present, otherwise `cpeUri` canonical string; ensure `cpeUri` is present and used as the unique key in Neo4j (`:Platform {cpeUri: ...}`).
   - PlatformConfiguration: use `matchCriteriaId` (UUID) as unique key in Neo4j.
   - Vulnerability: use `cveId` (CVE string) as unique key.

3. Neo4j ingestion performance strategy (fast, robust)
   - For initial bulk load (one-off, huge files):
     - Convert the TTL outputs into CSV node and relationship files and use `neo4j-admin import` (fastest) to load nodes and relationships. This requires breaking into node CSVs and rel CSVs with mapping headers and keys.
     - If `neo4j-admin import` not possible, use batched UNWIND via Bolt with large transactions:
       - Create constraints/indexes before load:
         - Platform: `CREATE CONSTRAINT IF NOT EXISTS FOR (p:Platform) REQUIRE p.cpeUri IS UNIQUE`
         - PlatformConfiguration: `... matchCriteriaId IS UNIQUE`
         - Vulnerability: `... cveId IS UNIQUE`
       - Use `UNWIND $rows AS row MERGE (p:Platform {cpeUri: row.cpeUri}) SET p += row.props` with row batches sized (2k–50k) depending on memory.
       - Use separate batches for nodes and relationships (first create all nodes, then create relationships by matching on the unique key properties).
       - For relationships, use UNWIND on rows containing keys only (e.g., {matchCriteriaId, cveId}) and run `MATCH` on the unique key properties and `MERGE` the relationship — this avoids expensive searches on non-indexed properties.
     - Use periodic commit / APOC `apoc.periodic.iterate` if running inside DB server to handle streaming insertion safely.
   - For incremental updates:
     - Use Bolt UNWIND with small batches, ensure idempotency with MERGE on keys.
     - Keep relationship batches larger than node updates to reduce overhead.
   - Avoid doing per-triple MERGE; always merge on the node's unique key and set properties via SET += row.props.

4. Relationship linking approach (how to relate CPE ↔ CVE via CPEMatch)
   - ETL pipeline order must be maintained:
     1. Generate Platforms (etl_cpe.py) — ensure `sec:CPEUri` and `sec:cpeNameId` are emitted.
     2. Generate PlatformConfigurations (etl_cpematch.py) — ensure `sec:matchCriteriaId` and link to platform using `sec:matchesPlatform` (match on platform URI or cpeNameId).
        - Emit both `matchesPlatform` (points to Platform URI) and `configurationFor` (inverse) if helpful.
     3. Generate Vulnerabilities (etl_cve.py) — reference PlatformConfiguration by `matchCriteriaId` (ETL already emits `affects` / `affected_by`).
   - For Neo4j loading:
     - When creating config→platform edges, match Platform by `cpeUri` (the stable key) and config by `matchCriteriaId` — then create the `CONFIGURATION_FOR` or similar labeled relationship in Neo4j. This is faster than matching on full URIs or labels.

5. Small code suggestions (quick wins)
   - Emit canonical `sec:matchesPlatform` in cpematch ETL instead of `sec:includes` and also emit `sec:CPEUri` rather than `sec#cpeUri`— implement both for a transition period (emit canonical + backward-compatible predicate).
   - Update load_to_neo4j.py to also accept backward-compatible predicates during a migration window (e.g., check `SEC.cpeUri` AND `SEC.CPEUri` when extracting), but plan to remove the compatibility code once ETL is fixed (do not keep permanent workaround that masks ontology drift).
   - Add a small unit test ensuring that `etl_cpematch` emits the `matchesPlatform` triple and `etl_cpe` emits the `CPEUri` predicate that `load_to_neo4j` expects.
