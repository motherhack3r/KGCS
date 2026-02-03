# Neo4j Knowledge Graph Load Plan - v1.0

**Date:** February 3, 2026  
**Status:** Ready for Execution  
**Target Database:** neo4j-2026-02-03-v1.0-enhanced-capec  
**Pipeline:** combined-pipeline-enhanced-capec.ttl (1.91 GB, 271 CAPEC→Technique relationships)

---

## 🎯 Objective

Create a production-quality, versioned Neo4j database containing:
- ✅ Complete causal chain: CVE→CWE→CAPEC→ATT&CK
- ✅ Enhanced CAPEC mapping (8.5x improvement: 36→271 relationships)
- ✅ All 9 standards integrated (CPE, CVE, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE)
- ✅ Proper graph constraints and indexes
- ✅ Production-ready schema

---

## 📋 Prerequisites Checklist

Before starting, verify:

- [ ] Neo4j installed and accessible (`bolt://localhost:7687` or configured URI)
- [ ] Neo4j credentials available (user/password in `.env` or environment)
- [ ] Combined pipeline exists: `tmp/combined-pipeline-enhanced-capec.ttl` (1.91 GB)
- [ ] Disk space available: ~10 GB (for TTL file + Neo4j database)
- [ ] Python environment active with dependencies: `pip list | grep rdflib neo4j`
- [ ] Git status clean: `git status` shows no uncommitted changes
- [ ] Recent backup of existing databases (if any)

**Verify Prerequisites:**
```bash
# Check Neo4j connection
python -c "from neo4j import GraphDatabase; gd = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); print('✅ Connected')"

# Check pipeline file
ls -lh tmp/combined-pipeline-enhanced-capec.ttl

# Check Python dependencies
python -m pip list | grep -E "rdflib|neo4j|pyshacl"
```

---

## 🚀 Execution Plan (5 Phases)

### Phase 1: Preparation (10-15 minutes)

**Goal:** Set up environment and verify all components

#### Step 1.1: Review Current State
```bash
# Check existing Neo4j databases
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as session:
    result = session.run('SHOW DATABASES')
    for record in result:
        print(record)
"

# Expected output: List of existing databases (e.g., neo4j-2026-01-29, system)
```

#### Step 1.2: Verify Pipeline File
```bash
# Check TTL file integrity
wc -l tmp/combined-pipeline-enhanced-capec.ttl
du -h tmp/combined-pipeline-enhanced-capec.ttl

# Spot-check file format (first 50 lines)
head -50 tmp/combined-pipeline-enhanced-capec.ttl
```

**Expected:**
- File size: ~1.9 GB
- Line count: ~2 million+ lines
- Format: Valid Turtle/RDF (starts with `@prefix` directives)

#### Step 1.3: Prepare Configuration
```bash
# Create/verify .env with Neo4j credentials
cat .env | grep NEO4J

# Expected output:
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=<your_password>
```

#### Step 1.4: Document Version Info
```bash
# Create version metadata
cat > tmp/neo4j-load-metadata.json <<EOF
{
  "database_name": "neo4j-2026-02-03-v1.0-enhanced-capec",
  "load_date": "2026-02-03",
  "version": "1.0",
  "pipeline_source": "combined-pipeline-enhanced-capec.ttl",
  "pipeline_size_gb": 1.91,
  "standards_included": ["CPE", "CVE", "CWE", "CAPEC", "ATT&CK", "D3FEND", "CAR", "SHIELD", "ENGAGE"],
  "features": [
    "Full causal chain (CVE→CWE→CAPEC→Technique)",
    "Enhanced CAPEC mapping (271 relationships, 8.5x improvement)",
    "Graph constraints (unique IDs)",
    "Production-ready indexes"
  ],
  "git_commit": "$(git rev-parse HEAD)",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD)"
}
EOF
cat tmp/neo4j-load-metadata.json
```

---

### Phase 2: Pre-Load Validation (15-20 minutes)

**Goal:** Ensure pipeline TTL is valid before loading

#### Step 2.1: Quick SHACL Validation
```bash
# Validate sample (first 10k lines) for syntax errors
head -10000 tmp/combined-pipeline-enhanced-capec.ttl | \
  python scripts/validation/validate_shacl_stream.py \
    --data /dev/stdin \
    --shapes docs/ontology/shacl/consolidated-shapes.ttl \
    --sample-only

# Expected output: PASS (or list of violations to fix)
```

#### Step 2.2: RDF Parsing Test
```bash
# Quick parse test (loads sample into memory)
python -c "
from rdflib import Graph
g = Graph()
# Load just first 100k lines for speed
import subprocess
result = subprocess.run(['head', '-100000', 'tmp/combined-pipeline-enhanced-capec.ttl'], 
                       capture_output=True, text=True)
g.parse(data=result.stdout, format='turtle')
print(f'✅ Loaded {len(g)} triples (sample)')
"

# Expected: ✅ Loaded [N] triples (sample)
```

#### Step 2.3: Document Expected Statistics
```bash
# From previous loads, we expect approximately:
cat > tmp/expected-load-statistics.txt <<EOF
Expected Node Counts:
  Platform (CPE):              ~1,560k nodes
  PlatformConfiguration:       ~614k nodes
  Vulnerability (CVE):         ~330k nodes
  Weakness (CWE):              ~950 nodes
  AttackPattern (CAPEC):       ~1.2k nodes
  Technique (ATT&CK):          ~1.1k nodes (techniques + sub-techniques)
  DefenseTechnique (D3FEND):   ~31 nodes
  DetectionAnalytic (CAR):     ~102 nodes
  DeceptionTechnique (SHIELD): ~33 nodes
  EngagementConcept (ENGAGE):  ~31 nodes
  
  TOTAL NODES: ~2.5M

Expected Relationship Counts:
  CVE → PlatformConfiguration: ~2.9M
  CVE → CWE:                   ~267k
  CWE → CAPEC:                 ~1.2k
  CAPEC → Technique:           271 (ENHANCED ⭐)
  Technique → Tactic:          ~500+
  
  TOTAL RELATIONSHIPS: ~26M+

Expected Graph Characteristics:
  - Full causal chain: CVE→CWE→CAPEC→Technique intact
  - CAPEC coverage: 271/568 techniques (31.2% vs 6.3% before)
  - Cross-standard links: All 9 standards connected
EOF
cat tmp/expected-load-statistics.txt
```

---

### Phase 3: Database Setup (5-10 minutes)

**Goal:** Create fresh database with proper configuration

#### Step 3.1: Create New Database
```bash
# Using Neo4j admin or via Cypher
python -c "
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

# Create new database
with driver.session() as session:
    try:
        session.run('CREATE DATABASE \`neo4j-2026-02-03-v1.0-enhanced-capec\`')
        print('✅ Database created: neo4j-2026-02-03-v1.0-enhanced-capec')
    except Exception as e:
        if 'already exists' in str(e):
            print('⚠️  Database already exists')
        else:
            raise
"
```

**Alternative (Neo4j Admin CLI):**
```bash
# If using Docker
docker exec neo4j neo4j-admin databases create neo4j-2026-02-03-v1.0-enhanced-capec

# Or local installation
/path/to/neo4j/bin/neo4j-admin databases create neo4j-2026-02-03-v1.0-enhanced-capec
```

#### Step 3.2: Configure Database Parameters
```bash
# Optional: Set Neo4j memory and performance tuning
# Edit neo4j.conf:
cat >> /path/to/neo4j/conf/neo4j.conf <<EOF
# Knowledge Graph Database Tuning (2026-02-03)
server.memory.heap.initial_size=4g
server.memory.heap.max_size=8g
server.memory.pagecache.size=2g
EOF

# Restart Neo4j if needed
# systemctl restart neo4j
```

#### Step 3.3: Verify Database Created
```bash
python -c "
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

with driver.session(database='neo4j-2026-02-03-v1.0-enhanced-capec') as session:
    result = session.run('RETURN 1 as status')
    print('✅ New database is accessible')
    
with driver.session() as session:
    result = session.run('SHOW DATABASES')
    for record in result:
        if 'enhanced-capec' in str(record):
            print(f'Database ready: {record}')
"
```

---

### Phase 4: Data Load (30-60 minutes)

**Goal:** Load TTL pipeline into Neo4j with progress tracking

#### Step 4.1: Run ETL Loader
```bash
# Execute the RDF to Neo4j loader
python src/etl/rdf_to_neo4j.py \
  --ttl tmp/combined-pipeline-enhanced-capec.ttl \
  --database neo4j-2026-02-03-v1.0-enhanced-capec \
  --batch-size 1000 \
  --verbose

# Expected output:
# [✓] Connecting to Neo4j...
# [✓] Database: neo4j-2026-02-03-v1.0-enhanced-capec
# [✓] Loading TTL file...
# [████████████████████] 100% (2.5M triples)
# [✓] Load complete: 2,500,000 nodes, 26,000,000 relationships
# [✓] Creating constraints...
# [✓] Creating indexes...
```

**Performance Expectation:**
- Load time: 30-60 minutes (depends on Neo4j instance size)
- Throughput: ~40k-100k triples/minute
- CPU: Will spike to high usage
- RAM: Monitor heap usage (should not exceed configured max)

#### Step 4.2: Monitor Progress
```bash
# In separate terminal, monitor Neo4j stats
while true; do
  python scripts/utilities/extract_neo4j_stats.py \
    --db neo4j-2026-02-03-v1.0-enhanced-capec
  sleep 30
done

# Or via Cypher (from Neo4j Browser):
# MATCH (n) RETURN labels(n) as label, count(*) as count ORDER BY count DESC
```

#### Step 4.3: Capture Load Logs
```bash
# Save loader output to file
python src/etl/rdf_to_neo4j.py \
  --ttl tmp/combined-pipeline-enhanced-capec.ttl \
  --database neo4j-2026-02-03-v1.0-enhanced-capec \
  --batch-size 1000 \
  --verbose 2>&1 | tee tmp/neo4j-load-2026-02-03.log

# Verify success
tail -20 tmp/neo4j-load-2026-02-03.log | grep -E "✓|complete"
```

---

### Phase 5: Post-Load Validation (20-30 minutes)

**Goal:** Verify data integrity and causal chain

#### Step 5.1: Extract Statistics
```bash
# Get comprehensive graph statistics
python scripts/utilities/extract_neo4j_stats.py \
  --db neo4j-2026-02-03-v1.0-enhanced-capec \
  --pretty > tmp/neo4j-stats-2026-02-03-v1.0.json

# Display summary
python -c "
import json
with open('tmp/neo4j-stats-2026-02-03-v1.0.json') as f:
    stats = json.load(f)
    
print('📊 LOAD STATISTICS')
print('=' * 50)
print(f\"Total Nodes: {stats.get('total_nodes'):,}\")
print(f\"Total Relationships: {stats.get('total_relationships'):,}\")
print()
print('By Type:')
for node_type, count in stats.get('nodes_by_label', {}).items():
    print(f\"  {node_type}: {count:,}\")
"
```

#### Step 5.2: Verify Causal Chain
```bash
# Test complete causal chain: CVE→CWE→CAPEC→Technique
python -c "
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

with driver.session(database='neo4j-2026-02-03-v1.0-enhanced-capec') as session:
    # Find sample CVE with complete chain
    query = '''
    MATCH (cve:Vulnerability)-[:caused_by]->(cwe:Weakness)
           -[:demonstrated_by]->(capec:AttackPattern)
           -[:implements]->(tech:Technique)
    RETURN cve.cveId, cwe.cweId, capec.capecId, tech.techniqueId
    LIMIT 5
    '''
    results = session.run(query)
    
    print('✅ CAUSAL CHAIN VERIFICATION')
    print('=' * 60)
    for record in results:
        print(f\"CVE {record[0]} → CWE {record[1]} → CAPEC {record[2]} → {record[3]}\")
    
    # Count CAPEC→Technique relationships
    count_query = '''
    MATCH ()-[:implements]->(:Technique)
    RETURN count(*) as capec_technique_links
    '''
    count_result = session.run(count_query)
    for record in count_result:
        links = record['capec_technique_links']
        print(f\"\\n📈 CAPEC→Technique Links: {links:,} (Expected: 271)\")
        if links >= 271:
            print('✅ CAPEC enhancement verified!')
        else:
            print('⚠️  WARNING: Less than expected links')
"
```

#### Step 5.3: Run Verification Scripts
```bash
# Visual inspection of causal chain
python tests/verification/verify_causal_chain.py \
  --database neo4j-2026-02-03-v1.0-enhanced-capec

# Visual inspection of defense coverage
python tests/verification/verify_defense_layers.py \
  --database neo4j-2026-02-03-v1.0-enhanced-capec

# Expected output: Detailed chain analysis with no errors
```

#### Step 5.4: Run Integration Tests
```bash
# Verify with automated test suite
pytest tests/data_load/test_neo4j_data_load.py \
  -v --database neo4j-2026-02-03-v1.0-enhanced-capec

# Expected: All tests pass ✓
```

#### Step 5.5: Validate Constraints and Indexes
```bash
# Check that constraints were created
python -c "
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

with driver.session(database='neo4j-2026-02-03-v1.0-enhanced-capec') as session:
    # Check constraints
    constraints = session.run('SHOW CONSTRAINTS')
    print('📋 CONSTRAINTS:')
    constraint_count = 0
    for record in constraints:
        print(f\"  ✓ {record}\")
        constraint_count += 1
    
    print(f\"\\nTotal constraints: {constraint_count}\")
    
    # Check indexes
    indexes = session.run('SHOW INDEXES')
    print('\\n📑 INDEXES:')
    index_count = 0
    for record in indexes:
        print(f\"  ✓ {record}\")
        index_count += 1
    
    print(f\"\\nTotal indexes: {index_count}\")
"
```

---

## 📊 Success Criteria

**Database load is successful if:**

| Criterion | Check | Expected |
|-----------|-------|----------|
| Load completes without errors | Loader exit code | 0 |
| Nodes created | Total node count | ~2.5M |
| Relationships created | Total relationship count | ~26M |
| Causal chain intact | Sample path CVE→CWE→CAPEC→Technique | ≥100 examples |
| CAPEC enhancement | CAPEC→Technique links | ≥271 (31.2% of techniques) |
| Constraints applied | Unique ID constraints | Present for all standards |
| Indexes created | Primary indexes | Present for uri, cveId, cweId, etc. |
| Tests pass | pytest tests/data_load/ | All ✓ |
| Verification runs | Manual verification scripts | No errors |

---

## 🔄 Phase 3.5: Optional Defense Layer Enhancement

**After main load completes, optionally:**

#### Step 3.5.1: Create Defense Links (1-2 hours)
```bash
# Add D3FEND→Technique relationships
python scripts/utilities/add_defense_relationships.py \
  --database neo4j-2026-02-03-v1.0-enhanced-capec \
  --source d3fend \
  --link-type mitigated_by

# Add CAR→Technique relationships  
python scripts/utilities/add_detection_relationships.py \
  --database neo4j-2026-02-03-v1.0-enhanced-capec \
  --link-type detected_by

# Add SHIELD→Technique relationships
python scripts/utilities/add_deception_relationships.py \
  --database neo4j-2026-02-03-v1.0-enhanced-capec \
  --link-type countered_by
```

#### Step 3.5.2: Verify Defense Coverage
```bash
python -c "
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

with driver.session(database='neo4j-2026-02-03-v1.0-enhanced-capec') as session:
    query = '''
    MATCH (tech:Technique)
    OPTIONAL MATCH (tech)<-[:mitigated_by]-(d3fend:DefenseTechnique)
    OPTIONAL MATCH (tech)<-[:detected_by]-(car:DetectionAnalytic)
    OPTIONAL MATCH (tech)<-[:countered_by]-(shield:DeceptionTechnique)
    RETURN COUNT(DISTINCT tech) as techniques_with_defenses
    '''
    result = session.run(query)
    for record in result:
        print(f\"Techniques with defense coverage: {record[0]}\")
"
```

---

## ⚠️ Rollback Plan

**If load fails or needs to be reverted:**

#### Option 1: Drop Database
```bash
python -c "
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

with driver.session() as session:
    # Force terminate connections
    session.run('KILL TRANSACTIONS')
    
    # Drop database
    session.run('DROP DATABASE \`neo4j-2026-02-03-v1.0-enhanced-capec\` FORCE')
    print('✅ Database dropped')
"
```

#### Option 2: Restore Previous Database
```bash
# If you have a backup
neo4j-admin databases copy neo4j-2026-01-29 neo4j-restore-backup
```

---

## 🏁 Final Checklist

- [ ] Phase 1: Preparation complete
- [ ] Phase 2: Pre-load validation passed
- [ ] Phase 3: Database created successfully
- [ ] Phase 4: Load complete without errors
- [ ] Phase 5: All validation criteria met
- [ ] Statistics captured to JSON
- [ ] Verification scripts run successfully
- [ ] Tests pass (pytest)
- [ ] Load logs saved
- [ ] Version metadata documented
- [ ] Update PROJECT-STATUS-SUMMARY.md with new database info
- [ ] Commit load metadata to git

---

## 📝 Post-Load Documentation

**After successful load, create load summary:**

```bash
# Capture final state
python scripts/utilities/extract_neo4j_stats.py \
  --db neo4j-2026-02-03-v1.0-enhanced-capec \
  --pretty > tmp/neo4j-load-summary-2026-02-03-v1.0.json

# Generate report
cat > NEO4J-LOAD-REPORT-2026-02-03-V1.0.md <<EOF
# Neo4j Load Report - 2026-02-03 (v1.0 Enhanced CAPEC)

**Database Name:** neo4j-2026-02-03-v1.0-enhanced-capec  
**Load Date:** 2026-02-03  
**Pipeline:** combined-pipeline-enhanced-capec.ttl (1.91 GB)  
**Status:** ✅ COMPLETE

## Statistics
[Include JSON statistics here]

## Verification Results
[Include verification results here]

## Test Results
[Include pytest results here]
EOF
```

---

## 🚀 Next Steps

After successful load:
1. Update PROJECT-STATUS-SUMMARY.md with database info
2. Begin Phase 3.5 work (defense layer integration)
3. Start Phase 5 (RAG integration) if ready
4. Create production backup
5. Document any issues or improvements

---

**Status:** Ready to Execute  
**Estimated Total Time:** 1.5-2.5 hours (including all phases)  
**Start Date:** When authorized
