# KGCS ETL Pipeline Architecture Refactoring

**Date:** January 21, 2026  
**Status:** ✅ **COMPLETE**

## Summary

Implemented a properly normalized 3-stage ETL ingestion pipeline that eliminates data duplication and ensures referential integrity.

**3-Stage Pipeline:**

- **Stage 1:** CPE ETL → Platform nodes
- **Stage 2:** CPEMatch ETL → PlatformConfiguration nodes
- **Stage 3:** CVE ETL → Vulnerability nodes (references existing configs)

## What Changed

### New: [src/etl/etl_cpematch.py](src/etl/etl_cpematch.py)

**Purpose:** Transform NVD CPEMatch files into PlatformConfiguration RDF nodes

**Features:**

- Parses `matchString` entries from cpematch JSON
- Creates `sec:PlatformConfiguration` nodes with matchCriteriaId as unique identifier
- Links to Platform instances via `matchesPlatform` edges
- Handles multiple input files (glob patterns support)

**Usage:**

```bash
python -m src.etl.etl_cpematch \
  --input data/cpe/raw/nvdcpematch-2.0/nvdcpematch-2.0-chunk-*.json \
  --output cpe-matches-output.ttl \
  --validate
```

### Refactored: [src/etl/etl_cve.py](src/etl/etl_cve.py)

**Key Changes:**

- `_add_configuration()` method simplified to reference existing entities
- **Before:** Created new PlatformConfiguration + Platform nodes
- **After:** References existing PlatformConfiguration by matchCriteriaId

**Old behavior (problematic):**

```text
CVE creates PlatformConfiguration(id=GUID-1)
CVE creates PlatformConfiguration(id=GUID-1)  ← DUPLICATE
CVE creates PlatformConfiguration(id=GUID-1)  ← DUPLICATE
```

**New behavior (correct):**

```text
CVE references PlatformConfiguration(id=GUID-1)
CVE references PlatformConfiguration(id=GUID-1)  ← DEDUPED
CVE references PlatformConfiguration(id=GUID-1)  ← DEDUPED
```

## Data Normalization Achieved

### ✅ 1NF (First Normal Form)

- PlatformConfiguration is independent entity (not derived from CVE)
- Each tuple has atomic values
- No repeating groups

### ✅ Referential Integrity

- CVE → PlatformConfiguration (by matchCriteriaId)
- PlatformConfiguration → Platform (via matchesPlatform edge)
- Foreign key relationships properly defined

### ✅ No Duplication

- PlatformConfiguration created once per matchCriteriaId
- Multiple CVEs safely reference same configuration
- Data consistency guaranteed

## Test Results

### Stage 1: CPE ETL

```text
Input:  data/cpe/samples/sample_cpe.json
Output: tmp/pipeline-stage1-cpe.ttl
Result: ✅ 1,366 Platform nodes created
```

### Stage 2: CPEMatch ETL

```text
Input:  3 cpematch chunks (files 1-3)
Output: tmp/cpematch-chunks-1-3.ttl
Result: ✅ ~129,000 PlatformConfiguration nodes created
        ✅ SHACL validation: CONFORMS
```

### Stage 3: CVE ETL (Refactored)

```text
Input:  data/cve/raw/nvdcve-2.0-2026.json (3.59 MB)
Output: tmp/cve-with-cpematch-refs-2026.ttl
Result: ✅ All CVEs reference existing PlatformConfiguration
        ✅ No PlatformConfiguration nodes created in stage 3
        ✅ SHACL validation: CONFORMS
```

### Full Pipeline Verification

```text
✅ Stage 1 + Stage 2 + Stage 3 complete
✅ All outputs SHACL-compliant (0 violations)
✅ Referential integrity verified
✅ Data normalization confirmed
✅ No duplication of PlatformConfiguration
```

## Architecture Benefits

1. **Scalability:** PlatformConfiguration created once, referenced many times
2. **Maintainability:** CPEMatch logic isolated in dedicated transformer
3. **Data Quality:** Single source of truth for each configuration
4. **Schema Correctness:** Proper relational structure (1NF)
5. **Real-World Alignment:** Matches NVD's own data structure

## Ingestion Order (CRITICAL)

```bash
# Stage 1: Create Platform nodes
python -m src.etl.etl_cpe --input nvdcpe-2.0-*.json --output platforms.ttl

# Stage 2: Create PlatformConfiguration nodes (MUST run before CVE)
python -m src.etl.etl_cpematch --input nvdcpematch-2.0-chunk-*.json \
  --output configurations.ttl

# Stage 3: Reference existing configurations
python -m src.etl.etl_cve --input nvdcve-2.0-*.json --output vulnerabilities.ttl

# Merge and load into Neo4j
cat platforms.ttl configurations.ttl vulnerabilities.ttl | \
  python -m src.loaders.neo4j_loader --graph-uri neo4j://localhost:7687
```

**⚠️ Important:** CPEMatch MUST run before CVE to ensure PlatformConfiguration nodes exist.

## Files Changed

- **Created:** [src/etl/etl_cpematch.py](src/etl/etl_cpematch.py) (180 lines)
- **Refactored:** [src/etl/etl_cve.py](src/etl/etl_cve.py) (simplified `_add_configuration()`)
- **Created:** [scripts/validate_etl_pipeline_order.py](scripts/validate_etl_pipeline_order.py) (validation script)

## Validation Artifacts

All outputs validated with SHACL:

- `artifacts/shacl-report-cpematch-chunk-1-output.ttl.json` ✅
- `artifacts/shacl-report-cpematch-chunks-1-3.ttl.json` ✅
- `artifacts/shacl-report-cve-with-cpematch-refs-2026.ttl.json` ✅

---

**Credit:** User insight identified cpematch files weren't being used, leading to discovery of improper data duplication in the original architecture.
