# ATT&CK Data/Ontology/ETL Gap Analysis (v2.0)

## Purpose

This document tracks the gap analysis, enrichment plan, and implementation steps for KGCS Ontology v2.0, aligned with the versioning-plan and schema-driven improvements.

---

## 1. Versioning Context

- v2.0 is a new, parallel ontology module, preserving v1.0 immutability.
- All changes are documented and versioned for traceability.

---

## 2. Key Improvements & Alignment

- Unified `Technique` class with `x_mitre_is_subtechnique` property (no separate SubTechnique class).
- Expanded mapping of all relevant STIX properties and relationships.
- CAPEC integration via `external_references`.
- Extension ontologies for Group, Software, Asset, DataSource, DataComponent, and new relationships.
- SHACL shapes updated for new fields and relationships.
- ETL refactored for v2.0 compliance.

---

## 3. Mapping All Relevant STIX Properties and Relationships

### Core Properties (for all ATT&CK objects)

- `id` → `sec:attackId`
- `type` → `rdf:type`
- `spec_version` → `sec:specVersion`
- `created` → `sec:created`
- `modified` → `sec:modified`
- `created_by_ref` → `sec:createdBy`
- `labels` → `sec:labels`
- `name` → `rdfs:label`
- `description` → `sec:description`
- `aliases` → `sec:aliases`
- `external_references` → `sec:externalReference`
- `object_marking_refs` → `sec:objectMarking`
- `kill_chain_phases` → `sec:killChainPhase`
- `x_mitre_domains` → `sec:domains`
- `x_mitre_attack_spec_version` → `sec:attackSpecVersion`
- `x_mitre_version` → `sec:attackVersion`
- `x_mitre_deprecated` → `sec:deprecated`
- `x_mitre_contributors` → `sec:contributors`

### Technique/Subtechnique Specific

- `x_mitre_is_subtechnique` → `sec:isSubtechnique`
- `x_mitre_platforms` → `sec:platforms`
- `x_mitre_detection` → `sec:detection`
- `x_mitre_data_sources` → `sec:dataSources`
- `x_mitre_permissions_required` → `sec:permissionsRequired`
- `x_mitre_effective_permissions` → `sec:effectivePermissions`
- `x_mitre_network_requirements` → `sec:networkRequirements`
- `subtechnique_of` → `sec:subtechnique_of`
- `sec:belongs_to` (Tactic)

### Group/Software/Asset/DataSource/DataComponent

- `intrusion-set` → `sec:Group`
- `malware`/`tool` → `sec:Malware`/`sec:Tool`
- `x-mitre-asset` → `sec:Asset`
- `x-mitre-data-source` → `sec:DataSource`
- `x-mitre-data-component` → `sec:DataComponent`

### Relationships

- `uses`, `employs`, `implements`, `targets`, `detects`, `associatedGroup`, `hasMitigation`, etc.
- CAPEC integration: `sec:capecReference` or `sec:derived_from` from Technique to CAPEC node.

---

## 4. Example: CAPEC Relationship via external_references

When processing an `attack-pattern`, create a relationship to CAPEC if `external_references` includes a CAPEC entry.

Example RDF:

```gql
sec:attack-pattern--... a sec:Technique ;
  sec:capecReference capec:CAPEC-13 ;
  ... .
capec:CAPEC-13 a capec:Attack_Pattern ;
  rdfs:label "CAPEC-13" .
```

---

## 5. Patch Plan & Implementation Steps

### 5.1. Scaffold v2.0 Ontology Files

- Copy v1.0 files as starting point.
- Rename and refactor for v2.0.

### 5.2. Refactor Technique/SubTechnique Modeling

- Unify as single `Technique` class.
- Remove SubTechnique class.

### 5.3. Expand Property and Relationship Mapping

- Map all STIX fields above.
- Add CAPEC integration.

### 5.4. Update Extension Ontologies

- Add/expand Group, Software, Asset, DataSource, DataComponent.
- Define new relationships.

### 5.5. Update SHACL Shapes

- Add shapes for new fields/relationships.
- Mark deprecated fields as optional.

### 5.6. Update ETL and Pipeline Scripts

- Refactor ETL for v2.0 triples.
- Add tests for v2.0 output.

### 5.7. Documentation

- Document all changes, rationale, and migration steps.
- Provide comparison tables between v1.0 and v2.0.

---

## 6. Next Actions

- Begin by copying and renaming v1.0 ontology files into `docs/ontology/v2.0/`.
- Incrementally refactor and enrich each file according to the plan above.
- Track all changes in version control and update documentation for transparency.
