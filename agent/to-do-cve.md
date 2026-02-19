# CVE Ontology & ETL Gap Analysis

**Branch:** feature/cve-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in CVE raw files (JSON, etc.)
- Identify entities (Vulnerability, Reference, Configuration, Impact, etc.) and their properties

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/cve-ontology-v1.0.owl and cve-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from cve-ontology-v1.0.owl)

- **Core Classes:**
  - `cve:Vulnerability` (root for all vulnerabilities)
    - Subclasses: `Configuration`, `Reference`, `Impact`, `Exploit`, `Patch`, `AffectedPlatform`, `AffectedProduct`
  - `cve:StakeholderImpact`
- **Key Datatype Properties:**
  - `cve:cveId`, `cve:name`, `cve:description`, `cve:publishedDate`, `cve:lastModifiedDate`, `cve:url`, `cve:severity`, `cve:cvssV2Score`, `cve:cvssV3Score`, `cve:cvssV4Score`, `cve:exploitabilityScore`, `cve:impactScore`, `cve:references`, `cve:patches`, `cve:affectedPlatforms`, `cve:affectedProducts`, `cve:configuration`, `cve:exploit`, `cve:impact`, `cve:status`, `cve:version`, `cve:vectorString`, `cve:attackVector`, `cve:attackComplexity`, `cve:privilegesRequired`, `cve:userInteraction`, `cve:scope`, `cve:confidentialityImpact`, `cve:integrityImpact`, `cve:availabilityImpact`, `cve:baseScore`, `cve:baseSeverity`, `cve:temporalScore`, `cve:temporalSeverity`, `cve:environmentalScore`, `cve:environmentalSeverity`
  - Impact-specific: `impactType`, `impactDescription`, `impactSeverity`
- **Key Object Properties:**
  - `cve:hasConfiguration` / `cve:configuration_of`
  - `cve:hasReference` / `cve:reference_of`
  - `cve:hasImpact` / `cve:impact_of`
  - `cve:hasPatch` / `cve:patch_of`
  - `cve:hasExploit` / `cve:exploit_of`
  - `cve:affectsPlatform` / `cve:affected_by_platform`
  - `cve:affectsProduct` / `cve:affected_by_product`
- **Constraints (SHACL-informative):**
  - Vulnerabilities must have: cveId, name, description, severity, publishedDate, and at least one configuration or impact relationship.
  - Configurations, References, Impacts, Exploits, Patches, AffectedPlatform/Product, and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - Vulnerabilities can have configurations, references, impacts, exploits, patches, affected platforms/products, and stakeholder impacts.

### Gaps vs. ETL

- Many ontology properties (cvss scores, exploitabilityScore, impactScore, references, patches, affectedPlatforms, affectedProducts, configuration, exploit, impact, status, version, vectorString, etc.) are not mapped in the ETL.
- Object properties like hasConfiguration, hasReference, hasImpact, hasPatch, hasExploit, affectsPlatform, affectsProduct are not present in the ETL output.
- Subclass structure (e.g., Configuration, Reference, Impact, Exploit, Patch) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_cve.py and sample TTL outputs
- Identify which raw fields are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required CVE ontology properties:**
   - Add support for cvssV2Score, cvssV3Score, cvssV4Score, exploitabilityScore, impactScore, references, patches, affectedPlatforms, affectedProducts, configuration, exploit, impact, status, version, vectorString, publishedDate, lastModifiedDate, url.
   - Ensure all required fields for Vulnerability, Configuration, Reference, Impact, Exploit, Patch, AffectedPlatform, AffectedProduct, and StakeholderImpact are present.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., Configuration, Reference, Impact, Exploit, Patch, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support hasConfiguration, hasReference, hasImpact, hasPatch, hasExploit, affectsPlatform, affectsProduct as per ontology.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review CVE raw data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external CVE ontologies in schemas folder
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
