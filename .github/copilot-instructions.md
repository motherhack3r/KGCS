# KGCS Copilot Instructions

Authoritative guidance for AI coding agents contributing to KGCS.

## Mission and invariants
- Preserve the frozen, standards-aligned ontology that maps 1:1 to authoritative MITRE/NVD schemas (CPE, CVE, CVSS, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).
- Enforce explicit provenance for every class and edge; no invented semantics or unlabeled relationships.
- Keep the core causal chain intact: **CPE → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}**
- Core remains immutable; extensions (Incident, Risk, ThreatActor) only reference core and never modify or override it.
- **Critical invariant:** Vulnerabilities affect `PlatformConfiguration` (version/update specifics), not `Platform` (atomic CPE identifier).

## Working rules
- Do not rename or repurpose core classes/edges; align any new element to a stable external ID and cite its source field.
- Avoid introducing organizational or contextual data into core; place such concepts in the relevant extension OWL module and keep imports one-way into core.
- Prefer additive changes; if you must touch existing semantics, pause and request human review.
- Keep ontology modules modular (no circular imports) and versioned as standalone OWL files under docs/ontology/.
- Core ontology modules live in docs/ontology/owl/ (e.g., cpe-ontology.owl, cve-ontology.owl, etc.); extensions live in docs/ontology/extensions/ (e.g., incident-extension.owl, risk-extension.owl); RAG templates in docs/ontology/rag/.
- When adding a new OWL module, register its `--owl <module.owl>` name in this file and in SHACL validator args so CI auto-detects it.
- **CVSS versioning:** Each version is a separate node (v2.0, v3.1, v4.0); never merge or overwrite—new versions coexist with old.
- **1:1 standards alignment:** Every ontology class maps directly to one source standard (e.g., `Platform` ↔ CPE 2.3, `Technique` ↔ ATT&CK STIX 2.1). If source doesn't have it, class doesn't have it.

## Validation and QA
- Run SHACL locally before pushing:
  - Canonical check against bundled shapes and samples: `python scripts/validate_shacl.py --data data/shacl-samples/sample_attack.ttl` (or iterate over all samples in data/shacl-samples/).
  - Module-specific check when an OWL changes: `python scripts/validate_shacl.py --data data/shacl-samples/sample_attack.ttl --owl <module.owl>`.
  - When OWL modules are added or changed, verify against both positive (good-*.ttl) and negative (bad-*.ttl) samples in data/shacl-samples/.
- Expect machine-readable reports in artifacts/; inspect failures and include the report when raising PRs.
- CI workflow .github/workflows/shacl-validation.yml auto-detects changed OWL files under docs/ontology/owl/ and validates them; when no OWL changes, it validates canonical bundles against data/shacl-samples/*.ttl.
- When ETL/ingestion validation is integrated (Phase 3), ensure pre-ingest SHACL checks emit failure payloads to artifacts/ and abort writes on invalid input.
- Keep sample TTLs small and deterministic; add positive and negative samples alongside new shapes.

## RAG and traversal safety
- Use only approved traversal templates (see ../docs/ontology/rag/RAG-travesal-templates.md for core and ../docs/ontology/rag/RAG-travesal-templates-extension.md for extensions); reject or flag free-form paths that skip the causal chain or mix standards without provenance.
- Every query or generated explanation must return paths with evidence (IDs and source fields). If provenance is missing, treat it as a failure.
- Enforce query-time traversal validation (planned in Phase 5); until then, ensure RAG templates are documented and reviewed before deployment.

## Ingestion and data handling
- Ingestion scripts (e.g., scripts/ingest_pipeline.py and etl_* loaders) must preserve source hashes, timestamps, and external IDs; ingestion should be idempotent.
- Never fabricate relationships to “connect the graph”; every edge must come from source data or a declared extension rule.
- Keep artifacts/ for validation outputs; avoid committing large raw datasets into data/ unless already curated samples.
## Common task patterns
- **Adding a new relationship:** Verify it exists in source standard → Update edge in core ontology → Add OWL axiom → Update RAG templates if reasoning path changes.
- **Ingesting new standard version:** Create versioned module (e.g., `cpe-ontology-v3.0.owl`) → Update mappings documentation → Decide if coexists or replaces → Validate no URI breakage.
- **Supporting new use case:** Classify as Core (authoritative standard mapping) or Extension (temporal, contextual, inference) → Never modify Core to support use cases → Define RAG templates → Add SHACL constraints.

## Golden rules
1. **External standards are authoritative.** If MITRE/NVD say it, we model it. If they don't, it belongs in an extension.
2. **Frozen Core, flowing Extensions.** Core changes rarely; extensions are where complexity grows.
3. **RAG is templated, not freeform.** LLM reasoning follows pre-approved traversal patterns only.
4. **Trace everything back.** Every statement traceable to source with stable ID.
5. **One-way import flow.** Core never polluted by extensions.
6. **No circular dependencies.** Ontology modules form a DAG.

## When in doubt
- Ask for human review before altering core semantics or SHACL shapes.
- Default to preserving immutability and provenance over convenience or inferred links.
