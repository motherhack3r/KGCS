# CAPEC Mapping Discovery & Fix Summary

## Discovery
From deep analysis of ATT&CK STIX raw data, we found:
- **32 unique CAPEC patterns** referenced by ATT&CK techniques  
- **36 CAPEC→Technique mappings** (some CAPEC patterns map to multiple techniques)
- **All mappings in Enterprise dataset only** (0 in ICS, Mobile, Pre)
- **Issue**: STIX stores CAPEC IDs with double prefix: `CAPEC-CAPEC-13` (malformed)

## What Was Fixed
✅ Updated `src/etl/etl_attack.py`:
  - Added `_extract_capec_ids()` method to parse CAPEC external references
  - Added normalization for double-prefixed IDs (`CAPEC-CAPEC-X` → `X`)
  - Create AttackPattern (CAPEC) nodes and `derived_from` relationships
  - **Result**: 36 CAPEC→Technique relationships now in pipeline-stage4-attack-capec-test.ttl

## Immediate Next Steps
1. **Validate the updated ATT&CK ETL output with SHACL**
   - Fix Python encoding issue in capec ETL for now
   - Run: `python -m src.etl.etl_attack --input data/attack/raw/enterprise-attack.json --output tmp/pipeline-stage4-attack-fixed.ttl --validate`

2. **Regenerate all pipeline stages** (in dependency order):
   - CPE, CPEMatch, CVE, CWE, CAPEC, ATT&CK (with CAPEC fix)
   - D3FEND, CAR, SHIELD, ENGAGE

3. **Reload Neo4j with combined TTL** containing:
   - 36 new CAPEC→Technique relationships
   - Existing 2.5M nodes + causal chain links

## Expected Impact
- **CAPEC coverage:** From 6.3% (36/568 techniques) → potentially much higher once CWE→CAPEC links work
- **Causal chain:** CVE→CWE→CAPEC now properly feeds into ATT&CK Technique layer
- **Graph completeness:** Blocking issue for Phase 3.5 defense recommendations partially resolved

## CAPEC IDs Found
13, 17, 132, 159, 163, 187, 270, 471, 478, 479, 532, 550, 551, 552, 555, 556, 558, 561, 563, 564, 569, 570, 571, 572, 578, 579, 639, 641, 644, 645, 649, 650

## Status
🟡 **In Progress**: CAPEC extraction verified, next is validation and reload
