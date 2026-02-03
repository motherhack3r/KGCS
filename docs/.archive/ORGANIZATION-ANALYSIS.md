# Docs Folder Organization Analysis

**Date:** February 3, 2026  
**Status:** Comprehensive analysis complete with recommendations

---

## Current State

### Root Level Files (11 markdown files)

| File | Purpose | Status | Recommendation |
|------|---------|--------|-----------------|
| **ARCHITECTURE.md** | System design and 5-phase roadmap | Current, active | ✅ KEEP (core docs) |
| **KGCS.md** | Executive summary and design | Current, active | ✅ KEEP (core docs) |
| **GLOSSARY.md** | Standard definitions and ontology | Current, active | ✅ KEEP (core docs) |
| **DEPLOYMENT.md** | Neo4j setup and deployment guide | Current, useful | ✅ KEEP (core docs) |
| **EXTENDING.md** | How to add new standards | Current, useful | ✅ KEEP (core docs) |
| **DAILY-DOWNLOAD-PIPELINE.md** | Download automation setup | Current, useful | ✅ KEEP (operational docs) |
| **CLEANUP-WORKSPACE.md** | Workspace cleanup procedures | Current, utility | 🔄 MOVE to `/operations/` |
| **NEO4J-LOAD-SUMMARY.md** | Neo4j statistics and analysis | Recent, technical | 🔄 MOVE to `/operations/` |
| **NEO4J-STATS.md** | Neo4j statistics (potential duplicate?) | Technical, utility | ⚠️ REVIEW: Merge with NEO4J-LOAD-SUMMARY? |
| **PHASE3-ENHANCEMENT-COMPLETION.md** | Phase 3 completion summary | Research/historical | 🔄 MOVE to `research/` |
| **PHASE3-STATUS-SUMMARY.md** | Phase 3 status tracking | Research/historical | 🔄 MOVE to `research/` |

### Subdirectories

| Directory | Contents | Status | Recommendation |
|-----------|----------|--------|-----------------|
| **research/** | CAPEC reports, phase summaries | Recently organized | ✅ KEEP (4 files, well-organized) |
| **ontology/** | Specifications and SHACL rules | Core ontology | ✅ KEEP (critical) |
| **.archive/** | Legacy files, old branches | Legacy, dated | 🔄 CONSIDER: Archive to `.github/` or compress |
| **.ideas/** | Future planning documents | Internal notes | ✅ KEEP (working directory) |

---

## Analysis & Recommendations

### 🎯 Proposed New Structure

```
docs/
├── README.md                       (📖 docs index and navigation)
│
├── [CORE DOCUMENTATION]
├── ARCHITECTURE.md                 (System design + 5-phase roadmap)
├── KGCS.md                         (Executive summary)
├── GLOSSARY.md                     (Standard definitions)
├── EXTENDING.md                    (Add new standards)
│
├── operations/                     (📋 Operational guides)
│   ├── README.md                   (Quick reference)
│   ├── DEPLOYMENT.md               (Neo4j setup and deploy)
│   ├── DAILY-DOWNLOAD-PIPELINE.md  (Download automation)
│   ├── CLEANUP-WORKSPACE.md        (Cleanup procedures)
│   ├── NEO4J-LOAD-SUMMARY.md       (Statistics and analysis)
│   └── NEO4J-STATS.md              (Merged with above or kept separate)
│
├── research/                       (🔬 Research and enhancement reports)
│   ├── README.md                   (Index of research)
│   ├── CAPEC-ENHANCEMENT-FINAL-REPORT.md
│   ├── PHASE3-ENHANCEMENT-COMPLETION.md
│   ├── PHASE3-STATUS-SUMMARY.md
│   ├── CAPEC_MAPPING_DISCOVERY.md
│   └── PIPELINE_REGENERATION_SUMMARY.md
│
├── ontology/                       (🏛️ Formal specifications)
│   └── [existing structure]
│
├── .ideas/                         (💡 Future planning - working docs)
│   ├── CLAUDE.md
│   ├── GROK-future-projects.md
│   └── OCSF.md
│
└── .archive/                       (📦 Legacy - consider moving out)
    └── [dated files]
```

---

## Detailed Recommendations

### MOVE to `/operations/` (3 files)

These are operational guides for running/maintaining the system:

1. **CLEANUP-WORKSPACE.md**
   - Purpose: Workspace cleanup procedures
   - Why move: Operational maintenance, not architecture
   - Impact: Low (reference documentation)

2. **NEO4J-LOAD-SUMMARY.md**
   - Purpose: Neo4j loading and statistics
   - Why move: Operational guide for Neo4j management
   - Impact: Low (reference documentation)

3. **NEO4J-STATS.md**
   - Purpose: Neo4j statistics (needs review)
   - Why move: Operational utility
   - **ACTION ITEM:** Check if duplicate of NEO4J-LOAD-SUMMARY.md

### MERGE (1 pair)

**NEO4J-LOAD-SUMMARY.md + NEO4J-STATS.md**
- **Action:** Review both files; if NEO4J-STATS.md is subset, merge into NEO4J-LOAD-SUMMARY.md
- **Result:** One comprehensive Neo4j operations guide
- **Location:** `docs/operations/NEO4J-OPERATIONS.md`

### MOVE to `research/` (2 files)

These are Phase 3 enhancement summaries (historical/research):

1. **PHASE3-ENHANCEMENT-COMPLETION.md** → `docs/research/`
2. **PHASE3-STATUS-SUMMARY.md** → `docs/research/`

Reasoning: These document completed enhancement work, belong with other research/completion reports.

### KEEP at Root (4 files - Core Documentation)

These are foundational architecture and design documents:

1. **ARCHITECTURE.md** - System design, 5-phase roadmap, critical reference
2. **KGCS.md** - Executive summary and big picture
3. **GLOSSARY.md** - Standard definitions and terminology
4. **EXTENDING.md** - How to extend the system

### KEEP in `/operations/` After Move (2 files)

1. **DEPLOYMENT.md** - Production deployment procedures
2. **DAILY-DOWNLOAD-PIPELINE.md** - Automation setup

### KEEP as-is

1. **`research/`** - Well-organized, 4 files
2. **`ontology/`** - Critical specifications
3. **`.ideas/`** - Internal future planning (working directory)
4. **`.archive/`** - Legacy files (consider: compress or remove later)

---

## Implementation Plan

### Phase 1: Create Operations Directory (Simple)

```bash
mkdir docs/operations
```

Move files:
- CLEANUP-WORKSPACE.md → docs/operations/
- DEPLOYMENT.md → docs/operations/
- DAILY-DOWNLOAD-PIPELINE.md → docs/operations/
- NEO4J-LOAD-SUMMARY.md → docs/operations/

### Phase 2: Handle NEO4J-STATS.md (Action Required)

**Before moving:**
1. Check if NEO4J-STATS.md is a duplicate of NEO4J-LOAD-SUMMARY.md
2. If duplicate/subset: Delete it, consolidate content into LOAD-SUMMARY
3. If different: Move to docs/operations/ as separate file

**Command to check:**
```bash
diff NEO4J-STATS.md NEO4J-LOAD-SUMMARY.md
```

### Phase 3: Move Research Files (Simple)

Move to `docs/research/`:
- PHASE3-ENHANCEMENT-COMPLETION.md
- PHASE3-STATUS-SUMMARY.md

### Phase 4: Create Navigation README

Create `docs/README.md` explaining folder structure:
```markdown
# KGCS Documentation

## Core Architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and 5-phase roadmap
- **[KGCS.md](KGCS.md)** - Executive summary
- **[GLOSSARY.md](GLOSSARY.md)** - Standard definitions and terminology
- **[EXTENDING.md](EXTENDING.md)** - How to add new standards

## Operations & Deployment
- **[operations/](operations/)** - Deployment, Neo4j setup, daily tasks
- **[operations/DEPLOYMENT.md](operations/DEPLOYMENT.md)** - Production setup
- **[operations/DAILY-DOWNLOAD-PIPELINE.md](operations/DAILY-DOWNLOAD-PIPELINE.md)** - Automation
- **[operations/NEO4J-LOAD-SUMMARY.md](operations/NEO4J-LOAD-SUMMARY.md)** - Neo4j operations

## Research & Analysis
- **[research/](research/)** - Enhancement reports and completion summaries
- **[research/CAPEC-ENHANCEMENT-FINAL-REPORT.md](research/CAPEC-ENHANCEMENT-FINAL-REPORT.md)** - CAPEC 8.5x improvement

## Formal Specifications
- **[ontology/](ontology/)** - OWL/SHACL specifications (core system)

## Future Planning
- **[.ideas/](.ideas/)** - Internal future project notes
```

---

## Expected Benefits

✅ **Clearer Navigation**
- Core docs at root (what you need to understand the system)
- Operations grouped together (how to run/maintain)
- Research separated (historical records)

✅ **Professional Structure**
- Follows documentation best practices
- Clear separation of concerns
- Easier to onboard new team members

✅ **Maintainability**
- Operations docs easy to find for ops team
- Research isolated for historical reference
- Core docs always in focus

✅ **Reduced Cognitive Load**
- 11 root files → 4 root files (keeps most important visible)
- 7 operational files grouped in one place
- Clear hierarchical organization

---

## Files Needing User Review

1. **NEO4J-STATS.md vs NEO4J-LOAD-SUMMARY.md**
   - Are these duplicates or different content?
   - User action: Review and decide merge/keep

---

## Git Strategy

When implementing:
1. Create operations/ directory
2. Use `git mv` to move files (preserves history)
3. Commit with message: `"docs: reorganize into core/operations/research structure"`
4. Create docs/README.md navigation
5. Update REPOSITORY-ORGANIZATION-SUMMARY.md with new structure

**Result:** All changes tracked, git history preserved, professional structure achieved.

---

**Ready to implement?** Let me know if you'd like to proceed with any/all of these recommendations!
