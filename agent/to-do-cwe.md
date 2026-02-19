# CWE Ontology & ETL Gap Analysis

**Branch:** feature/cwe-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in CWE raw files (XML, JSON, etc.)
- Identify entities (Weakness, Category, Relationship, etc.) and their properties

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/cwe-ontology-v1.0.owl and cwe-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from cwe-ontology-v1.0.owl)

- **Core Classes:**
  - `cwe:Weakness` (root for all weaknesses)
    - Subclasses: `Category`, `CompoundWeakness`, `BaseWeakness`, `VariantWeakness`
  - `cwe:Relationship`
  - `cwe:StakeholderImpact`
- **Key Datatype Properties:**
  - `cwe:cweId`, `cwe:name`, `cwe:description`, `cwe:likelihoodOfExploit`, `cwe:severity`, `cwe:relatedCVE`, `cwe:relatedCAPEC`, `cwe:relatedCWEs`, `cwe:example`, `cwe:references`, `cwe:publishedDate`, `cwe:lastModifiedDate`, `cwe:url`
  - Impact-specific: `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `cwe:hasRelationship` / `cwe:relationship_of`
  - `cwe:relatedTo` (links Weakness to other Weaknesses)
  - `cwe:relatedCVE` (links to CVE)
  - `cwe:relatedCAPEC` (links to CAPEC)
  - `cwe:hasImpact` / `cwe:impact_of`
- **Constraints (SHACL-informative):**
  - Weaknesses must have: cweId, name, description, likelihoodOfExploit, severity, and at least one relationship or relatedCVE/CAPEC.
  - Relationships and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - Weaknesses can have relationships, related CVEs, related CAPECs, related weaknesses, and impacts.

### Gaps vs. ETL

- Many ontology properties (likelihoodOfExploit, severity, relatedCVE, relatedCAPEC, relatedCWEs, example, references, etc.) are not mapped in the ETL.
- Object properties like hasRelationship, relatedTo, relatedCVE, relatedCAPEC, hasImpact are not present in the ETL output.
- Subclass structure (e.g., CompoundWeakness, BaseWeakness) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_cwe.py and sample TTL outputs
- Identify which raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required CWE ontology properties:**
   - Add support for likelihoodOfExploit, severity, relatedCVE, relatedCAPEC, relatedCWEs, example, references, publishedDate, lastModifiedDate, url.
   - Ensure all required fields for Weakness, Relationship, Category, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., CompoundWeakness, BaseWeakness, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support hasRelationship, relatedTo, relatedCVE, relatedCAPEC, hasImpact as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review CWE raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external CWE ontologies in schemas folder
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
