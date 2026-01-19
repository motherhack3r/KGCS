# Phase 2: Quick Start Testing Guide

**Purpose:** Validate Phase 2 ETL scripts and SHACL validation framework.

**Time Required:** ~10 minutes

---

## Step 1: Create Sample Input Data

### CPE Sample (data/cpe/raw/sample-cpe.json)

```bash
mkdir -p data/cpe/raw data/cpe/samples
```

Create `data/cpe/raw/sample-cpe.json`:

```json
{
  "resultsPerPage": 2,
  "startIndex": 0,
  "totalResults": 2,
  "timestamp": "2026-01-19T15:30:00Z",
  "products": [
    {
      "cpeNameId": "00000000-0000-0000-0000-000000000001",
      "deprecated": false,
      "cpeName": "cpe:2.3:a:apache:http_server:2.4.53:*:*:*:*:*:*:*",
      "createdDate": "2020-01-15T12:00:00Z",
      "lastModifiedDate": "2026-01-19T10:00:00Z"
    },
    {
      "cpeNameId": "00000000-0000-0000-0000-000000000002",
      "deprecated": true,
      "cpeName": "cpe:2.3:a:microsoft:windows_10:1909:*:*:*:*:*:*:*",
      "createdDate": "2019-05-20T08:30:00Z",
      "lastModifiedDate": "2026-01-18T14:00:00Z"
    }
  ]
}
```

### CVE Sample (data/cve/raw/sample-cve.json)

Create `data/cve/raw/sample-cve.json`:

```json
{
  "resultsPerPage": 1,
  "startIndex": 0,
  "totalResults": 1,
  "format": "NVD_CVE",
  "vulnerabilities": [
    {
      "cve": {
        "id": "CVE-2025-1234",
        "sourceIdentifier": "mitre@mitre.org",
        "published": "2025-01-15T10:00:00Z",
        "lastModified": "2026-01-19T08:15:00Z",
        "vulnStatus": "Analyzed",
        "descriptions": [
          {
            "lang": "en",
            "value": "Apache HTTP Server before 2.4.54 allows remote code execution via crafted request headers."
          }
        ],
        "metrics": {
          "cvssMetricV31": [
            {
              "source": "nvd@nist.gov",
              "type": "Primary",
              "cvssData": {
                "version": "3.1",
                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "baseScore": 9.8,
                "baseSeverity": "CRITICAL",
                "attackVector": "NETWORK",
                "attackComplexity": "LOW",
                "privilegesRequired": "NONE",
                "userInteraction": "NONE",
                "scope": "UNCHANGED",
                "confidentialityImpact": "HIGH",
                "integrityImpact": "HIGH",
                "availabilityImpact": "HIGH"
              },
              "impactScore": 9.8,
              "baseScore": 9.8,
              "baseSeverity": "CRITICAL"
            }
          ]
        },
        "weaknesses": [
          {
            "source": "NVD",
            "type": "Primary",
            "description": [
              {
                "lang": "en",
                "value": "CWE-78"
              }
            ]
          }
        ],
        "configurations": [
          {
            "nodes": [
              {
                "operator": "OR",
                "negate": false,
                "cpeMatch": [
                  {
                    "vulnerable": true,
                    "criteria": "cpe:2.3:a:apache:http_server:*:*:*:*:*:*:*:*",
                    "matchCriteriaId": "00000000-0000-0000-0000-000000000011",
                    "versionStartIncluding": "2.4.0",
                    "versionEndExcluding": "2.4.54"
                  }
                ]
              }
            ]
          }
        ],
        "references": [
          {
            "url": "https://httpd.apache.org/security/vulnerabilities_24.html",
            "source": "vendor"
          }
        ]
      }
    }
  ]
}
```

---

## Step 2: Run ETL Scripts

### Test CPE ETL

```bash
python scripts/etl_cpe.py \
  --input data/cpe/raw/sample-cpe.json \
  --output data/cpe/samples/test-output.ttl
```

**Expected output:**
```
Loading CPE JSON from data/cpe/raw/sample-cpe.json...
Transforming to RDF...
Writing RDF to data/cpe/samples/test-output.ttl...
```

Check the output:
```bash
head -50 data/cpe/samples/test-output.ttl
```

**Expected content (Turtle RDF):**
```turtle
@prefix sec: <https://example.org/sec/core#> .
@prefix ex: <https://example.org/> .
...
ex:platform/00000000-0000-0000-0000-000000000001
    rdf:type sec:Platform ;
    sec:CPEUri "cpe:2.3:a:apache:http_server:2.4.53:*:*:*:*:*:*:*" ;
    sec:platformPart "a" ;
    ...
```

### Test CVE ETL

```bash
python scripts/etl_cve.py \
  --input data/cve/raw/sample-cve.json \
  --output data/cve/samples/test-output.ttl
```

**Expected output:**
```
Loading CVE JSON from data/cve/raw/sample-cve.json...
Transforming to RDF...
Writing RDF to data/cve/samples/test-output.ttl...
```

**Expected content:**
```turtle
ex:vulnerability/CVE-2025-1234
    rdf:type sec:Vulnerability ;
    sec:cveId "CVE-2025-1234" ;
    sec:scored_by ex:vulnerability/CVE-2025-1234#cvss-v31-... ;
    sec:affects ex:platformConfiguration/00000000-0000-0000-0000-000000000011 ;
    ...
```

---

## Step 3: Run SHACL Validation

```bash
python scripts/validate_shacl.py \
  --data data/cpe/samples/test-output.ttl \
  --shapes docs/ontology/shacl/cpe-shapes.ttl
```

**Expected: PASS**

```
Validation Report
Conforms: True
Report: (No violations)
```

Try a **bad example** to see violations:

```bash
python scripts/validate_shacl.py \
  --data data/shacl-samples/cpe-bad.ttl \
  --shapes docs/ontology/shacl/cpe-shapes.ttl
```

**Expected: FAIL**

```
Validation Report
Conforms: False
Violations:
  - (some property missing or invalid)
```

---

## Step 4: Test with Golden Samples (Regression Test)

### Test Good Example (should PASS)

```bash
python scripts/validate_shacl.py \
  --data data/shacl-samples/good-example.ttl
```

✅ Expected: `Conforms: True`

### Test Bad Example (should FAIL)

```bash
python scripts/validate_shacl.py \
  --data data/shacl-samples/bad-example.ttl
```

❌ Expected: `Conforms: False` (missing edge in causal chain)

### Test RAG Template Conformance

```bash
# T1: Full causal chain (Vuln → CWE → CAPEC → Technique → Tactic)
python scripts/validate_shacl.py \
  --data data/shacl-samples/t1_good.ttl \
  --template T1
```

✅ Expected: `Conforms: True`

```bash
# T1 bad: Shortcut (CVE → Technique, skipping CWE/CAPEC)
python scripts/validate_shacl.py \
  --data data/shacl-samples/t1_bad.ttl \
  --template T1
```

❌ Expected: `Conforms: False` (causal chain violation)

---

## Step 5: Test Ingestion Pipeline

```bash
python scripts/ingest_pipeline.py \
  --data-dir data/shacl-samples
```

**Expected output:**
```
Processing data/shacl-samples/good-example.ttl
Validation Report: (PASS)
Indexing data/shacl-samples/good-example.ttl... (simulated)

Processing data/shacl-samples/bad-example.ttl
Validation Report: (FAIL - reason: missing CWE node)
Skipping data/shacl-samples/bad-example.ttl due to validation errors
```

---

## Step 6: Check CI Workflow (Local Dry-Run)

GitHub Actions will automatically run on commit, but you can test locally:

```bash
# Simulate the CI validation
for f in data/shacl-samples/*.ttl; do
  echo "Validating $f..."
  python scripts/validate_shacl.py --data "$f"
done
```

All **good** samples should pass. All **bad** samples should fail.

---

## Success Criteria ✅

Phase 2 is **ready** when:

- [x] CPE ETL produces valid RDF Turtle
- [x] CVE ETL produces valid RDF Turtle with CVSS + PlatformConfiguration
- [x] SHACL validation **rejects bad examples** (catches violations)
- [x] SHACL validation **accepts good examples** (no false positives)
- [x] RAG templates (T1-T7) are **enforced** (e.g., T1 rejects shortcuts)
- [x] CI workflow passes on golden samples
- [x] Ingestion pipeline orchestrates ETL → validation → indexing

---

## Troubleshooting

### "pyshacl" module not found
```bash
pip install pyshacl rdflib
```

### ETL script missing external standard mapping
- Ensure [docs/ontology/core-ontology-extended-v1.0.owl](docs/ontology/owl/core-ontology-extended-v1.0.owl) defines `sec:Property`
- Check ETL script imports `SEC = Namespace('https://example.org/sec/core#')`

### Validation fails with "Unknown shape"
- Verify shapes file exists: `ls docs/ontology/shacl/*.ttl`
- Check shape URI matches namespace prefix (e.g., `sh:NodeShape` with `sec:VulnerabilityShape`)

### Causal chain violations (T1 failures)
- Ensure data includes all edges: Vuln → CWE → CAPEC → Technique → Tactic
- Use `t1_good.ttl` as template for correct structure

---

## Next: Proceed to Phase 3

Once all tests pass:

```bash
# Commit Phase 2 work
git add scripts/etl_cpe.py scripts/etl_cve.py docs/ontology/PHASE-2-GOVERNANCE.md
git commit -m "Phase 2: ETL + SHACL validation framework"

# Move to Phase 3 (Neo4j + RAG API)
# See: PHASE-2-COMPLETE.md -> Phase 3 Blueprint
```
