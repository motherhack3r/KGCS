#!/bin/bash
# KGCS Neo4j Loading Commands - Quick Reference
# For 22.42 GB combined-pipeline.ttl file

# ============================================================
# STEP 1: VALIDATION (Recommended - 5-10 min)
# ============================================================

echo "=== STEP 1: Validate combined TTL file ==="
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --dry-run \
    --fast-parse \
    --parse-heartbeat-seconds 30

# If validation passes, proceed to loading:

# ============================================================
# STEP 2A: Load Nodes Only (15-30 min)
# ============================================================

echo "=== STEP 2A: Loading nodes only ==="
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --nodes-only \
    --fast-parse \
    --batch-size 3000 \
    --database neo4j-2026-02-03 \
    --reset-db

# After nodes finish, proceed to relationships:

# ============================================================
# STEP 2B: Load Relationships (30-60 min)
# ============================================================

echo "=== STEP 2B: Loading relationships ==="
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --rel-batch-size 2000 \
    --batch-size 1 \
    --database neo4j-2026-02-03

# ============================================================
# TOTAL TIME: ~45-90 minutes
# ============================================================

# ============================================================
# ALTERNATIVE: Single-Pass Load (if preferred)
# ============================================================

echo "=== Alternative: Single-pass load (1-2 hours) ==="
python src/etl/rdf_to_neo4j.py \
    --ttl tmp/combined-pipeline.ttl \
    --fast-parse \
    --batch-size 3000 \
    --rel-batch-size 2000 \
    --database neo4j-2026-02-03 \
    --reset-db

# ============================================================
# NOTES:
# ============================================================
# --fast-parse:         Critical for 22GB file (10-100x faster)
# --nodes-only:         Phase 1 loads just nodes (cheaper)
# --batch-size:         Number of nodes per Neo4j write (3000 recommended)
# --rel-batch-size:     Number of relationships per Neo4j write (2000 recommended)
# --database:           Target Neo4j database name
# --reset-db:           Drop and recreate database (use on first load)
# --parse-heartbeat:    Show progress every 30 seconds
#
# TWO-PHASE APPROACH:
#   - Phase 1 (nodes): Fast because no relationships
#   - Phase 2 (rels):  Can be optimized separately
#   - Total: Faster and more reliable than single-pass
#
# MEMORY USAGE:
#   - Two-phase: 4-8 GB (recommended)
#   - Single-pass: 8-12 GB
#   - Chunked (if needed): 2-4 GB per chunk
# ============================================================
