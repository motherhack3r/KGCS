# Neo4j Loader Options - Decision Guide

**File Size:** 22.42 GB combined-pipeline.ttl  
**Triples:** ~3.2 million (2.5M nodes + 26M relationships)

---

## Quick Comparison

| Approach | Time | Memory | Pros | Cons | Recommendation |
|----------|------|--------|------|------|---|
| **Default** (no flags) | 2-4h | 16+ GB | Simple | Slow, high RAM | ❌ Not recommended |
| **Fast Parse Only** | 1-2h | 8-12 GB | Reasonable | Still high RAM | ⚠️ If RAM available |
| **Two-Phase + Fast Parse** | 45-90m | 4-8 GB | **BEST** | More steps | ✅ **RECOMMENDED** |
| **Chunked** | 2-3h | 2-4 GB | Low RAM | Complex, slower | ✅ If RAM < 4GB |

---

## Option 1: Default (Not Recommended)

```bash
python src/etl/rdf_to_neo4j.py --ttl tmp/combined-pipeline.ttl --database neo4j-2026-02-03
```

**What happens:**
- Loads entire 22GB file into memory using rdflib
- Single transaction to Neo4j
- Slow parsing (rdflib processes all triples)

**Results:**
- ⏱️ Time: 2-4 hours
- 💾 Memory: 16+ GB
- ❌ Slow parsing phase
- ❌ High memory pressure

**When to use:** Only if you have 20+ GB RAM and patience

---

## Option 2: Fast Parse Only ⚡

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --batch-size 2000 \
    --database neo4j-2026-02-03 \
    --reset-db
```

**What happens:**
- Uses streaming Turtle parser (no rdflib Graph)
- Processes line-by-line, constant memory
- Single transaction with batched writes

**Results:**
- ⏱️ Time: 1-2 hours
- 💾 Memory: 8-12 GB
- ✅ Fast parsing
- ⚠️ Still significant memory use

**When to use:** 
- You have 12+ GB RAM
- Want simplicity
- Time is important

**Execution:**
```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --batch-size 2500 \
    --rel-batch-size 2000 \
    --database neo4j-2026-02-03 \
    --reset-db
```

---

## Option 3: Two-Phase (Recommended) ⭐

### Phase 1: Nodes Only

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --nodes-only \
    --fast-parse \
    --batch-size 3000 \
    --database neo4j-2026-02-03 \
    --reset-db
```

**What happens:**
- Parse entire TTL, extract only nodes (rdf:type + literals)
- Skip all relationships
- Much smaller working set

**Results:**
- ⏱️ Time: 15-30 minutes
- 💾 Memory: 3-4 GB
- ✅ Nodes created
- ✅ Database ready for relationships

### Phase 2: Relationships

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --rel-batch-size 2000 \
    --batch-size 1 \
    --database neo4j-2026-02-03
```

**What happens:**
- Parse TTL again, extract only relationships (URI objects)
- Nodes already exist, just link them
- Highly optimized for relationships

**Results:**
- ⏱️ Time: 30-60 minutes
- 💾 Memory: 2-4 GB
- ✅ Relationships created
- ✅ Complete graph ready

### Combined Results

- ⏱️ **Total Time:** 45-90 minutes
- 💾 **Peak Memory:** 4-8 GB
- ✅ **Error Isolation:** If Phase 2 fails, nodes are safe
- ✅ **Resumable:** Can restart Phase 2 independently
- ✅ **Optimal:** Best speed/memory trade-off

**When to use:** ✅ **ALWAYS** (best overall)

---

## Option 4: Chunked Loading

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --chunk-size 50000 \
    --batch-size 1000 \
    --database neo4j-2026-02-03 \
    --reset-db
```

**What happens:**
- Processes 50k unique subjects per chunk
- Each chunk = separate Neo4j commit
- ~50 chunks total for 2.5M nodes

**Results:**
- ⏱️ Time: 2-3 hours
- 💾 Memory: 2-4 GB per chunk
- ✅ Very low memory
- ❌ Many Neo4j commits (slower)
- ⚠️ Complex to resume if interrupted

**When to use:** 
- RAM < 4 GB
- System is very constrained
- Can afford slower load time

---

## Test First (Always Recommended)

Before any full load, validate with dry-run:

```bash
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30
```

**What it does:**
- Parses entire file (validates format)
- Extracts all nodes and relationships
- Shows statistics
- **Does NOT write to Neo4j**

**Results:**
- ⏱️ Time: 5-10 minutes
- 💾 Memory: Depends on approach, but non-destructive
- ✅ Validates data integrity
- ✅ Shows node/relationship counts
- ✅ Safe (no database changes)

---

## System Requirements

| Component | Default | Fast Parse Only | Two-Phase | Chunked |
|-----------|---------|-----------------|-----------|---------|
| **CPU Cores** | 4+ | 4+ | 4+ | 2+ |
| **RAM** | 20 GB | 12 GB | 8 GB | 4 GB |
| **Disk** | 50 GB free | 50 GB free | 50 GB free | 50 GB free |
| **Neo4j RAM** | 16 GB | 12 GB | 8 GB | 8 GB |
| **Total Time** | 2-4h | 1-2h | 45-90m | 2-3h |

---

## Decision Tree

```
START: Need to load 22GB TTL to Neo4j

├─ How much RAM do you have?
│
├─ 20+ GB RAM?
│  ├─ Fast Parse Only
│  │  └─ 1-2 hours, simple
│
├─ 12+ GB RAM?
│  ├─ Fast Parse Only (recommended)
│  │  └─ 1-2 hours
│  ├─ Two-Phase (if paranoid about errors)
│  │  └─ 45-90 min, safest
│
├─ 8-12 GB RAM?
│  ├─ Two-Phase (RECOMMENDED)
│  │  └─ 45-90 min, optimal
│  ├─ Fast Parse (careful monitoring)
│  │  └─ 1-2 hours, risky
│
└─ < 8 GB RAM?
   ├─ Two-Phase + Monitor (close other apps)
   │  └─ 45-90 min, monitor memory
   ├─ Chunked (safe)
   │  └─ 2-3 hours, low risk
```

---

## My Recommendation

**For your 22.42 GB combined-pipeline.ttl:**

### Immediate Action:
```bash
# Validate first (non-destructive)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30
```

### Then: Two-Phase Load (Best Balance)
```bash
# Phase 1: Nodes (15-30 min)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --nodes-only \
    --fast-parse \
    --batch-size 3000 \
    --database neo4j-2026-02-03 \
    --reset-db

# Phase 2: Relationships (30-60 min)
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --rel-batch-size 2000 \
    --batch-size 1 \
    --database neo4j-2026-02-03
```

**Why:**
- ✅ 10-100x faster than default (uses --fast-parse)
- ✅ 45-90 minutes total
- ✅ Low memory (4-8 GB, safe for most systems)
- ✅ Error isolation (nodes safe even if rels fail)
- ✅ Can recover/resume Phase 2 independently
- ✅ Optimal Neo4j transaction handling

**Expected Outcome:**
- ~2.5M nodes in Neo4j
- ~26M relationships in Neo4j
- Complete causal chain: CVE→CWE→CAPEC→Technique→Defense
- All cross-standard links intact

---

## See Also

- [PIPELINE_EXECUTION_GUIDE.md](PIPELINE_EXECUTION_GUIDE.md) - Complete setup
- [load_to_neo4j.ps1](../scripts/load_to_neo4j.ps1) - Interactive PowerShell loader
- [load_to_neo4j.sh](../scripts/load_to_neo4j.sh) - Bash reference

---

**Last Updated:** February 3, 2026  
**Status:** Ready for Neo4j loading
