# KGCS Phase 2: Data Governance & Lifecycle

**Version:** 1.0  
**Date:** January 2026  
**Status:** Phase 2 Final Specification

---

## 1. Overview

This document defines the **data governance, lifecycle, and quality assurance** for KGCS Phase 2, ensuring that all ingested data is:
- **Validated** against SHACL constraints before indexing
- **Traceable** to official NVD/MITRE sources
- **Versioned** for reproducibility and audit
- **Tested** against golden datasets

---

## 2. Data Ownership & Stewardship

| Layer | Owner | Frequency | Source Authority |
|-------|-------|-----------|-------------------|
| **Core Ontology** | KGCS Team | Frozen v1.0 | [core-ontology-v1.0.md](../docs/ontology/core-ontology-v1.0.md) |
| **CPE Platforms** | NVD CPE API | Weekly | [https://nvd.nist.gov/products/cpe/api](https://nvd.nist.gov/products/cpe/api) |
| **CVE Vulnerabilities** | NVD CVE API 2.0 | Daily | [https://nvd.nist.gov/products/cve-api-20](https://nvd.nist.gov/products/cve-api-20) |
| **CWE Weaknesses** | MITRE CWE JSON | Quarterly | [https://cwe.mitre.org/data/json/1000.json](https://cwe.mitre.org/data/json/1000.json) |
| **CAPEC Patterns** | MITRE CAPEC JSON | Quarterly | [https://capec.mitre.org/data/json/capec_latest.json](https://capec.mitre.org/data/json/capec_latest.json) |
| **ATT&CK Techniques** | MITRE ATT&CK STIX 2.1 | Monthly | [https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/](https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/) |
| **D3FEND Defenses** | MITRE D3FEND STIX 2.1 | Quarterly | [https://raw.githubusercontent.com/d3fend/d3fend/master/d3fend.json](https://raw.githubusercontent.com/d3fend/d3fend/master/d3fend.json) |
| **CAR Analytics** | MITRE CAR JSON | Quarterly | [https://car.mitre.org/data/car_latest.json](https://car.mitre.org/data/car_latest.json) |
| **SHIELD Deception** | MITRE SHIELD STIX 2.1 | Quarterly | [https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/](https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/) |
| **ENGAGE Framework** | MITRE ENGAGE | Quarterly | [https://engage.mitre.org/data/engage-latest.json](https://engage.mitre.org/data/engage-latest.json) |
| **Incidents** | SOC / MDR Partner | Continuous | [Incident Extension](../docs/ontology/incident-ontology-extension-v1.0.md) |
| **Risk Assessments** | Risk Team | Quarterly | [Risk Extension](../docs/ontology/risk-ontology-extension-v1.0.md) |

---

## 3. Data Ingestion Pipeline

### 3.1 ETL Workflow

```
External Source (JSON/STIX/CSV)
    ↓
[1] Fetch & Cache (in data/{standard}/raw/)
    ↓
[2] Transform → RDF Turtle (using etl_{standard}.py)
    ↓
[3] SHACL Validation (against docs/ontology/shacl/{standard}-shapes.ttl)
    ↓
[4] If PASS: Write to data/{standard}/samples/ + Index in Knowledge Graph
    If FAIL: Generate report in artifacts/ + Alert
    ↓
[5] Audit Log: Record import timestamp, version, record count
```

### 3.2 ETL Scripts (Phase 2)

Available transformers:

| Standard | Script | Status | Transforms |
|----------|--------|--------|------------|
| CPE | [etl_cpe.py](../../scripts/etl_cpe.py) | ✅ Ready | NVD CPE API JSON → `sec:Platform` |
| CVE | [etl_cve.py](../../scripts/etl_cve.py) | ✅ Ready | NVD CVE API 2.0 → `sec:Vulnerability` + `sec:VulnerabilityScore` + `sec:PlatformConfiguration` |
| CWE | [etl_cwe.py](../../scripts/etl_cwe.py) | 🔄 In Progress | MITRE CWE JSON → `sec:Weakness` |
| CAPEC | [etl_capec.py](../../scripts/etl_capec.py) | 🔄 Queued | MITRE CAPEC JSON → `sec:AttackPattern` |
| ATT&CK | [etl_attck.py](../../scripts/etl_attck.py) | 🔄 Queued | MITRE ATT&CK STIX 2.1 → `sec:Technique` + `sec:SubTechnique` + `sec:Tactic` |
| D3FEND | [etl_d3fend.py](../../scripts/etl_d3fend.py) | 🔄 Queued | MITRE D3FEND STIX → `sec:DefensiveTechnique` |
| CAR | [etl_car.py](../../scripts/etl_car.py) | 🔄 Queued | MITRE CAR JSON → `sec:DetectionAnalytic` |
| SHIELD | [etl_shield.py](../../scripts/etl_shield.py) | 🔄 Queued | MITRE SHIELD STIX → `sec:DeceptionTechnique` |
| ENGAGE | [etl_engage.py](../../scripts/etl_engage.py) | 🔄 Queued | MITRE ENGAGE JSON → `sec:EngagementConcept` |
| Incident | [ingest_incident.py](../../scripts/ingest_incident.py) | 🔄 Queued | SOC JSON → `inc:Incident` + `inc:ObservedTechnique` |

### 3.3 Usage (Phase 2)

```bash
# Transform NVD CPE API response to RDF with validation
python scripts/etl_cpe.py \
  --input data/cpe/raw/cpe-api-response.json \
  --output data/cpe/samples/cpe-snapshot-2026-01-19.ttl \
  --validate

# Transform CVE API response (includes PlatformConfiguration linking)
python scripts/etl_cve.py \
  --input data/cve/raw/cve-api-response.json \
  --output data/cve/samples/cve-snapshot-2026-01-19.ttl \
  --validate
```

---

## 4. Quality Assurance & Validation

### 4.1 SHACL Validation Gates

Every ingested file **must pass** SHACL validation before indexing.

**Shapes Library:** [docs/ontology/shacl/](../docs/ontology/shacl/)

| Shape | Validates | Constraints |
|-------|-----------|-------------|
| [core-shapes.ttl](../docs/ontology/shacl/core-shapes.ttl) | All Core classes | Mandatory properties, cardinality, typing |
| [cpe-shapes.ttl](../docs/ontology/shacl/cpe-shapes.ttl) | `sec:Platform` | `cpeUri` unique, format validation |
| [cve-shapes.ttl](../docs/ontology/shacl/cve-shapes.ttl) | `sec:Vulnerability` | `cveId` unique, CVSS score bounds (0.0-10.0) |
| [cwe-shapes.ttl](../docs/ontology/shacl/cwe-shapes.ttl) | `sec:Weakness` | `cweId` unique, no cycles |
| [capec-shapes.ttl](../docs/ontology/shacl/capec-shapes.ttl) | `sec:AttackPattern` | `capecId` unique |
| [attck-shapes.ttl](../docs/ontology/shacl/attck-shapes.ttl) | `sec:Technique` + `sec:Tactic` | Unique IDs, subtechnique parent validation |
| [d3fend-shapes.ttl](../docs/ontology/shacl/d3fend-shapes.ttl) | `sec:DefensiveTechnique` | Unique IDs, relationship integrity |
| [car-shapes.ttl](../docs/ontology/shacl/car-shapes.ttl) | `sec:DetectionAnalytic` | Unique IDs |
| [shield-shapes.ttl](../docs/ontology/shacl/shield-shapes.ttl) | `sec:DeceptionTechnique` | Unique IDs |
| [engage-shapes.ttl](../docs/ontology/shacl/engage-shapes.ttl) | `sec:EngagementConcept` | Unique IDs |
| [rag-shapes.ttl](../docs/ontology/shacl/rag-shapes.ttl) | RAG Traversal Paths | Template conformance (T1-T7) |

### 4.2 Golden Test Datasets

Located: [data/shacl-samples/](../../data/shacl-samples/)

**Purpose:** Regression testing to detect ontology/ETL regressions.

| Sample | Type | Expected Result | Validates |
|--------|------|-----------------|-----------|
| [good-example.ttl](../../data/shacl-samples/good-example.ttl) | Complete CVE→CWE→CAPEC→ATT&CK path | ✅ PASS | Core ontology alignment |
| [bad-example.ttl](../../data/shacl-samples/bad-example.ttl) | Missing CWE node in causal chain | ❌ FAIL | Mandatory edge detection |
| [cpe-good.ttl](../../data/shacl-samples/cpe-good.ttl) | Valid CPE with all metadata | ✅ PASS | CPE completeness |
| [cpe-bad.ttl](../../data/shacl-samples/cpe-bad.ttl) | CPE missing cpeUri | ❌ FAIL | Mandatory property detection |
| [cve-good.ttl](../../data/shacl-samples/cve-good.ttl) | Valid CVE with CVSS and config | ✅ PASS | CVE+CVSS+Config linking |
| [cve-bad.ttl](../../data/shacl-samples/cve-bad.ttl) | CVE with CVSS score > 10.0 | ❌ FAIL | Score bounds validation |
| [t1_good.ttl](../../data/shacl-samples/t1_good.ttl) | Template T1 path (Vuln→CWE→CAPEC→Technique→Tactic) | ✅ PASS | T1 traversal conformance |
| [t1_bad.ttl](../../data/shacl-samples/t1_bad.ttl) | Template T1 with shortcut (CVE→Technique) | ❌ FAIL | Causal chain enforcement |

### 4.3 CI/CD Validation

GitHub Actions Workflow: [.github/workflows/shacl-validation.yml](../../.github/workflows/shacl-validation.yml)

**Triggers:**
- `push` to `main`
- `pull_request` to `main`

**Actions:**
1. Detect changed OWL modules
2. Run `validate_shacl.py` against golden samples
3. Report violations in PR comments
4. **Block merge if validation fails**

---

## 5. Data Versioning & Snapshots

### 5.1 Snapshot Naming Convention

```
data/{standard}/samples/{standard}-snapshot-YYYY-MM-DD.ttl
```

**Examples:**
- `data/cpe/samples/cpe-snapshot-2026-01-19.ttl`
- `data/cve/samples/cve-snapshot-2026-01-20.ttl`
- `data/attck/samples/attck-snapshot-2026-02-15.ttl`

### 5.2 Metadata Files

Each snapshot includes a companion `.meta.json`:

```json
{
  "standard": "CPE",
  "snapshot_date": "2026-01-19T15:30:00Z",
  "source_url": "https://nvd.nist.gov/products/cpe/api",
  "record_count": 45231,
  "validation_status": "PASSED",
  "validation_timestamp": "2026-01-19T15:35:22Z",
  "validator_version": "validate_shacl.py v1.0",
  "ontology_version": "core-ontology-v1.0.md",
  "import_digest": "sha256:abc123...",
  "breaking_changes": []
}
```

---

## 6. Data Quality Metrics

### 6.1 Ingestion Health Dashboard

Track per-standard:

| Metric | Target | Current |
|--------|--------|---------|
| Validation Pass Rate | 100% | — |
| Avg Ingestion Latency | < 5 min | — |
| Data Completeness (mandatory fields) | 100% | — |
| Edge Integrity (violated constraints) | 0 | — |
| Causal Chain Violations (T1-T7) | 0 | — |

### 6.2 Alerting Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| Validation FAIL on new snapshot | 🔴 Critical | Block merge, notify team |
| Ingestion latency > 10 min | 🟡 Warning | Log, monitor |
| Record count decrease > 10% | 🟡 Warning | Investigate source |
| Unknown reference to external standard | 🔴 Critical | Quarantine, audit |

---

## 7. Access & Audit

### 7.1 Data Access Policies

| Role | Can Read | Can Ingest | Can Validate | Can Release |
|------|----------|-----------|--------------|------------|
| **Developer** | ✅ | ✅ (PR only) | ✅ | ❌ |
| **Data Engineer** | ✅ | ✅ | ✅ | ✅ |
| **Security Lead** | ✅ | ❌ | ✅ | ✅ |
| **RAG User** | ✅ | ❌ | ❌ | ❌ |

### 7.2 Audit Log

All ingestions logged to `logs/ingestion-audit.log`:

```
2026-01-19T15:32:10Z | INGEST | CPE      | 45231 records | PASSED | etl_cpe.py v1.0 | engineer-alice
2026-01-19T15:40:22Z | INGEST | CVE      | 128956 records | PASSED | etl_cve.py v1.0 | engineer-bob
2026-01-20T03:15:45Z | INGEST | CWE      | 2104 records | FAILED | etl_cwe.py v1.0 | engineer-alice
  └─ Reason: Missing cweId in 3 entries | Shapes: cwe-shapes.ttl
```

---

## 8. Rollback & Disaster Recovery

### 8.1 Snapshot Retention

Keep **all** snapshots in `data/{standard}/samples/`:

- Enables version-pinned RAG queries
- Allows time-travel analysis (e.g., "what changed in last week?")
- Supports incident reconstruction

### 8.2 Rollback Procedure

If a snapshot introduces hallucinations or breaks RAG:

```bash
# Identify broken snapshot
git log --oneline data/cve/samples/ | grep 2026-01-20

# Revert to known-good version
git checkout 1a2b3c -- data/cve/samples/cve-snapshot-2026-01-19.ttl

# Re-validate
python scripts/validate_shacl.py --data data/cve/samples/cve-snapshot-2026-01-19.ttl

# Test RAG queries (T1-T7 templates)
python scripts/test_rag_templates.py --data data/cve/samples/cve-snapshot-2026-01-19.ttl
```

---

## 9. Phase 2 Completion Checklist

- [x] Core Ontology v1.0 frozen
- [x] SHACL shapes defined
- [x] CI workflow active ([shacl-validation.yml](../../.github/workflows/shacl-validation.yml))
- [x] ETL scripts for CPE & CVE (Phase 2 MVP)
- [x] Golden test datasets ([data/shacl-samples/](../../data/shacl-samples/))
- [x] Governance document (this file)
- [ ] ETL scripts for CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE (Phase 2 Extended)
- [ ] Automated weekly ingestion schedule (GitHub Actions)
- [ ] Data quality dashboard
- [ ] RAG template validation tests

---

## 10. Phase 3: Data Ingestion & RAG (Next)

Once Phase 2 is complete:

1. **Run automated ETL** for all 9 standards → produce validated snapshots
2. **Load snapshots into Neo4j** or equivalent graph database
3. **Validate RAG traversals** (T1-T7 templates) against live graph
4. **Expose RAG API** for integration with LLM reasoning layer
5. **Test against adversarial prompts** to detect hallucinations

---

## References

- [Core Ontology v1.0](../core-ontology-v1.0.md)
- [SHACL Constraints](SHACL-constraints.md)
- [SHACL Profiles](SHACL-profiles.md)
- [RAG Traversal Templates](rag/RAG-travesal-templates.md)
- [Incident Extension](incident-ontology-extension-v1.0.md)
- [Risk Extension](risk-ontology-extension-v1.0.md)
- [ThreatActor Extension](threatactor-ontology-extension-v1.0.md)
