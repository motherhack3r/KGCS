# CVE Data/Ontology/ETL Gap Analysis (v2.0)

## Purpose

This document tracks the gap analysis, enrichment plan, and implementation steps for KGCS Ontology v2.0 CVE integration, aligned with the versioning-plan and schema-driven improvements.

---

## 1. Versioning Context

- v2.0 is a new, parallel ontology module, preserving v1.0 immutability.
- All changes are documented and versioned for traceability.

---

## 2. Key Improvements & Alignment

- Expanded mapping of all CVE properties and relationships, schema-aligned.
- CVE integration with CWE, CAPEC, and other standards via canonical relationships.
- Subclass structure (Configuration, Reference, Impact, Exploit, Patch, etc.) explicitly modeled.
- SHACL shapes updated for new fields and relationships.
- ETL refactored for v2.0 compliance and traceability.

---

## 3. Mapping All Relevant CVE Properties and Relationships

### Core Properties (for all CVE objects)

- `cveId` → `cve:cveId`
- `name` → `rdfs:label`
- `description` → `cve:description`
- `publishedDate` → `cve:publishedDate`
- `lastModifiedDate` → `cve:lastModifiedDate`
- `url` → `cve:url`
- `severity` → `cve:severity`
- `cvssV2Score` → `cve:cvssV2Score`
- `cvssV3Score` → `cve:cvssV3Score`
- `cvssV4Score` → `cve:cvssV4Score`
- `exploitabilityScore` → `cve:exploitabilityScore`
- `impactScore` → `cve:impactScore`
- `references` → `cve:references`
- `patches` → `cve:patches`
- `affectedPlatforms` → `cve:affectedPlatforms`
- `affectedProducts` → `cve:affectedProducts`
- `configuration` → `cve:configuration`
- `exploit` → `cve:exploit`
- `impact` → `cve:impact`
- `status` → `cve:status`
- `version` → `cve:version`
- `vectorString` → `cve:vectorString`
- `attackVector` → `cve:attackVector`
- `attackComplexity` → `cve:attackComplexity`
- `privilegesRequired` → `cve:privilegesRequired`
- `userInteraction` → `cve:userInteraction`
- `scope` → `cve:scope`
- `confidentialityImpact` → `cve:confidentialityImpact`
- `integrityImpact` → `cve:integrityImpact`
- `availabilityImpact` → `cve:availabilityImpact`
- `baseScore` → `cve:baseScore`
- `baseSeverity` → `cve:baseSeverity`
- `temporalScore` → `cve:temporalScore`
- `temporalSeverity` → `cve:temporalSeverity`
- `environmentalScore` → `cve:environmentalScore`
- `environmentalSeverity` → `cve:environmentalSeverity`

### Subclass Structure

- `Configuration`, `Reference`, `Impact`, `Exploit`, `Patch`, `AffectedPlatform`, `AffectedProduct` as subclasses of `cve:Vulnerability`.

### Object Properties

- `hasConfiguration`, `hasReference`, `hasImpact`, `hasPatch`, `hasExploit`, `affectsPlatform`, `affectsProduct`.

### Constraints (SHACL)

- Vulnerabilities must have: cveId, name, description, severity, publishedDate, and at least one configuration or impact relationship.
- Configurations, References, Impacts, Exploits, Patches, AffectedPlatform/Product, and StakeholderImpact have required fields as well.

---

## 4. Example: CVE Relationship to CWE and CAPEC

When processing a CVE Vulnerability, create relationships to CWE and CAPEC if `configuration` or `references` include such entries.

Example RDF:

```gql
cve:CVE-2023-1234 a cve:Vulnerability ;
  cve:hasConfiguration cwe:CWE-79 ;
  cve:hasReference capec:CAPEC-13 ;
  rdfs:label "CVE-2023-1234" .
cwe:CWE-79 a cwe:Weakness ;
  rdfs:label "CWE-79" .
capec:CAPEC-13 a capec:AttackPattern ;
  rdfs:label "CAPEC-13" .
```

---

## 5. Patch Plan & Implementation Steps

### 5.1. Scaffold v2.0 Ontology Files

- Copy v1.0 files as starting point.
- Rename and refactor for v2.0.

### 5.2. Expand Property and Relationship Mapping

- Map all CVE fields above.
- Add explicit subclass structure.

### 5.3. Add Object Property Relationships

- Support all canonical relationships (see above).
- Ensure relationships are traceable to source data and not fabricated.

### 5.4. Update SHACL Shapes

- Add shapes for new fields/relationships.
- Mark deprecated fields as optional.

### 5.5. Update ETL and Pipeline Scripts

- Refactor ETL for v2.0 triples.
- Add tests for v2.0 output.

### 5.6. Documentation

- Document all changes, rationale, and migration steps.
- Provide comparison tables between v1.0 and v2.0.

---

## 6. Next Actions

- Begin by copying and renaming v1.0 ontology files into `docs/ontology/v2.0/`.
- Incrementally refactor and enrich each file according to the plan above.
- Track all changes in version control and update documentation for transparency.
