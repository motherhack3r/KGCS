# Utility Tests

**Purpose:** Validate specific features and specialized functionality  
**Approach:** Test individual utilities and tools in context  
**Exit Code:** 0 (pass) or 1 (fail) for CI/CD gates

---

## Test Files

- `test_rag_shapes.py` — RAG traversal template validation
  - Validates approved query templates (T1-T7)
  - Tests SHACL constraint enforcement for RAG queries
  - Verifies safe traversal paths
  - Checks that LLM queries conform to templates

- `test_standards_downloader.py` — Standard data downloader testing
  - Tests downloading CPE, CVE, CWE, CAPEC, etc. from official sources
  - Validates checksums and data integrity
  - Checks manifest creation
  - Tests retry and resumable downloads

- `test_download_integration.py` — Download workflow integration
  - Full download pipeline testing
  - Tests parallel downloads
  - Validates chaining of download steps
  - Checks error handling and recovery

---

## Running Utility Tests

```bash
# All utility tests
pytest tests/utilities/ -v

# Specific test file
pytest tests/utilities/test_rag_shapes.py -v

# Specific test
pytest tests/utilities/test_standards_downloader.py::test_download_cpe -v
```

---

## Expected Results

✅ RAG template validation works  
✅ Downloads complete successfully  
✅ Data integrity verified (checksums)  
✅ Manifests created correctly  
✅ Error handling functional

---

## When to Use

- ✅ Testing RAG safety constraints
- ✅ Validating data download workflows
- ✅ Before production download runs
- ✅ Checking download error recovery
- ✅ CI/CD data preparation validation

---

## Network Requirements

Some tests require internet:
- `test_download_integration.py` — Requires network access to NVD, MITRE
- `test_standards_downloader.py` — Requires network access

Can be skipped offline:
```bash
pytest tests/utilities/test_rag_shapes.py -v  # Works offline
pytest tests/utilities/test_download_integration.py -v  # Requires network
```

---

## Performance Notes

- RAG shape tests: ~2-5 seconds
- Downloader tests: ~5-30 seconds (depends on network)
- Full utility suite: ~30-60 seconds
