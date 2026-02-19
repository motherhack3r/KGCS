# CAPEC Ontology & ETL Gap Analysis

**Branch:** feature/capec-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in CAPEC raw files (XML, JSON, etc.)
- Identify entities (Attack Pattern, Category, Prerequisite, Consequence, etc.) and their properties

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/capec-ontology-v1.0.owl and capec-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from capec-ontology-v1.0.owl)

- **Core Classes:**
  - `capec:AttackPattern` (root for all attack patterns)
    - Subclasses: `MetaAttackPattern`, `Category`, `CompositePattern`, `IndividualPattern`
  - `capec:Prerequisite`
  - `capec:Consequence`
  - `capec:Mitigation`
  - `capec:StakeholderImpact`
- **Key Datatype Properties:**
  - `capec:capecId`, `capec:name`, `capec:description`, `capec:likelihoodOfAttack`, `capec:severity`, `capec:prerequisite`, `capec:consequence`, `capec:mitigation`, `capec:example`, `capec:relatedWeakness`, `capec:relatedAttackPattern`, `capec:references`, `capec:publishedDate`, `capec:lastModifiedDate`, `capec:url`
  - Impact-specific: `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `capec:hasPrerequisite` / `capec:prerequisite_for`
  - `capec:hasConsequence` / `capec:consequence_of`
  - `capec:hasMitigation` / `capec:mitigation_for`
  - `capec:relatedTo` (links AttackPattern to other AttackPatterns)
  - `capec:relatedWeakness` (links to CWE)
  - `capec:relatedCategory` (links to Category)
  - `capec:hasImpact` / `capec:impact_of`
- **Constraints (SHACL-informative):**
  - AttackPatterns must have: capecId, name, description, likelihoodOfAttack, severity, and at least one prerequisite or consequence relationship.
  - Prerequisites, Consequences, Mitigations, and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - AttackPatterns can have prerequisites, consequences, mitigations, related weaknesses, related categories, and impacts.

### Gaps vs. ETL

- Many ontology properties (likelihoodOfAttack, severity, mitigation, example, relatedWeakness, relatedAttackPattern, references, etc.) are not mapped in the ETL.
- Object properties like hasPrerequisite, hasConsequence, hasMitigation, relatedTo, relatedWeakness, relatedCategory, hasImpact are not present in the ETL output.
- Subclass structure (e.g., MetaAttackPattern, CompositePattern) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_capec.py and sample TTL outputs
- Identify which raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required CAPEC ontology properties:**
   - Add support for likelihoodOfAttack, severity, mitigation, example, relatedWeakness, relatedAttackPattern, references, publishedDate, lastModifiedDate, url.
   - Ensure all required fields for AttackPattern, Prerequisite, Consequence, Mitigation, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., MetaAttackPattern, CompositePattern, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support hasPrerequisite, hasConsequence, hasMitigation, relatedTo, relatedWeakness, relatedCategory, hasImpact as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review CAPEC raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external CAPEC ontologies in schemas folder
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
