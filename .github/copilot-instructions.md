# KGCS Copilot Instructions

## Mission & Invariants
- KGCS is a frozen, standards-backed knowledge graph; refer to docs/KGCS.md and docs/ARCHITECTURE.md for the layered design and the requirement that every statement trace back to NVD/MITRE sources.
- Keep the causal chain $CPE \to \text{CPEMatch} \to CVE \to CWE \to CAPEC \to ATT\&CK \to \{D3FEND, CAR, SHIELD, ENGAGE\}$ intact, never invent semantics, and link vulnerabilities to PlatformConfiguration (version/update context) rather than the atomic Platform identifier.
- Preserve the immutable core (11 OWL modules under docs/ontology/owl) and treat any addition as an extension that imports the core without altering it.

## Architecture & Docs
- Use docs/ARCHITECTURE.md and docs/DAILY-DOWNLOAD-PIPELINE.md to understand the five-phase roadmap, the download-plus-manifest pipeline, and the provenance-first policies before touching code.
- Treat docs/ontology/shacl, the JSON/markdown manifest, and the samples directory as the ground truth for validation; every new OWL module must be registered there so the validator and CI discover it.

## Key Workflows
- Run the daily fetch with `python -m src.ingest.download_manager`; src/ingest/download_manager orchestrates StandardDownloader subclasses, writes SHA256 checksums into data/{standard}/raw, records manifests under data/{standard}/manifest.json, and logs to logs/download_manager.log.
- Generate Turtle with the ETL transformers (`python -m src.etl.etl_cpe --input data/cpe/samples/sample_cpe.json --output tmp/cpe-output.ttl --validate`) and always validate via `scripts/validate_shacl_stream.py` before loading; use `scripts/validate_etl_pipeline_order.py` for production-scale downloads.
- Ingest validated TTL through the CLI wrappers (`python -m src.cli.ingest --file ...` and `python -m src.cli.validate --data ...`); they call `src/ingest/pipeline` (which prints simulated indexing) and `src/core/validation`, accepting `--shapes`, `--template`, or `--owl` to pick the right subset defined in `TEMPLATE_SHAPE_MAP`.

## Conventions & Patterns
- Every ontology change must map 1:1 to a standard field; new modules live in docs/ontology/owl and their SHACL shapes must be declared in docs/ontology/shacl/manifest (JSON or Markdown) so the validator can auto-select them with the --owl flag.
- RAG safety is enforced by the approved templates in docs/ontology/rag/RAG-traversal-templates.md (and the extension companion document); do not craft free-form traversal paths because the validator and TEMPLATE_SHAPE_MAP expect those exact subsets, e.g., T1–T7.
- Extension work (Incident, Risk, ThreatActor) stays in docs/ontology/extensions and src/extensions; extensions import the frozen core but never back-mutate it.

## Data Flow & Integrations
- Raw files downloaded from NVD/MITRE flow through `src/etl/etl_*` transformers, produce Turtle under `tmp/`, feed `docs/ontology/shacl` shapes via `scripts/validate_shacl_stream`, and then hit the Neo4j loader at `src/etl/rdf_to_neo4j.py`; `src/config.py` captures Neo4j credentials, batch size, and other ETL knobs via the `.env` file.
- Validation artifacts land in artifacts/ (for example, artifacts/shacl-report-*.json); keep running the validator so tests and CI can consume those JSON reports before merging.

## Testing & Validation
- Run `pytest tests/test_phase3_comprehensive.py -v` (plus `pytest tests/test_etl_pipeline.py` when modifying one transformer) to cover transformation and validation as described in `docs/ARCHITECTURE.md`.
- Use `scripts/validate_shacl_stream.py` for per-file reports and `scripts/validate_etl_pipeline_order.py` to orchestrate the full ingestion; both obey the same `shapes`/`template`/`owl` selection logic that powers the CLI wrappers.

Please flag anything that feels unclear or incomplete so we can iterate on these instructions together.
