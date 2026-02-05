# KGCS Data Pipeline: Complete Setup & Execution Guide

**Last Updated:** February 3, 2026  
**Status:** Production Ready (Phase 3 MVP)

## Quick Start (5 Steps)

```bash
# Step 1: Activate conda environment
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\software\miniconda\envs\metadata
cd e:\DEVEL\LAIA\KGCS

# Step 2: Download all raw data from authoritative sources
python -m src.ingest.download_manager

# Step 3: Run ETL pipeline (transforms raw data to RDF Turtle)
python scripts/run_all_etl.py

# Step 4: Combine all TTL outputs into single file
python scripts/combine_ttl_pipeline.py

# Step 5: Load to Neo4j
python src/etl/rdf_to_neo4j.py --database neo4j-2026-02-03 --ttl tmp/combined-pipeline.ttl
```

## Detailed Steps

### Step 1: Environment Setup

```bash
# Open PowerShell and navigate to project
cd e:\DEVEL\LAIA\KGCS

# Activate conda environment
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\software\miniconda\envs\metadata

# Verify Python and dependencies
python --version
pip list | grep rdflib
```

**Required Environment:**
- Conda: `E:\DEVEL\software\miniconda\envs\metadata`
- Python: 3.9+
- Key packages: rdflib, requests, pyshacl, neo4j

### Step 2: Download Raw Data

Downloads all authoritative standards data from NVD and MITRE:

```bash
python -m src.ingest.download_manager
```

**What it downloads:**
- **CPE** (NVD): 15 chunks → `data/cpe/raw/` (~100 MB)
- **CPEMatch** (NVD): 55 chunks → `data/cpematch/raw/` (~125 MB)
- **CVE** (NVD): 25 files (2002-2026) → `data/cve/raw/` (~10 MB)
- **CWE** (MITRE): 1 XML file → `data/cwe/raw/` (~5 MB)
- **CAPEC** (MITRE): 1 XML file → `data/capec/raw/` (~2 MB)
- **ATT&CK** (MITRE): 4 STIX variants → `data/attack/raw/` (~3 MB)
- **D3FEND** (MITRE): 2 JSON files → `data/d3fend/raw/` (~46 MB)
- **CAR** (MITRE): 122 YAML files → `data/car/raw/` (~1 MB)
- **SHIELD** (MITRE): 12 JSON files → `data/shield/raw/` (~0.5 MB)
- **ENGAGE** (MITRE): 12 JSON files → `data/engage/raw/` (~0.2 MB)

**Output:**
- Manifests: `data/{standard}/manifest.json` (checksums, timestamps)
- Log: `logs/download_manager.log`

**Time:** ~10-20 minutes depending on network

### Step 3: Run ETL Pipeline

Transforms raw JSON/XML/YAML data into RDF Turtle format:

```bash
python scripts/run_all_etl.py
```

**Processing stages (in order):**

1. **Stage 1: CPE** (15 chunks)
   - Input: `data/cpe/raw/*.json` (chunked)
   - Output: `tmp/pipeline-stage1-cpe.ttl` (~2.5 GB)
   - Processing: Loop with append mode, accumulate all chunks

2. **Stage 2: CPEMatch** (55 chunks)
   - Input: `data/cpematch/raw/*.json` (chunked)
   - Output: `tmp/pipeline-stage2-cpematch.ttl` (~18.7 GB)
   - Processing: Loop with append mode, accumulate all chunks
   - **Note:** This is the largest stage - creates 614k PlatformConfiguration nodes

3. **Stage 3: CVE** (25 files)
   - Input: `data/cve/raw/nvdcve-2.0-*.json` (one per year)
   - Output: `tmp/pipeline-stage3-cve.ttl` (~1.8 GB)
   - Processing: Loop with append mode, accumulate all years
   - Links CVE → CWE relationships

4. **Stage 4: ATT&CK** (4 variants)
   - Input: `data/attack/raw/enterprise|ics|mobile|pre.json`
   - Output: `tmp/pipeline-stage4-attack.ttl` (~3.3 MB)
   - Processing: Loop with append mode, merge all variants

5. **Stage 5: D3FEND** (2 files) ⭐ ENHANCED
   - Input: `data/d3fend/raw/d3fend.json` + `d3fend-full-mappings.json`
   - Output: `tmp/pipeline-stage5-d3fend.ttl` (~0.43 MB)
   - Processing: Loop with append mode
   - **New:** SPARQL binding extraction yields 3,109 D3FEND→Technique relationships

6. **Stage 6: CAPEC**
   - Input: `data/capec/raw/capec_latest.xml`
   - Output: `tmp/pipeline-stage6-capec.ttl` (~1.67 MB)
   - Processing: Single file
   - Links CAPEC → ATT&CK Technique (271 relationships)

7. **Stage 7: CWE**
   - Input: `data/cwe/raw/cwe_latest.xml`
   - Output: `tmp/pipeline-stage7-cwe.ttl` (~1.31 MB)
   - Processing: Single file
   - Parent/child hierarchy preserved

8. **Stage 8: CAR** (122 analytics)
   - Input: `data/car/raw/**/*.yaml`
   - Output: `tmp/pipeline-stage8-car.ttl` (~0.14 MB)
   - Processing: Loop with append mode, accumulate all YAML files
   - Links CAR analytics → ATT&CK Techniques

9. **Stage 9: SHIELD** (12 files)
   - Input: `data/shield/raw/*.json`
   - Output: `tmp/pipeline-stage9-shield.ttl` (~0.31 MB)
   - Processing: Directory merge (loads all in memory)
   - Deception techniques

10. **Stage 10: ENGAGE** (12 files)
    - Input: `data/engage/raw/*.json`
    - Output: `tmp/pipeline-stage10-engage.ttl` (~0.05 MB)
    - Processing: Directory merge (loads all in memory)
    - Strategic engagement concepts

**Output:**
- 10 TTL files in `tmp/pipeline-stage*.ttl`
- Total: ~28.6 GB of RDF data
- Log: `logs/etl_run_*.log`

**Time:** ~1-2 hours depending on system performance

**IMPORTANT:** Do NOT run monitoring commands while ETL is running - it may interrupt the background job!

### Step 4: Combine TTL Files

Merges all 10 stage outputs into single combined file (removes duplicate headers):

```bash
python scripts/combine_ttl_pipeline.py
```

**Output:**
- `tmp/combined-pipeline.ttl` (~28.6 GB)
- Log: `logs/combine_ttl.log`

**Time:** ~5-10 minutes

### Step 5: Load to Neo4j

Loads RDF data into Neo4j graph database:

```bash
# Load to specific Neo4j instance
python src/etl/rdf_to_neo4j.py --database neo4j-2026-02-03 --ttl tmp/combined-pipeline.ttl --batch-size 1000

# Or use default (neo4j)
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-pipeline.ttl
```

**Processing:**
- Batch writes (default 1000 nodes per batch)
- Creates label-specific indexes on `uri` field
- Applies graph constraints (uniqueness)
- Cross-standard relationship linking

**Output:**
- Neo4j graph with ~2.5M nodes and 26M relationships
- Constraints and indexes applied
- Success message with statistics

**Time:** ~30-60 minutes

## Expected Output Sizes

After complete pipeline execution:

```
tmp/pipeline-stage1-cpe.ttl            2,472.68 MB   (15 chunks)
tmp/pipeline-stage2-cpematch.ttl      18,689.66 MB   (55 chunks)
tmp/pipeline-stage3-cve.ttl            1,792.56 MB   (25 files)
tmp/pipeline-stage4-attack.ttl             3.29 MB   (4 variants)
tmp/pipeline-stage5-d3fend.ttl             0.43 MB   (2 files)
tmp/pipeline-stage6-capec.ttl              1.67 MB   (1 file)
tmp/pipeline-stage7-cwe.ttl                1.31 MB   (1 file)
tmp/pipeline-stage8-car.ttl                0.14 MB   (122 files)
tmp/pipeline-stage9-shield.ttl             0.31 MB   (12 files)
tmp/pipeline-stage10-engage.ttl            0.05 MB   (12 files)
────────────────────────────────────────────────────
tmp/combined-pipeline.ttl            ~28,600 MB   (all stages combined)
```

**Total RDF triples:** ~3.2M triples across all standards

## Troubleshooting

### Download Fails
- Check network connectivity
- Review `logs/download_manager.log` for failed URLs
- Manually download from NVD/MITRE and place in `data/{standard}/raw/`

### ETL Produces Small Output
- Check if input files exist: `Get-ChildItem data/{standard}/raw/`
- Review `logs/etl_run_*.log` for errors
- Verify file format matches expected (JSON, XML, YAML)
- For multi-file stages, ensure append mode is working (check for increasing file sizes)

### Neo4j Load Fails
- Verify Neo4j service is running: `neo4j status`
- Check database connection: `neo4j console`
- Review Neo4j logs: `logs/neo4j.log`
- Ensure combined TTL file is valid: `python -c "from rdflib import Graph; g = Graph(); g.parse('tmp/combined-pipeline.ttl', format='turtle'); print(f'Loaded {len(g)} triples')"`

### Out of Memory
- Reduce batch size: `--batch-size 500` instead of 1000
- Process stages individually instead of combined
- Increase system RAM or virtual memory

## Architecture

The pipeline follows a strict 10-stage architecture with immutable ontologies:

```
Stage 1-10 (ETL):     Raw data → RDF Turtle
   ↓ (Combine)
Single TTL file:      All 10 stages merged
   ↓ (Load)
Neo4j graph:          Queryable knowledge graph
   ↓ (Query)
Causal chain:         CVE → CWE → CAPEC → Technique → Defense
```

**Key Invariants:**
1. Each stage produces idempotent output (same input → same output)
2. Multi-file stages use append mode to accumulate data
3. Header deduplication when combining files
4. Provenance metadata preserved (source_uri, source_hash, timestamp)
5. No circular dependencies in imports

## Validation

Optional: Validate outputs with SHACL before loading:

```bash
# Validate individual stage
python scripts/validate_shacl_stream.py --data tmp/pipeline-stage1-cpe.ttl --shapes docs/ontology/shacl/cpe-shapes.ttl

# Validate all outputs
python scripts/validate_all_standards.py
```

## References

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 5-phase roadmap
- [KGCS.md](../docs/KGCS.md) - Executive summary
- [GLOSSARY.md](../docs/GLOSSARY.md) - Standard definitions
- [D3FEND_DATA_RECOVERY.md](../docs/D3FEND_DATA_RECOVERY.md) - D3FEND fix details

---

**Total Pipeline Time:** ~3-4 hours (download + ETL + combine + load)  
**Last Run:** February 3, 2026 @ 17:47  
**Status:** ✅ Production Ready
