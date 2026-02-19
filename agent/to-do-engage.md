# ENGAGE Ontology & ETL Gap Analysis

**Branch:** feature/engage-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in ENGAGE raw files (JSON, etc.)
- Identify entities (Engagement Activity, Category, Asset, etc.) and their properties

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/engage-ontology-v1.0.owl and engage-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from engage-ontology-v1.0.owl)

- **Core Classes:**
  - `engage:EngagementConcept` (root for all engagement strategies)
    - Subclasses: `DisruptionStrategy`, `OperationalInterference`, `CapabilityDegradation`, `AttributionStrategy`, `CoordinationDisruption`, `ResilienceBuilding`
  - `engage:EngagementObjective`
  - `engage:OperationalContext`
  - `engage:StakeholderImpact`
- **Key Datatype Properties:**
  - `engage:engageId`, `engage:name`, `engage:description`, `engage:strategyType`, `engage:timeframe`, `engage:operationalLevel`, `engage:riskLevel`, `engage:sophisticationRequired`, `engage:costLevel`, `engage:effectivenessMetric`, `engage:applicableAdversary`, `engage:legalConsiderations`, `engage:implementationStatus`, `engage:publishedDate`, `engage:lastModifiedDate`, `engage:url`
  - Objective/context/impact-specific: `objectiveName`, `objectiveDescription`, `successCondition`, `contextName`, `contextDescription`, `contextTriggered`, `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `engage:disrupts` / `engage:disrupted_by` (links EngagementConcept to sec:Technique)
  - `engage:targets` / `engage:targeted_by_engagement`
  - `engage:achieves` / `engage:achieved_by` (links EngagementConcept to EngagementObjective)
  - `engage:applicableInContext` / `engage:context_for_engagement`
  - `engage:hasImpact` / `engage:impact_of`
  - `engage:complementedBy` (symmetric, between EngagementConcepts)
  - `engage:requiresCoordination` / `engage:coordinated_with`
  - `engage:affects` / `engage:affected_by_engagement` (links to sec:AttackPattern)
- **Constraints (SHACL-informative):**
  - EngagementConcepts must have: engageId, name, description, strategyType, timeframe, operationalLevel, effectivenessMetric, and at least one disrupts or affects relationship.
  - Objectives, Contexts, and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - EngagementConcepts can disrupt or affect techniques, achieve objectives, be applicable in contexts, have stakeholder impacts, complement or coordinate with other strategies.

### Gaps vs. ETL

- Many ontology properties (risk, cost, sophistication, legal, effectivenessMetric, etc.) are not mapped in the ETL.
- Object properties like achieves, applicableInContext, hasImpact, complementedBy, requiresCoordination, and affects are not present in the ETL output.
- Subclass structure (e.g., DisruptionStrategy, AttributionStrategy) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_engage.py and sample TTL outputs
- Identify which raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required ENGAGE ontology properties:**
   - Add support for `riskLevel`, `costLevel`, `sophisticationRequired`, `effectivenessMetric`, `legalConsiderations`, `strategyType`, `timeframe`, `operationalLevel`, `implementationStatus`, `publishedDate`, `lastModifiedDate`, `url`.
   - Ensure all required fields for EngagementConcept, EngagementObjective, OperationalContext, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., DisruptionStrategy, AttributionStrategy, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support `achieves`, `applicableInContext`, `hasImpact`, `complementedBy`, `requiresCoordination`, `affects`, `targets` as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review ENGAGE raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external ENGAGE ontologies in schemas folder
- List additional properties/relationships that could enrich KGCS

## 5. Gap Table

| Raw Field/Relationship | Ontology | ETL | TTL Output | External Ontology | Gap/Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 6. Recommendations

- Propose ontology/ETL/SHACL updates to cover gaps
- Prioritize by reasoning value, RAG, downstream use

## 7. Next Steps

- Plan implementation tasks for branch
- Update this file as analysis progresses
