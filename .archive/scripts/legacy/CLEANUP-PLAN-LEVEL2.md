# Workspace Cleanup Plan - Level 2 (Moderate)

**Date:** February 3, 2026  
**Level:** 2 (Moderate cleanup - removes clutter, retains important data)  
**Status:** Ready to execute

---

## Overview

Level 2 cleanup removes temporary build artifacts, cache files, old reports, and logs while retaining:
- Latest combined pipeline (TTL)
- Most recent SHACL validation summaries
- All source code and configurations
- All documentation and ontology definitions

---

## Cleanup Items by Category

### 1. ✅ Cache Files (Always Safe - Auto-Regenerates)

| Item | Location | Size Impact | Reason |
|------|----------|------------|--------|
| Python cache | `__pycache__/` (recursive) | ~50-100 MB | Auto-regenerated on next run |
| Pytest cache | `.pytest_cache/` | ~10 MB | Auto-regenerated on next pytest |
| RDFlib store | `.rdflib_default/` | ~5 MB | Auto-regenerated if needed |
| `.pyc` files | (recursive) | ~20 MB | Compiled Python bytecode |
| `.pyo` files | (recursive) | ~5 MB | Optimized Python bytecode |

**Decision:** ✅ **REMOVE ALL** (safe, regenerates automatically)

### 2. ⚠️ Temporary Files (Keep Latest, Remove Old)

| Item | Location | Count | Action |
|------|----------|-------|--------|
| Pipeline TTL files | `tmp/*.ttl` | 10+ files | Keep: `combined-pipeline-enhanced-capec.ttl` (latest) |
| | | | Remove: All `pipeline-stage-*.ttl` files |
| | | | Remove: All `sample-*.ttl` files |
| Test outputs | `tmp/*.json` | 5+ files | Remove: Old test outputs |

**Decision:** ✅ **REMOVE OLD, KEEP LATEST** (saves ~2-3 GB)

### 3. ⚠️ Reports and Logs (Keep Recent, Archive Old)

| Item | Location | Count | Action |
|------|----------|-------|--------|
| SHACL reports | `artifacts/shacl-report-*.json` | 10+ files | Keep: Latest summaries (dated 2026-02-03) |
| | | | Remove: Pre-CAPEC enhancement reports |
| Application logs | `logs/` | 10+ files | Keep: Last 5 log files |
| | | | Archive: Older log files to `.archive/logs/` |

**Decision:** ✅ **ARCHIVE OLD, KEEP RECENT** (saves ~500 MB)

### 4. 🔍 Analysis and Build Files (Optional Cleanup)

| Item | Location | Action | Note |
|------|----------|--------|------|
| Build cache | `build/`, `dist/`, `*.egg-info` | Remove if exists | Development only |
| Coverage reports | `htmlcov/`, `.coverage` | Remove | Regenerated on next coverage run |
| Docs temporary | `docs/ORGANIZATION-ANALYSIS.md` | Archive | Analysis complete, can reference in docs/.archive/ |

**Decision:** ✅ **REMOVE** (saves ~100 MB)

---

## Execution Plan

### Step 1: Dry Run (Preview What Will Be Deleted)

```bash
python scripts/utilities/cleanup_workspace.py --dry-run
```

**Purpose:** See exactly what will be removed before committing to the action

**Expected Output:**
- List of files/directories to remove
- Total space to be freed
- No actual deletion occurs

### Step 2: Execute Cleanup

```bash
python scripts/utilities/cleanup_workspace.py --execute
```

**Actions Performed:**
- ✅ Remove all `__pycache__/` directories
- ✅ Remove `.pytest_cache/`
- ✅ Remove `.rdflib_default/`
- ✅ Remove `.pyc`, `.pyo` files
- ✅ Remove old log files (keep recent)
- ✅ Remove old TTL files (keep combined pipeline)
- ✅ Remove old SHACL reports (keep summaries)

### Step 3: Verify Cleanup

```bash
git status
du -sh .  # Check disk space recovered
```

### Step 4: Commit Cleanup

```bash
git add -A
git commit -m "chore: cleanup workspace - Level 2 (cache, logs, old reports)"
```

---

## Expected Results

### Disk Space Recovery

| Category | Before | After | Recovered |
|----------|--------|-------|-----------|
| Python cache | ~80 MB | 0 MB | 80 MB |
| Old TTL files | ~5 GB | ~1.9 GB | 3.1 GB |
| Old reports | ~500 MB | ~50 MB | 450 MB |
| Logs | ~200 MB | ~20 MB | 180 MB |
| **TOTAL** | **~5.8 GB** | **~2 GB** | **~3.8 GB** |

### Workspace Quality

- ✅ Cleaner, more professional repository
- ✅ Faster git operations (fewer files to track)
- ✅ Reduced storage requirements
- ✅ Nothing critical lost (all in git/archives)

---

## Safety Considerations

### What's Being Kept

✅ **All source code** (`src/`, `tests/`, `scripts/`)  
✅ **All documentation** (`docs/`, `README.md`)  
✅ **All ontologies** (`docs/ontology/`)  
✅ **All data samples** (`data/*/samples/`)  
✅ **Latest pipeline output** (`tmp/combined-pipeline-enhanced-capec.ttl`)  
✅ **Latest reports** (`artifacts/shacl-report-*-summary.json`)  

### What's Being Removed

❌ **Python cache** (auto-regenerates)  
❌ **Old test files** (keep samples only)  
❌ **Old logs** (keep recent)  
❌ **Superseded TTL files** (keep combined only)  
❌ **Old SHACL reports** (keep latest)  

### Git Safety

- All changes trackable via git
- Cleanup is a single commit
- Easy to revert if needed
- Working directory clean before commit

---

## Post-Cleanup Tasks

1. ✅ Verify all tests still pass: `pytest tests/`
2. ✅ Verify ETL scripts still work: `python -m src.etl.etl_cpe --help`
3. ✅ Commit cleanup: `git commit -m "chore: cleanup workspace"`
4. ✅ Document completion in PROJECT-STATUS-SUMMARY.md

---

## Timeline

- **Dry Run:** 2-3 minutes
- **Execute:** 5-10 minutes
- **Verify:** 5 minutes
- **Commit:** 1 minute

**Total Time:** ~15-20 minutes

---

## Next Steps

After cleanup is complete:
1. ✅ Commit changes to git
2. ✅ Prepare for Phase 3.5 (defense layer linking)
3. ✅ Consider cloud migration planning

---

**Status:** Ready to execute Level 2 cleanup  
**Safety Level:** High (cache + old reports, nothing critical lost)  
**Approval:** Waiting for user confirmation
