# Data Load Tests

**Purpose:** Validate Neo4j persistence, graph creation, and data integrity  
**Approach:** Test database connection, load paths, constraints, and relationships  
**Exit Code:** 0 (pass) or 1 (fail) for CI/CD gates (may skip if Neo4j unavailable)

---

## Test Files

- `test_neo4j_connection.py` — Neo4j connectivity validation
  - Tests driver initialization
  - Validates authentication
  - Checks database availability
  - Tests basic Cypher queries

- `test_neo4j_data_load.py` — Graph data integrity validation
  - Loads sample TTL data via transformer
  - Verifies nodes created with correct properties
  - Validates relationship establishment
  - Checks graph constraints and indexes
  - Tests causal chain traversal in graph

---

## Running Data Load Tests

```bash
# All data load tests
pytest tests/data_load/ -v

# Specific test file
pytest tests/data_load/test_neo4j_data_load.py -v

# Specific test
pytest tests/data_load/test_neo4j_connection.py::test_neo4j_connection -v
```

---

## Expected Results

✅ Neo4j connection successful  
✅ Sample data loads into graph  
✅ Nodes have correct properties  
✅ Relationships properly established  
✅ Constraints applied (unique IDs)  
✅ Causal chain traversable (CVE→CWE→CAPEC→Technique)

---

## Prerequisites

Neo4j must be running:
```bash
# Start Neo4j (docker or local)
docker run -d -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest

# Or configure connection in src/config.py
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>
```

---

## When to Use

- ✅ Before loading production data
- ✅ Validating Neo4j schema after modifications
- ✅ Testing graph query performance
- ✅ Verifying constraint enforcement
- ✅ CI/CD data persistence validation

---

## Skipping Tests

If Neo4j is unavailable:
```bash
# Tests will be skipped gracefully (pass with skipped status)
pytest tests/data_load/ -v
# Output: ... SKIPPED (Neo4j not available)
```

---

## Performance Notes

- Connection tests: ~1 second
- Data load tests: ~10-30 seconds (depends on sample size)
- Full test suite: ~30-60 seconds

---

## Troubleshooting

**Connection refused:**
```
Error: Could not establish connection: [Errno 111] Connection refused

Solution: Start Neo4j service and check URI in .env
```

**Authentication failed:**
```
Error: [Auth] 401: "Invalid username or password"

Solution: Verify NEO4J_USER and NEO4J_PASSWORD in .env
```

**Database error:**
```
Error: Database 'neo4j' does not exist

Solution: Check Neo4j is fully initialized; may need manual database creation
```
