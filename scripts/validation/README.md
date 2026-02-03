# Validation Scripts

Quality assurance utilities for ETL pipeline, SHACL compliance, and data integrity checks.

## Scripts

### `validate_all_standards.py`
Validates all ETL outputs against their respective SHACL shapes.

**Usage:**
```bash
python scripts/validation/validate_all_standards.py
```

**Features:**
- Validates all 10+ standards in parallel
- Generates per-standard summary reports
- Outputs to `artifacts/shacl-report-*.json`

---

### `validate_shacl_stream.py`
Memory-efficient streaming SHACL validator for large files.

**Usage:**
```bash
python scripts/validation/validate_shacl_stream.py \
  --data tmp/pipeline-stage3-cve.ttl \
  --shapes docs/ontology/shacl/cve-shapes.ttl
```

**Features:**
- Processes files in 10k-triple chunks
- Minimal memory footprint
- Ideal for large files (100+ MB)

---

### `validate_etl_pipeline_order.py`
Validates ETL dependency order and transformation completeness.

**Usage:**
```bash
python scripts/validation/validate_etl_pipeline_order.py
```

**Checks:**
- ETL stages execute in correct dependency order
- Each stage produces expected outputs
- Causal chain completeness

---

### `validate_shacl_parallel.py`
Parallel SHACL validation runner for faster validation.

**Usage:**
```bash
python scripts/validation/validate_shacl_parallel.py
```

**Features:**
- Multi-threaded validation
- Process multiple standards simultaneously
- Progress tracking per standard

---

### `regenerate_pipeline.py`
Regenerates complete pipeline with timeout handling and validation.

**Usage:**
```bash
python scripts/validation/regenerate_pipeline.py
```

**Features:**
- Runs all 13 ETL stages sequentially
- Handles stage timeouts gracefully
- Validates each stage output
- Skips stages that already completed successfully

---

## Common Validation Workflows

### Validate Everything
```bash
python scripts/validation/validate_all_standards.py
```

### Validate Single Standard
```bash
python scripts/validation/validate_shacl_stream.py \
  --data tmp/pipeline-stage1-cpe.ttl \
  --shapes docs/ontology/shacl/cpe-shapes.ttl
```

### Full Pipeline Regeneration
```bash
python scripts/validation/regenerate_pipeline.py
```

---

## Output & Reports

All validation results are saved to `artifacts/`:
- `shacl-report-*.json` - Per-standard validation results
- `shacl-report-consolidated.json` - Summary across all standards
- `validation-errors.log` - Detailed error logs

---

**Last Updated:** February 3, 2026
