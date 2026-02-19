# CWE Data/Ontology/ETL Gap Analysis (v2.0)

## Purpose

This document tracks the gap analysis, enrichment plan, and implementation steps for KGCS Ontology v2.0 CWE integration, aligned with the versioning-plan and schema-driven improvements.

---

## 1. Versioning Context

- v2.0 is a new, parallel ontology module, preserving v1.0 immutability.
- All changes are documented and versioned for traceability.

---

## 2. Key Improvements & Alignment

- Expanded mapping of all CWE properties and relationships, schema-aligned.
- CWE integration with CAPEC, CVE, and other standards via canonical relationships.
- Subclass structure (CompoundWeakness, BaseWeakness, etc.) explicitly modeled.
- SHACL shapes updated for new fields and relationships.
- ETL refactored for v2.0 compliance and traceability.

---

## 3. Mapping All Relevant CWE Properties and Relationships

### Core Properties (for all CWE objects)

- `cweId` → `cwe:cweId`
- `name` → `rdfs:label`
- `description` → `cwe:description`
- `likelihoodOfExploit` → `cwe:likelihoodOfExploit`
- `severity` → `cwe:severity`
- `relatedCVE` → `cwe:relatedCVE`
- `relatedCAPEC` → `cwe:relatedCAPEC`
- `relatedCWEs` → `cwe:relatedCWEs`
- `example` → `cwe:example`
- `references` → `cwe:references`
- `publishedDate` → `cwe:publishedDate`
- `lastModifiedDate` → `cwe:lastModifiedDate`
- `url` → `cwe:url`

### Subclass Structure

- `Category`, `CompoundWeakness`, `BaseWeakness`, `VariantWeakness` as subclasses of `cwe:Weakness`.

### Object Properties

- `hasRelationship`, `relatedTo`, `relatedCVE`, `relatedCAPEC`, `hasImpact`.

### Constraints (SHACL)

- Weaknesses must have: cweId, name, description, likelihoodOfExploit, severity, and at least one relationship or relatedCVE/CAPEC.
- Relationships and StakeholderImpact have required fields as well.

---

## 4. Example: CWE Relationship to CAPEC and CVE

When processing a CWE Weakness, create relationships to CAPEC and CVE if `relatedCAPEC` or `relatedCVE` are present.

Example RDF:

```gql
cwe:CWE-79 a cwe:Weakness ;
  cwe:relatedCAPEC capec:CAPEC-13 ;
  cwe:relatedCVE cve:CVE-2023-1234 ;
  rdfs:label "CWE-79" .
capec:CAPEC-13 a capec:AttackPattern ;
  rdfs:label "CAPEC-13" .
cve:CVE-2023-1234 a cve:Vulnerability ;
  rdfs:label "CVE-2023-1234" .
```

---

## 5. Patch Plan & Implementation Steps

### 5.1. Scaffold v2.0 Ontology Files

- Copy v1.0 files as starting point.
- Rename and refactor for v2.0.

### 5.2. Expand Property and Relationship Mapping

- Map all CWE fields above.
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
