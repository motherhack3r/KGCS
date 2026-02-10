# KGCS Data Pipeline: Complete Setup & Execution Guide

**Last Updated:** February 10, 2026  
**Status:** Production Ready (Phase 3 MVP)

## Quick Start (6 Steps)

```bash
# Step 1: Activate conda environment
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\software\miniconda\envs\metadata
cd e:\DEVEL\LAIA\KGCS

# Step 2: Download all raw data from authoritative sources
python -m src.ingest.download_manager

# Step 3: Run ETL pipeline (transforms raw data to RDF Turtle)
python scripts/run_all_etl.py

# Step 4: Validate outputs with SHACL (recommended)
# Run SHACL validation for all standards before combining/loading
python scripts/validation/validate_all_standards.py

# Step 5: Combine all TTL outputs into nodes + relationships files (optional)
python scripts/combine_ttl_pipeline.py --nodes-out tmp/combined-nodes.ttl --rels-out tmp/combined-rels.ttl
```

Note: ETL output locations

- Stages 1–10 write per-standard TTLs into `data/{standard}/samples/`.
- `tmp/` is used only for intermediate chunked processing and combined outputs.
- `scripts/combine_ttl_pipeline.py` auto-discovers stage TTLs under both `data/*/samples/` and `tmp/`.

```bash
# Step 6: Load to Neo4j (nodes first, then relationships)
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-nodes.ttl --db-version 2026-02-08 --reset-db --nodes-only
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-rels.ttl --db-version 2026-02-08 --rels-only
```

Recommended safe two-step load (nodes first, then relationships)

Prepare DB and load nodes-only (creates DB + indexes):

```bash
python src/etl/rdf_to_neo4j.py \
   --ttl tmp/combined-nodes.ttl \
   --chunk-size 20000 \
   --fast-parse \
   --progress-newline \
   --parse-heartbeat-seconds 30 \
   --db-version 2026-02-08 \
   --reset-db \
   --nodes-only
```

After nodes complete, load relationships-only (do NOT use `--reset-db`):

```bash
python src/etl/rdf_to_neo4j.py \
   --ttl tmp/combined-rels.ttl \
   --chunk-size 20000 \
   --fast-parse \
   --progress-newline \
   --parse-heartbeat-seconds 30 \
   --db-version 2026-02-08 \
   --rel-batch-size 1000 \
   --rels-only
```

Notes:

- `--workers` is used only for dry-run estimation and is ignored for actual writes.
- Run a `--dry-run --workers 4` first to estimate label and relationship counts without writing.
- Verify node counts after the nodes-only step before running the relationships-only step.

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

# Run ETL and combine stages (combine is optional for per-standard loads)
python scripts/run_all_etl.py
python scripts/combine_ttl_pipeline.py --nodes-out tmp/combined-nodes.ttl --rels-out tmp/combined-rels.ttl

# Optional: produce a single full-load file (nodes then relationships)
# Useful when your loader accepts a single input file. Use `--full-out` to write a concatenated file.
python scripts/combine_ttl_pipeline.py --inputs tmp/pipeline-stage6-capec.nt tmp/pipeline-stage7-cwe.nt \
    --nodes-out tmp/selected-nodes.nt --rels-out tmp/selected-rels.nt --full-out tmp/selected-full.nt

# Load to Neo4j using the helper wrappers (nodes then relationships)
.\scripts\load_nodes_all.ps1 -DbVersion 2026-02-08 -FastParse -ProgressNewline
.\scripts\load_rels_all.ps1 -DbVersion 2026-02-08 -FastParse -ProgressNewline
```

See Appendix for verification notes and troubleshooting.

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
- **CWE** (MITRE): 1 XML file (cwe_latest.xml) → `data/cwe/raw/`; also downloads the CWE XSD → `data/cwe/schemas/`
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
   - Output: `data/cpe/samples/pipeline-stage1-cpe.ttl` (~2.5 GB)
   - Processing: Loop with append mode, accumulate all chunks

2. **Stage 2: CPEMatch** (55 chunks)
   - Input: `data/cpematch/raw/*.json` (chunked)
   - Output: `data/cpe/samples/pipeline-stage2-cpematch.ttl` (~18.7 GB)
   - Processing: Loop with append mode, accumulate all chunks
   - **Note:** This is the largest stage - creates 614k PlatformConfiguration nodes

3. **Stage 3: CVE** (25 files)
   - Input: `data/cve/raw/nvdcve-2.0-*.json` (one per year)
   - Output: `data/cve/samples/pipeline-stage3-cve.ttl` (~1.8 GB)
   - Processing: Loop with append mode, accumulate all years
   - Links CVE → CWE relationships

4. **Stage 4: ATT&CK** (4 variants)
   - Input: `data/attack/raw/enterprise|ics|mobile|pre.json`
   - Output: `data/attack/samples/pipeline-stage4-attack.ttl` (~3.3 MB)
   - Processing: Loop with append mode, merge all variants

5. **Stage 5: D3FEND** (2 files) ⭐ ENHANCED
   - Input: `data/d3fend/raw/d3fend.json` + `d3fend-full-mappings.json`
   - Output: `data/d3fend/samples/pipeline-stage5-d3fend.ttl` (~0.43 MB)
   - Processing: Loop with append mode
   - **New:** SPARQL binding extraction yields 3,109 D3FEND→Technique relationships

6. **Stage 6: CAPEC**
   - Input: `data/capec/raw/capec_latest.xml`
   - Output: `data/capec/samples/pipeline-stage6-capec.ttl` (~1.67 MB)
   - Processing: Single file
   - Links CAPEC → ATT&CK Technique (271 relationships)

7. **Stage 7: CWE**
   - Input: `data/cwe/raw/cwe_latest.xml`
   - Output: `data/cwe/samples/pipeline-stage7-cwe.ttl` (~1.31 MB)
   - Processing: Single file
   - Parent/child hierarchy preserved

8. **Stage 8: CAR** (122 analytics)
   - Input: `data/car/raw/**/*.yaml`
   - Output: `data/car/samples/pipeline-stage8-car.ttl` (~0.14 MB)
   - Processing: Loop with append mode, accumulate all YAML files
   - Links CAR analytics → ATT&CK Techniques

9. **Stage 9: SHIELD** (12 files)
   - Input: `data/shield/raw/*.json`
   - Output: `data/shield/samples/pipeline-stage9-shield.ttl` (~0.31 MB)
   - Processing: Directory merge (loads all in memory)
   - Deception techniques

10. **Stage 10: ENGAGE** (12 files)
   - Input: `data/engage/raw/*.json`
   - Output: `data/engage/samples/pipeline-stage10-engage.ttl` (~0.05 MB)
   - Processing: Directory merge (loads all in memory)
   - Strategic engagement concepts

**Output:**

- Stage TTLs in `data/{standard}/samples/`
- Split outputs alongside each stage: `pipeline-stageX-*-nodes.ttl` and `pipeline-stageX-*-rels.ttl`
- Total: ~28.6 GB of RDF data
- Log: `logs/etl_run_*.log`

**Time:** ~1-2 hours depending on system performance

**IMPORTANT:** Do NOT run monitoring commands while ETL is running - it may interrupt the background job!

### Step 4: Combine TTL Files

Combine stage outputs into nodes and relationships TTLs (streaming, memory-safe):

```bash
python scripts/combine_ttl_pipeline.py --nodes-out tmp/combined-nodes.ttl --rels-out tmp/combined-rels.ttl
```

Options:

- `--heuristic-threshold N` — file size in bytes above which the combine step will use a simple line-based heuristic instead of rdflib parsing (default ~200MB).
- `--node-predicate <URI>` — repeatable; force triples whose predicate contains this substring into the nodes file.

**Output:**

- `tmp/combined-nodes.ttl`
- `tmp/combined-rels.ttl`
- Log: `logs/combine_ttl.log`

**Time:** ~5-10 minutes

If you still need a separate splitter utility for special cases, `scripts/utilities/split_ttl.py` remains available as a fallback (it parses a single TTL and emits nodes/rels outputs).

See Appendix for the selected-standards workflow, tuning notes, and troubleshooting tips.

### Step 5: Load to Neo4j

Load RDF into Neo4j using a nodes-first then relationships-second approach (recommended). The loader supports chunked, streaming parsing and a variety of tuning options to match your machine resources.

Quick workflow (recommended):

1. Dry-run to estimate counts (uses --workers to parallelize estimation):

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-nodes.ttl --chunk-size 50000 --fast-parse --dry-run --workers 8 --progress-newline
```

1. Nodes load (reset DB, create indexes, load nodes):

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-nodes.ttl --chunk-size 100000 --fast-parse --batch-size 20000 --db-version 2026-02-08 --reset-db --nodes-only --progress-newline --parse-heartbeat-seconds 30
```

1. Relationships load (no reset):

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-rels.ttl --chunk-size 100000 --fast-parse --batch-size 20000 --rel-batch-size 5000 --db-version 2026-02-08 --rels-only --progress-newline --parse-heartbeat-seconds 30
```

Processing performed by the loader:

- Chunking (optional) to break the TTL into manageable pieces
- Streaming extraction of nodes and relationship triples
- Create constraints and indexes (unique constraints on key properties and URI indexes)
- Two-pass load: nodes first (create/merge nodes), relationships second (MERGE relationships between existing nodes)

Expected time depends on hardware and Neo4j configuration; on a modern workstation with tuned Neo4j, nodes + relationships can complete in under an hour but may take longer for very large datasets.

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
python scripts/validation/validate_shacl_stream.py --data tmp/pipeline-stage1-cpe.ttl --shapes docs/ontology/shacl/cpe-shapes.ttl

# Validate all outputs
python scripts/validation/validate_all_standards.py
```

## Appendix: Development Notes and Troubleshooting

### Verification Notes

**Verification note (Feb 8, 2026):** After activating the `metadata` conda environment (Step 1), running the downloader (`python -m src.ingest.download_manager`) successfully fetched raw files, wrote per-standard manifests (`data/{standard}/manifest.json`), and saved official schemas under `data/{standard}/schemas/` (for example, CVSS JSON schemas under `data/cve/schemas/`).

### Combine Fallback (if auto-discovery is unavailable)

```powershell
# Copy per-standard samples into tmp/ (idempotent)
Get-ChildItem -Path data\*\samples -Filter pipeline-stage*-*.ttl -Recurse | ForEach-Object { Copy-Item $_.FullName -Destination tmp -Force }
python scripts/combine_ttl_pipeline.py
```

### E2E Run for Selected Standards (nodes-first, rels-second)

Use this when you want to run the pipeline only for a subset of standards (for faster iteration or debugging). The pattern is:

1. Run ETL for each selected standard and emit N-Triples (one triple per line) using `--format nt` so normalization is guaranteed:

```bash
# Example: run CWE and CAR only (writes to tmp/)
python -m src.etl.etl_cwe --input data/cwe/samples/sample_cwe.json --output tmp/pipeline-stage7-cwe.nt --format nt
python -m src.etl.etl_car --input data/car/samples --output tmp/pipeline-stage8-car.nt --format nt
```

1. Combine only the `tmp/` pipeline-stage files (the combine script auto-discovers `.ttl` and `.nt`):

```bash
python scripts/combine_ttl_pipeline.py --nodes-out tmp/selected-nodes.nt --rels-out tmp/selected-rels.nt
```

1. Validate combined outputs with SHACL (mandatory):

```bash
python scripts/validation/validate_all_standards.py --input tmp/selected-nodes.nt
# or run targeted shape checks for the standards involved
```

1. Dry-run the Neo4j loader to inspect label & relationship counts and reveal missing types or subjects:

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/selected-nodes.nt --fast-parse --dry-run --workers 4
```

1. Load nodes-only for the selected standards (create DB, indexes, insert nodes):

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/selected-nodes.nt --reset-db --nodes-only --chunk-size 50000 --fast-parse
```

1. Load relationships-only (no reset):

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/selected-rels.nt --rels-only --rel-batch-size 1000 --fast-parse
```

Notes & troubleshooting:

- Use `--dry-run` first to avoid partial writes and to inspect diagnostics (`logs/combine-*.json` and `logs/bad_node_subjects.log`).
- If the combine diagnostics show `bad_node_subjects_count > 0`, fix the originating ETL (do not fabricate types) and re-run the ETL + combine steps.
- Keep ETL pipeline outputs in *N-Triples* format for the pipeline (human-readable TTL can still be generated separately if needed).
- For large selections, run nodes load in the KGCS-prescribed causal order (CPE → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}) to ensure relationship targets exist before rel ingestion.

### Loader Tuning Notes

- `--chunk-size` — number of unique subjects per chunk. Use chunking (50k–100k) to avoid large in-memory loads and to parallelize work across chunks.
- `--fast-parse` — use the streaming extractor to avoid building an rdflib Graph for very large TTLs.
- `--batch-size` — controls node insert batch size (5k–20k). Increase if Neo4j can handle larger transactions.
- `--rel-batch-size` — relationship insert batch size (start at 1k).
- `--reset-db` — drop & recreate the target versioned DB (requires admin privileges); fallback is `MATCH (n) DETACH DELETE n`.
- `--db-version` — append a version suffix to the configured DB name so you can create/reset a versioned DB safely.
- `--progress-newline` — print progress updates as new lines (useful for log capture).
- `--parse-heartbeat-seconds` — heartbeat interval during long parses (e.g., 30s).

### Expected Output Sizes

After complete pipeline execution:

```text
data/cpe/samples/pipeline-stage1-cpe.ttl            2,472.68 MB   (15 chunks)
data/cpe/samples/pipeline-stage2-cpematch.ttl      18,689.66 MB   (55 chunks)
data/cve/samples/pipeline-stage3-cve.ttl            1,792.56 MB   (25 files)
data/attack/samples/pipeline-stage4-attack.ttl          3.29 MB   (4 variants)
data/d3fend/samples/pipeline-stage5-d3fend.ttl          0.43 MB   (2 files)
data/capec/samples/pipeline-stage6-capec.ttl           1.67 MB   (1 file)
data/cwe/samples/pipeline-stage7-cwe.ttl               1.31 MB   (1 file)
data/car/samples/pipeline-stage8-car.ttl               0.14 MB   (122 files)
data/shield/samples/pipeline-stage9-shield.ttl         0.31 MB   (12 files)
data/engage/samples/pipeline-stage10-engage.ttl        0.05 MB   (12 files)
────────────────────────────────────────────────────────────────
tmp/combined-nodes.ttl + tmp/combined-rels.ttl     ~28,600 MB   (combined total)
```

**Total RDF triples:** ~3.2M triples across all standards

### Troubleshooting

#### Download Fails

- Check network connectivity
- Review `logs/download_manager.log` for failed URLs
- Manually download from NVD/MITRE and place in `data/{standard}/raw/`

#### ETL Produces Small Output

- Check if input files exist: `Get-ChildItem data/{standard}/raw/`
- Review `logs/etl_run_*.log` for errors
- Verify file format matches expected (JSON, XML, YAML)
- For multi-file stages, ensure append mode is working (check for increasing file sizes)

#### Neo4j Load Fails

- Verify Neo4j service is running: `neo4j status`
- Check database connection: `neo4j console`
- Review Neo4j logs: `logs/neo4j.log`
- Ensure combined TTL file is valid: `python -c "from rdflib import Graph; g = Graph(); g.parse('tmp/combined-nodes.ttl', format='turtle'); print(f'Loaded {len(g)} triples')"`

#### Out of Memory

- Reduce batch size: `--batch-size 500` instead of 1000
- Process stages individually instead of combined
- Increase system RAM or virtual memory

## References

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 5-phase roadmap
- [KGCS.md](../docs/KGCS.md) - Executive summary
- [GLOSSARY.md](../docs/GLOSSARY.md) - Standard definitions
- [D3FEND_DATA_RECOVERY.md](../docs/D3FEND_DATA_RECOVERY.md) - D3FEND fix details

---

**Total Pipeline Time:** ~3-4 hours (download + ETL + combine + load)  
**Last Run:** February 3, 2026 @ 17:47  
**Status:** ✅ Production Ready
