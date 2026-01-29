# KGCS Copilot Instructions

## 1. Big picture (read first)
- KGCS is a frozen, standards‑backed knowledge graph. Every class/property maps 1:1 to an authoritative NVD/MITRE field – no invented semantics. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) and [docs/KGCS.md](../docs/KGCS.md).
- The core causal chain is **mandatory**: `CPE → CPEMatch → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}`.
- Vulnerabilities point to `PlatformConfiguration` (version/update context), not the atomic `Platform`.
- Core OWL modules (docs/ontology/owl/) are immutable; extensions (Incident, Risk, ThreatActor) import core only.

## 2. Data flow & boundaries
- **Download**: `python -m src.ingest.download_manager` → `data/{standard}/raw/` + `manifest.json` + `logs/download_manager.log`.
- **ETL**: `src/etl/etl_*.py` parses NVD/MITRE JSON/XML → `tmp/*.ttl`.
- **Validate**: `scripts/validate_shacl_stream.py` runs SHACL against shapes in `docs/ontology/shacl` (canonical bundle: `kgcs-shapes.ttl`).
- **Load**: `src/etl/rdf_to_neo4j.py` transforms Turtle to Neo4j nodes/relationships.

## 3. Project‑specific patterns
- **Streaming ETL**: Each transformer writes one triple per line and uses helpers like `turtle_escape()` and `subject_for_*` (see `src/etl/etl_cpe.py`). Output is idempotent – same input always yields the same TTL.
- **Template‑aware SHACL**: `TEMPLATE_SHAPE_MAP` in `src/core/validation.py` selects a subset of shapes for a given RAG template. Reports are written to `artifacts/shacl-report-*.json`.
- **Offline sanity checks**: `tests/verify_causal_chain.py` and `tests/verify_defense_layers.py` are manual utilities that read the pipeline TTLs in `tmp/`.

## 4. Core workflows (examples)
- **Download raw data**: `python -m src.ingest.download_manager`
- **Transform one standard**: `python -m src.etl.etl_cpe --input data/cpe/samples/sample_cpe.json --output tmp/cpe-output.ttl --validate`
- **Validate a TTL file**: `python scripts/validate_shacl_stream.py --data tmp/cpe-output.ttl --shapes docs/ontology/shacl/cpe-shapes.ttl`
- **End‑to‑end ETL validation**: `python scripts/validate_etl_pipeline_order.py`
- **Neo4j load**: `python src/etl/rdf_to_neo4j.py --ttl tmp/cpe-output.ttl --batch-size 1000`

## 5. Build / test / CI
- **Dependencies**: `pip install -r requirements.txt` (Python 3.10+). Neo4j driver is pulled automatically.
- **Unit tests**: `pytest tests/` – covers ETL transformers and validation helpers.
- **Integration tests**: `pytest tests/test_phase3_comprehensive.py` – runs the full pipeline against sample data.
- **CI**: GitHub Actions (`.github/workflows/shacl-validation.yml`) runs SHACL validation on every push/PR. The workflow also builds the Docker image for the Neo4j loader.

## 6. Debugging & logs
- All download and ETL steps write to `logs/` (e.g., `download_manager.log`, `etl.log`).
- SHACL validation outputs a machine‑readable JSON report in `artifacts/` and a human‑readable summary to stdout.
- Neo4j loader prints progress bars and a final summary of nodes/relationships loaded.

## 7. Non‑negotiables
- Preserve the causal chain and per‑standard IDs (`cveId`, `cweId`, `capecId`, etc.).
- Keep CVSS versions separate nodes (`v2.0`, `v3.1`, `v4.0`).
- Do **not** alter core OWL modules for extensions; add new extension OWL/SHACL/ETL in isolation.
- Always validate with SHACL before any Neo4j load.

## 8. Quick reference
- **Core ontology**: `docs/ontology/owl/`
- **SHACL shapes**: `docs/ontology/shacl/`
- **RAG templates**: `docs/ontology/rag/`
- **Extensions**: `docs/ontology/extensions/` + `src/extensions/`
- **ETL entry points**: `src/etl/etl_*.py`
- **Neo4j loader**: `src/etl/rdf_to_neo4j.py`
- **Validation CLI**: `scripts/validate_shacl_stream.py`
- **Pipeline orchestrator**: `src/ingest/pipeline.py`

---

Feel free to ask for clarification on any of the steps above. Happy coding!