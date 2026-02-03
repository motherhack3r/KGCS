# Unit Tests

**Purpose:** Validate individual ETL transformers and isolated components  
**Approach:** Test single components in isolation without external dependencies  
**Exit Code:** 0 (pass) or 1 (fail) for CI/CD gates

---

## Test Files

- `test_etl_pipeline.py` — Individual transformer validation
  - Tests CPE, CVE, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE transformers
  - Uses sample data from `data/*/samples/`
  - Validates SHACL constraints

---

## Running Unit Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific test
pytest tests/unit/test_etl_pipeline.py::test_cpe_etl -v
```

---

## Expected Results

✅ All transformers should process sample data without errors  
✅ Output TTL should conform to SHACL shapes  
✅ No external dependencies required (no Neo4j, no network)

---

## When to Use

- ✅ Quick validation of ETL logic (few seconds)
- ✅ During development of new transformer
- ✅ Checking specific standard compliance
- ✅ CI/CD pre-commit validation
