# Workspace Cleanup Guide

This guide explains how to use the `cleanup_workspace.py` utility to maintain a clean development environment and reclaim disk space.

## Overview

The cleanup script removes temporary files, cache, logs, and test artifacts that accumulate during development:

- **Temporary files:** `tmp/` directory (development working space)
- **Test reports:** `artifacts/` directory (SHACL validation outputs)
- **Logs:** `logs/` directory (application runtime logs)
- **Python cache:** `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo`
- **RDFlib cache:** `.rdflib_default/` directory
- **Coverage reports:** `htmlcov/`, `.coverage*` files
- **Optional (sources):** Downloaded source data in `data/*/raw/` directories (with `--sources` flag)
- **Optional (data):** Transformed sample data in `data/*/samples/` directories (with `--data` flag)

## Usage

### List Items to Clean (Default)

Show what would be removed without deleting:

```bash
python scripts/cleanup_workspace.py
```

Output:
```
📋 Items to Clean:

  • artifacts                               - SHACL validation reports
  • logs                               - Application logs
  • tmp                               - Temporary working files

📊 Summary:
  Directories: 3
  Files: 103
  Total size: 509.38 MB

💡 Tip: Use --execute to actually delete, or --dry-run to preview
```

### Dry-Run Preview

Preview deletion with detailed output (no files deleted):

```bash
python scripts/cleanup_workspace.py --dry-run
```

### Execute Cleanup

Actually delete the files:

```bash
python scripts/cleanup_workspace.py --execute
```

Output:
```
🗑️  Cleaning workspace...

  ✅ Deleted: artifacts/
  ✅ Deleted: logs/
  ✅ Deleted: tmp/
  ...

✅ Cleaned 3 items
```

### Source Data Cleanup (Include Downloaded Source Data)

Include downloaded source data from `data/*/raw/` directories (CPE, CVE, CWE, etc.):

```bash
python scripts/cleanup_workspace.py --sources --execute
```

⚠️ **Warning:** This will delete downloaded source data. Re-run the data ingestion pipeline to re-download.

### Data Cleanup (Include Transformed Data)

Include transformed sample data in `data/` folder:

```bash
python scripts/cleanup_workspace.py --data --execute
```

⚠️ **Warning:** This will delete transformed sample outputs. Re-run ETL transformers to recreate.

### Complete Cleanup (Everything)

Combine both flags to clean everything:

```bash
python scripts/cleanup_workspace.py --sources --data --execute
```

⚠️ **This will delete:**
- All temporary files and cache
- All test artifacts and logs
- All downloaded source data (data/*/raw/)
- All transformed sample data (data/*/samples/)

Manifest files are preserved for reference.

## Categories Cleaned

### Always Cleaned (unless excluded by code)

| Directory/Pattern | Purpose | Recoverable |
|---|---|---|
| `tmp/` | Temporary working files | Yes - recreated as needed |
| `artifacts/` | SHACL validation reports (JSON) | Yes - re-run validation |
| `logs/` | Application runtime logs | Yes - recreated on next run |
| `__pycache__/` | Python bytecode cache | Yes - auto-regenerated |
| `.pytest_cache/` | Pytest test cache | Yes - auto-regenerated |
| `*.pyc`, `*.pyo` | Python compiled files | Yes - auto-regenerated |
| `.rdflib_default/` | RDFlib triple store cache | Yes - can be recreated |
| `htmlcov/` | HTML coverage reports | Yes - re-run coverage |
| `.coverage*` | Coverage data files | Yes - re-run tests with coverage |

### Optional (with `--sources` flag)

| Directory | Purpose | Size | Recoverable |
| --- | --- | --- | --- |
| `data/attack/raw/` | Downloaded ATT&CK source data | 10-50 MB | Yes - requires re-download |
| `data/capec/raw/` | Downloaded CAPEC source data | 10-50 MB | Yes - requires re-download |
| `data/car/raw/` | Downloaded CAR source data | 1-10 MB | Yes - requires re-download |
| `data/cpe/raw/` | Downloaded CPE source data | 800+ MB | Yes - requires re-download |
| `data/cve/raw/` | Downloaded CVE source data | 5+ GB | Yes - requires re-download |
| `data/cwe/raw/` | Downloaded CWE source data | 10-50 MB | Yes - requires re-download |
| `data/d3fend/raw/` | Downloaded D3FEND source data | 10-50 MB | Yes - requires re-download |
| `data/engage/raw/` | Downloaded ENGAGE source data | 1-10 MB | Yes - requires re-download |
| `data/shield/raw/` | Downloaded SHIELD source data | 10-50 MB | Yes - requires re-download |

### Optional (with `--data` flag)

| Directory | Purpose | Recoverable |
|---|---|---|
| `data/attack/samples/` | Transformed ATT&CK sample data | Yes - re-run ETL |
| `data/capec/samples/` | Transformed CAPEC sample data | Yes - re-run ETL |
| `data/car/samples/` | Transformed CAR sample data | Yes - re-run ETL |
| `data/cpe/samples/` | Transformed CPE sample data | Yes - re-run ETL |
| `data/cve/samples/` | Transformed CVE sample data | Yes - re-run ETL |
| `data/cwe/samples/` | Transformed CWE sample data | Yes - re-run ETL |
| `data/d3fend/samples/` | Transformed D3FEND sample data | Yes - re-run ETL |
| `data/engage/samples/` | Transformed ENGAGE sample data | Yes - re-run ETL |
| `data/shield/samples/` | Transformed SHIELD sample data | Yes - re-run ETL |

**Note:** Manifest files in `data/*/` are preserved.

## When to Clean

**Regular cleanup** (safe, daily):
```bash
# Remove test artifacts and cache
python scripts/cleanup_workspace.py --execute
```

**Before committing** (recommended):
```bash
# Check what would be cleaned
python scripts/cleanup_workspace.py

# Clean if happy with the list
python scripts/cleanup_workspace.py --execute
```

**Before deployment** (good practice):
```bash
# Full clean including optional source and sample data
python scripts/cleanup_workspace.py --sources --data --execute
```

**Troubleshooting** (when tests act weird):
```bash
# Clean all cache and restart
python scripts/cleanup_workspace.py --execute
pytest tests/ -v
```

## Disk Space Saved

Typical cleanup recovers:

- **After test runs:** 100-500 MB (artifacts, logs)
- **After development:** 500 MB - 1 GB (cache, compiled files)
- **After full cleanup:** 1-5 GB+ (includes downloaded data)

Example from development run:
```
Total size: 509.38 MB
Directories: 3
Files: 103
```

## Safety Considerations

✅ **Safe to delete:**
- All cache directories (auto-regenerated)
- All test artifacts (can be re-created)
- All logs (new ones created on next run)
- Temporary working files (recreated as needed)

⚠️ **Be careful with:**
- `data/*/raw/` - Contains downloaded source data (use `--sources` only if needed)

✅ **Never deleted:**
- Source code (`src/`, `tests/`, `scripts/`)
- Documentation (`docs/`)
- Configuration files (`.env`, `*.json`, `*.yaml`)
- Ontology files (`docs/ontology/`)
- Git history (`.git/`)

## Integration with CI/CD

The cleanup script can be integrated into CI/CD pipelines:

```yaml
# Example: GitHub Actions workflow
- name: Clean workspace
  run: python scripts/cleanup_workspace.py --execute

- name: Run tests
  run: pytest tests/ -v
```

## Script Location

- **Location:** `scripts/cleanup_workspace.py`
- **Executable:** Yes (has shebang `#!/usr/bin/env python3`)
- **Dependencies:** None (uses Python stdlib only: `os`, `shutil`, `pathlib`, `argparse`)

## Options Reference

```
python scripts/cleanup_workspace.py [OPTIONS]

Options:
  --dry-run      Show what would be deleted without actually deleting
  --execute      Actually delete the files (default is to list only)
  --sources      Include downloaded source data (data/*/raw/)
  --data         Include transformed sample data (data/*/samples/)
  --help         Show help message
```

## Examples

### Example 1: Clean before pushing to git

```bash
# See what would be removed
python scripts/cleanup_workspace.py

# Remove all temporary files and cache
python scripts/cleanup_workspace.py --execute

# Now safe to commit
git add .
git commit -m "feat: new feature"
git push
```

### Example 2: Troubleshoot failing tests

```bash
# Clean all cache that might interfere
python scripts/cleanup_workspace.py --execute

# Re-run tests to see if they pass
pytest tests/test_phase3_comprehensive.py -v
```

### Example 3: Free up disk space before heavy processing

```bash
# See how much space can be freed
python scripts/cleanup_workspace.py

# Free up space
python scripts/cleanup_workspace.py --execute

# If you have raw data downloads, also clean those
python scripts/cleanup_workspace.py --sources --execute
```

## Troubleshooting

### Script fails with "permission denied"

On Linux/macOS, ensure the script is executable:
```bash
chmod +x scripts/cleanup_workspace.py
```

### Some files won't delete

The script will report which files failed. This may happen if:
- Files are open in an editor or IDE
- Files are locked by another process
- Insufficient permissions

Solution: Close the application and retry, or use `--force` equivalent.

### "No items found to clean" message

Your workspace is already clean! Nothing needs to be removed.

## Related Commands

Clean related tasks:

```bash
# List cache items only (dry-run)
python scripts/cleanup_workspace.py --dry-run

# Clean everything
python scripts/cleanup_workspace.py --execute

# Clean including downloaded data
python scripts/cleanup_workspace.py --full --execute

# Git garbage collection (additional cleanup)
git gc --aggressive

# Remove untracked files
git clean -fd
```

## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md) - Setup and deployment guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Project structure overview
- [EXTENDING.md](EXTENDING.md) - How to extend the project
