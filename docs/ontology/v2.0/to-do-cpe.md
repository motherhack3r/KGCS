# CPE Data/Ontology/ETL Gap Analysis (v2.0)

## Purpose

This document tracks the gap analysis, enrichment plan, and implementation steps for KGCS Ontology v2.0 CPE integration, aligned with the versioning-plan and schema-driven improvements.

---

## 1. Versioning Context

- v2.0 is a new, parallel ontology module, preserving v1.0 immutability.
- All changes are documented and versioned for traceability.

---

## 2. Key Improvements & Alignment

- Expanded mapping of all CPE and CPEmatch properties and relationships, schema-aligned.
- CPE/CPEmatch integration with CVE and other standards via canonical relationships.
- Subclass structure (HardwareConfiguration, ApplicationConfiguration, etc.) explicitly modeled.
- SHACL shapes updated for new fields and relationships.
- ETL refactored for v2.0 compliance and traceability.

---

## 3. Mapping All Relevant CPE/CPEmatch Properties and Relationships

### Core Properties (for all CPE/CPEmatch objects)

- `cpeId` → `cpe:cpeId`
- `name` → `rdfs:label`
- `description` → `cpe:description`
- `version` → `cpe:version`
- `update` → `cpe:update`
- `edition` → `cpe:edition`
- `language` → `cpe:language`
- `part` → `cpe:part`
- `vendor` → `cpe:vendor`
- `product` → `cpe:product`
- `deprecated` → `cpe:deprecated`
- `status` → `cpe:status`
- `publishedDate` → `cpe:publishedDate`
- `lastModifiedDate` → `cpe:lastModifiedDate`
- `url` → `cpe:url`
- `matchCriteria` → `cpe:matchCriteria`
- `matchStatus` → `cpe:matchStatus`
- `matchReferences` → `cpe:matchReferences`
- CPEmatch-specific: `cpematchId`, `cpematchCriteria`, `cpematchReferences`, `cpematchStatus`, `cpematchPublishedDate`, `cpematchLastModifiedDate`
- Impact-specific: `impactType`, `impactDescription`, `impactSeverity`

### Subclass Structure

- `HardwareConfiguration`, `SoftwareConfiguration`, `OSConfiguration`, `ApplicationConfiguration` as subclasses of `cpe:PlatformConfiguration`.

### Object Properties

- `hasMatch`, `hasImpact`, `linkedToCVE`.

### Constraints (SHACL)

- PlatformConfigurations must have: cpeId, name, description, version, vendor, product, and at least one hasMatch relationship.
- CPEMatch must have: cpematchId, cpematchCriteria, cpematchReferences, cpematchStatus, and linkedToCVE.
- StakeholderImpact has required fields as well.

---

## 4. Example: CPE/CPEmatch Relationship to CVE

When processing a PlatformConfiguration, create a relationship to CVE via CPEMatch if `linkedToCVE` is present.

Example RDF:

```gql
cpe:CPE-1234 a cpe:PlatformConfiguration ;
  cpe:hasMatch cpe:CPEmatch-5678 ;
  rdfs:label "CPE-1234" .
cpe:CPEmatch-5678 a cpe:CPEMatch ;
  cpe:linkedToCVE cve:CVE-2023-1234 ;
  rdfs:label "CPEmatch-5678" .
cve:CVE-2023-1234 a cve:Vulnerability ;
  rdfs:label "CVE-2023-1234" .
```

---

## 5. Patch Plan & Implementation Steps

### 5.1. Scaffold v2.0 Ontology Files

- Copy v1.0 files as starting point.
- Rename and refactor for v2.0.

### 5.2. Expand Property and Relationship Mapping

- Map all CPE/CPEmatch fields above.
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
