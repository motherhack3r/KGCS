# CAPEC Data/Ontology/ETL Gap Analysis (v2.0)

## Purpose

This document tracks the gap analysis, enrichment plan, and implementation steps for KGCS Ontology v2.0 CAPEC integration, aligned with the versioning-plan and schema-driven improvements.

---

## 1. Versioning Context

- v2.0 is a new, parallel ontology module, preserving v1.0 immutability.
- All changes are documented and versioned for traceability.

---

## 2. Key Improvements & Alignment

- Expanded mapping of all CAPEC properties and relationships, schema-aligned.
- CAPEC integration with ATT&CK and other standards via canonical relationships.
- Subclass structure (MetaAttackPattern, CompositePattern, etc.) explicitly modeled.
- SHACL shapes updated for new fields and relationships.
- ETL refactored for v2.0 compliance and traceability.

---

## 3. Mapping All Relevant CAPEC Properties and Relationships

### Core Properties (for all CAPEC objects)

- `capecId` → `capec:capecId`
- `name` → `rdfs:label`
- `description` → `capec:description`
- `likelihoodOfAttack` → `capec:likelihoodOfAttack`
- `severity` → `capec:severity`
- `prerequisite` → `capec:prerequisite`
- `consequence` → `capec:consequence`
- `mitigation` → `capec:mitigation`
- `example` → `capec:example`
- `relatedWeakness` → `capec:relatedWeakness` (CWE)
- `relatedAttackPattern` → `capec:relatedAttackPattern`
- `relatedCategory` → `capec:relatedCategory`
- `references` → `capec:references`
- `publishedDate` → `capec:publishedDate`
- `lastModifiedDate` → `capec:lastModifiedDate`
- `url` → `capec:url`

### Subclass Structure

- `MetaAttackPattern`, `Category`, `CompositePattern`, `IndividualPattern` as subclasses of `capec:AttackPattern`.

### Object Properties

- `hasPrerequisite`, `hasConsequence`, `hasMitigation`, `relatedTo`, `relatedWeakness`, `relatedCategory`, `hasImpact`.

### Constraints (SHACL)

- AttackPatterns must have: capecId, name, description, likelihoodOfAttack, severity, and at least one prerequisite or consequence relationship.
- Prerequisites, Consequences, Mitigations, and StakeholderImpact have required fields as well.

---

## 4. Example: CAPEC Relationship to CWE

When processing a CAPEC AttackPattern, create a relationship to CWE if `relatedWeakness` is present.

Example RDF:

```gql
capec:CAPEC-13 a capec:AttackPattern ;
  capec:relatedWeakness cwe:CWE-79 ;
  rdfs:label "CAPEC-13" .
cwe:CWE-79 a cwe:Weakness ;
  rdfs:label "CWE-79" .
```

---

## 5. Patch Plan & Implementation Steps

### 5.1. Scaffold v2.0 Ontology Files

- Copy v1.0 files as starting point.
- Rename and refactor for v2.0.

### 5.2. Expand Property and Relationship Mapping

- Map all CAPEC fields above.
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
