# Incident Ontology Extension v2.0 To-Do List

This document is _Aligned with KGCS v2.0 Versioning Plan and Incident Extension v1.0_

---

## 1. Versioning & Scope

- Freeze v1.0 as immutable, authoritative reference.
- Scaffold incident-ontology-extension-v2.0.md and incident-ontology-extension-v2.0.owl as new, parallel modules.
- Ensure v2.0 remains strictly layered on top of Core, with no semantic pollution or causality leakage.
- Document all changes, rationale, and migration steps for transparency and traceability.

## 2. Schema-Driven Enrichment

- Review incident data models and authoritative sources for new or updated fields, relationships, and identifiers.
- Expand property and relationship mapping to cover all relevant, standards-backed fields (e.g., ObservedTechnique, DetectionEvent, Evidence, AffectedAsset).
- Maintain strict separation of observation (incident) from abstraction (core concepts).

## 3. Temporal & Evidence Modeling

- Ensure all temporal, evidence, and asset relationships are explicit and RAG-safe.
- No probabilistic or threat actor semantics in Incident Extension.
- Enforce mandatory instance_of (ObservedTechnique → Technique) edge.

## 4. SHACL & Validation

- Update SHACL shapes to reflect any new or refined properties and relationships.
- Add tests to validate v2.0 data against SHACL constraints and extension invariants.

## 5. Documentation & RAG Safety

- Document all ontology, SHACL, and ETL changes in this file and supporting docs.
- Provide canonical traversal examples and RAG-safe query templates.
- Update migration and enrichment documentation as analysis progresses.

## 6. Next Steps

- Plan and assign implementation tasks for the feature branch.
- Incrementally update this file as work progresses and new gaps are identified.

---

**References:**

- [Incident Ontology Extension v1.0](../incident-ontology-extension-v1.0.md)
- [KGCS v2.0 Versioning Plan](versioning-plan.md)
- [SHACL: docs/ontology/shacl/]
