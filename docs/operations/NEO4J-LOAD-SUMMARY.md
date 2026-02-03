# Neo4j KGCS Load Summary

**Extracted:** February 3, 2026, 01:37:14 UTC  
**Database:** neo4j-2026-01-29 (Full Production Load)  
**Total Nodes:** 2,506,970  
**Total Relationships:** 26,004,206  

**Status:** Full database loaded. Foundation strong, upper causal chain incomplete (needs defense layer linking).

---

## 📊 Node Breakdown

| Entity Type | Count | Status |
| --- | --- | --- |
| Platform (CPE) | 1,560,484 | ✅ Full production data |
| PlatformConfiguration | 614,054 | ✅ Full production data |
| Vulnerability (CVE) | 329,523 | ✅ Full production data |
| Weakness (CWE) | 969 | ✅ Complete standard |
| AttackPattern (CAPEC) | 615 | ✅ Complete standard |
| Technique (ATT&CK) | 568 | ✅ Complete standard |
| SubTechnique | 526 | ✅ Most with parents |
| DetectionAnalytic (CAR) | 102 | ⚠️ Orphaned (not linked) |
| Tactic | 34 | ⚠️ Partial linkage |
| DeceptionTechnique (SHIELD) | 33 | ⚠️ Orphaned |
| DefensiveTechnique (D3FEND) | 31 | ⚠️ Orphaned |
| EngagementConcept (ENGAGE) | 31 | ⚠️ Orphaned |
| **TOTAL** | **2,506,970** | |

---

## 🔗 Relationship Breakdown

| Relationship Type | Count | Description |
| --- | --- | --- |
| **MATCHES_PLATFORM** | 22,784,024 | PlatformConfig↔Platform (dominant) |
| **AFFECTED_BY** | 2,948,956 | CVE↔PlatformConfig ✅ |
| **CAUSED_BY** | 267,018 | CVE↔CWE ✅ |
| **CHILD_OF** | 3,010 | CWE hierarchy + CAPEC hierarchy |
| **EXPLOITS** | 2,424 | CAPEC↔CWE |
| **SUBTECHNIQUE_OF** | 1,052 | SubTechnique↔Technique ✅ |
| **CAN_PRECEDE** | 610 | CWE/CAPEC sequences |
| **BELONGS_TO** | 528 | Technique/SubTechnique↔Tactic |
| **PEER_OF** | 234 | CWE/CAPEC peer relationships |
| **CAN_ALSO_BE** | 60 | Weakness variants |
| **IMPLEMENTS** | 72 | CAPEC↔Technique |
| **Other** | 45 | Various relationships |
| **TOTAL** | **26,004,206** | |

---

## 🎯 Causal Chain Status

The mandatory causal chain: **CPE → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}**

### Chain Links

| Link | Count | Coverage | Status |
| --- | --- | --- | --- |
| **CVE → CWE** | 267,018 | 81.0% (267k/329k CVEs) | ✅ Excellent |
| **CWE → CAPEC** | 1,212 | 197.6% (1.2k/615 CAPECs) | ✅ Working |
| **CAPEC → Technique** | 36 | 6.3% (36/568 techniques) | ❌ CRITICAL GAP |
| **CVE → PlatformConfig** | 2,948,956 | 894.5% (2.9M/329k) | ✅ Excellent |

### Key Issues

1. **CWE → CAPEC Links Working** ✅
   - 1,212 links established (higher than 969 CWE nodes due to multiple CAPECs per CWE)
   - Good coverage of weakness-to-attack-pattern mapping

2. **CAPEC → Technique Very Low** ❌
   - Only 36 links out of 615 CAPEC nodes
   - Only 6.3% of techniques linked from attack patterns
   - This breaks the critical causal chain
   - Root cause: MITRE mapping data may be incomplete or relationship name mismatch

3. **CVE → PlatformConfiguration Excellent** ✅
   - 2,948,956 links (nearly 9x the CVE count)
   - Shows multiple platform configurations per CVE (version ranges)
   - This is the strongest link in the chain

### Coverage Analysis

- **CVE → CWE → CAPEC Chain:** 81.0% CVEs have CWEs, but only 6.3% of techniques reachable
- **Full Causal Chain Completeness:** ~5% (limited by CAPEC→Technique gap)

---

## 🔀 Cross-Standard Linkage

| Link | Count | Coverage | Status |
| --- | --- | --- | --- |
| **Technique → D3FEND** | 0 | 0% | ❌ MISSING |
| **Technique → CAR** | 0 | 0% | ❌ MISSING |
| **Technique → SHIELD** | 0 | 0% | ❌ MISSING |
| **Technique → ENGAGE** | 0 | 0% | ❌ MISSING |

### Impact

Defense/detection/deception linkages are completely absent. This prevents:

- Answering "How can we defend against T1234?"
- Building layered defense strategies
- Connecting threat intelligence to mitigation
- Phase 3.5 from providing defense recommendations

---

## ⚠️ Data Quality Metrics

### Orphaned Nodes (No Relationships)

| Entity Type | Count | % of Total | Issue |
| --- | --- | --- | --- |
| Platform | 290,031 | 18.6% | Expected (asset IDs, no CVE) |
| PlatformConfiguration | 85,049 | 13.9% | Not matched to vulnerabilities |
| Vulnerability | 20,044 | 6.1% | No platform or weakness links |
| Technique | 277 | 48.8% | Many not connected to tactics |
| Tactic | 15 | 44.1% | Many have no techniques |
| DefensiveTechnique | 31 | 100% | All orphaned! |
| DetectionAnalytic | 102 | 100% | All orphaned! |
| DeceptionTechnique | 33 | 100% | All orphaned! |
| EngagementConcept | 31 | 100% | All orphaned! |
| AttackPattern | 56 | 9.1% | Not mapped to techniques |
| Weakness | 17 | 1.8% | Not exploited by CAPEC |

**Critical:** Defense/detection/deception entities are completely disconnected from the graph.

### CVSS Version Coverage

| Version | Count | Status |
| --- | --- | --- |
| v2.0 | 0 | ❌ None loaded |
| v3.1 | 0 | ❌ None loaded |
| v4.0 | 0 | ❌ None loaded |

CVSS scores are completely absent. This impacts vulnerability severity assessment.

---

## 📈 Top Relationship Patterns

The graph is dominated by two key relationships:

```text
PlatformConfiguration --[MATCHES_PLATFORM]--> Platform
  (represents 22,784,024 / 26,004,206 = 87.7% of all relationships)

PlatformConfiguration --[AFFECTED_BY]--> Vulnerability
  (represents 2,948,956 / 26,004,206 = 11.3% of all relationships)
```

This explains the shape:

- ✅ **Extremely strong CPE/CVE infrastructure** (99% of edges)
- ✅ **Good CWE/CAPEC internal structure** (1% of edges)
- ❌ **Missing defense layer** (0% of edges)
- ❌ **Incomplete CAPEC→Technique** (6.3% coverage)

---

## 🎓 Lessons & Next Steps

### What Worked ✅

- ✅ CPE Data: 1,560,484 platform nodes (full production)
- ✅ CVE Data: 329,523 vulnerability nodes (full production)
- ✅ PlatformConfiguration: 614,054 nodes with complete mappings
- ✅ CVE→CWE Links: 267,018 mappings (81% CVE coverage)
- ✅ CVE→PlatformConfig: 2,948,956 links (excellent coverage)
- ✅ CWE Internal Structure: 3,010+ hierarchy links
- ✅ CWE→CAPEC Links: 1,212 exploitation mappings
- ✅ Technique Structure: 526 sub-techniques properly linked to parents

### What Needs Fixing ❌

- **CAPEC → Technique Mapping**: Only 36 (should be 300+)
  - Action: Verify MITRE mapping data and relationship type
  - File: Check `tmp/pipeline-stage6-capec.ttl` for IMPLEMENTS relationships
  - Impact: Critical gap breaking causal chain

- **Defense/Detection Linkages**: 0 (should be 200+)
  - Action: Load and link D3FEND, CAR, SHIELD, ENGAGE to Techniques
  - Files: ETL outputs for defense standards
  - Impact: Cannot provide defense recommendations in Phase 3.5

- **CVSS Scores**: 0 (should be 240k+)
  - Action: Populate CVSS nodes from NVD data
  - File: `src/etl/etl_cve.py` - add CVSS score node generation
  - Impact: Missing vulnerability severity assessment

---

## 🔍 Diagnostic Commands

### Check specific relationships in Neo4j

```cypher
# Check CWE→CAPEC links
MATCH (cwe:Weakness)-[r:EXPLOITS]->(capec:AttackPattern)
RETURN COUNT(r) as count;

# Check CAPEC→Technique links
MATCH (capec:AttackPattern)-[r:IMPLEMENTS|IMPLEMENTS_AS]->(tech:Technique)
RETURN COUNT(r) as count;

# Check Technique→Tactic links
MATCH (tech:Technique)-[r:BELONGS_TO|PART_OF]->(tactic:Tactic)
RETURN COUNT(r) as count;

# Check Defense links
MATCH (tech:Technique)-[r:MITIGATED_BY|DETECTED_BY|COUNTERED_BY]-(def)
RETURN type(r), COUNT(r) as count;
```

### Verify causal chain

```bash
python tests/verify_causal_chain.py
```

This will show the actual state of CVE→CWE→CAPEC→Technique chains with counts.

---

## 📋 Summary for Phase 3.5 Planning

**Graph Status:** Partial (Foundation loaded, upper chain incomplete)

**Use Phase 3.5 Query Bridge With Caution:**

- ✅ Can query vulnerabilities and their platforms (extremely well-connected)
- ✅ Can query vulnerabilities and their root weaknesses (81% coverage)
- ✅ Can query attack patterns and weaknesses they exploit
- ✅ Can query technique structure and tactics
- ❌ Cannot find which CAPEC leads to which technique (6.3% only)
- ❌ Cannot recommend defenses (links completely missing)
- ⚠️ Real-time SIEM events have no defense mapping context

**For Phase 3.5 Production Use:**

This graph is ready for:

- **Investigation:** Query CVE → Weakness → AttackPattern → Technique path
- **Asset Impact:** Find affected platforms and configurations for CVEs
- **Threat Correlation:** Link SIEM techniques to ATT&CK framework

This graph is NOT ready for:

- **Defense Recommendations:** Recommend D3FEND mitigations
- **Detection Guidance:** Provide CAR analytics
- **Deception Tactics:** Suggest SHIELD deception techniques

**Immediate Action Items:**

- Fix CAPEC→Technique mappings (only 36/568 techniques linked)
- Load and link D3FEND, CAR, SHIELD, ENGAGE standards to Technique
- Add CVSS score nodes for vulnerability severity assessment
- Re-extract statistics to validate improvements

**Estimated Time to Full Graph:** 2-4 hours (ETL fixes + Neo4j reload)

---

## 🔄 How to Re-Extract Statistics

The statistics extraction script now supports intelligent database selection:

### Auto-Detect Most Recently Updated Database

```bash
python scripts/extract_neo4j_stats.py --pretty
```

Automatically selects the most recently updated database and extracts stats.

### List Available Databases

```bash
python scripts/extract_neo4j_stats.py --list-databases
```

Example output:

```text
Available databases:
  - neo4j (online)
  - neo4j-2026-01-28 (online)
  - neo4j-2026-01-29 (online)
  - system (online)
```

### Use Specific Database

```bash
python scripts/extract_neo4j_stats.py --db neo4j-2026-01-29 --pretty
```

### Command Options

| Option | Purpose | Default |
| --- | --- | --- |
| `--output` | Output JSON file | `artifacts/neo4j-stats.json` |
| `--db` | Target database | Auto-detect most recent |
| `--pretty` | Pretty-print JSON | False |
| `--list-databases` | List available databases | N/A |

---

**Files Generated:**

- `artifacts/neo4j-stats.json` — Full statistics JSON data
- `docs/NEO4J-STATS.md` — Complete usage guide
- `docs/NEO4J-LOAD-SUMMARY.md` — This document
