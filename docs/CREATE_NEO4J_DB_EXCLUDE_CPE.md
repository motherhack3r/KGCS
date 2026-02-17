# Create Neo4j DB (exclude CPE & CPEmatch)

Purpose: build a Neo4j database containing all standards except `cpe` and `cpematch`.

Prerequisites

- Work from repository root: `e:\DEVEL\LAIA\KGCS`
- Activate conda env: `conda activate E:\DEVEL\LAIA\KGCS\.conda`
- Ensure downloaded sources exist under `data/{standard}/raw/` for: `attack, capec, cve, cwe, d3fend, car, shield, engage`.
- Neo4j reachable by configuration in `src/config.py`.

Steps (copy/paste)

1. Activate environment

```powershell
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\LAIA\KGCS\.conda
cd e:\DEVEL\LAIA\KGCS
```

1. (Optional) Download only chosen standards

```bash
python -m src.ingest.download_manager --standards attack,capec,cve,cwe,d3fend,car,shield,engage
```

3. Run per-standard ETLs (nodes + rels).

Preferred: use the guided helper to run a single standard and step. Example interactive flow:

```bash
python scripts/run_standard_pipeline.py
# When prompted: enter the standard (e.g., capec) and choose `etl`.
```

Direct (non-interactive) example — the helper constructs these commands for you:

```bash
# Run CAPEC ETL (helper will ask and run similar command)
python scripts/run_standard_pipeline.py
# or run the per-standard module directly when needed:
python -m src.etl.etl_capec --input data/capec/raw/capec_latest.xml --output data/capec/samples/pipeline-stage6-capec-full.ttl \
  --nodes-out data/capec/samples/pipeline-stage6-capec-nodes.ttl \
  --rels-out data/capec/samples/pipeline-stage6-capec-rels.ttl --attack-input data/attack/raw
```

1. Validate outputs (recommended)

```bash
python scripts/validation/validate_shacl_stream.py --data data/capec/samples/pipeline-stage6-capec-nodes.ttl --shapes docs/ontology/shacl/capec-shapes.ttl
# or run all
python scripts/validation/validate_all_standards.py
```

1. Combine per-standard nodes/rels into `tmp/` (optional)

```powershell
# copy canonical split outputs into tmp/
Get-ChildItem -Path data\*\samples -Filter '*-nodes.ttl' -Recurse | ForEach-Object { Copy-Item $_.FullName -Destination tmp -Force }
Get-ChildItem -Path data\*\samples -Filter '*-rels.ttl' -Recurse | ForEach-Object { Copy-Item $_.FullName -Destination tmp -Force }

# combine
python scripts/combine_ttl_pipeline.py --nodes-out tmp/combined-nodes.ttl --rels-out tmp/combined-rels.ttl
```

1. Create the Neo4j DB and load nodes (nodes-first)

```bash
# create DB named e.g. neo4j-2026-02-17 and load nodes (reset DB)
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-nodes.ttl --reset-db --nodes-only --db-version 2026-02-17 --fast-parse --chunk-size 50000
```

1. Load relationships (no reset)

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-rels.ttl --rels-only --db-version 2026-02-17 --fast-parse --rel-batch-size 500
```

1. Re-run stats and verify CAPEC→Technique + defense links

```bash
python scripts/utilities/extract_neo4j_stats.py --db neo4j-2026-02-17 --output artifacts/neo4j-stats-2026-02-17.json --pretty
```

Notes & Warnings

- Excluding CPE/CPEmatch removes Platform and PlatformConfiguration nodes; asset/impact queries will be incomplete.
- CAPEC ETL emits `IMPLEMENTED_AS` relationships; loader preserves predicate names. If you require canonical `IMPLEMENTS`, run a one‑time Cypher migration (see README Appendix).
- Use `--dry-run` to preview counts without writing to the DB.
- For large files prefer `--fast-parse`, `--chunk-size`, and tune `--rel-batch-size`.

Optional: one-time Cypher migration example (if you decide to canonicalize):

```cypher
MATCH (c:AttackPattern)-[r:IMPLEMENTED_AS]->(t)
MERGE (c)-[r2:IMPLEMENTS]->(t) SET r2 += properties(r)
DELETE r
```

---

File: docs/CREATE_NEO4J_DB_EXCLUDE_CPE.md
