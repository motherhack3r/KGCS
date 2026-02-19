# ENGAGE Ontology v2.0 To-Do List

This document is _Aligned with KGCS v2.0 Versioning Plan and ENGAGE Gap Analysis_

---

## 1. Schema & Ontology Alignment

- Review all ENGAGE raw schemas and enumerate all fields, relationships, and entities (EngagementConcept, EngagementObjective, OperationalContext, StakeholderImpact, etc.).
- Ensure v2.0 ontology covers all core classes, subclasses, and properties as defined in authoritative ENGAGE schemas.
- Document any schema fields or relationships not present in v1.0 ontology.

## 2. ETL & Property Mapping

- Update ETL (src/etl/etl_engage.py) to map all required ENGAGE ontology and schema properties:
  - riskLevel, costLevel, sophisticationRequired, effectivenessMetric, legalConsiderations, strategyType, timeframe, operationalLevel, implementationStatus, publishedDate, lastModifiedDate, url, and all required fields for EngagementConcept, EngagementObjective, OperationalContext, StakeholderImpact.
- Implement subclass structure in ETL output (DisruptionStrategy, AttributionStrategy, etc.) using correct RDF types.
- Add support for all key object properties: achieves, applicableInContext, hasImpact, complementedBy, requiresCoordination, affects, targets.
- Ensure all relationships are traceable to source data (no fabricated edges).

## 3. SHACL Validation

- Define and update SHACL shapes for all new/expanded ENGAGE classes and properties.
- Enforce SHACL constraints in ETL output: all mandatory fields and relationships must be present.
- Add tests to validate ETL output against SHACL shapes.

## 4. Enrichment & Gap Closure

- Review ENGAGE raw data and schemas for any unmapped fields or relationships; extend ETL and ontology to cover them.
- Compare with any external ENGAGE ontologies in schemas/ for enrichment opportunities.
- Maintain a gap table tracking raw fields, ontology mapping, ETL status, TTL output, and external ontology coverage.

## 5. Documentation & Traceability

- Document all ontology, ETL, and SHACL changes in this file and supporting docs.
- Provide rationale for all modeling decisions and enrichment steps.
- Update migration and enrichment documentation as analysis progresses.

## 6. Prioritization & Reasoning Value

- Prioritize implementation of properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.
- Focus on high-value engagement relationships and provenance.

## 7. Next Steps

- Plan and assign implementation tasks for the feature branch.
- Incrementally update this file as work progresses and new gaps are identified.

---

**References:**

- [ENGAGE Gap Analysis](../../../agent/to-do-engage.md)
- [KGCS v2.0 Versioning Plan](versioning-plan.md)
- [ENGAGE Schemas](../../../data/engage/schemas/)
- [ETL: src/etl/etl_engage.py](../../../src/etl/etl_engage.py)
- [SHACL: docs/ontology/shacl/]
