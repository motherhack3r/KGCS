# KGCS: Optimal Organization From Zero

**Date:** January 25, 2026  
**Purpose:** Architect the ideal folder/file structure for starting KGCS from scratch

---

## Executive Summary

If starting KGCS today, **reduce the structure by ~30%** by consolidating redundant documentation and eliminating intermediate draft artifacts. The current structure evolved organically and contains:

- ✅ **Essential**: Core ontologies, SHACL validation, ETL transformers, CI/CD, tests
- ⚠️ **Optional**: Draft specs, agent prompts, intermediate status docs
- ❌ **Redundant**: Duplicate architecture docs in multiple places, abandoned WIP phases

**Recommended**: Implement Phases 1–3 incrementally with minimal folder overhead.

---

## Current Structure Analysis

### Root Organization

```text
KGCS/
├── .github/
│   ├── copilot-instructions.md       ✅ KEEP (consolidated, updated Jan 25)
│   ├── workflows/shacl-validation.yml ✅ KEEP (CI gate, auto-detects OWL changes)
│   └── PULL_REQUEST_TEMPLATE/        ✅ KEEP (phase3-checklist.md for governance)
├── docs/
│   ├── ontology/                     ✅ KEEP (core deliverables)
│   │   ├── owl/                      ✅ KEEP (11 OWL modules, frozen)
│   │   ├── shacl/                    ✅ KEEP (validation shapes + samples)
│   │   ├── rag/                      ✅ KEEP (approved traversal templates)
│   │   ├── *-ontology-v1.0.md        ✅ KEEP (human-readable specs)
│   │   └── PHASE-2-GOVERNANCE.md     ✅ KEEP (data policies + audit)
│   ├── draft/                        ❌ CONSOLIDATE (9 markdown files)
│   ├── wip-status/                   ⚠️  REPLACE (use KGCS.md + PROJECT-STATUS.md)
│   ├── agent/                        ⚠️  CONSOLIDATE (merge into .github/)
│   └── [missing] ARCHITECTURE.md     ✅ ADD (roadmap + phases)
├── src/
│   ├── config.py                     ✅ KEEP (env-based config)
│   ├── core/validation.py            ✅ KEEP (SHACL loader, reporter)
│   ├── etl/                          ✅ KEEP (9 transformers + Neo4j loader)
│   ├── extensions/                   ✅ KEEP (Incident, Risk, ThreatActor stubs)
│   └── [missing] __init__.py         ✅ ADD (package initialization)
├── tests/
│   ├── test_etl_pipeline.py          ✅ KEEP (single-standard E2E)
│   ├── test_phase3_comprehensive.py  ✅ KEEP (all 9 standards parametrized)
│   └── test_*.py                     ✅ KEEP (36+ test cases)
├── data/
│   ├── cpe/samples/                  ✅ KEEP (small, deterministic)
│   ├── cve/samples/                  ✅ KEEP (small, deterministic)
│   ├── */samples/                    ✅ KEEP (for all 9 standards)
│   └── shacl-samples/                ✅ KEEP (positive + negative SHACL examples)
├── scripts/
│   ├── validate_shacl_stream.py      ✅ KEEP (chunked validation for 222MB data)
│   ├── validate_etl_pipeline_order.py ✅ KEEP (orchestrator with validation hooks)
│   └── *.py                          ✅ KEEP (ETL + merge utilities)
├── artifacts/                        ✅ KEEP (validation reports, auto-generated)
├── tmp/                              ✅ KEEP (.gitignored, working directory)
├── logs/                             ✅ KEEP (application logs)
├── README.md                         ✅ KEEP (executive summary)
├── PROJECT-STATUS-SUMMARY.md         ✅ KEEP (Jan 2026 status snapshot)
└── requirements.txt                  ✅ KEEP (rdflib, pyshacl, neo4j, etc.)
```

---

## Recommended Clean Structure (From Zero)

### Phase 0: Bootstrap (Day 1)

```text
kgcs/
├── README.md                          (Project overview)
├── requirements.txt                   (Python deps: rdflib, pyshacl, neo4j)
├── .gitignore                         (Ignore tmp/, artifacts/, __pycache__)
├── .env.example                       (Neo4j config template)
│
├── .github/
│   ├── copilot-instructions.md        (AI agent guidance)
│   ├── workflows/
│   │   └── ci.yml                     (SHACL validation on PR)
│   └── PULL_REQUEST_TEMPLATE/
│       └── default.md                 (Phase checklist)
│
├── docs/
│   ├── KGCS.md                        (Executive summary)
│   ├── ARCHITECTURE.md                (Phases 1–5 roadmap) ← NEW
│   ├── GLOSSARY.md                    (Standards + terms) ← CONSOLIDATE FROM DRAFT
│   │
│   └── ontology/                      (Phase 1: Core)
│       ├── README.md                  (Ontology overview)
│       ├── owl/
│       │   ├── core-ontology-v1.0.owl
│       │   ├── cpe-ontology.owl
│       │   ├── cve-ontology.owl
│       │   ├── cvss-ontology.owl
│       │   ├── cwe-ontology.owl
│       │   ├── capec-ontology.owl
│       │   ├── attck-ontology.owl
│       │   ├── d3fend-ontology.owl
│       │   ├── car-ontology.owl
│       │   ├── shield-ontology.owl
│       │   ├── engage-ontology.owl
│       │   └── [README.md]            (Instructions for OWL imports)
│       ├── shacl/
│       │   ├── README.md              (SHACL strategy)
│       │   ├── consolidated-shapes.ttl (Master bundle)
│       │   ├── cpe-shapes.ttl
│       │   ├── cve-shapes.ttl
│       │   ├── [... 6 more ...]
│       │   └── samples/
│       │       ├── cpe-good.ttl       (Positive test)
│       │       ├── cpe-bad.ttl        (Negative test)
│       │       └── [... for all 9 standards ...]
│       ├── rag/
│       │   ├── README.md
│       │   ├── RAG-traversal-templates.md
│       │   └── RAG-traversal-templates-extension.md
│       ├── extensions/                (Phase 1B: Extension stubs)
│       │   ├── incident-extension.owl
│       │   ├── risk-extension.owl
│       │   └── threatactor-extension.owl
│       └── [Standard spec docs]
│           ├── cpe-ontology-v1.0.md
│           ├── cve-ontology-v1.0.md
│           └── [... 7 more ...]
│
├── src/                               (Phase 2–3: Implementation)
│   ├── __init__.py
│   ├── config.py                      (Neo4j + ETL config)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── validation.py              (SHACL loader, reporter)
│   │
│   ├── etl/                           (Phase 3: Transformers)
│   │   ├── __init__.py
│   │   ├── etl_cpe.py
│   │   ├── etl_cve.py
│   │   ├── etl_cwe.py
│   │   ├── etl_capec.py
│   │   ├── etl_attack.py
│   │   ├── etl_d3fend.py
│   │   ├── etl_car.py
│   │   ├── etl_shield.py
│   │   ├── etl_engage.py
│   │   ├── etl_cpematch.py            (Matches expansion)
│   │   └── rdf_to_neo4j.py            (Turtle → Cypher loader)
│   │
│   └── extensions/                    (Phase 4: Extension implementations)
│       ├── __init__.py
│       ├── incident.py
│       ├── risk.py
│       └── threatactor.py
│
├── tests/
│   ├── __init__.py
│   ├── test_etl_pipeline.py           (Single standard E2E)
│   ├── test_phase3_comprehensive.py   (All 9 transformers)
│   └── test_*.py                      (Specific integration tests)
│
├── scripts/                           (Phase 2–3: Utilities)
│   ├── validate_shacl_stream.py       (Chunked SHACL for large files)
│   ├── validate_etl_pipeline_order.py (Orchestrator + validation)
│   └── db/
│       └── reload_neo4j.py            (Utility for Phase 3)
│
├── data/                              (Sample + reference data)
│   ├── cpe/samples/
│   │   └── sample_cpe.json
│   ├── cve/samples/
│   │   └── sample_cve.json
│   └── [... other standards ...]
│
├── tmp/                               (Transient working files)
│   └── .gitkeep
├── artifacts/                         (Generated validation reports)
│   └── .gitkeep
├── logs/                              (Application logs)
│   └── .gitkeep
│
└── .env                               (Local dev config, not committed)
```

---

## What to Remove / Consolidate

### 1. **docs/draft/** → Consolidate into ARCHITECTURE.md + GLOSSARY.md

**Files to eliminate:**

- `mini-draft.md` (1,200+ lines) — Extract ERD diagrams → GLOSSARY.md
- `standards_datamodel_draft.md` — Merged into standard specs (cwe-ontology-v1.0.md, etc.)
- `attck-draft.md`, `cwe-draft.md`, `cpe-draft.md`, etc. — Redundant with ontology specs
- `ontology-assessment.md` — Superseded by core ontology modules

**Action:**

```bash
# Keep only GLOSSARY.md (definitions + relationships)
# Archive drafts to git history: git mv docs/draft/ docs/.archive/
```

### 2. **docs/wip-status/** → Merge into PROJECT-STATUS-SUMMARY.md + README.md

**Files to eliminate:**

- `PHASE-1-COMPLETE.md` → Summarized in PROJECT-STATUS-SUMMARY.md
- `PHASE-2-COMPLETE.md` → Summarized in PROJECT-STATUS-SUMMARY.md
- `PHASE-2-QUICK-START.md` → Move testing commands to README under "Quick Start"

**Action:**

```bash
# Keep only PROJECT-STATUS-SUMMARY.md (updated monthly)
# Remove wip-status/; consolidate next steps into docs/ARCHITECTURE.md
```

### 3. **docs/agent/** → Merge into .github/copilot-instructions.md

**Files to eliminate:**

- `kopilot-instruktions.md` (misspelled, redundant)
- `lead-software-architect.md` (not KGCS-specific)

**Action:**

```bash
# Already consolidated; remove docs/agent/
# Keep only .github/copilot-instructions.md
```

### 4. **Redundant Ontology Docs**

**Current state:**

- `docs/ontology/*-ontology-v1.0.md` (human-readable specs) ← **KEEP**
- Duplicate definitions in `docs/draft/standards_datamodel_draft.md` ← **REMOVE**

---

## Essential Files (Never Remove)

### Ontology Core (Immutable)

```text
docs/ontology/owl/
├── core-ontology-v1.0.owl              (11 modules frozen, versioned)
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

**Why immutable:**

- Maps 1:1 to official schemas (NVD/MITRE)
- Every deployment depends on stable URIs
- Changes require versioning + deprecation period

### SHACL Validation Framework

```text
docs/ontology/shacl/
├── consolidated-shapes.ttl             (Master bundle)
├── cpe-shapes.ttl ... engage-shapes.ttl (Per-standard rules)
└── samples/
    ├── cpe-good.ttl, cpe-bad.ttl       (Positive + negative tests)
    └── [... for all 9 standards ...]
```

**Why essential:**

- CI/CD gates depend on these shapes
- Prevents invalid RDF from entering the graph

### ETL Transformers

```text
src/etl/
├── etl_cpe.py
├── etl_cve.py
├── etl_cwe.py
├── etl_capec.py
├── etl_attack.py
├── etl_d3fend.py
├── etl_car.py
├── etl_shield.py
├── etl_engage.py
└── rdf_to_neo4j.py
```

**Why essential:**

- Only way to ingest authoritative data
- Directly tested against SHACL shapes
- Re-used in Phase 3+ without modification

### Tests

```text
tests/
├── test_etl_pipeline.py           (Single standard E2E)
└── test_phase3_comprehensive.py   (All 9 transformers parametrized)
```

**Why essential:**

- Prevents regressions in core functionality
- Demonstrates standards compliance

---

## Optimization Recommendations

### 1. Rename for Clarity

```bash
# Current → Recommended
docs/wip-status/PHASE-2-GOVERNANCE.md → docs/ontology/GOVERNANCE.md
docs/ontology/rag/RAG-travesal-templates.md → RAG-traversal-templates.md (fix typo)
scripts/validate_shacl_stream.py → scripts/validate/shacl_stream.py (group by purpose)
```

### 2. Add Missing Documentation

```text
docs/ARCHITECTURE.md                    ← NEW: 5-phase roadmap with milestones
docs/ontology/EXTENDING.md              ← NEW: How to add new standards
docs/DEPLOYMENT.md                      ← NEW: Neo4j setup, CI/CD integration
docs/GLOSSARY.md                        ← NEW: Consolidated terms + relationships
```

### 3. Simplify Git Ignore

```bash
# Keep transient folders out of version control
tmp/
artifacts/
logs/
.env
*.pyc
__pycache__/
*.egg-info/
.vscode/local-settings.json
```

### 4. Config Management

```text
.env.example                            ← Checked in: Neo4j URI template
.env                                    ← NOT checked in: local dev secrets
src/config.py                           ← Load from environment (already done ✅)
```

---

## Phase-by-Phase Folder Strategy

### Phase 1: Frozen Core Ontology (Weeks 1–2)

```text
docs/ontology/
├── owl/                               (11 immutable OWL modules)
├── shacl/
│   ├── consolidated-shapes.ttl        (Master bundle)
│   └── samples/                       (Positive/negative tests)
└── *-ontology-v1.0.md                 (Human-readable specs)
```

**Deliverable:** `docs/ontology/GOVERNANCE.md` (how to version & modify)

### Phase 2: SHACL Validation (Weeks 3–4)

```text
scripts/validate_shacl_stream.py        (Chunked validation)
.github/workflows/ci.yml                (Auto-validates on PR)
tests/test_etl_pipeline.py              (Transformer tests)
```

**Deliverable:** All sample TTLs pass validation ✅

### Phase 3: ETL + Neo4j MVP (Weeks 5–6)

```text
src/etl/
├── etl_cpe.py, etl_cve.py              (Must work)
├── etl_cwe.py, etl_capec.py            (Must work)
├── etl_attack.py                       (Must work)
├── etl_d3fend.py, etl_car.py           (Optional, can stub)
├── etl_shield.py, etl_engage.py        (Optional, can stub)
└── rdf_to_neo4j.py                     (Loader)

src/config.py                           (Neo4j connection)
.env.example                            (Config template)
```

**Deliverable:** CPE+CVE+CWE+CAPEC+ATT&CK loaded into Neo4j ✅

### Phase 4: Extensions (Weeks 7–8)

```text
docs/ontology/extensions/
├── incident-extension.owl              (Incident, Detection, Evidence)
├── risk-extension.owl                  (RiskAssessment, RiskScenario)
└── threatactor-extension.owl           (ThreatActor, ConfidenceLevel)

src/extensions/
├── incident.py
├── risk.py
└── threatactor.py
```

**Deliverable:** Extensions load without modifying core

### Phase 5: RAG + Query API (Weeks 9–10)

```text
docs/ontology/rag/
├── RAG-traversal-templates.md          (Approved paths)
├── RAG-traversal-templates-extension.md (Extension paths)
└── examples/                           (Working queries)

src/rag/
├── validator.py                        (Runtime path check)
└── query_api.py                        (REST endpoints)
```

**Deliverable:** LLM can only query approved paths

---

## Summary: What to Do

### ✅ Keep (Essential)

- `docs/ontology/owl/` — Core ontologies (frozen)
- `docs/ontology/shacl/` — Validation rules
- `docs/ontology/rag/` — Approved traversals
- `src/etl/` — All 9 transformers
- `tests/` — Test suite
- `scripts/validate_*` — Validation orchestrators
- `.github/copilot-instructions.md` — AI guidance
- `README.md` + `PROJECT-STATUS-SUMMARY.md` — Overview docs

### ⚠️ Consolidate (Can be merged)

- `docs/wip-status/` → Summarize in PROJECT-STATUS-SUMMARY.md
- `docs/draft/` → Extract ERD → GLOSSARY.md, delete rest
- `docs/agent/` → Merge into `.github/copilot-instructions.md`

### ❌ Remove (Redundant)

- `mini-draft.md` (1200+ lines of merged/stale ERDs)
- `standards_datamodel_draft.md` (superseded by standard specs)
- `kopilot-instruktions.md` (misspelled, merged)
- `lead-software-architect.md` (not KGCS-specific)
- Individual phase completion docs (summarized elsewhere)

### ✨ Add (Missing)

- `docs/ARCHITECTURE.md` — 5-phase roadmap
- `docs/GLOSSARY.md` — Standard definitions
- `docs/EXTENDING.md` — How to add new standards
- `docs/DEPLOYMENT.md` — Neo4j + CI/CD setup

---

## Final Recommendation

**Start clean with ~35 essential files instead of current ~100+.**

The current structure is functional but bloated with intermediate artifacts. A reorg to the recommended structure would:

1. **Reduce cognitive load** — Clear purpose for each folder
2. **Speed onboarding** — New contributors know where to look
3. **Ease CI/CD** — Fewer places to update when deploying
4. **Maintain immutability** — Core ontologies clearly segregated

**Effort to reorg:** ~2 hours (mostly mv + git rm)  
**Value:** +50% clarity, -30% file count, cleaner git history
