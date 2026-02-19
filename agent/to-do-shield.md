# SHIELD Ontology & ETL Gap Analysis

**Branch:** feature/shield-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in SHIELD raw files (JSON, etc.)
- Identify entities (Deception Technique, Category, Asset, etc.) and their properties

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/shield-ontology-v1.0.owl and shield-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from shield-ontology-v1.0.owl)

- **Core Classes:**
  - `shield:DeceptionTechnique` (root for all deception strategies)
    - Subclasses: `Misdirection`, `Obfuscation`, `Honeytoken`, `Decoy`, `Disinformation`, `Redirection`, `Simulation`
  - `shield:DeceptionObjective`
  - `shield:OperationalContext`
  - `shield:StakeholderImpact`
- **Key Datatype Properties:**
  - `shield:shieldId`, `shield:name`, `shield:description`, `shield:techniqueType`, `shield:timeframe`, `shield:operationalLevel`, `shield:riskLevel`, `shield:sophisticationRequired`, `shield:costLevel`, `shield:effectivenessMetric`, `shield:applicableAdversary`, `shield:legalConsiderations`, `shield:implementationStatus`, `shield:publishedDate`, `shield:lastModifiedDate`, `shield:url`
  - Objective/context/impact-specific: `objectiveName`, `objectiveDescription`, `successCondition`, `contextName`, `contextDescription`, `contextTriggered`, `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `shield:misleads` / `shield:misled_by` (links DeceptionTechnique to sec:AttackPattern)
  - `shield:targets` / `shield:targeted_by_deception`
  - `shield:achieves` / `shield:achieved_by` (links DeceptionTechnique to DeceptionObjective)
  - `shield:applicableInContext` / `shield:context_for_deception`
  - `shield:hasImpact` / `shield:impact_of`
  - `shield:complementedBy` (symmetric, between DeceptionTechniques)
  - `shield:requiresCoordination` / `shield:coordinated_with`
  - `shield:affects` / `shield:affected_by_deception` (links to sec:Asset)
- **Constraints (SHACL-informative):**
  - DeceptionTechniques must have: shieldId, name, description, techniqueType, timeframe, operationalLevel, effectivenessMetric, and at least one misleads or affects relationship.
  - Objectives, Contexts, and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - DeceptionTechniques can mislead attack patterns, achieve objectives, be applicable in contexts, have stakeholder impacts, complement or coordinate with other strategies.

### Gaps vs. ETL

- Many ontology properties (risk, cost, sophistication, legal, effectivenessMetric, etc.) are not mapped in the ETL.
- Object properties like achieves, applicableInContext, hasImpact, complementedBy, requiresCoordination, and affects are not present in the ETL output.
- Subclass structure (e.g., Misdirection, Honeytoken) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_shield.py and sample TTL outputs
- Identify which raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required SHIELD ontology properties:**
   - Add support for `riskLevel`, `costLevel`, `sophisticationRequired`, `effectivenessMetric`, `legalConsiderations`, `techniqueType`, `timeframe`, `operationalLevel`, `implementationStatus`, `publishedDate`, `lastModifiedDate`, `url`.
   - Ensure all required fields for DeceptionTechnique, DeceptionObjective, OperationalContext, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., Misdirection, Honeytoken, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support `achieves`, `applicableInContext`, `hasImpact`, `complementedBy`, `requiresCoordination`, `affects`, `targets` as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review SHIELD raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external SHIELD ontologies in schemas folder
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
