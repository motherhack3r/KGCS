# KGCS Copilot Instructions

## Mission & Core Invariants

KGCS is a frozen, standards-backed knowledge graph unifying 9 MITRE taxonomies into a single authoritative source. Every statement must be traceable to NVD/MITRE sources—never invent semantics.

**Critical causal chain:** `CPE → CPEMatch → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}`  
**Key mapping:** Link vulnerabilities to **PlatformConfiguration** (version/update context), not atomic Platform.  
**Architecture:** Immutable 11-module core (docs/ontology/owl) + extensions (Incident, Risk, ThreatActor) that import core but never modify it.

Read [ARCHITECTURE.md](../docs/ARCHITECTURE.md) and [KGCS.md](../docs/KGCS.md) first for context.

---

## Data Flow: Download → ETL → Validate → Load

```
NVD/MITRE APIs
    ↓ [src/ingest/download_manager.py]
data/{standard}/raw/ (JSON/XML + checksums)
    ↓ [src/etl/etl_*.py transformers]
tmp/*.ttl (RDF Turtle)
    ↓ [scripts/validate_shacl_stream.py]
artifacts/shacl-report-*.json (validation)
    ↓ [src/etl/rdf_to_neo4j.py] — PENDING
Neo4j Graph DB
```

---

## Key Workflows & Commands

### Download & Manifest
```bash
python -m src.ingest.download_manager
# Output: data/{standard}/raw/ files + data/{standard}/manifest.json (SHA256, timestamps)
# Logs: logs/download_manager.log
```

### Transform JSON → RDF
```bash
# Single standard (CPE example)
python -m src.etl.etl_cpe \
  --input data/cpe/samples/sample_cpe.json \
  --output tmp/cpe-output.ttl \
  --validate

# All 9 standards (via test suite)
pytest tests/test_phase3_comprehensive.py -v
```

### Validate with SHACL
```bash
# Per-file streaming validation (handles 222 MB CPE data)
python scripts/validate_shacl_stream.py \
  --data tmp/cpe-output.ttl \
  --shapes docs/ontology/shacl/cpe-shapes.ttl

# Production batch validation
python scripts/validate_etl_pipeline_order.py
```

### CLI Ingestion (Validation + Simulated Indexing)
```bash
python -m src.cli.validate --data tmp/cpe-output.ttl [--shapes docs/ontology/shacl] [--template T1-T7] [--owl core]
python -m src.cli.ingest --file tmp/cpe-output.ttl
```

---

## Code Organization & Patterns

| Layer | Files | Purpose |
|-------|-------|---------|
| **Ontology (Core)** | docs/ontology/owl/*.owl | Frozen 11 modules: 1:1 mapping to NVD/MITRE schemas |
| **Validation** | docs/ontology/shacl/*.ttl | SHACL shapes + samples (good/bad test cases) |
| **ETL** | src/etl/etl_*.py | JSON/XML → RDF transformers (idempotent) |
| **Ingestion** | src/ingest/pipeline.py + src/cli/ | Validation gates + (simulated) indexing |
| **Download** | src/ingest/download_manager.py | Daily fetch + checksums + resumable |
| **Config** | src/config.py | Neo4j connection, batch sizes (.env) |
| **Extensions** | docs/ontology/extensions/ + src/extensions/ | Incident, Risk, ThreatActor (contextual layers) |

### ETL Transformer Pattern
Each `etl_*.py` follows:
1. **Input:** NVD/MITRE JSON/XML
2. **Process:** Parse → extract entities → write RDF triples (turtle_escape strings, subject_for_* URIs)
3. **Output:** Turtle (.ttl file)
4. **Example:** [etl_cpe.py](../src/etl/etl_cpe.py) — Platform + PlatformConfiguration classes

### Validation Pattern
1. **SHACL shapes** auto-selected via `--template`, `--owl`, or `--shapes` flag
2. **TEMPLATE_SHAPE_MAP** (src/core/validation.py) maps template names → shape files
3. **Output:** Validation report in artifacts/shacl-report-{timestamp}.json (conforms: true/false + detailed violations)

---

## Critical Do's & Don'ts

✅ **DO:**
- Preserve `CPE → CVEMatch → CVE → CWE → CAPEC → ATT&CK → Defense` causal chain
- Link versioning (CVSS v2.0, v3.1, v4.0) as separate classes—never merge
- Use approved RAG templates (docs/ontology/rag/RAG-traversal-templates.md) for graph queries
- Run validation before any Neo4j load
- Store raw files + manifests together in data/{standard}/

❌ **DON'T:**
- Modify core OWL modules to support extensions (extend instead)
- Invent properties not in official schema
- Create circular imports in ontology
- Skip validation between ETL and ingestion
- Free-form SPARQL/Cypher without approved templates

---

## Testing & CI Integration

```bash
# Unit tests + comprehensive ETL
pytest tests/test_phase3_comprehensive.py -v

# Single standard (when modifying etl_cpe.py, etc.)
pytest tests/test_etl_pipeline.py -v -k cpe

# Verify causal chain integrity
pytest tests/verify_causal_chain.py -v
```

All tests load samples from `data/{standard}/samples/` and validate against shapes in `docs/ontology/shacl/`.

---

## Common Tasks

**Add a new standard:** Follow [EXTENDING.md](../docs/EXTENDING.md) — OWL module + SHACL shapes + ETL transformer + test case.

**Modify ontology:** Update OWL → Markdown spec → SHACL → ETL tests. All in sync.

**Debug ETL failure:** Check logs/download_manager.log, review sample data in data/{standard}/samples/, run individual transformer with `--validate` flag.

**Check Neo4j readiness:** See [rdf_to_neo4j.py](../src/etl/rdf_to_neo4j.py) (pending) and [DEPLOYMENT.md](../docs/DEPLOYMENT.md).

---

## References
- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) — 5-phase roadmap + detailed specs
- [DAILY-DOWNLOAD-PIPELINE.md](../docs/DAILY-DOWNLOAD-PIPELINE.md) — Downloader orchestration
- [EXTENDING.md](../docs/EXTENDING.md) — Adding standards & extensions
- [docs/ontology/](../docs/ontology) — All specs, OWL, SHACL, RAG templates
