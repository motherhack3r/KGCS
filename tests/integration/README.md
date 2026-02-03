# Integration Tests

**Purpose:** Validate multiple standards working together with full causal chain  
**Approach:** End-to-end testing of ETL → SHACL validation → optionally Neo4j load  
**Exit Code:** 0 (pass) or 1 (fail) for CI/CD gates

---

## Test Files

- `test_phase3_comprehensive.py` — All 9 standards tested together
  - Runs complete ETL pipeline
  - Validates causal chain: CVE→CWE→CAPEC→ATT&CK→Defenses
  - Checks SHACL constraints on all outputs
  - Verifies cross-standard relationships

- `test_phase3_end_to_end.py` — Full pipeline end-to-end
  - Complete workflow: Download → ETL → SHACL validation → Neo4j load
  - Uses production-like data flows
  - Validates entire system integration

---

## Running Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/integration/test_phase3_comprehensive.py -v

# Specific test
pytest tests/integration/test_phase3_comprehensive.py::test_capec_etl -v
```

---

## Expected Results

✅ All 9 standards process successfully  
✅ Causal chain relationships established (CVE→CWE→CAPEC→Technique)  
✅ Cross-standard links verified  
✅ SHACL validation passes on all outputs  
✅ Optional: Neo4j load completes without errors

---

## When to Use

- ✅ Before committing large ETL changes
- ✅ Verifying causal chain after enhancements
- ✅ Checking defense layer integration (D3FEND, CAR, SHIELD)
- ✅ CI/CD full validation (before production load)
- ✅ Regression testing on standard updates

---

## Performance Notes

- Unit tests: ~10-30 seconds
- Integration tests: ~2-5 minutes (depending on sample size)
- End-to-end tests: ~5-15 minutes (if including Neo4j load)

---

## Dependencies

- ✅ Sample data in `data/*/samples/`
- ⚠️ Neo4j optional (skipped if unavailable)
- ⚠️ Network optional (downloads skipped if offline)
