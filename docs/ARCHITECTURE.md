# KGCS Architecture & Roadmap

**Version:** 1.0  
**Date:** January 25, 2026  
**Status:** Phase 3 MVP (Neo4j integration pending)

---

## Project Vision

KGCS (Cybersecurity Knowledge Graph) is a **frozen, standards-backed ontology** that unifies nine MITRE security taxonomies into a single source of truth for AI systems to reason about vulnerabilities, attacks, defenses, and threat intelligence without hallucination.

**Core principle:** Every statement is traceable to an authoritative external standard (NVD, MITRE).

---

## 5-Phase Implementation Roadmap

### Phase 1: Frozen Core Ontology ✅ **COMPLETE**

**Duration:** Weeks 1–2  
**Status:** Production-ready  
**Deliverables:**

- 11 OWL modules (immutable, versioned)
  - Core bridge + 9 standard-specific modules (CPE, CVE, CVSS, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE)
- 1:1 mapping to official schemas (NVD 2.3, MITRE STIX 2.1)
- No circular imports (DAG structure)
- CVSS version separation (v2.0, v3.1, v4.0 coexist, never merged)

**Key invariant:** Causal chain maintained: `CPE → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}`

**Files:**
```
docs/ontology/owl/
├── core-ontology-v1.0.owl           (Core + bridge)
├── cpe-ontology.owl
├── cve-ontology.owl
├── cvss-ontology.owl
├── cwe-ontology.owl
├── capec-ontology.owl
├── attck-ontology.owl
├── d3fend-ontology.owl
├── car-ontology.owl
├── shield-ontology.owl
└── engage-ontology.owl
```

---

### Phase 2: SHACL Validation Framework ✅ **COMPLETE**

**Duration:** Weeks 3–4  
**Status:** Production-ready, CI integrated  
**Deliverables:**

- 25+ SHACL shape files (positive + negative test samples)
- Consolidated master bundle + per-standard shapes
- CI/CD workflow auto-detects OWL changes and validates
- Machine-readable validation reports to `artifacts/`
- Governance document (data policies, audit trail, rollback procedures)

**Testing:** 36+ test cases covering all standards

**Key workflow:**
```bash
# Single file validation
python scripts/validate_shacl_stream.py \
  --data data/cpe/samples/cpe-output.ttl \
  --shapes docs/ontology/shacl/cpe-shapes.ttl

# All samples (parametrized)
pytest tests/test_phase3_comprehensive.py -v
```

**Files:**
```
docs/ontology/shacl/
├── consolidated-shapes.ttl          (Master bundle)
├── cpe-shapes.ttl ... engage-shapes.ttl
└── samples/
    ├── *-good.ttl (positive tests)
    └── *-bad.ttl (negative tests)

docs/ontology/GOVERNANCE.md           (Policies + procedures)
```

---

### Phase 3: Data Ingestion & Neo4j MVP 🟢 **IN PROGRESS**

**Duration:** Weeks 5–7 (MVP) | Weeks 8–10 (full)  
**Status:** ETL complete, Neo4j loader pending  
**MVP Scope:** CPE + CVE + CWE + CAPEC + ATT&CK

**Deliverables (MVP):**

1. **ETL Transformers** ✅ Complete
   - JSON/STIX → RDF (Turtle) for all 9 standards
   - Idempotent transformers (same input → same output)
   - Preserves source hashes, timestamps, external IDs

2. **Streaming Validator** ✅ Complete
   - Chunks large files (tested with 222 MB CPE data)
   - SHACL validation per chunk
   - Reports to `artifacts/` with failure payloads

3. **Neo4j Loader** ⏳ Pending
   - Parse Turtle RDF → Cypher CREATE statements
   - Batch node/relationship creation (configurable batch size)
   - Auto-create indexes on standard IDs (cpeUri, cveId, cweId, etc.)
   - Graph constraints (unique, cardinality)

4. **Configuration Management** ✅ Complete
   - Environment-based setup (src/config.py)
   - Neo4j connection via .env file
   - ETL pipeline orchestration

**Key workflow:**
```bash
# Transform CPE JSON to RDF
python -m src.etl.etl_cpe \
  --input data/cpe/samples/sample_cpe.json \
  --output tmp/cpe-output.ttl \
  --validate

# Load into Neo4j (pending implementation)
python src/etl/rdf_to_neo4j.py \
  --ttl tmp/cpe-output.ttl \
  --batch-size 1000
```

**Files:**
```
src/etl/
├── etl_cpe.py, etl_cve.py, etl_cwe.py, ...
├── etl_cpematch.py                  (Matches expansion)
└── rdf_to_neo4j.py                  (Loader, pending)

src/config.py                         (Neo4j + ETL config)

tests/
├── test_etl_pipeline.py              (Single standard)
└── test_phase3_comprehensive.py      (All 9 standards)
```

**Critical invariant:** `PlatformConfiguration` (version/update) ≠ `Platform` (atomic CPE)

---

### Phase 4: Extensions & Contextual Reasoning 🔵 **DESIGNED**

**Duration:** Weeks 8–10  
**Status:** Spec complete, implementation pending  
**Scope:** Add temporal, contextual, subjective layers WITHOUT modifying core

**Deliverables:**

1. **Incident Extension**
   - Observed techniques, detections, evidence
   - Temporal tracking (when/where observed)
   - Never asserts ground truth

2. **Risk Extension**
   - Risk assessments, scenarios, decisions
   - Only layer where subjectivity allowed
   - Decision types: ACCEPT, MITIGATE, TRANSFER, AVOID

3. **ThreatActor Extension**
   - Attribution claims, capabilities, tools
   - Always includes confidence level
   - Never asserts ground truth

**Key principle:** Extensions import core only (one-way flow); core never modified to support extensions.

**Files:**
```
docs/ontology/extensions/
├── incident-extension.owl
├── risk-extension.owl
└── threatactor-extension.owl

src/extensions/
├── incident.py
├── risk.py
└── threatactor.py
```

---

### Phase 5: RAG Safety & Query API 🔵 **PLANNED**

**Duration:** Weeks 11–12  
**Status:** Spec complete, implementation pending  
**Scope:** Ensure LLM reasoning follows approved paths only

**Deliverables:**

1. **RAG Traversal Templates**
   - T1–T7: Pre-approved reasoning paths (documented + reviewed)
   - Core templates: Core chain (CPE→CVE→CWE→CAPEC→ATT&CK→Defenses)
   - Extension templates: Cross-layer reasoning (Incident→Risk→ThreatActor)

2. **Query Validator**
   - Runtime checks: LLM queries only use approved templates
   - Reject freeform paths that skip causal chain or mix standards without provenance
   - Flag hallucination patterns

3. **Query API**
   - REST endpoints: `/query/{template_id}`
   - Neo4j Cypher or SPARQL backend
   - Evidence + provenance in every response

**Key principle:** LLM reasoning is **templated, not freeform**.

**Files:**
```
docs/ontology/rag/
├── RAG-traversal-templates.md
├── RAG-traversal-templates-extension.md
└── examples/

src/rag/
├── validator.py                     (Runtime path check)
└── query_api.py                     (REST endpoints)
```

---

## Critical Design Principles

### 1. Authoritativeness
- Every ontology class maps 1:1 to a stable ID in NVD or MITRE
- If a standard doesn't define it, we don't model it
- Extensions are for subjective/contextual data only

### 2. Immutability of Core
- Phase 1 OWL modules are **frozen** (no modifications post-release)
- Changes require versioning + deprecation period
- Extensions add layers; never override core

### 3. Explicit Provenance
- Every edge is traceable to source data or extension rule
- Never fabricate relationships to "complete the graph"
- All statements must include source field (cveId, techniqueId, etc.)

### 4. No Hallucination
- RAG queries follow pre-approved templates only
- LLM responses include evidence + source IDs
- Query validation prevents shortcuts in causal chain

### 5. One-Way Import Flow
- Core imports external standards only
- Extensions import core only
- No circular dependencies (DAG structure)

---

## Folder Structure (Current)

```text
KGCS/
├── .github/
│   ├── copilot-instructions.md       (AI agent guidance)
│   ├── workflows/shacl-validation.yml (CI gate)
│   └── PULL_REQUEST_TEMPLATE/
├── docs/
│   ├── ARCHITECTURE.md               (This file)
│   ├── GLOSSARY.md                   (Standard definitions) ← NEW
│   ├── DEPLOYMENT.md                 (Neo4j setup) ← NEW
│   ├── EXTENDING.md                  (Add new standards) ← NEW
│   ├── KGCS.md                       (Executive summary)
│   ├── README.md                     (Quick start)
│   ├── PROJECT-STATUS-SUMMARY.md     (Latest status)
│   ├── ontology/
│   │   ├── owl/                      (11 frozen OWL modules)
│   │   ├── shacl/                    (Validation shapes + samples)
│   │   ├── rag/                      (Approved traversal templates)
│   │   ├── extensions/               (Incident, Risk, ThreatActor)
│   │   ├── GOVERNANCE.md             (Data policies)
│   │   └── *-ontology-v1.0.md        (Human-readable specs)
│   └── .archive/                     (Old docs: draft/, wip-status/, agent/)
├── src/
│   ├── config.py                     (Configuration)
│   ├── core/validation.py            (SHACL validator)
│   ├── etl/                          (9 transformers + Neo4j loader)
│   ├── extensions/                   (Phase 4+)
│   └── rag/                          (Phase 5+)
├── tests/
│   ├── test_etl_pipeline.py
│   └── test_phase3_comprehensive.py
├── scripts/
│   ├── validate_shacl_stream.py
│   └── validate_etl_pipeline_order.py
├── data/
│   └── */samples/                    (Small test data)
├── artifacts/                        (Generated reports)
├── tmp/                              (Working files)
└── logs/                             (Application logs)
```

---

## Next Steps

### Immediate (Phase 3 MVP, Weeks 5–7)
- [ ] Implement Neo4j loader (Turtle → Cypher)
- [ ] Create graph constraints + indexes
- [ ] End-to-end tests (ETL → SHACL → Neo4j)
- [ ] Update CI pipeline for ingestion

### Short-term (Phase 3 Full, Weeks 8–10)
- [ ] Complete all 9 ETL transformers
- [ ] Test production-scale data (222 MB CPE + CVE)
- [ ] Finalize data quality metrics

### Medium-term (Phase 4, Weeks 11–12)
- [ ] Implement extensions (Incident, Risk, ThreatActor)
- [ ] Extension-to-core loading
- [ ] Cross-layer traversals

### Long-term (Phase 5, Weeks 13–14)
- [ ] RAG traversal validator
- [ ] Query API
- [ ] LLM integration + safety enforcement

---

## References

- [GOVERNANCE.md](ontology/GOVERNANCE.md) — Data policies, audit, rollback
- [copilot-instructions.md](../.github/copilot-instructions.md) — AI agent guide
- [RAG-traversal-templates.md](ontology/rag/RAG-traversal-templates.md) — Approved paths
- [ZERO-START-ARCHITECTURE.md](ZERO-START-ARCHITECTURE.md) — Detailed structure review
- [CLEANUP-CHECKLIST.md](CLEANUP-CHECKLIST.md) — File-by-file decisions

