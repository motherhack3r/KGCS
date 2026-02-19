# D3FEND Data/Ontology/ETL Gap Analysis (v2.0)

## Purpose

This document tracks the gap analysis, enrichment plan, and implementation steps for KGCS Ontology v2.0 D3FEND integration, aligned with the versioning-plan and schema-driven improvements.

---

## 1. Versioning Context

- v2.0 is a new, parallel ontology module, preserving v1.0 immutability.
- All changes are documented and versioned for traceability.

---

## 2. Key Improvements & Alignment

- Expanded mapping of all D3FEND properties and relationships, schema-aligned.
- D3FEND integration with ATT&CK and other standards via canonical relationships.
- Subclass structure (Detection, Deception, etc.) explicitly modeled.
- SHACL shapes updated for new fields and relationships.
- ETL refactored for v2.0 compliance and traceability.

---

## 3. Mapping All Relevant D3FEND Properties and Relationships

### Core Properties (for all D3FEND objects)

- `d3fendId` → `d3fend:d3fendId`
- `name` → `rdfs:label`
- `description` → `d3fend:description`
- `techniqueType` → `d3fend:techniqueType`
- `timeframe` → `d3fend:timeframe`
- `operationalLevel` → `d3fend:operationalLevel`
- `riskLevel` → `d3fend:riskLevel`
- `sophisticationRequired` → `d3fend:sophisticationRequired`
- `costLevel` → `d3fend:costLevel`
- `effectivenessMetric` → `d3fend:effectivenessMetric`
- `applicableAdversary` → `d3fend:applicableAdversary`
- `legalConsiderations` → `d3fend:legalConsiderations`
- `implementationStatus` → `d3fend:implementationStatus`
- `publishedDate` → `d3fend:publishedDate`
- `lastModifiedDate` → `d3fend:lastModifiedDate`
- `url` → `d3fend:url`
- Objective/context/impact-specific: `objectiveName`, `objectiveDescription`, `successCondition`, `contextName`, `contextDescription`, `contextTriggered`, `impactType`, `impactDescription`, `impactSeverity`

### Subclass Structure

- `Detection`, `Prevention`, `Response`, `Recovery`, `Mitigation`, `Deception`, `Obfuscation` as subclasses of `d3fend:DefensiveTechnique`.

### Object Properties

- `mitigates`, `targets`, `achieves`, `applicableInContext`, `hasImpact`, `complementedBy`, `requiresCoordination`, `affects`.

### Constraints (SHACL)

- DefensiveTechniques must have: d3fendId, name, description, techniqueType, timeframe, operationalLevel, effectivenessMetric, and at least one mitigates or affects relationship.
- Objectives, Contexts, and StakeholderImpact have required fields as well.

---

## 4. Example: D3FEND Relationship to ATT&CK

When processing a D3FEND DefensiveTechnique, create a relationship to ATT&CK Technique if `mitigates` is present.

Example RDF:

```gql
d3fend:D3FEND-001 a d3fend:DefensiveTechnique ;
  d3fend:mitigates sec:attack-pattern--1234 ;
  rdfs:label "D3FEND-001" .
sec:attack-pattern--1234 a sec:Technique ;
  rdfs:label "T1234" .
```

---

## 5. Patch Plan & Implementation Steps

### 5.1. Scaffold v2.0 Ontology Files

- Copy v1.0 files as starting point.
- Rename and refactor for v2.0.

### 5.2. Expand Property and Relationship Mapping

- Map all D3FEND fields above.
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
