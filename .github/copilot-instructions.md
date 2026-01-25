# KGCS Copilot Instructions

Authoritative guidance for AI coding agents contributing to KGCS (Cybersecurity Knowledge Graph).

## Mission and Core Invariants
- **Preserve the frozen, standards-aligned ontology** that maps 1:1 to authoritative MITRE/NVD schemas (CPE, CVE, CVSS, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).
- **Enforce explicit provenance** for every class and edge; no invented semantics or unlabeled relationships.
- **Keep the core causal chain intact:** `CPE → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}`
- **Core is immutable.** Extensions (Incident, Risk, ThreatActor) reference core only; never modify or override.
- **Critical invariant:** Vulnerabilities affect `PlatformConfiguration` (version/update specifics), not `Platform` (atomic CPE identifier).

## Working rules
- Do not rename or repurpose core classes/edges; align any new element to a stable external ID and cite its source field.
- Avoid introducing organizational or contextual data into core; place such concepts in the relevant extension OWL module and keep imports one-way into core.
- Prefer additive changes; if you must touch existing semantics, pause and request human review.
- Keep ontology modules modular (no circular imports) and versioned as standalone OWL files under docs/ontology/.
- Core ontology modules live in docs/ontology/owl/ (e.g., cpe-ontology.owl, cve-ontology.owl, etc.); extensions live in docs/ontology/extensions/ (e.g., incident-extension.owl, risk-extension.owl); RAG templates in docs/ontology/rag/.
- When adding a new OWL module, register its `--owl <module.owl>` name in this file and in SHACL validator args so CI auto-detects it.
- **CVSS versioning:** Each version is a separate node (v2.0, v3.1, v4.0); never merge or overwrite—new versions coexist with old.
- **1:1 standards alignment:** Every ontology class maps directly to one source standard (e.g., `Platform` ↔ CPE 2.3, `Technique` ↔ ATT&CK STIX 2.1). If source doesn't have it, class doesn't have it.

## Critical Developer Workflows

### Running SHACL Validation
```bash
# Validate a single ETL output file against its standard's shapes
python scripts/validate_shacl_stream.py \
  --data data/cpe/samples/cpe-output.ttl \
  --shapes docs/ontology/shacl/cpe-shapes.ttl \
  --output artifacts

# Validate all samples in a directory
for f in data/shacl-samples/*.ttl; do
  python scripts/validate_shacl.py --data "$f"
done
```

### Running ETL Tests
```bash
# Test a single transformer
python -m src.etl.etl_cpe --input data/cpe/samples/sample_cpe.json \
                          --output tmp/cpe-test.ttl \
                          --validate

# Run full test suite
pytest tests/test_phase3_comprehensive.py -v
```

### Neo4j Integration (Phase 3 MVP)
```bash
# Load validated RDF into Neo4j
python src/etl/rdf_to_neo4j.py --ttl tmp/cpe-validated.ttl \
                                --batch-size 1000
```

### CI/CD Integration
- Workflow: `.github/workflows/shacl-validation.yml` auto-detects changed OWL files.
- On OWL change: Validates changed module against `data/shacl-samples/`.
- On no OWL change: Validates canonical bundle against all samples.
- Artifacts output: JSON reports in `artifacts/shacl-report-*.json`.

## Code Patterns and Project Structure

### Ontology Organization
- **Core**: `docs/ontology/owl/` – 11 OWL modules (standard 1:1 mappings + core bridge). Immutable.
- **Extensions**: `docs/ontology/extensions/` – Incident, Risk, ThreatActor. Import core only; never modify core.
- **SHACL**: `docs/ontology/shacl/` – Shapes per standard + consolidated bundle. Positive/negative samples in `data/shacl-samples/`.
- **RAG**: `docs/ontology/rag/` – Approved traversal templates. Use only pre-approved paths; reject freeform queries.

### ETL Implementation
- **Input**: JSON from NVD (CPE, CVE) or MITRE (CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).
- **Transformer class** structure:
  ```python
  class XyztoRDFTransformer:
      def __init__(self):
          self.graph = Graph()
          self.namespaces = {…}  # Standard URIs
      
      def transform(self, json_data: dict) -> Graph:
          # Idempotent: same input → same Graph
          for item in json_data[...]:
              self._add_triples(item)
          return self.graph
  ```
- **Output**: Turtle RDF ready for SHACL validation and Neo4j load.

### Test Organization
- `tests/test_etl_pipeline.py` – Single standard end-to-end (load JSON → transform → validate → report).
- `tests/test_phase3_comprehensive.py` – Parametrized test of all 9 transformers.
- Sample data: `data/*/samples/sample_*.json` – Small, deterministic sets for fast testing.
- Raw data validation: `scripts/validate_etl_pipeline_order.py` – Production-scale (222 MB CPE + CVE tested).

### Neo4j Integration (Phase 3 MVP)
- **Loader**: `src/etl/rdf_to_neo4j.py` – Parses TTL, batches node/relationship creation.
- **Config**: `src/config.py` – Neo4jConfig, ETLConfig dataclasses with .env support.
- **Indexes**: Auto-created on cpeUri, cveId, cweId, techniqueId, etc.
- **Status**: Designed; implementation pending.



## RAG and traversal safety
- Use only approved traversal templates (see ../docs/ontology/rag/RAG-travesal-templates.md for core and ../docs/ontology/rag/RAG-travesal-templates-extension.md for extensions); reject or flag free-form paths that skip the causal chain or mix standards without provenance.
- Every query or generated explanation must return paths with evidence (IDs and source fields). If provenance is missing, treat it as a failure.
- Enforce query-time traversal validation (planned in Phase 5); until then, ensure RAG templates are documented and reviewed before deployment.

## ETL Architecture and Data Flows

### ETL Pipeline Structure (Phase 3)
- **9 ETL transformers** (`src/etl/etl_*.py`): JSON/STIX → RDF (CPE, CVE, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).
- **Streaming validator** (`scripts/validate_shacl_stream.py`): Chunks large Turtle files, validates each chunk, emits reports to `artifacts/`.
- **RDF-to-Neo4j loader** (`src/etl/rdf_to_neo4j.py`): Parses TTL, creates nodes/relationships with indexes and constraints.
- **Config-driven setup** (`src/config.py`): Environment-based Neo4j connection (URI, auth, database name).

### ETL Transformer Pattern
- Each transformer class accepts JSON, returns `rdflib.Graph`.
- Example: `CPEtoRDFTransformer.transform(cpe_json: dict) -> Graph`
- Input: NVD API JSON (e.g., `data/cpe/samples/sample_cpe.json`).
- Output: Turtle RDF conforming to `docs/ontology/shacl/cpe-shapes.ttl`.
- No side effects; idempotent transformation.

### Ingestion and Data Handling
- Ingestion scripts (e.g., `src/etl/etl_*.py`) must preserve source hashes, timestamps, and external IDs; ingestion is idempotent.
- Never fabricate relationships; every edge comes from source data or explicit extension rules.
- Keep `artifacts/` for validation outputs; avoid committing large raw datasets into `data/` unless already curated samples.

### Testing and Validation
- Unit tests: `tests/test_etl_pipeline.py`, `test_phase3_comprehensive.py`.
- Run tests with pytest: `pytest tests/test_*.py -v`.
- ETL output **must pass SHACL validation** before Neo4j load:
  - Single file: `python scripts/validate_shacl_stream.py --data tmp/output.ttl --shapes docs/ontology/shacl/<standard>-shapes.ttl`
  - Batch: `scripts/validate_etl_pipeline_order.py` orchestrates all 9 transformers with validation hooks.
## Common task patterns
- **Adding a new relationship:** Verify it exists in source standard → Update edge in core ontology → Add OWL axiom → Update RAG templates if reasoning path changes.
- **Ingesting new standard version:** Create versioned module (e.g., `cpe-ontology-v3.0.owl`) → Update mappings documentation → Decide if coexists or replaces → Validate no URI breakage.
- **Supporting new use case:** Classify as Core (authoritative standard mapping) or Extension (temporal, contextual, inference) → Never modify Core to support use cases → Define RAG templates → Add SHACL constraints.

## Golden rules
1. **External standards are authoritative.** If MITRE/NVD say it, we model it. If they don't, it belongs in an extension.
2. **Frozen Core, flowing Extensions.** Core changes rarely; extensions are where complexity grows.
3. **RAG is templated, not freeform.** LLM reasoning follows pre-approved traversal patterns only.
4. **Trace everything back.** Every statement traceable to source with stable ID.
5. **One-way import flow.** Core never polluted by extensions.
6. **No circular dependencies.** Ontology modules form a DAG.

## When in doubt
- Ask for human review before altering core semantics or SHACL shapes.
- Default to preserving immutability and provenance over convenience or inferred links.
