# KGCS Test Suite

**Organization:** Functional test structure with clear separation of concerns  
**Status:** Complete with 11 tests covering ETL, integration, data load, and verification

---

## Test Categories

### 🧪 [Unit Tests](unit/) — Individual Component Validation

Single-component tests that validate transformers and isolated functionality.

**Files:**
- `test_etl_pipeline.py` — Individual ETL transformer unit tests

**Run:**
```bash
pytest tests/unit/ -v
```

**Purpose:** Ensure each transformer (CPE, CVE, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE) works correctly in isolation.

---

### 🔗 [Integration Tests](integration/) — Multi-Standard Validation

End-to-end tests covering multiple standards working together.

**Files:**
- `test_phase3_comprehensive.py` — All 9 standards tested together with SHACL validation
- `test_phase3_end_to_end.py` — Full pipeline (download → ETL → SHACL → Neo4j)

**Run:**
```bash
pytest tests/integration/ -v

# Or specific test:
pytest tests/integration/test_phase3_comprehensive.py -v
```

**Purpose:** Verify causal chain (CVE→CWE→CAPEC→ATT&CK→Defenses) and cross-standard relationships.

---

### 💾 [Data Load Tests](data_load/) — Neo4j Persistence Validation

Tests for Neo4j connection, graph creation, and data integrity.

**Files:**
- `test_neo4j_connection.py` — Neo4j driver and connection tests
- `test_neo4j_data_load.py` — Graph load validation and constraint checks

**Run:**
```bash
pytest tests/data_load/ -v
```

**Purpose:** Ensure data persists correctly to Neo4j with proper constraints and relationships.

---

### 🛠️ [Utility Tests](utilities/) — Feature-Specific Tests

Tests for specific utilities and specialized functionality.

**Files:**
- `test_rag_shapes.py` — RAG traversal template SHACL validation
- `test_standards_downloader.py` — Standard data download testing
- `test_download_integration.py` — Download integration workflow tests

**Run:**
```bash
pytest tests/utilities/ -v
```

**Purpose:** Validate specialized tools (RAG safety, data downloads) work correctly.

---

### ✅ [Verification Scripts](verification/) — Manual Inspection Tools

Interactive scripts for visual graph inspection and debugging (always exit code 0).

**Files:**
- `verify_causal_chain.py` — Display CVE→CWE→CAPEC→Technique chain
- `verify_defense_layers.py` — Show defense/detection/deception coverage per technique

**Run:**
```bash
# Visual inspection (informational, always succeeds)
python tests/verification/verify_causal_chain.py
python tests/verification/verify_defense_layers.py
```

**Purpose:** Explore graph structure, understand relationships, debug connections.

**Note:** These scripts are **exploratory tools**, not CI gates. They always exit with code 0 (informational only).

---

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Category
```bash
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only
pytest tests/data_load/ -v     # Data load tests only
pytest tests/utilities/ -v     # Utility tests only
```

### With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
# Coverage report in: htmlcov/index.html
```

### Specific Test
```bash
pytest tests/integration/test_phase3_comprehensive.py::test_cpe_etl -v
```

---

## Test Strategy

### Automated Tests (CI/CD Gates)

**Files:** `test_*.py` in all directories  
**Exit Code:** 0 (pass) or 1 (fail)  
**Usage:** CI/CD validation, commit gates  
**Approach:** Assert relationships exist and conform to SHACL

**Example:**
```python
def test_cpe_etl():
    # Load sample CPE → check SHACL validation passes
    assert validate_ttl(output) == PASS
```

### Manual Verification (Exploratory Tools)

**Files:** `verify_*.py` in verification/  
**Exit Code:** Always 0 (informational)  
**Usage:** Developer debugging, before committing  
**Approach:** Display graph structure with labels for human review

**Example:**
```bash
python verify_causal_chain.py
# Output: Visual chain CVE-X → CWE-Y → CAPEC-Z → T1234
```

---

## Test Data

Sample data locations:
- CPE samples: `data/cpe/samples/`
- CVE samples: `data/cve/samples/`
- CWE samples: `data/cwe/samples/`
- CAPEC samples: `data/capec/samples/`
- ATT&CK samples: `data/attack/samples/`
- D3FEND samples: `data/d3fend/samples/`
- SHACL samples: `data/shacl-samples/`

**Size:** Small datasets (1-100 records) for fast testing

---

## Test Expectations

### ✅ Should Pass

- ✅ CPE/CVE/CWE/CAPEC ETL transformers (sample data)
- ✅ SHACL validation on valid data (positive test samples)
- ✅ Neo4j connection and load (if Neo4j available)
- ✅ Causal chain relationships (CVE→CWE→CAPEC→Technique)
- ✅ RAG shape validation on approved traversal templates

### ⚠️ May Fail (Conditional)

- ⚠️ Neo4j tests (if server not running)
- ⚠️ Download integration tests (if network unavailable)
- ⚠️ Full-scale data tests (if production data not available)

### ℹ️ Informational Only

- ℹ️ Verification scripts (visual inspection, exit 0 always)

---

## Debugging Failed Tests

### 1. Check Test Logs

```bash
pytest tests/ -v --tb=short  # Detailed error output
```

### 2. Run Verification Script

```bash
python tests/verification/verify_causal_chain.py  # Understand structure
```

### 3. Review Validation Reports

```bash
cat artifacts/shacl-report-*.json  # SHACL violations
```

### 4. Run Specific Test

```bash
pytest tests/integration/test_phase3_comprehensive.py::test_capec_etl -vvv
```

---

## Test Organization Philosophy

**Why This Structure?**

1. **Clarity:** Intent visible from directory name
2. **Isolation:** Unit tests don't require Neo4j; integration tests exercise full stack
3. **CI/CD Ready:** Run `pytest tests/unit/` for quick feedback; `tests/integration/` for full validation
4. **Scalability:** Easy to add new tests in appropriate category
5. **Consistency:** Matches organization of scripts/ and docs/ folders

---

## References

- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — Project roadmap and phases
- [docs/GLOSSARY.md](../docs/GLOSSARY.md) — Standard definitions
- [scripts/validation/README.md](../scripts/validation/README.md) — Validation scripts
- [PROJECT-STATUS-SUMMARY.md](../PROJECT-STATUS-SUMMARY.md) — Current phase status
