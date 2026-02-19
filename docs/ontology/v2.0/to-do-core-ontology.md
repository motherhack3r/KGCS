# Core Ontology v2.0 To-Do List

This document is _Aligned with KGCS v2.0 Versioning Plan and Core Ontology v1.0 Constitution_

---

## 1. Versioning & Scope

- Freeze v1.0 as immutable, authoritative reference.
- Scaffold core-ontology-v2.0.md and core-ontology-v2.0.owl as new, parallel modules.
- Ensure v2.0 remains strictly standards-backed, with no invented semantics or shortcuts.
- Document all changes, rationale, and migration steps for transparency and traceability.

## 2. Schema-Driven Enrichment

- Review all authoritative standards (CPE, CVE, CVSS, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE) for new or updated schema fields, relationships, and identifiers.
- Expand property and relationship mapping to cover all relevant, standards-backed fields.
- Ensure multi-version coexistence (e.g., CVSS v2/v3/v4) is explicit and lossless.
- Maintain strict separation of conceptual layers (no semantic leakage across layers).

## 3. Causal Backbone & Invariants

- Preserve the non-negotiable causality chain:
  - PlatformConfiguration → Vulnerability → Weakness → AttackPattern → Technique
- Ensure all relationships are traceable to source data and have standard provenance.
- No temporal, probabilistic, or threat actor semantics in Core.

## 4. SHACL & Validation

- Update SHACL shapes to reflect any new or refined properties and relationships.
- Add tests to validate v2.0 data against SHACL constraints and core invariants.

## 5. Documentation & RAG Safety

- Document all ontology, SHACL, and ETL changes in this file and supporting docs.
- Provide canonical traversal examples and RAG-safe query templates.
- Update migration and enrichment documentation as analysis progresses.

## 6. Next Steps

- Plan and assign implementation tasks for the feature branch.
- Incrementally update this file as work progresses and new gaps are identified.

---

**References:**

- [Core Ontology v1.0](../core-ontology-v1.0.md)
- [KGCS v2.0 Versioning Plan](versioning-plan.md)
- [SHACL: docs/ontology/shacl/]
