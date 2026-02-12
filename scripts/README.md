# KGCS Scripts Directory

Comprehensive collection of production and support scripts for the Knowledge Graph Cybersecurity (KGCS) system.

---

## 🎯 Quick Navigation

**Core Pipeline Scripts** (run these)

- [`run_all_etl.py`](#run_all_etlpy) - Main ETL orchestrator
- [`combine_pipeline.py`](#combine_pipelinepy) - Combine pipeline stages
- [`verify_combined_capec.py`](#verify_combined_capecpy) - Verify CAPEC enhancement

**Validation Scripts** (`validation/`)

- Run quality assurance checks on ETL outputs
- See [Validation README](validation/README.md)

**Utility Scripts** (`utilities/`)

- Support tools for database operations and data export
- See [Utilities README](utilities/README.md)

---

## 📋 Core Scripts (Root Level)

### `run_all_etl.py`

**Purpose:** Main ETL pipeline orchestrator  
**Usage:** `python scripts/run_all_etl.py`  
**What it does:**

- Orchestrates all 13 ETL transformation stages
- Manages dependencies between stages
- Handles timeouts and error recovery
- Generates combined pipeline output

**Key Features:**

- Sequential/parallel execution modes
- Progress tracking and logging
- Automatic validation hooks
- Idempotent (safe to re-run)

---

### `combine_pipeline.py`

**Purpose:** Combine all pipeline stages into single file  
**Usage:** `python scripts/combine_pipeline.py`  
**What it does:**

- Merges 13 stage TTL files into combined output
- Validates file integrity
- Generates statistics and summary

**Output:** `tmp/combined-pipeline-enhanced-capec.ttl` (1.91 GB)

---

### `verify_combined_capec.py`

**Purpose:** Verify CAPEC enhancement in combined pipeline  
**Usage:** `python scripts/verify_combined_capec.py`  
**What it does:**

- Scans for CAPEC→Technique relationships
- Counts patterns and relationships
- Compares pre/post enhancement metrics
- Shows sample mappings

**Example Output:**

```text
CAPEC patterns with techniques: 179
Implements relationships: 307
Unique techniques: 225
Coverage: 39.6% of ATT&CK techniques
```

---

## 📁 Directory Structure

```text
scripts/
├── run_all_etl.py                    ⭐ MAIN ENTRY POINT
├── combine_pipeline.py               ⭐ PIPELINE ORCHESTRATION
├── verify_combined_capec.py          ⭐ VERIFICATION
├── load_full_ordered.ps1             ⭐ COMBINED ORDERED LOAD
│
├── validation/                       📋 VALIDATION SCRIPTS
│   ├── __init__.py
│   ├── validate_all_standards.py
│   ├── validate_shacl_stream.py
│   ├── validate_etl_pipeline_order.py
│   ├── validate_shacl_parallel.py
│   ├── regenerate_pipeline.py
│   └── README.md                     (detailed docs)
│
├── utilities/                        🔧 SUPPORT TOOLS
│   ├── __init__.py
│   ├── extract_neo4j_stats.py
│   ├── inspect_combined_ttl.py
│   ├── reload_neo4j.py
│   ├── export_ttl_to_csv.py
│   ├── cleanup_workspace.py
│   ├── create_phase3_samples.py
│   └── README.md                     (detailed docs)
│
├── .archive/                         📦 LEGACY FILES
│   ├── legacy/
│   └── db/
│
├── README.md                         (this file)
└── .pytest_cache/                    (testing artifacts)
```

---

## 🚀 Common Workflows

### Running the Full ETL Pipeline

```bash
# Execute all 13 transformation stages
python scripts/run_all_etl.py

# Then validate the outputs
python scripts/validation/validate_all_standards.py

# Then combine into single file
python scripts/combine_pipeline.py

# Finally verify CAPEC enhancement
python scripts/verify_combined_capec.py
```

### Validating Specific Standards

```bash
# Validate SHACL with streaming (for large files)
python scripts/validation/validate_shacl_stream.py --data tmp/pipeline-stage3-cve.ttl --shapes docs/ontology/shacl/cve-shapes.ttl

# Validate ETL pipeline order/dependencies
python scripts/validation/validate_etl_pipeline_order.py

# Regenerate with validation (includes timeout handling)
python scripts/validation/regenerate_pipeline.py
```

### Database Operations

```bash
# Extract Neo4j statistics
python scripts/utilities/extract_neo4j_stats.py

# Reload data into Neo4j
python scripts/utilities/reload_neo4j.py

# Combine ordered TTL and load full graph
.
\scripts\load_full_ordered.ps1 -DbVersion 2026-02-10 -FastParse -ProgressNewline -ResetDb

# Load relationships only (canonical stage relationship files)
.\scripts\load_rels_all.ps1 -DbVersion 2026-02-12 -FastParse -ProgressNewline

# Include DEPRECATES edges explicitly (disabled by default)
.\scripts\load_rels_all.ps1 -DbVersion 2026-02-12 -FastParse -ProgressNewline -SkipDeprecates:$false

# Create phase 3 test samples
python scripts/utilities/create_phase3_samples.py
```

### Data Export

```bash
# Export RDF/TTL to CSV format
python scripts/utilities/export_ttl_to_csv.py --input tmp/combined-pipeline-enhanced-capec.ttl --output artifacts/graph.csv

# Cleanup temporary files
python scripts/utilities/cleanup_workspace.py
```

---

## 📊 Script Categories

### Validation Scripts (`validation/`)

Quality assurance and conformance checking:

- **validate_all_standards.py** - SHACL validation for all standards
- **validate_shacl_stream.py** - Memory-efficient streaming SHACL validator
- **validate_etl_pipeline_order.py** - Verify ETL dependency order
- **validate_shacl_parallel.py** - Parallel SHACL validation
- **regenerate_pipeline.py** - Full pipeline regeneration with validation

### Utility Scripts (`utilities/`)

Support tools and administrative tasks:

- **extract_neo4j_stats.py** - Extract statistics from Neo4j database
- **inspect_combined_ttl.py** - Inspect combined TTL files for quick sanity checks
- **reload_neo4j.py** - Load RDF data into Neo4j
- **export_ttl_to_csv.py** - Convert RDF/TTL to CSV format
- **cleanup_workspace.py** - Clean temporary files and caches
- **create_phase3_samples.py** - Generate sample data for testing

---

## 🔧 Development Notes

### Adding New Scripts

1. **Core Pipeline Scripts:** Keep at `scripts/` root level
   - Must be called from project root: `python scripts/script_name.py`
   - Example: `run_all_etl.py`, `combine_pipeline.py`

2. **Validation Scripts:** Place in `scripts/validation/`
   - Import: `from scripts.validation import validate_module`
   - Use for quality assurance checks

3. **Utility Scripts:** Place in `scripts/utilities/`
   - Import: `from scripts.utilities import utility_module`
   - Use for support operations

### Running Scripts from Code

```python
# Core scripts
from scripts.validation import validate_all_standards
from scripts.utilities import extract_neo4j_stats

# Or execute via subprocess
import subprocess
result = subprocess.run(['python', 'scripts/validation/validate_all_standards.py'], ...)
```

---

## 📚 Related Documentation

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Overall system design
- [CAPEC-ENHANCEMENT-FINAL-REPORT.md](../docs/CAPEC-ENHANCEMENT-FINAL-REPORT.md) - Enhancement details
- [PROJECT-STATUS-SUMMARY.md](../PROJECT-STATUS-SUMMARY.md) - Project progress

---

## 📝 Notes

- All scripts are idempotent (safe to re-run)
- Scripts log output to `logs/` directory
- Temporary outputs go to `tmp/` directory
- Final artifacts stored in `artifacts/` directory
- Legacy/archived scripts in `.archive/` (not actively used)
- `load_rels_all.ps1` uses canonical relationship TTL inputs from `data/*/samples/pipeline-stage*-rels.ttl` only (no `artifacts/*dedup*.ttl` or `tmp/*` fallbacks)
- `load_rels_all.ps1` sets `-SkipDeprecates` to true by default; pass `-SkipDeprecates:$false` to include DEPRECATES relationships
- `src/etl/rdf_to_neo4j.py` infers endpoint labels from URI paths during `--rels-only` loads to keep relationship `MATCH` clauses label-scoped even when `rdf:type` triples are absent in rel files
- Supported URI aliases include canonical and ETL-emitted forms: `attackPattern|capec`, `defensiveTechnique|deftech`, `detectionAnalytic|analytic`, plus `consequence` and `prerequisite` endpoints used by CAPEC relations

---

**Last Updated:** February 3, 2026  
**Organization:** Scripts grouped by functional purpose (core/validation/utilities)
