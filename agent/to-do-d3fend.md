# D3FEND Ontology & ETL Gap Analysis

**Branch:** feature/d3fend-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in D3FEND raw files (JSON, etc.)
- Identify entities (Defensive Technique, Category, Asset, etc.) and their properties

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/d3fend-ontology-v1.0.owl and d3fend-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from d3fend-ontology-v1.0.owl)

- **Core Classes:**
  - `d3fend:DefensiveTechnique` (root for all defensive strategies)
    - Subclasses: `Detection`, `Prevention`, `Response`, `Recovery`, `Mitigation`, `Deception`, `Obfuscation`
  - `d3fend:DefensiveObjective`
  - `d3fend:OperationalContext`
  - `d3fend:StakeholderImpact`
- **Key Datatype Properties:**
  - `d3fend:d3fendId`, `d3fend:name`, `d3fend:description`, `d3fend:techniqueType`, `d3fend:timeframe`, `d3fend:operationalLevel`, `d3fend:riskLevel`, `d3fend:sophisticationRequired`, `d3fend:costLevel`, `d3fend:effectivenessMetric`, `d3fend:applicableAdversary`, `d3fend:legalConsiderations`, `d3fend:implementationStatus`, `d3fend:publishedDate`, `d3fend:lastModifiedDate`, `d3fend:url`
  - Objective/context/impact-specific: `objectiveName`, `objectiveDescription`, `successCondition`, `contextName`, `contextDescription`, `contextTriggered`, `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `d3fend:mitigates` / `d3fend:mitigated_by` (links DefensiveTechnique to sec:AttackPattern)
  - `d3fend:targets` / `d3fend:targeted_by_defense`
  - `d3fend:achieves` / `d3fend:achieved_by` (links DefensiveTechnique to DefensiveObjective)
  - `d3fend:applicableInContext` / `d3fend:context_for_defense`
  - `d3fend:hasImpact` / `d3fend:impact_of`
  - `d3fend:complementedBy` (symmetric, between DefensiveTechniques)
  - `d3fend:requiresCoordination` / `d3fend:coordinated_with`
  - `d3fend:affects` / `d3fend:affected_by_defense` (links to sec:Asset)
- **Constraints (SHACL-informative):**
  - DefensiveTechniques must have: d3fendId, name, description, techniqueType, timeframe, operationalLevel, effectivenessMetric, and at least one mitigates or affects relationship.
  - Objectives, Contexts, and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - DefensiveTechniques can mitigate attack patterns, achieve objectives, be applicable in contexts, have stakeholder impacts, complement or coordinate with other strategies.

### Gaps vs. ETL

- Many ontology properties (risk, cost, sophistication, legal, effectivenessMetric, etc.) are not mapped in the ETL.
- Object properties like achieves, applicableInContext, hasImpact, complementedBy, requiresCoordination, and affects are not present in the ETL output.
- Subclass structure (e.g., Detection, Deception) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_d3fend.py and sample TTL outputs
- Identify which raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required D3FEND ontology properties:**
   - Add support for `riskLevel`, `costLevel`, `sophisticationRequired`, `effectivenessMetric`, `legalConsiderations`, `techniqueType`, `timeframe`, `operationalLevel`, `implementationStatus`, `publishedDate`, `lastModifiedDate`, `url`.
   - Ensure all required fields for DefensiveTechnique, DefensiveObjective, OperationalContext, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., Detection, Deception, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support `achieves`, `applicableInContext`, `hasImpact`, `complementedBy`, `requiresCoordination`, `affects`, `targets` as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review D3FEND raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external D3FEND ontologies in schemas folder
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
