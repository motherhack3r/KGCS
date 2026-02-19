# ThreatActor Ontology Extension v2.0 To-Do List

This document is _Aligned with KGCS v2.0 Versioning Plan and ThreatActor Extension v1.0_

---

## 1. Versioning & Scope

- Freeze v1.0 as immutable, authoritative reference.
- Scaffold threatactor-ontology-extension-v2.0.md and threatactor-ontology-extension-v2.0.owl as new, parallel modules.
- Ensure v2.0 remains strictly layered on top of Core, with all attribution and intelligence logic contained in the extension.
- Document all changes, rationale, and migration steps for transparency and traceability.

## 2. Schema-Driven Enrichment

- Review threat intelligence models and authoritative sources for new or updated fields, relationships, and identifiers.
- Expand property and relationship mapping to cover all relevant, standards-backed fields (e.g., ThreatActor, AttributionClaim, Capability, Tool, Malware).
- Maintain strict separation of attribution (claim-based) from core factual knowledge.

## 3. Attribution & Intelligence Logic

- Ensure all attribution, confidence, and provenance relationships are explicit and RAG-safe.
- No overwriting or mutation of Core facts in ThreatActor Extension.
- Enforce claim-based attribution with confidence and rationale for every claim.

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

- [ThreatActor Ontology Extension v1.0](../threatactor-ontology-extension-v1.0.md)
- [KGCS v2.0 Versioning Plan](versioning-plan.md)
- [SHACL: docs/ontology/shacl/]
