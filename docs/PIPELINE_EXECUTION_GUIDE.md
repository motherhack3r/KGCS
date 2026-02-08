# KGCS Data Pipeline: Complete Setup & Execution Guide

**Last Updated:** February 8, 2026  
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

Note: ETL output locations

- Stages 4–10 now write stage TTL outputs into per-standard sample folders: `data/{standard}/samples/`.
- Stages 1–3 (CPE, CPEMatch, CVE) also write stage TTLs into `data/{standard}/samples/` (before the pipeline places outputs in `tmp/`, may still be used for intermediate chunked processing).
- The combine step must therefore merge TTLs from both `tmp/` and `data/*/samples/`. If your `scripts/combine_ttl_pipeline.py` has not been updated to discover `data/*/samples/`, you can copy the per-standard sample TTLs into `tmp/` before running the combine script:

```powershell
# Copy per-standard samples into tmp/ (idempotent)
Get-ChildItem -Path data\*\samples -Filter pipeline-stage*-*.ttl -Recurse | ForEach-Object { Copy-Item $_.FullName -Destination tmp -Force }
python scripts/combine_ttl_pipeline.py
```

# Step 5: Load to Neo4j
python src/etl/rdf_to_neo4j.py --database neo4j-2026-02-08 --ttl tmp/combined-pipeline.ttl
```

### PowerShell Example (Windows)

```powershell
# PowerShell: activate conda, create logs, run downloader + ETL + combine + load
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\software\miniconda\envs\metadata
cd e:\DEVEL\LAIA\KGCS

# Ensure logs directory exists
if (!(Test-Path -Path logs)) { New-Item -ItemType Directory -Path logs }

# Run downloader (creates data/{standard}/raw, data/{standard}/schemas, manifests)
python -m src.ingest.download_manager

# Run ETL and combine stages
python scripts/run_all_etl.py
python scripts/combine_ttl_pipeline.py

# Load to Neo4j (example)
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-pipeline.ttl --batch-size 1000
```

**Verification note (Feb 8, 2026):** After activating the `metadata` conda environment (Step 1), running the downloader (`python -m src.ingest.download_manager`) successfully fetched raw files, wrote per-standard manifests (`data/{standard}/manifest.json`), and saved official schemas under `data/{standard}/schemas/` (for example, CVSS JSON schemas under `data/cve/schemas/`).

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

- **CPE** (NVD): 15 chunk files (nvdcpe-2.0) → `data/cpe/raw/` (chunked extraction created `nvdcpe-2.0-chunks`)
- **CPEMatch** (NVD): 55 chunk files (nvdcpematch-2.0) → `data/cpematch/raw/` (chunked extraction)
- **CVE** (NVD): 25 yearly files (nvdcve-2.0-2002.json … nvdcve-2.0-2026.json) → `data/cve/raw/`; also downloads the CVE JSON schema and related CVSS JSON schemas → `data/cve/schemas/`
- **CWE** (MITRE): 1 XML file (cwec_latest.xml) → `data/cwe/raw/`; also downloads the CWE XSD → `data/cwe/schemas/`
- **CAPEC** (MITRE): 1 XML file (capec_latest.xml) plus STIX (`stix-capec.json`) and XSD (`ap_schema_latest.xsd`) → `data/capec/raw/` and `data/capec/schemas/`
- **ATT&CK** (MITRE): 4 STIX variants (enterprise, ics, mobile, pre-attack) → `data/attack/raw/`
- **D3FEND** (MITRE): 4 files (d3fend.json, d3fend-full-mappings.json, d3fend.owl, d3fend.ttl) → `data/d3fend/raw/`
- **CAR** (MITRE): 122 YAML files → `data/car/raw/`
- **SHIELD** (MITRE): 12 JSON files → `data/shield/raw/`
- **ENGAGE** (MITRE): 12 JSON files → `data/engage/raw/`
- **CPE** (NVD): 15 chunk files (nvdcpe-2.0) → `data/cpe/raw/` (chunked extraction created `nvdcpe-2.0-chunks`) — approx. 100–800 MB depending on extraction (single zip ~757 MB)
- **CPEMatch** (NVD): 55 chunk files (nvdcpematch-2.0) → `data/cpematch/raw/` (chunked extraction) — approx. 125–800 MB depending on extraction
- **CVE** (NVD): 25 yearly files (nvdcve-2.0-2002.json … nvdcve-2.0-2026.json) → `data/cve/raw/`; also downloads the CVE JSON schema and related CVSS JSON schemas → `data/cve/schemas/` — approx. 10–800 MB total for raw files (individual years small; archive set ~hundreds MB)
- **CWE** (MITRE): 1 XML file (cwec_latest.xml) → `data/cwe/raw/`; also downloads the CWE XSD → `data/cwe/schemas/` — approx. 16 MB (XML + XSD)
- **CAPEC** (MITRE): 1 XML file (capec_latest.xml) plus STIX (`stix-capec.json`) and XSD (`ap_schema_latest.xsd`) → `data/capec/raw/` and `data/capec/schemas/` — approx. 2–4 MB
- **ATT&CK** (MITRE): 4 STIX variants (enterprise, ics, mobile, pre-attack) → `data/attack/raw/` — approx. 3–10 MB total
- **D3FEND** (MITRE): 4 files (d3fend.json, d3fend-full-mappings.json, d3fend.owl, d3fend.ttl) → `data/d3fend/raw/` — approx. 40–50 MB
- **CAR** (MITRE): 122 YAML files → `data/car/raw/` — approx. 1–5 MB
- **SHIELD** (MITRE): 12 JSON files → `data/shield/raw/` — approx. 0.5–2 MB
- **ENGAGE** (MITRE): 12 JSON files → `data/engage/raw/` — approx. 0.2–1 MB

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

```text
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

```text
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
