# KGCS Copilot Instructions

## Big picture (read first)
- KGCS is a frozen, standards-backed knowledge graph. Every class/property must map to an authoritative NVD/MITRE field (no invented semantics). See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) and [docs/KGCS.md](../docs/KGCS.md).
- Core causal chain is mandatory: CPE → CPEMatch → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}.
- Vulnerabilities link to `PlatformConfiguration` (version/update context), not the atomic `Platform`.
- Core ontology (docs/ontology/owl/) is immutable; extensions (Incident/Risk/ThreatActor) import core only.

## Data flow & boundaries
- Download: [src/ingest/download_manager.py](../src/ingest/download_manager.py) → data/{standard}/raw/ + manifest.json + logs/download_manager.log.
- ETL: [src/etl/etl_*.py](../src/etl) parses NVD/MITRE JSON/XML → tmp/*.ttl.
- Validate: [scripts/validate_shacl_stream.py](../scripts/validate_shacl_stream.py) with shapes in docs/ontology/shacl (canonical bundle: kgcs-shapes.ttl).
- Load: [src/etl/rdf_to_neo4j.py](../src/etl/rdf_to_neo4j.py) transforms Turtle to Neo4j nodes/relationships.

## Project-specific patterns
- ETL files follow a streaming write pattern with helpers like `turtle_escape()` and `subject_for_*` (see [src/etl/etl_cpe.py](../src/etl/etl_cpe.py)). Output must be idempotent: same input → same TTL.
- SHACL validation is template-aware via `TEMPLATE_SHAPE_MAP` in [src/core/validation.py](../src/core/validation.py). Reports go to artifacts/shacl-report-*.json.
- Offline sanity checks are separate utilities (not pytest): [tests/verify_causal_chain.py](../tests/verify_causal_chain.py) and [tests/verify_defense_layers.py](../tests/verify_defense_layers.py) read tmp/pipeline-stage*.ttl.

## Critical workflows (examples)
- Download raw data: `python -m src.ingest.download_manager`
- Transform one standard: `python -m src.etl.etl_cpe --input data/cpe/samples/sample_cpe.json --output tmp/cpe-output.ttl --validate`
- Validate a TTL file: `python scripts/validate_shacl_stream.py --data tmp/cpe-output.ttl --shapes docs/ontology/shacl/cpe-shapes.ttl`
- End-to-end ETL validation: `python scripts/validate_etl_pipeline_order.py`
- Neo4j load: `python src/etl/rdf_to_neo4j.py --ttl tmp/cpe-output.ttl --batch-size 1000`

## Non-negotiables
- Preserve the causal chain and per-standard IDs (cveId, cweId, capecId, etc.).
- Keep CVSS versions separate nodes (v2.0, v3.1, v4.0).
- Do not alter core OWL modules for extensions; add new extension OWL/SHACL/ETL in isolation.
- Always validate with SHACL before any Neo4j load.
