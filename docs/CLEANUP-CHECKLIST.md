# Quick Reference: Current vs. Zero-Start Folder Structure

**Purpose:** Side-by-side comparison for decision-making

---

## Current Structure (Evolved, ~100+ files)

```text
docs/
├── agent/ (5 files)                ❌ REMOVE — Merge into .github/
│   ├── kopilot-instruktions.md (misspelled, redundant)
│   ├── lead-software-architect.md (off-topic)
│   └── [3 more]
├── draft/ (9 files)                ❌ REMOVE — Extract essentials
│   ├── mini-draft.md (1200+ lines, merged ERDs)
│   ├── standards_datamodel_draft.md (superseded)
│   ├── attck-draft.md (→ attck-ontology-v1.0.md)
│   ├── cwe-draft.md (→ cwe-ontology-v1.0.md)
│   └── [5 more]
├── wip-status/ (4 files)           ⚠️ REPLACE — Summarize
│   ├── PHASE-1-COMPLETE.md (→ PROJECT-STATUS-SUMMARY.md)
│   ├── PHASE-2-COMPLETE.md (→ PROJECT-STATUS-SUMMARY.md)
│   ├── PHASE-2-QUICK-START.md (→ README.md "Quick Start")
│   └── PHASE-2-GOVERNANCE.md (→ docs/ontology/GOVERNANCE.md)
└── ontology/ (✅ KEEP)
    ├── owl/ (11 OWL modules, FROZEN)
    ├── shacl/ (25+ SHACL shapes + samples)
    ├── rag/ (traversal templates)
    ├── extensions/ (Incident, Risk, ThreatActor stubs)
    └── *-ontology-v1.0.md (7 human-readable specs)
```

## Recommended Zero-Start Structure (Clean, ~65 files)

```text
docs/
├── KGCS.md                          (Executive summary)
├── ARCHITECTURE.md                  ← NEW: 5-phase roadmap + milestones
├── GLOSSARY.md                      ← NEW: Standard definitions + relationships
├── DEPLOYMENT.md                    ← NEW: Neo4j + CI/CD setup
├── EXTENDING.md                     ← NEW: How to add new standards
│
└── ontology/ (✅ KEEP)
    ├── README.md
    ├── GOVERNANCE.md                ← Moved from wip-status/
    ├── owl/ (11 OWL modules, FROZEN)
    ├── shacl/
    │   ├── README.md
    │   ├── consolidated-shapes.ttl
    │   ├── *-shapes.ttl (per-standard)
    │   └── samples/ (positive + negative)
    ├── rag/
    │   ├── README.md
    │   ├── RAG-traversal-templates.md
    │   └── RAG-traversal-templates-extension.md
    ├── extensions/
    │   ├── incident-extension.owl
    │   ├── risk-extension.owl
    │   └── threatactor-extension.owl
    └── [Standard specs]
        ├── cpe-ontology-v1.0.md
        ├── cve-ontology-v1.0.md
        └── [5+ more]
```

**Files deleted:** ~35  
**Files added:** ~4  
**Net reduction:** ~31 files (-31%)

---

## File-by-File Decision Matrix

| Current File | Status | Recommendation | Action |
| --- | --- | --- | --- |
| `docs/agent/kopilot-instruktions.md` | ❌ Misspelled, redundant | Remove | `git rm` |
| `docs/agent/lead-software-architect.md` | ❌ Off-topic | Remove | `git rm` |
| `docs/draft/mini-draft.md` | ❌ 1200+ lines of old ERDs | Archive | `git mv → .archive/` |
| `docs/draft/standards_datamodel_draft.md` | ❌ Superseded | Archive | `git mv → .archive/` |
| `docs/draft/attck-draft.md` | ❌ → `docs/ontology/attck-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/draft/cwe-draft.md` | ❌ → `docs/ontology/cwe-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/draft/cpe-draft.md` | ❌ → `docs/ontology/cpe-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/draft/capec-draft.md` | ❌ → `docs/ontology/capec-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/draft/car-draft.md` | ❌ → `docs/ontology/car-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/draft/d3fend-draft.md` | ❌ → `docs/ontology/d3fend-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/draft/engage-draft.md` | ❌ → `docs/ontology/engage-ontology-v1.0.md` | Archive | `git mv → .archive/` |
| `docs/wip-status/PHASE-1-COMPLETE.md` | ⚠️ Info merged elsewhere | Consolidate | Extract key points → `PROJECT-STATUS-SUMMARY.md` |
| `docs/wip-status/PHASE-2-COMPLETE.md` | ⚠️ Info merged elsewhere | Consolidate | Extract key points → `PROJECT-STATUS-SUMMARY.md` |
| `docs/wip-status/PHASE-2-QUICK-START.md` | ⚠️ Commands → README | Consolidate | Extract "Quick Start" → `README.md` section |
| `docs/wip-status/PHASE-2-GOVERNANCE.md` | ✅ Essential | Move | `git mv → docs/ontology/GOVERNANCE.md` |
| `docs/ontology/owl/` | ✅ FROZEN | Keep | No changes |
| `docs/ontology/shacl/` | ✅ Essential | Keep | No changes |
| `docs/ontology/rag/` | ✅ Essential | Keep | No changes |
| `docs/ontology/*-ontology-v1.0.md` | ✅ Essential | Keep | No changes |
| `.github/copilot-instructions.md` | ✅ Consolidated | Keep | No changes (updated Jan 25) |
| `.github/workflows/shacl-validation.yml` | ✅ Essential | Keep | No changes |
| `README.md` | ✅ Essential | Keep | Add "Quick Start" section |
| `PROJECT-STATUS-SUMMARY.md` | ✅ Essential | Keep | Consolidate wip-status updates |
| `src/etl/` | ✅ Essential | Keep | No changes |
| `src/config.py` | ✅ Essential | Keep | No changes |
| `tests/` | ✅ Essential | Keep | No changes |
| `scripts/validate_*.py` | ✅ Essential | Keep | No changes |

---

## What Gets Consolidated into What

### 1. wip-status/ Content

```text
PHASE-1-COMPLETE.md         → Summarized in PROJECT-STATUS-SUMMARY.md (section: "Phase 1 ✅")
PHASE-2-COMPLETE.md         → Summarized in PROJECT-STATUS-SUMMARY.md (section: "Phase 2 ✅")
PHASE-2-QUICK-START.md      → New README.md section "Quick Start"
PHASE-2-GOVERNANCE.md       → docs/ontology/GOVERNANCE.md (already referenced)
```

### 2. draft/ Content

```text
mini-draft.md               → Extract ERD → docs/GLOSSARY.md; Archive rest
standards_datamodel_draft.md → Extract diagram → docs/GLOSSARY.md; Archive rest
*-draft.md files            → Already have *-ontology-v1.0.md (more authoritative)
```

### 3. agent/ Content

```text
kopilot-instruktions.md     → Already merged into .github/copilot-instructions.md
lead-software-architect.md  → Addressed in .github/copilot-instructions.md "Working rules"
```

---

## Quick Cleanup Script (Git-Safe)

```bash
#!/bin/bash
# Archive old WIP and draft directories (keeps git history)

# Move entire directories to .archive
mkdir -p docs/.archive
git mv docs/draft/ docs/.archive/draft-$(date +%Y%m%d)
git mv docs/wip-status/ docs/.archive/wip-status-$(date +%Y%m%d)
git mv docs/agent/ docs/.archive/agent-$(date +%Y%m%d)

# Commit with clear message
git commit -m "chore: archive preliminary docs to .archive/

- Moved draft/ specs (superseded by ontology/*.md)
- Moved wip-status/ (info merged into PROJECT-STATUS-SUMMARY.md)
- Moved agent/ (merged into .github/copilot-instructions.md)

See docs/.archive/ for historical context."

# Git history preserved; can restore with: git checkout HEAD~1 -- docs/draft/
```

---

## Existing Files That Are Already Optimal

✅ These need **no changes**:

```text
.github/
├── copilot-instructions.md (comprehensive, updated Jan 25)
├── workflows/shacl-validation.yml (CI gate, auto-detects OWL changes)
└── PULL_REQUEST_TEMPLATE/phase3-checklist.md (governance + checklist)

docs/ontology/
├── owl/ (11 frozen OWL modules)
├── shacl/ (25+ validation shapes + samples)
├── rag/ (approved traversal templates)
├── extensions/ (Incident, Risk, ThreatActor stubs)
└── *-ontology-v1.0.md (human-readable specs, authoritative)

src/
├── etl/ (9 transformers + Neo4j loader)
├── config.py (environment-based config)
└── core/validation.py (SHACL validator)

tests/
├── test_etl_pipeline.py
└── test_phase3_comprehensive.py

scripts/
├── validate_shacl_stream.py (chunked validation)
└── validate_etl_pipeline_order.py (orchestrator)

data/
└── */samples/ (small, deterministic test data)

ROOT
├── README.md (good overview)
├── PROJECT-STATUS-SUMMARY.md (current status)
├── requirements.txt (dependencies)
└── .gitignore (sensible defaults)
```

---

## New Files to Create (Optional but Recommended)

For clarity in a zero-start scenario:

```text
docs/
├── ARCHITECTURE.md                  (5-phase roadmap + milestones)
├── GLOSSARY.md                      (Standard definitions + diagram)
├── EXTENDING.md                     (How to add new standards)
└── DEPLOYMENT.md                    (Neo4j setup + CI/CD)
```

---

## Rough Effort Estimate

| Task | Effort | Notes |
| --- | --- | --- |
| Archive docs/draft → .archive/ | 5 min | `git mv` commands |
| Archive docs/wip-status → .archive/ | 5 min | `git mv` commands |
| Archive docs/agent → .archive/ | 5 min | `git mv` commands |
| Move PHASE-2-GOVERNANCE.md → docs/ontology/ | 2 min | `git mv` |
| Consolidate wip-status into PROJECT-STATUS-SUMMARY.md | 10 min | Copy + summarize key points |
| Add "Quick Start" section to README.md | 10 min | Extract from PHASE-2-QUICK-START.md |
| Create docs/ARCHITECTURE.md (NEW) | 20 min | Adapt from README + PROJECT-STATUS |
| Create docs/GLOSSARY.md (NEW) | 20 min | Extract ERD from mini-draft.md |
| Create docs/EXTENDING.md (NEW) | 15 min | Write how-to guide |
| Create docs/DEPLOYMENT.md (NEW) | 20 min | Write setup instructions |
| **Total** | **~2 hours** | Mostly straightforward moves + light writing |

---

## Summary

| Aspect | Current | Zero-Start | Benefit |
| --- | --- | --- | --- |
| Total files | ~110 | ~70 | -36% clutter |
| Essential files | ~40 | ~40 | No loss of function |
| Redundant docs | ~35 | ~0 | Easier to find truth |
| Phase clarity | Scattered | Organized | Better onboarding |
| Maintenance burden | High | Low | Less to update |

**Recommendation:** Start fresh with the recommended structure. The archive is kept safe in git history.
