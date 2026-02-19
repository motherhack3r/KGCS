# KGCS Ontology v2.0 Versioning Plan and Initial Steps

## Versioning Plan

- **Purpose:** KGCS Ontology v2.0 will incorporate schema-aligned improvements, richer property/relationship mapping, and CAPEC integration, while preserving the immutability and traceability of v1.0.
- **Core Principles:**
  - v1.0 remains immutable and authoritative for legacy and traceability.
  - v2.0 will be a new, parallel ontology module, not a replacement.
  - All changes will be documented and versioned for downstream users.
- **Naming:**
  - Folder: `docs/ontology/v2.0/`
  - Files: `core-ontology-v2.0.md`, `attack-ontology-v2.0.md`, `threatactor-ontology-extension-v2.0.md`, etc.
- **Migration:**
  - Existing ETL, SHACL, and pipeline scripts will be updated to support v2.0 as an option.
  - v1.0 and v2.0 can coexist for comparison and validation.

## Initial Steps

1. **Scaffold v2.0 Ontology Files:**
   - Create new markdown and OWL files for core, attack, and extension ontologies.
   - Copy v1.0 files as a starting point, then incrementally refactor.

2. **Refactor Technique/SubTechnique Modeling:**
   - Unify as a single `Technique` class with `x_mitre_is_subtechnique` property.
   - Remove separate SubTechnique class.

3. **Expand Property and Relationship Mapping:**
   - Map all relevant STIX properties and relationships (see enrichment doc).
   - Add CAPEC integration via `external_references`.

4. **Update Extension Ontologies:**
   - Add/expand classes for Group, Software, Asset, DataSource, DataComponent.
   - Define new relationships (uses, employs, implements, targets, detects, etc.).

5. **Update SHACL Shapes:**
   - Add shapes for new properties and relationships.
   - Mark deprecated fields as optional or to be removed in future.

6. **Update ETL and Pipeline Scripts:**
   - Refactor ETL logic to emit v2.0-compliant triples.
   - Add tests for v2.0 output and validation.

7. **Documentation:**
   - Document all changes, rationale, and migration steps.
   - Provide comparison tables between v1.0 and v2.0.

---

**Next Actions:**

- Begin by copying and renaming v1.0 ontology files into `docs/ontology/v2.0/`.
- Incrementally refactor and enrich each file according to the plan above.
- Track all changes in version control and update documentation for transparency.
