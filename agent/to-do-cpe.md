# CPE Ontology & ETL Gap Analysis

**Branch:** feature/cpe-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in CPE and CPEmatch raw files (JSON, XML, etc.)
- Identify entities (Platform, PlatformConfiguration, CPEMatch, etc.) and their properties, including all CPEmatch-specific fields and references

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/cpe-ontology-v1.0.owl and cpe-ontology-v1.0.md, including all CPEmatch-related classes and properties
- Note which CPE and CPEmatch fields/relationships are modeled and which are missing

### Ontology Coverage (from cpe-ontology-v1.0.owl)

- **Core Classes:**
  - `cpe:PlatformConfiguration` (root for all platform configurations)
    - Subclasses: `HardwareConfiguration`, `SoftwareConfiguration`, `OSConfiguration`, `ApplicationConfiguration`
  - `cpe:CPEMatch` (linkage between PlatformConfiguration and CVE)
  - `cpe:Platform` (abstract platform, not directly affected)
  - `cpe:StakeholderImpact`
- **Key Datatype Properties:**
  - `cpe:cpeId`, `cpe:name`, `cpe:description`, `cpe:version`, `cpe:update`, `cpe:edition`, `cpe:language`, `cpe:part`, `cpe:vendor`, `cpe:product`, `cpe:deprecated`, `cpe:status`, `cpe:publishedDate`, `cpe:lastModifiedDate`, `cpe:url`, `cpe:matchCriteria`, `cpe:matchStatus`, `cpe:matchReferences`
  - CPEmatch-specific: `cpematchId`, `cpematchCriteria`, `cpematchReferences`, `cpematchStatus`, `cpematchPublishedDate`, `cpematchLastModifiedDate`
  - Impact-specific: `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `cpe:hasMatch` / `cpe:match_of` (links PlatformConfiguration to CPEMatch)
  - `cpe:hasImpact` / `cpe:impact_of`
  - `cpe:linkedToCVE` / `cpe:linked_by_cpematch` (links CPEMatch to CVE)
- **Constraints (SHACL-informative):**
  - PlatformConfigurations must have: cpeId, name, description, version, vendor, product, and at least one hasMatch relationship.
  - CPEMatch must have: cpematchId, cpematchCriteria, cpematchReferences, cpematchStatus, and linkedToCVE.
  - StakeholderImpact has required fields as well.
- **Example Relationships:**
  - PlatformConfigurations can have matches, impacts, and be linked to CVEs via CPEMatch.

### Gaps vs. ETL

- Many ontology properties (matchCriteria, matchStatus, matchReferences, cpematchCriteria, cpematchReferences, cpematchStatus, etc.) are not mapped in the ETL.
- Object properties like hasMatch, hasImpact, linkedToCVE are not present in the ETL output.
- Subclass structure (e.g., HardwareConfiguration, ApplicationConfiguration) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_cpe.py, src/etl/etl_cpematch.py, and sample TTL outputs
- Identify which CPE and CPEmatch raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required CPE and CPEmatch ontology properties:**
   - Add support for matchCriteria, matchStatus, matchReferences, cpematchCriteria, cpematchReferences, cpematchStatus, cpematchPublishedDate, cpematchLastModifiedDate, url.
   - Ensure all required fields for PlatformConfiguration, CPEMatch, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., HardwareConfiguration, ApplicationConfiguration, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support hasMatch, hasImpact, linkedToCVE as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review CPE and CPEmatch raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external CPE and CPEmatch ontologies in schemas folder
- List additional properties/relationships that could enrich KGCS, especially for CPEmatch linkage

## 5. Gap Table

| Raw Field/Relationship (CPE/CPEmatch) | Ontology | ETL | TTL Output | External Ontology | Gap/Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 6. Recommendations

- Propose ontology/ETL/SHACL updates to cover CPE and CPEmatch gaps
- Prioritize by reasoning value, RAG, downstream use

## 7. Next Steps

- Plan implementation tasks for branch (including CPE and CPEmatch enrichment)
- Update this file as analysis progresses
