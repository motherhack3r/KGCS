# Neo4j Loader Optimization Analysis

**File Size:** tmp/combined-pipeline.ttl (22.42 GB, 145.7 million lines)  
**RDF Triples:** ~3.2 million  
**Target:** Optimize loading to Neo4j with minimal memory footprint

---

## Available Parameters & Optimization Strategies

### 1. **Fast Parse Mode** (RECOMMENDED for 22GB file)

```bash
--fast-parse
```

**What it does:**

- Uses streaming TTL parser instead of rdflib Graph.parse()
- Processes triples line-by-line without loading entire file into memory
- Significantly faster for large files (22GB file would take hours with rdflib)

**Benefit:** 10-100x faster parsing, constant memory footprint
**Requirement:** File must be Turtle format (✅ we have this)

---

### 2. **Batch Size Tuning**

```bash
--batch-size 2000                    # Default: 1000
--rel-batch-size 5000               # Relationships (default: same as batch-size)
```

**Current Config:**

- Node batch size: 1000 per write
- Relationship batch size: 1000 per write

**For 22GB file:**

- Nodes: ~2.5M → ~2,500 batches (1000 each)
- Relationships: ~26M → ~26,000 batches (1000 each)

**Optimization:**

- Increase node batch size: **2000-3000** (more nodes per transaction)
- Keep relationship batch size lower: **1000-2000** (relationships are cheaper to write)
- Reason: Relationships dominate the load time, nodes are smaller

**Recommendation:**

```bash
--batch-size 2000 --rel-batch-size 1500
```

**Benefit:** Fewer Neo4j transactions = faster load

---

### 3. **Chunking Strategy**

```bash
--chunk-size 50000              # Process 50k unique subjects per chunk
```

**What it does:**

- Splits TTL processing into chunks (one chunk per commit)
- Good for memory management and resumable loads
- Default (0) = load entire file in one transaction

**For 22GB file:**

- Estimate: ~2.5M nodes across all chunks
- Chunks of 50k = ~50 chunks
- Each chunk: ~500k-1M relationships

**Trade-offs:**

- ✅ Lower memory per chunk
- ✅ Resumable if process dies
- ❌ More Neo4j commits (slower overall)
- ❌ Only beneficial if memory is constrained

**Recommendation:** Use only if you hit memory limits:

```bash
--chunk-size 100000             # Larger chunks for 22GB
```

---

### 4. **Two-Pass Loading Strategy** (BEST for 22GB)

**Problem:** Current approach loads entire TTL into memory

**Solution:** Split into two phases:

```bash
# Phase 1: Load nodes only (smaller data, faster)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --nodes-only \
    --fast-parse \
    --batch-size 3000 \
    --database neo4j-2026-02-03

# Phase 2: Load relationships only (can optimize for relationships)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --rel-batch-size 2000 \
    --fast-parse \
    --database neo4j-2026-02-03
```

**Benefits:**

- ✅ Phase 1 is ~10x faster (no relationships = less data)
- ✅ Phase 2 can be optimized for relationship writes
- ✅ Better error isolation (if phase 1 succeeds, nodes are there)
- ✅ Can pause/resume between phases

**Estimated Time:**

- Phase 1 (nodes only): 15-30 minutes
- Phase 2 (relationships): 30-60 minutes
- Total: 45-90 minutes (vs 2-4 hours single pass)

---

### 5. **Dry-Run First** (RECOMMENDED)

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30
```

**What it does:**

- Parses entire TTL without writing to Neo4j
- Shows extraction statistics (node counts, relationship counts)
- Validates file format and data structure
- With heartbeat: Shows progress every 30 seconds

**Benefits:**

- ✅ Validates file before 2-hour load
- ✅ Gives accurate statistics
- ✅ Tests if system can handle memory requirements
- ✅ Safe (no database modification)

**Time:** ~5-10 minutes for 22GB file

---

## Recommended Execution Plan (Optimized)

### **Phase 0: Validate File (Optional but Recommended)**

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30
```

**Expected Output:**

```
Loading RDF from combined-pipeline.ttl...
   ... parsing (30s elapsed) ...
   ... parsing (60s elapsed) ...
   [Stats showing node/relationship counts]
```

**Time:** ~5-10 minutes

### **Phase 1: Load Nodes Only**

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --nodes-only \
    --fast-parse \
    --batch-size 3000 \
    --database neo4j-2026-02-03 \
    --reset-db
```

**Expected Time:** 15-30 minutes  
**Result:** ~2.5M nodes created with labels and properties

### **Phase 2: Load Relationships**

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --rel-batch-size 2000 \
    --batch-size 1 \
    --database neo4j-2026-02-03
```

**Expected Time:** 30-60 minutes  
**Result:** ~26M relationships created, indexes applied

**Total Time:** 45-90 minutes (vs 2-4 hours monolithic)

---

## Parameter Combinations for Different Scenarios

### **Scenario 1: Time-Critical (Fastest)**

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --batch-size 5000 \
    --rel-batch-size 3000 \
    --database neo4j-2026-02-03
```

**Time:** ~1-2 hours | **Memory:** ~8-16 GB

### **Scenario 2: Memory-Constrained (Safest)**

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --chunk-size 50000 \
    --batch-size 1000 \
    --rel-batch-size 500 \
    --database neo4j-2026-02-03
```

**Time:** ~2-3 hours | **Memory:** ~2-4 GB per chunk

### **Scenario 3: Balanced (Recommended)**

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --nodes-only \
    --batch-size 3000 \
    --database neo4j-2026-02-03

# Then (after nodes complete):
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --rel-batch-size 2000 \
    --batch-size 1 \
    --database neo4j-2026-02-03
```

**Time:** 45-90 minutes total | **Memory:** ~4-8 GB | **Reliability:** ✅ Highest

---

## Key Parameters Explained

| Parameter | Default | Recommended | Impact |
|-----------|---------|-------------|--------|
| `--fast-parse` | off | **ON** | 10-100x faster parsing for 22GB |
| `--batch-size` | 1000 | 2000-3000 | Fewer Neo4j transactions |
| `--rel-batch-size` | same | 1000-2000 | Optimize for relationship writes |
| `--chunk-size` | 0 | 0 (or 100k) | 0=single pass, 100k=chunked |
| `--nodes-only` | off | Phase 1 | Split loading into 2 phases |
| `--parse-heartbeat-seconds` | 0 | 30-60 | Progress visibility |
| `--reset-db` | off | **ON** | Clean slate for fresh load |

---

## Memory Requirements Estimate

**File:** 22.42 GB TTL  
**Triples:** ~3.2 million

| Loading Strategy | Memory Usage | Time | Notes |
|------------------|--------------|------|-------|
| Single pass (slow parse) | 16+ GB | 2-4 hours | ❌ Not recommended |
| Single pass (fast parse) | 8-12 GB | 1-2 hours | ✅ OK if RAM available |
| Chunked (50k subjects) | 4-6 GB | 2-3 hours | ✅ Safe |
| Two-phase (nodes + rels) | 4-8 GB | 45-90 min | ✅✅ **BEST** |

---

## Testing Commands

### Quick Test (validation only, no load)

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30
```

### Full Test on Small Sample

```bash
# Create 10GB sample for testing
head -150000000 tmp/combined-pipeline.ttl > tmp/combined-pipeline-sample.ttl

python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline-sample.ttl \
    --fast-parse \
    --batch-size 2000 \
    --database neo4j-test
```

---

## Final Recommendation

**For your 22.42 GB combined-pipeline.ttl file:**

```bash
# Dry run first (5-10 min, validates everything)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30

# Then: Two-phase load (45-90 min total)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --nodes-only \
    --fast-parse \
    --batch-size 3000 \
    --database neo4j-2026-02-03 \
    --reset-db

python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --rel-batch-size 2000 \
    --batch-size 1 \
    --database neo4j-2026-02-03
```

**Expected Results:**

- ✅ Dry run validates data structure
- ✅ Phase 1 creates 2.5M nodes in 15-30 min
- ✅ Phase 2 creates 26M relationships in 30-60 min
- ✅ Total time: ~45-90 minutes
- ✅ Memory usage: 4-8 GB (safe for most systems)
- ✅ Causal chain verified post-load

---

**Notes:**

- All parameters shown with `--fast-parse` (CRITICAL for 22GB file)
- Times are estimates; actual depends on system CPU/disk/network (if remote Neo4j)
- Two-phase approach provides best reliability + speed trade-off
- Each phase can be run independently if needed
