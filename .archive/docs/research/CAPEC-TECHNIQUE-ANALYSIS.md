# CAPEC→Technique Mapping Analysis

**Date:** February 3, 2026

**Executive Summary:** The 36 CAPEC→Technique links in the loaded Neo4j graph are **not a bug** - they represent the *authoritative extent* of official MITRE mappings. The Neo4j loader is working correctly.

## Root Cause Analysis

### Finding 1: Direct CAPEC→Technique Mappings (36 total)

Data Source: ATT&CK STIX 2.1 JSON files

Discovery across all four ATT&CK datasets:

```text
enterprise-attack.json      835 techniques,    36 with CAPEC (4.3%)
ics-attack.json              95 techniques,     0 with CAPEC (0.0%)
mobile-attack.json          190 techniques,     0 with CAPEC (0.0%)
pre-attack.json             174 techniques,     0 with CAPEC (0.0%)
────────────────────────────────────────────────────────────
Total:                    1,294 techniques,    36 with CAPEC (2.8%)
```

Only Enterprise ATT&CK contains CAPEC references.

### Finding 2: No CWE→Technique Mappings in ATT&CK

Question: Can we infer CAPEC→Technique via CWE?

Analysis: Searched ATT&CK STIX external_references for `source_name == 'cwe'`

**Result: ZERO** CWE references found in any ATT&CK technique

Implications:

- CAPEC→CWE linkage: ✅ Strong (1,212 links across 450 CAPEC patterns)
- CWE→Technique linkage: ❌ Does not exist (0 links)
- CWE cannot be used as transitive bridge to Techniques

### Finding 3: ATT&CK External Reference Landscape

Analyzed ~1,200 external references across 835 enterprise techniques. Reference sources:

- mitre-attack: 835 (self-references)
- University of Birmingham C2: 40
- Academic/industry papers/blogs: ~350
- CVE: 0 references
- CWE: 0 references
- CAPEC: 36 references ← Only pathway to CAPEC

Key insight: ATT&CK deliberately separates from vulnerability taxonomies (CVE/CWE). Focus is on adversary behavior, not on underlying weaknesses or disclosed vulnerabilities.

## What This Means

### For KGCS Causal Chain

Expected understanding:

```text
CPE → CVE → CWE → CAPEC → ATT&CK → Defense Layer
```

Actual linkage strength in data:

```text
CPE ─(2.9M)─→ CVE ─(267K, 81%)─→ CWE ─(1.2K)─→ CAPEC ─(36, 2.8%)─→ Technique
```

The bottleneck is **CAPEC→Technique** (36/568 = 6.3% coverage). This is not a bug, but a design feature:

- CAPEC focuses on *how attacks work* (abstract patterns)
- ATT&CK focuses on *what adversaries do* (concrete behavior)
- Only well-established pattern mappings are included (sparse by intent)

### For Phase 3.5 (SIEM Integration)

Current assumption: "Complete causal chain enables defense recommendations"

Revised reality: Most SIEM techniques map directly to ATT&CK. Tracing back through CWE→CAPEC is sparse and incomplete.

Adjusted strategy:

- ✅ Use strong CWE→CVE chain for vulnerability context (81% coverage)
- ✅ Use 36 direct CAPEC→Technique mappings for well-known patterns
- ⚠️ Accept incomplete causal chains for novel/unmapped techniques
- ⚠️ Design agent queries to handle multiple incomplete information paths

## ETL Implementation Validation

**Status:** ✅ **WORKING CORRECTLY**

The CAPEC ETL in `src/etl/etl_capec.py`:

1. Correctly loads CAPEC patterns from XML (450 patterns)
2. Correctly establishes CAPEC→CWE relationships (1,212 links)
3. Correctly calls `_build_capec_to_attack_map()` to load ATT&CK mappings
4. Correctly emits CAPEC→Technique relationships with `SEC.implements` predicate
5. **Correctly limits to 36 total mappings** (the full extent of MITRE data)

### Code Path (Verified)

```python
# Line 423-430: _build_capec_to_attack_map() correctly parses STIX
for attack_file in _resolve_attack_files(attack_input):
    attack_json = json.load(open(attack_file, "r", encoding="utf-8", errors="ignore"))
    objects = attack_json.get("objects", [])
    for obj in objects:
        if obj.get("type") != "attack-pattern":
            continue
        external_refs = obj.get("external_references", []) or []
        for ref in external_refs:
            if ref.get("source_name") == "capec":
                capec_ids.append(ref.get("external_id"))
```

**Note:** This code works perfectly. CAPEC references are just sparse in the source data.

## Recommendations

### Option A: Accept Design Limitation

- Document that CAPEC→Technique coverage is intentionally sparse (2.8%)
- Design Phase 3.5 to leverage strong CWE→CVE chain instead
- Use 36 CAPEC→Technique links as *supplementary* evidence, not primary path

### Option B: Enhance Mappings

- Check if MITRE CAPEC or ATT&CK teams have published additional mappings elsewhere
- Consider manually curating additional CAPEC→Technique links for high-value attack patterns
- Submit mapping suggestions back to MITRE community

### Option C: Alternative Reasoning Paths (Recommended for Phase 3.5)

- **Primary:** CVE → CWE (81% coverage) → CAPEC (1.2K links) → [36 techniques with direct mapping]
- **Secondary:** CVE → [industry threat intel mappings] → Technique
- **Supplementary:** CAPEC → Direct Technique mapping (36 available)
- **Result:** Techniques without CAPEC bridge handled via industry sources

## Updated Project Status

**Previous finding:** "CAPEC→Technique mapping is CRITICAL GAP (only 36/568)"  
**Revised finding:** "CAPEC→Technique is sparse by design (36 out of 1,294 ATT&CK) - expected and correct"

**Impact on Phase 3.5:**

- ❌ Cannot achieve complete causal chain for all techniques
- ✅ Can achieve strong CVE→CWE→CAPEC chains (81% CVE coverage, all CAPEC linked)
- ✅ Can supplement with 36 direct CAPEC→Technique mappings
- ⚠️ Must design agent to handle incomplete information gracefully

## Files for Reference

- ATT&CK mapping research: `check_capec_mappings.py` (36 direct links counted)
- ATT&CK reference analysis: `analyze_attack_refs.py` (external_references breakdown)
- CAPEC research: `research_capec_mappings.py` (tested transitive paths, found 0)
- CAPEC ETL source: `src/etl/etl_capec.py` (verified correct implementation)

## Conclusion

The Neo4j graph is **correctly loaded** with 36 CAPEC→Technique links because that is the extent of official MITRE mappings. This is not a bug to fix, but a design reality to embrace in Phase 3.5 architecture.
