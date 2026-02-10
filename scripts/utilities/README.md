# Utility Scripts

Support tools for ETL processing, Neo4j database operations, data export, and administrative tasks.

## Scripts

### `extract_neo4j_stats.py`

Extracts comprehensive statistics and metrics from Neo4j database.

**Usage:**

```bash
python scripts/utilities/extract_neo4j_stats.py

# Or specify database
python scripts/utilities/extract_neo4j_stats.py --db neo4j-2026-01-29

# List available databases
python scripts/utilities/extract_neo4j_stats.py --list-databases
```

**Output:**

- Node counts by label
- Relationship counts by type
- Graph statistics and metrics
- Saved to `artifacts/neo4j-stats-*.json`

---

### `reload_neo4j.py`

Loads RDF/TTL data into Neo4j database.

**Usage:**

```bash
python scripts/utilities/reload_neo4j.py --ttl tmp/combined-pipeline-enhanced-capec.ttl
```

**Features:**

- Batch loading with configurable batch size
- Constraint and index creation
- Transaction rollback on failure
- Progress tracking

---

### `export_ttl_to_csv.py`

Converts RDF/TTL format to CSV for analysis and reporting.

**Usage:**

```bash
python scripts/utilities/export_ttl_to_csv.py \
  --input tmp/combined-pipeline-enhanced-capec.ttl \
  --output artifacts/graph.csv
```

**Output Formats:**

- Nodes CSV
- Relationships CSV
- Summary statistics

---

### `ttl_rel_stats.py`

Computes relationship counts for TTL files.

**Usage:**

```bash
python scripts/utilities/ttl_rel_stats.py --inputs data/cpe/samples/*-rels.ttl --out-dir artifacts --top 20
```

**Outputs:**

- Top counts for (source,target)
- Top counts for (source,predicate,target)
- Predicate totals

---

### `ttl_rel_dedup.py`

Deduplicates relationship triples in TTL files using a disk-backed index.

**Usage:**

```bash
python scripts/utilities/ttl_rel_dedup.py --inputs data/cpe/samples/*-rels.ttl --out-dir artifacts
```

---

### `ttl_rel_split_predicate.py`

Splits relationship TTL files by predicate for staged loading.

**Usage:**

```bash
python scripts/utilities/ttl_rel_split_predicate.py \
  --inputs data/cpe/samples/pipeline-stage1-cpe-rels.ttl \
  --predicates <https://example.org/sec/core#deprecates> \
  --out-dir artifacts
```

---

### `cleanup_workspace.py`

Cleans up temporary files, caches, and generated artifacts.

**Usage:**

```bash
python scripts/utilities/cleanup_workspace.py

# Dry run (show what would be deleted)
python scripts/utilities/cleanup_workspace.py --dry-run
```

**Cleans:**

- `tmp/*.ttl` (temporary RDF files)
- `__pycache__/` directories
- `.pytest_cache/` directories
- Old log files
- Temporary generated files

---

### `create_phase3_samples.py`

Generates sample data for testing and validation.

**Usage:**

```bash
python scripts/utilities/create_phase3_samples.py
```

**Generates:**

- Small sample ETL inputs for each standard
- Test data for validation checks
- Sample outputs in `data/*/samples/`

---

## Common Utility Workflows

### Extract Database Statistics

```bash
python scripts/utilities/extract_neo4j_stats.py
```

### Load Data into Neo4j

```bash
python scripts/utilities/reload_neo4j.py --ttl tmp/combined-pipeline-enhanced-capec.ttl --batch-size 1000
```

### Export for Analysis

```bash
python scripts/utilities/export_ttl_to_csv.py \
  --input tmp/combined-pipeline-enhanced-capec.ttl \
  --output artifacts/graph.csv
```

### Clean Workspace

```bash
# Preview what will be deleted
python scripts/utilities/cleanup_workspace.py --dry-run

# Actually delete
python scripts/utilities/cleanup_workspace.py
```

### Create Test Data

```bash
python scripts/utilities/create_phase3_samples.py
```

---

## Output & Results

Utility script results are saved to various locations:

- `artifacts/` - Analysis results, exports, statistics
- `logs/` - Operation logs
- `data/*/samples/` - Generated test data
- Database directly for reload operations

---

**Last Updated:** February 3, 2026
