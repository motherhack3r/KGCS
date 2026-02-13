# Phase 3.5 Graph Enrichment: Issues and Fix Tasks

**Date:** 2026-02-13  
**Branch:** `feat/phase35-graph-enrichment`  
**Scope:** Pre-implementation analysis before applying enrichment fixes.

## Status Update (2026-02-13, Post Phase A Validation)

Recent Phase A work has been validated and committed. This document now tracks both outstanding enrichment gaps and items already addressed.

### Completed in current branch

- D3FEND Phase A relationship families now materialize in Neo4j (`ANALYZES`, `MONITORS`, `HARDENS`, `FILTERS`, `ISOLATES`, `RESTRICTS`, `ENABLES`, `BLOCKS`) with non-zero counts in validation artifacts.
- D3FEND ETL emits stronger reference/resource typing for Phase A assertions.
- SHACL constraints for D3FEND Phase A were aligned for operational validation (including `ex:references` IRI-kind enforcement and dedicated reference shape checks).
- Loader write concurrency hardening is in place via a single-writer lock to prevent concurrent rel-load deadlocks.
- Label inference coverage was extended for D3FEND resource URIs (`/d3fentity/` → `D3fendResource`) to reduce rel-only endpoint misses.
- CAPEC ATT&CK technique ID normalization is implemented in ETL (`src/etl/etl_capec.py`) so mappings are canonicalized to `Txxxx` / `Txxxx.xxx` before URI emission.
- Task 5 regression coverage was added and validated (`tests/unit/test_etl_capec_attack_id_normalization.py`; `2 passed`).
- CWE XML extraction was expanded for schema-defined fields including introduction modes, likelihood, consequences, detection methods, mitigations, references, notes, and observed CVE examples (`src/etl/etl_cwe.py`).
- CWE extraction now preserves schema-native sub-entity IDs (`Consequence_ID`, `Detection_Method_ID`, `Mitigation_ID`) for stable URI emission and provenance fidelity.
- CWE SHACL status enum was aligned with current CWE schema values (`Deprecated|Draft|Incomplete|Obsolete|Stable|Usable`) in `docs/ontology/shacl/cwe-shapes.ttl`.
- Task 7/8 regression coverage was added and validated (`tests/unit/test_etl_cwe_enrichment_extraction.py`; focused suite passing).
- CAR ETL now extracts ATT&CK IDs from `coverage[].technique` and `coverage[].subtechniques`, with canonical `Txxxx` / `Txxxx.xxx` normalization for `DETECTS` emission (`src/etl/etl_car.py`).
- SHIELD ETL directory normalization now preserves `attack_techniques` (and `Counters*` variants) from detail-file shapes and emits `COUNTERS` links (`src/etl/etl_shield.py`).
- ENGAGE ETL now ingests list-based and dict-based `attack_mapping.json` forms (including `eac_id` ↔ `attack_id`) and additional activity `attack_techniques`, normalized before `DISRUPTS` emission (`src/etl/etl_engage.py`).
- D3FEND ETL SPARQL mapping ingestion now canonicalizes ATT&CK IDs from URI/literal forms (including slash-form subtechniques) before `MITIGATES` emission (`src/etl/etl_d3fend.py`).
- P2 regression coverage added and validated (`tests/unit/test_etl_car_coverage_attack_links.py`, `tests/unit/test_etl_shield_attack_mapping.py`, `tests/unit/test_etl_engage_attack_mapping.py`, `tests/unit/test_etl_d3fend_attack_id_normalization.py`; focused suite passing).

### Still pending

- P1 reporting/statistics correctness items (Section 1 tasks) remain open.
- CVE CVSS v2.0/v3.0/v3.1/v4.0 ingestion update remains open.
- Remaining loader/stat audits and full post-fix Neo4j rerun/stat publication remain open.

---

## (A) Detailed List of Issues Found

## 1) Metrics/Reporting Issues (False negatives in stats)

### 1.1 Directionality is misreported for relationships

- **Observed:** Stats report the same relationship in both directions (for example `SUBTECHNIQUE_OF`, `HAS_CONSEQUENCE`, `EXPLOITED_BY`).
- **Root cause:** Relationship pattern query uses undirected Cypher (`MATCH (source)-[r]-(target)`), so each directed edge is counted from both endpoint perspectives.
- **Impact:** Creates the appearance that inverse edges exist in Neo4j when only one directed edge was loaded.
- **Evidence:** `scripts/utilities/extract_neo4j_stats.py` relationship pattern query.

### 1.2 Causal-chain and cross-standard counters use stale relationship names

- **Observed:** `capec_to_technique=0`, `cve_to_platform_config=0`, and all cross-standard counters are 0 despite ETL outputs containing those predicates.
- **Root cause:** Stats use legacy relationship names (`AFFECTS`, `IMPLEMENTS`, `MITIGATED_BY`, `DETECTED_BY`, etc.) that do not match current loader output naming (`AFFECTED_BY`, `IMPLEMENTED_AS`, `MITIGATES`, `DETECTS`, `COUNTERS`, `DISRUPTS`).
- **Impact:** Underestimates graph completeness and misguides prioritization.
- **Evidence:** `scripts/utilities/extract_neo4j_stats.py` vs relationship naming behavior in `src/etl/rdf_to_neo4j.py`.

### 1.3 CVE→CWE coverage metric is computed incorrectly

- **Observed:** `cves_with_cwe=714` for 332,481 CVEs (0.21%), inconsistent with direct relationship totals (`CAUSED_BY=270,321`).
- **Root cause:** Query counts distinct CWE nodes, not distinct CVE nodes that have at least one CWE edge.
- **Impact:** Severe understatement of causal-chain coverage.
- **Evidence:** Coverage query in `scripts/utilities/extract_neo4j_stats.py`.

### 1.4 Platform configuration coverage metric uses stale edge type

- **Observed:** `total_configs=0` despite 617,105 `PlatformConfiguration` nodes.
- **Root cause:** Query expects `INCLUDES`, while ETL/loader uses `MATCHES_PLATFORM`.
- **Impact:** Incorrect platform-configuration health signal.
- **Evidence:** `scripts/utilities/extract_neo4j_stats.py` and loaded relationship stats.

---

## 2) CVE Standard Gaps

### 2.1 CVSS not ingested from NVD 2.0 schema path

- **Observed:** No `Score` nodes and no CVSS version counts.
- **Root cause:** CVE ETL reads legacy `impact.baseMetricV2/baseMetricV3` style, while current schema defines CVSS in `metrics.cvssMetricV2/cvssMetricV30/cvssMetricV31/cvssMetricV40`.
- **Impact:** Loss of severity information and version-specific risk attributes.
- **Evidence:** `src/etl/etl_cve.py` CVSS extraction logic vs `data/cve/schemas/cve_api_json_2.0.schema`.

### 2.2 CVE configuration logic is flattened in graph usage

- **Observed:** `AFFECTED_BY` links exist, but decision logic fields (for example `vulnerable`, version bounds) are not leveraged in relationship semantics and downstream reporting.
- **Root cause:** CVE ETL links CVE to precomputed `PlatformConfiguration` by `matchCriteriaId`, but no additional derived relationship-level semantics are represented.
- **Impact:** Difficult to reason over include/exclude/version-bound logic directly from relationship view.
- **Evidence:** `src/etl/etl_cve.py`, `src/etl/etl_cpematch.py`.

---

## 3) CAPEC / ATT&CK Linking Gaps

### 3.1 CAPEC→ATT&CK links are underloaded due ATT&CK ID normalization mismatch

- **Observed:** `IMPLEMENTED_AS` count in Neo4j is far below expected mappings.
- **Root cause:** CAPEC ETL emits ATT&CK URIs with mixed ID formats (`1110`, `T1148`, `1574.010`), while ATT&CK ETL creates nodes with canonical `Txxxx` / `Txxxx.xxx` IDs.
- **Impact:** Many valid CAPEC mappings fail endpoint match during relationship load.
- **Evidence:** `data/capec/samples/pipeline-stage6-capec-rels.ttl` and ID handling in `src/etl/etl_attack.py` / `src/etl/etl_capec.py`.

---

## 4) CWE Standard Enrichment Gaps

### 4.1 CWE XML parser drops many schema-defined fields before transform

- **Observed:** Missing rich CWE properties such as `Modes_Of_Introduction`, `Likelihood_Of_Exploit`, `Detection_Methods`, `Potential_Mitigations`, and additional narrative structures.
- **Root cause:** XML normalization (`_cwe_xml_to_json`) currently extracts a reduced field set only.
- **Impact:** Graph has structural CWE links but reduced semantic depth compared with CWE source standard.
- **Evidence:** `src/etl/etl_cwe.py` normalization function and `data/cwe/raw/cwec_v4.19.1.xml`.

### 4.2 CWE relationship model is present but not fully exploited

- **Observed:** Some relationship types are ingested (`CHILD_OF`, `PEER_OF`, `CAN_PRECEDE`, etc.), but additional relational richness from source can still be expanded.
- **Root cause:** Limited extraction from all available CWE relationship/context blocks.
- **Impact:** Reduced navigability and explainability in weakness reasoning paths.

---

## 5) Cross-Standard Defense/Detection/Engagement Gaps

### 5.1 D3FEND cross links are blocked by raw input availability

- **Observed:** No D3FEND→ATT&CK link presence in final stats.
- **Root cause:** Current raw folder contains only `d3fend.owl`; stage flow expects JSON-compatible sources for implemented transformer path.
- **Impact:** Defense layer remains disconnected from ATT&CK techniques.
- **Evidence:** `data/d3fend/raw/` current contents and `scripts/run_all_etl.py` stage 5 file expectations.

### 5.2 CAR technique mappings are under-extracted from YAML shape

- **Observed:** Very low cross links (`REQUIRES=13`; no meaningful `DETECTS` in final graph stats).
- **Root cause:** Extractor focuses on top-level technique-key variants, while many CAR files encode ATT&CK coverage under `coverage[].technique` and `coverage[].subtechniques`.
- **Impact:** Detection analytics are mostly disconnected from ATT&CK layer.
- **Evidence:** `src/etl/etl_car.py` extraction functions and CAR raw examples.

### 5.3 SHIELD ATT&CK mappings are lost during normalization

- **Observed:** High node count for `DeceptionTechnique` but no meaningful technique links.
- **Root cause:** Directory loader normalization retains only ID/name/description; ATT&CK mapping structures from raw detail files are dropped.
- **Impact:** Deception layer is effectively orphaned.
- **Evidence:** `src/etl/etl_shield.py` `_load_shield_data` behavior and SHIELD raw details data.

### 5.4 ENGAGE ATT&CK disruptions likely under-extracted

- **Observed:** `EngagementConcept` nodes exist but no technique disruption links in stats.
- **Root cause:** Mapping depends on `attack_mapping.json` shape and ID compatibility; extraction path is narrow and may miss valid mappings.
- **Impact:** Engagement layer remains disconnected from ATT&CK reasoning path.
- **Evidence:** `src/etl/etl_engage.py` normalization and disruption-link creation logic.

---

## 6) Additional Loader/URI Alignment Risks

### 6.1 URI alias mismatches can silently drop relationships

- **Observed:** Relationship loading relies on URI-to-label inference for rel-only files.
- **Risk:** Any URI pattern not covered by `_infer_label_from_uri` can create missing source/target label inference and reduce loaded edges.
- **Impact:** Silent graph incompleteness for affected standards.
- **Evidence:** `src/etl/rdf_to_neo4j.py` label inference + rel-only load strategy.

---

## (B) List of Fix Tasks

## P1 — Correctness First (required before interpreting KPIs)

1. **Fix stats relationship-pattern directionality**

   - Update relationship pattern query to directed traversal (`MATCH (source)-[r]->(target)`).
   - Remove synthetic reverse rows.
   - **Acceptance:** `SUBTECHNIQUE_OF` appears only as `SubTechnique -> Technique` in stats output.

2. **Align all stats queries with current relationship semantics**

   - Replace stale edge names with canonical loader names:
     - `AFFECTED_BY`, `IMPLEMENTED_AS`, `MITIGATES`, `DETECTS`, `COUNTERS`, `DISRUPTS`, `MATCHES_PLATFORM`, etc.
   - **Acceptance:** non-zero values where corresponding relationships exist in database.

3. **Fix CVE→CWE coverage computation**

   - Count distinct CVE nodes that have at least one `CAUSED_BY` relationship.
   - **Acceptance:** coverage percentage aligns with observed relationship totals.

4. **Fix platform/config coverage query**

   - Use `MATCHES_PLATFORM` semantics instead of `INCLUDES`.
   - **Acceptance:** `total_configs` > 0 and consistent with node counts.

---

## P1 — Causal Chain Integrity (core chain completion)

- **Task 5: Normalize CAPEC ATT&CK technique IDs before emitting URIs**
  Details: Canonicalize all mapped ATT&CK IDs to `Txxxx` / `Txxxx.xxx`; preserve source ID as provenance literal if needed.  
  Acceptance: significant increase in `IMPLEMENTED_AS` loaded relationships.
  Status: **Completed (implementation + unit tests)**. Neo4j delta verification deferred until full graph reload.

- **Task 6: Update CVE ETL to ingest NVD 2.0 CVSS metrics**
  Details: Parse `metrics.cvssMetricV2`, `cvssMetricV30`, `cvssMetricV31`, `cvssMetricV40`; emit version-separated score nodes and CVE→score edges.  
  Acceptance: non-zero `Score` nodes and non-zero per-version counts.

---

## P2 — Standards Depth Enrichment

- **Task 7: Expand CWE XML extraction coverage**
   Details: Add extraction for `Modes_Of_Introduction`, `Likelihood_Of_Exploit`, `Detection_Methods`, `Potential_Mitigations`, and additional consequence/context fields present in source; map only to existing ontology predicates/classes or approved extension points.  
   Acceptance: measurable increase in CWE property and relationship richness without SHACL regressions.
  Status: **Completed (implementation + focused unit tests)**.

- **Task 8: Expand CWE relationship/context extraction**
   Details: Include additional valid relationship/context structures where supported by ontology.  
   Acceptance: increased inter-weakness and context linkage with provenance retained.
  Status: **Completed (implementation + focused unit tests)**.

---

## P2 — Cross-Standard Defense/Detection/Engagement Connectivity

- **Task 9: CAR: parse ATT&CK mappings from `coverage[]` structures**
  Details: Extract both primary techniques and subtechniques from YAML coverage blocks and emit `DETECTS` edges against canonical technique/subtechnique URIs.  
  Acceptance: substantial increase in CAR↔ATT&CK links.
  Status: **Completed (implementation + focused unit tests)**. Neo4j delta verification deferred until full graph reload.

- **Task 10: SHIELD: preserve and map ATT&CK technique associations from raw detail files**
  Details: Extend normalization to keep `attack_techniques` and map to graph relationships.  
  Acceptance: non-zero SHIELD↔ATT&CK relationship counts.
  Status: **Completed (implementation + focused unit tests)**. Neo4j delta verification deferred until full graph reload.

- **Task 11: ENGAGE: broaden attack mapping extraction and ID normalization**
  Details: Ensure `DisruptsTechniques` is populated from available mapping files and canonicalized.  
  Acceptance: non-zero ENGAGE↔ATT&CK relationship counts.
  Status: **Completed (implementation + focused unit tests)**. Neo4j delta verification deferred until full graph reload.

- **Task 12: D3FEND ingestion compatibility pass**
  Details: Support available raw source forms (`.owl` and/or generated mapping artifacts) to emit valid ATT&CK links.  
  Acceptance: non-zero D3FEND↔ATT&CK relationship counts from current dataset.
  Status: **Completed (implementation + focused unit tests for mapping normalization paths)**. Full dataset-level Neo4j count verification deferred until full graph reload.

---

## P3 — Loader Robustness and Validation

- **Task 13: Audit `_infer_label_from_uri` coverage against all rel-only stage outputs**
  Details: Add alias support for any uncovered URI patterns.  
  Acceptance: zero or near-zero missing source/target label inference for rel files.
  Status: **Partially complete** (D3FEND `/d3fentity/` mapping plus SHIELD/ENGAGE aliases `/deception/` and `/engagement/` added after regenerating stages 5/8/9/10; targeted rel-file audit for those stages now reports zero unknown endpoint labels. Full multi-standard audit remains pending).

- **Task 14: Add targeted verification scripts and regression checks**
  Details: Add relationship directionality checks, causal chain completeness checks, and per-standard link coverage checks (CAPEC↔ATT&CK, ATT&CK↔Defense layers).  
  Acceptance: repeatable pre-load and post-load quality gates.

- **Task 15: Regenerate and publish updated stats artifact after fixes**
  Details: Re-run ETL stages affected by fixes, reload Neo4j, and extract revised stats.  
  Acceptance: artifact demonstrates corrected metrics and expected enrichment improvements.
  Status: **Partially complete** (Stage 5 D3FEND-focused artifacts published; full Phase 3.5 post-fix global artifact still pending).

---

## Execution Note

Implementation should proceed in this order:

1) Stats correctness (P1 reporting),
2) Causal-chain integrity fixes (CAPEC ID normalization + CVSS ingestion),
3) Cross-standard enrichment,
4) Full rerun + refreshed artifact publication.
