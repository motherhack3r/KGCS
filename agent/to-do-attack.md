# ATT&CK Data/Ontology/ETL Gap Analysis

Here’s a summary of the ATT&CK data/ontology/ETL situation and next steps for gap analysis:

- [ATT\&CK Data/Ontology/ETL Gap Analysis](#attck-dataontologyetl-gap-analysis)
  - [1. Raw Data (enterprise-attack.json)](#1-raw-data-enterprise-attackjson)
  - [2. Current Ontology (attack-ontology-v1.0.md \& SHACL)](#2-current-ontology-attack-ontology-v10md--shacl)
  - [3. ETL (etl\_attack.py)](#3-etl-etl_attackpy)
    - [Prioritized ETL/Ontology Enrichment Tasks](#prioritized-etlontology-enrichment-tasks)
  - [4. External Ontology Comparison](#4-external-ontology-comparison)
    - [4.1. External Ontology (data/attack/schemas/ontology.ttl)](#41-external-ontology-dataattackschemasontologyttl)
    - [4.2. STIX Schema (attack-pattern.json)](#42-stix-schema-attack-patternjson)
  - [5. Gaps \& Opportunities](#5-gaps--opportunities)
    - [Gap Table](#gap-table)
  - [6. Recommendations](#6-recommendations)
    - [Mapping Plan for Missing/Partial Properties](#mapping-plan-for-missingpartial-properties)
    - [SHACL Review and Recommendations](#shacl-review-and-recommendations)
    - [Mapping Decisions and Rationale](#mapping-decisions-and-rationale)
  - [7. Next Steps](#7-next-steps)
    - [Descriptions of remaining tasks](#descriptions-of-remaining-tasks)
  - [8. Implementation Details: Subclass Structure and Enrichment](#8-implementation-details-subclass-structure-and-enrichment)
    - [8.1 Task: Implement Subclass Structure in ETL Output](#81-task-implement-subclass-structure-in-etl-output)
      - [8.1.1 Review of Current ETL Logic](#811-review-of-current-etl-logic)
      - [8.1.2 Implementation Plan](#812-implementation-plan)
      - [8.1.3 Gaps or Improvements Needed](#813-gaps-or-improvements-needed)
      - [8.1.4 Next Steps](#814-next-steps)
    - [8.2 Subclass Structure: Full Analysis](#82-subclass-structure-full-analysis)
      - [8.2.1 Tactic Nodes](#821-tactic-nodes)
      - [8.2.2 Technique and SubTechnique Nodes](#822-technique-and-subtechnique-nodes)
      - [8.2.3 Relationships](#823-relationships)
      - [8.2.4 Other Classes/Extensions](#824-other-classesextensions)
    - [8.3 Summary Table: Subclass Structure Coverage](#83-summary-table-subclass-structure-coverage)
    - [8.4 Recommendations](#84-recommendations)
    - [8.5 Subclass Structure: Additional ATT\&CK Classes](#85-subclass-structure-additional-attck-classes)
      - [8.5.1 Group (Intrusion Set/Group)](#851-group-intrusion-setgroup)
      - [8.5.2 Software (Tool/Malware)](#852-software-toolmalware)
      - [8.5.3 DataSource / DataComponent](#853-datasource--datacomponent)
      - [8.5.4 Asset](#854-asset)
    - [8.6 Summary Table: Coverage of Additional Classes](#86-summary-table-coverage-of-additional-classes)
    - [8.7 Recommendations (Additional Classes)](#87-recommendations-additional-classes)
- [ANNEX: External ATT\&CK Schema Analyses](#annex-external-attck-schema-analyses)
  - [ATT\&CK-STIX Schema Reference](#attck-stix-schema-reference)
    - [STIX Domain Objects](#stix-domain-objects)
    - [STIX Relationship Objects](#stix-relationship-objects)
    - [STIX Meta Objects](#stix-meta-objects)
  - [A.1 Tactic Schema Mapping (version 3.3.0)](#a1-tactic-schema-mapping-version-330)
  - [A.2 Technique Schema Mapping (version 3.3.0)](#a2-technique-schema-mapping-version-330)
  - [A.3 Mitigation Schema Mapping (version 3.3.0)](#a3-mitigation-schema-mapping-version-330)
  - [A.4 Group Schema Mapping (version 3.3.0)](#a4-group-schema-mapping-version-330)
  - [A.5 Software Schema Mapping (version 3.3.0)](#a5-software-schema-mapping-version-330)
  - [A.6 Relationship Types Schema Mapping (version 3.3.0)](#a6-relationship-types-schema-mapping-version-330)

---

## 1. Raw Data (enterprise-attack.json)

- Contains rich STIX 2.1 objects: x-mitre-matrix, x-mitre-tactic, attack-pattern, course-of-action, group, software, marking, etc.
- Each object has many attributes: id, type, created, modified, external_references, platforms, domains, kill_chain_phases, etc.
- Relationships are often implicit via references (e.g., tactic_refs, kill_chain_phases, object_marking_refs).

## 2. Current Ontology (attack-ontology-v1.0.md & SHACL)

- **KGCS core ontology/SHACL models only:** Tactic, Technique, SubTechnique (with required properties and relationships).
- **Not present in KGCS core ontology/SHACL:** Group, Software, Asset (these are present only in the external ontology or not at all).
- **DataSource/DataComponent:** Only present as properties (not as node types/classes) in KGCS core ontology/SHACL.
- **External ontology (ontology.ttl):** Models additional classes and relationships (Group, Software, DataSource, DataComponent, Asset, etc.).
- Main relationships: contains, subtechnique_of, uses, detects, targets (coverage varies by ontology).
- SHACL shapes enforce basic structure for core classes (e.g., Technique must have attackTechniqueId, label, belongs_to Tactic).

## 3. ETL (etl_attack.py)

- Transforms STIX JSON to RDF, mapping only a subset of fields (mainly id, name, description, tactic-technique links).
- Focuses on Tactic, Technique, SubTechnique.
- **Does not emit:** Group, Software, Asset, or DataSource/DataComponent as nodes (only as properties for the latter two).
- Likely omits: kill_chain_phases, platforms, domains, marking, external references, detection, mitigations, and other STIX object types.

### Prioritized ETL/Ontology Enrichment Tasks

1. **Map all required ATT&CK ontology properties:**
   - Add support for platforms, domains, kill_chain_phases, object_marking_refs, external_references, detection, mitigations, aliases, and all required fields for Tactic, Technique, SubTechnique. (Group, Software, DataSource, DataComponent, Asset require ontology extension first.)
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., SubTechnique, DataComponent, etc.) in ETL output, using correct RDF types. (Only Tactic, Technique, SubTechnique currently supported.)
3. **Add object property relationships:**
   - Support accomplishesTactic, associatedGroup, hasAdversaryGroup, hasMitigation, hasPlatform, hasDataSource, detects, targets, uses, contains, subtechnique_of, as per ontology and external ontology.ttl. (Some require ontology extension.)
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped STIX fields:**
   - Review ATT&CK STIX data for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

### 4.1. External Ontology (data/attack/schemas/ontology.ttl)

- More detailed: includes properties like accomplishesTactic, associatedGroup, hasAdversaryGroup, hasMitigation, hasPlatform, hasDataSource, etc.
- Models more relationships and attributes than current KGCS ontology.

### 4.2. STIX Schema (attack-pattern.json)

- Defines all possible fields for attack-pattern objects, including aliases, kill_chain_phases, external references, etc.

## 5. Gaps & Opportunities

- **Missing in KGCS graph:** Many STIX fields (aliases, platforms, domains, kill_chain_phases, marking, external references, detection, mitigations, etc.) are not mapped or represented in the ontology or ETL output.
- **Ontology enrichment:** The external ontology (ontology.ttl) models more relationships and attributes—these can be selectively adopted to enrich the KGCS ontology.
- **ETL enhancement:** The ETL should be extended to extract and emit all relevant fields and relationships, not just the core tactic/technique structure.
- **SHACL/validation:** SHACL shapes should be updated to validate the richer structure if new fields/relationships are added.

### Gap Table

> **Legend:**
>
> - "Yes": Present in KGCS core ontology/ETL/TTL output
> - "Partial": Some mapping exists, but not complete
> - "No": Not present in KGCS core ontology/ETL/TTL output
> - "External Ontology": Present only in external ontology.ttl

| Raw Field/Relationship | Ontology Property | ETL | TTL Output | External Ontology | Gap/Notes |
| --- | --- | --- | --- | --- | --- |
| type | attack:type | Yes | Yes | Yes | |
| spec_version | attack:specVersion | No | No | Yes | Needs mapping |
| id | attack:attackId | Yes | Yes | Yes | |
| created_by_ref | attack:createdBy | No | No | Yes | Needs mapping |
| labels | attack:labels | No | No | Yes | Needs mapping |
| created | attack:created | Yes | Yes | Yes | |
| modified | attack:modified | Yes | Yes | Yes | |
| name | attack:name/label | Yes | Yes | Yes | |
| description | attack:description | Yes | Yes | Yes | |
| aliases | attack:aliases | No | No | Yes | Needs mapping |
| kill_chain_phases | attack:killChainPhase | No | No | Yes | Needs mapping |
| external_references | attack:externalReference | No | No | Yes | Needs mapping |
| object_marking_refs | attack:objectMarking | No | No | Yes | Needs mapping |
| tactic_refs | Yes | Yes | Yes | Yes | |
| subtechnique_of | Yes | Yes | Yes | Yes | |
| uses (group/software) | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| detects | Partial | No | No | Yes | Needs enrichment |
| mitigations | Partial | No | No | Yes | Needs enrichment |
| associatedGroup | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| hasAdversaryGroup | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| hasMitigation | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| hasPlatform | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| hasDataSource | Partial (property only) | As property | As property | Yes | Promote to node if needed |
| contains | Yes | Yes | Yes | Yes | |
| targets | Partial | No | No | Yes | Needs enrichment |
| data_source | Partial (property only) | As property | As property | Yes | Promote to node if needed |
| data_component | Partial (property only) | As property | As property | Yes | Promote to node if needed |
| asset | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| course_of_action | Partial | No | No | Yes | Needs enrichment |
| marking | No | No | No | Yes | Needs enrichment |
| status | No | No | No | Yes | Needs enrichment |
| version | No | No | No | Yes | Needs enrichment |
| references | Partial | No | No | Yes | Needs enrichment |
| accomplishesTactic | No (KGCS) / Yes (Ext) | No | No | Yes | Requires ontology extension |
| related_techniques | Partial | No | No | Yes | Needs enrichment |
| related_groups | Partial | No | No | Yes | Needs enrichment |
| related_software | Partial | No | No | Yes | Needs enrichment |
| related_mitigations | Partial | No | No | Yes | Needs enrichment |

## 6. Recommendations

- Propose ontology/ETL/SHACL updates to cover gaps
- Prioritize by reasoning value, RAG, downstream use

### Mapping Plan for Missing/Partial Properties

- **spec_version**: Add mapping from STIX `spec_version` to `attack:specVersion` in RDF. Store as a datatype property on all core nodes.
- **created_by_ref**: Map STIX `created_by_ref` to `attack:createdBy`. If present, create a node for the creator (if not already present) and link.
- **labels**: Map STIX `labels` array to `attack:labels` (multi-valued). Store as datatype properties on the node.
- **aliases**: Map STIX `aliases` array to `attack:aliases` (multi-valued). Store as datatype properties on the node.
- **kill_chain_phases**: Map STIX `kill_chain_phases` array to `attack:killChainPhase`. Each phase should be a node or literal, linked to the technique/attack-pattern.
- **external_references**: Map STIX `external_references` array to `attack:externalReference`. Each reference should be a node or literal, linked to the technique/attack-pattern.
- **object_marking_refs**: Map STIX `object_marking_refs` array to `attack:objectMarking`. Each marking should be a node or literal, linked to the technique/attack-pattern.

For each property:

- Update ETL to extract the field from STIX JSON.
- Add RDF triple(s) using the correct SEC/attack namespace property.
- Ensure multi-valued fields are handled as repeated triples.
- If the property is a reference (e.g., created_by_ref, external_references), create/link the referenced node as needed.
- Update SHACL shapes to require or validate the new property if mandatory.
- Add tests to confirm correct mapping in sample TTL output.

### SHACL Review and Recommendations

- Current SHACL shapes (attack-shapes.ttl) require: attackTechniqueId, rdfs:label, sec:belongs_to (Tactic), and optionally sec:description for Technique and SubTechnique.
- The following properties are not currently required or validated by SHACL:
  - spec_version
  - created_by_ref
  - labels
  - aliases
  - kill_chain_phases
  - external_references
  - object_marking_refs
- Recommendation: Extend SHACL shapes to include these properties as required or recommended, based on their importance for traceability, reasoning, and standards alignment.
  - For multi-valued fields (labels, aliases, kill_chain_phases, external_references, object_marking_refs), use sh:minCount 0 and sh:datatype xsd:string or sh:class as appropriate.
  - For references (created_by_ref, external_references, object_marking_refs), ensure referenced nodes are validated if present.
- Update SHACL validation tests to cover new/extended properties.

### Mapping Decisions and Rationale

- Each missing or partial property was reviewed for:
  - Presence in authoritative STIX schema and ATT&CK data
  - Value for traceability, reasoning, and RAG safety
  - Alignment with KGCS ontology governance and SHACL constraints
- Properties prioritized for mapping/enrichment:
  - spec_version, created_by_ref, labels, aliases, kill_chain_phases, external_references, object_marking_refs
- Mapping approach:
  - Use canonical SEC/attack namespace predicates for all new properties
  - Multi-valued fields (labels, aliases, kill_chain_phases, external_references, object_marking_refs) mapped as repeated triples
  - References (created_by_ref, external_references, object_marking_refs) create/link referenced nodes as needed
  - SHACL shapes updated to require or recommend new properties as appropriate
- Rationale:
  - Ensures full traceability to source data and standards
  - Enables richer reasoning and RAG-safe traversals
  - Aligns with KGCS governance: no fabricated edges, all relationships traceable to authoritative data
  - Supports downstream applications and analytics

## 7. Next Steps

The following tasks remain to complete the ATT&CK enrichment and alignment process. (✔ = completed, ☐ = not started, ⧗ = in progress)

- ✔ Checklist for mapping all required ATT&CK ontology properties
- ⧗ Implement subclass structure in ETL output
- ☐ Add object property relationships to ETL and ontology
- ☐ Enforce SHACL constraints for new fields/relationships
- ☐ Extend ETL for unmapped STIX fields
- ☐ Document all changes and gaps
- ☐ Prioritize by reasoning and RAG value
- ✔ Checklist: ATT&CK property mapping subtasks
- ✔ Inventory all STIX fields and relationships
- ✔ Crosswalk each field to ontology property
- ✔ Identify missing or partial mappings in ETL
- ✔ Draft mapping plan for each property
- ✔ Review SHACL for required fields
- ✔ Document mapping decisions and rationale

### Descriptions of remaining tasks

- **Implement subclass structure in ETL output (⧗):** Complete and validate the ETL logic for correct subclass typing and relationships (Technique, SubTechnique, Tactic).
- **Add object property relationships to ETL and ontology (☐):** Map and emit all relevant relationships (e.g., uses, detects, targets, associatedGroup) as per ontology and source data.
- **Enforce SHACL constraints for new fields/relationships (☐):** Update SHACL shapes and validate ETL output for all new/enriched properties and relationships.
- **Extend ETL for unmapped STIX fields (☐):** Add support for any STIX fields not yet mapped (e.g., labels, aliases, external references, marking, etc.).
- **Document all changes and gaps (☐):** Maintain up-to-date documentation of all changes, gaps, and rationale in this file and supporting docs.
- **Prioritize by reasoning and RAG value (☐):** Focus implementation and enrichment on properties/relationships that maximize reasoning value and RAG safety.

## 8. Implementation Details: Subclass Structure and Enrichment

This section provides a detailed analysis and implementation plan for subclass structure, property mapping, and enrichment tasks identified in the gap analysis above.

### 8.1 Task: Implement Subclass Structure in ETL Output

#### 8.1.1 Review of Current ETL Logic

- The ETL (`src/etl/etl_attack.py`) distinguishes between Techniques and SubTechniques:
  - If the ATT&CK ID contains a dot (e.g., `T1059.001`), it is treated as a SubTechnique (`SEC.SubTechnique`).
  - Otherwise, it is treated as a Technique (`SEC.Technique`).
- The ETL adds the `SEC.subtechnique_of` relationship for subtechniques, pointing to their parent technique.
- All required SHACL properties are present in the ETL logic:
  - `attackTechniqueId`, `rdfs:label`, `sec:description` (optional), `sec:belongs_to` (tactic) for both classes.
  - `sec:subtechnique_of` (parent technique) for subtechniques.

#### 8.1.2 Implementation Plan

1. **Audit ETL Output:**
   - Ensure all subtechniques are output as `SEC.SubTechnique` and have a valid `sec:subtechnique_of` triple.
   - Ensure all techniques are output as `SEC.Technique` only.
   - Validate that all required properties are present for each node type.
2. **Edge Case Handling:**
   - Confirm that subtechniques with missing or malformed parent IDs are handled (e.g., log or skip with warning).
   - Ensure no node is output as both Technique and SubTechnique.
3. **Testing:**
   - Generate sample output and validate against SHACL shapes.
   - Add/extend tests to cover subclass structure and relationships.

#### 8.1.3 Gaps or Improvements Needed

- If any subtechnique lacks a valid parent technique, the ETL should log a warning and skip or flag the node.
- Consider refactoring for clarity if logic is duplicated or unclear.
- Ensure all subclass relationships are traceable to source data (per governance rules).

#### 8.1.4 Next Steps

- Implement or refactor ETL logic as needed.
- Validate output with SHACL.
- Document any issues or edge cases found during implementation.

### 8.2 Subclass Structure: Full Analysis

#### 8.2.1 Tactic Nodes

- **ETL Handling:**
  - The ETL creates a node for each STIX object of type `x-mitre-tactic` as `SEC.Tactic`.
  - Properties mapped: `sec:tacticId` (from `x_mitre_shortname`), `rdfs:label` (from `name`), `sec:description`, `sec:deprecated`, `sec:created`, `sec:modified`.
  - SHACL requires: `sec:tacticId` (required), `rdfs:label` (required).
- **Gaps/Improvements:**
  - All required properties are mapped. Optional properties are included if present.
  - No subclassing of Tactic is required in the core ontology.
  - Ensure that every `sec:belongs_to` on Technique/SubTechnique points to a valid Tactic node.

#### 8.2.2 Technique and SubTechnique Nodes

- **ETL Handling:**
  - Techniques: STIX `attack-pattern` with ATT&CK ID (no dot) → `SEC.Technique`.
  - SubTechniques: STIX `attack-pattern` with ATT&CK ID (dot) → `SEC.SubTechnique`.
  - Properties mapped: `sec:attackTechniqueId`, `rdfs:label`, `sec:description`, `sec:belongs_to`, `sec:subtechnique_of` (for subtechniques), plus optional fields (platform, dataSource, etc.).
  - SHACL requires: `sec:attackTechniqueId`, `rdfs:label`, `sec:belongs_to` (both), `sec:subtechnique_of` (subtechniques only).
- **Gaps/Improvements:**
  - All required properties are mapped.
  - Ensure that subtechniques always have a valid parent technique and that all relationships are present.
  - No node should be both Technique and SubTechnique.

#### 8.2.3 Relationships

- **ETL Handling:**
  - `sec:belongs_to`: Technique/SubTechnique → Tactic (from `kill_chain_phases` mapping to `tactics_map`).
  - `sec:subtechnique_of`: SubTechnique → Technique (from ATT&CK ID parent extraction).
  - `sec:derived_from`: Technique → CAPEC (from external references).
- **Gaps/Improvements:**
  - All required relationships for subclass structure are present.
  - Ensure that all referenced nodes (Tactic, Technique) exist in the output graph.
  - Consider logging or flagging if a referenced node is missing.

#### 8.2.4 Other Classes/Extensions

- **ETL Handling:**
  - The ETL does not currently emit other ATT&CK subclasses (e.g., Group, Software, Mitigation) as these are not present in the current STIX input or core ontology.
  - If/when these are added to the ontology, ETL logic will need to be extended accordingly.

### 8.3 Summary Table: Subclass Structure Coverage

| Class | ETL Node Type | Required Properties (SHACL) | ETL Coverage | Gaps/Notes |
| --- | --- | --- | --- | --- |
| Tactic | SEC.Tactic | tacticId, rdfs:label | Yes | None |
| Technique | SEC.Technique | attackTechniqueId, rdfs:label, belongs_to | Yes | None |
| SubTechnique | SEC.SubTechnique | attackTechniqueId, rdfs:label, belongs_to, subtechnique_of | Yes | Must ensure parent exists |

### 8.4 Recommendations

- Validate that all subclass relationships are present and correct in ETL output.
- Add logging for any missing referenced nodes (tactic, parent technique).
- Extend ETL and ontology if new ATT&CK subclasses are introduced in future standards.

### 8.5 Subclass Structure: Additional ATT&CK Classes

#### 8.5.1 Group (Intrusion Set/Group)

- **Ontology/SHACL:**
  - Not present in current core ontology or SHACL shapes for ATT&CK.
  - In STIX, represented as `intrusion-set` objects (sometimes called Group in MITRE ATT&CK docs).
- **ETL Handling:**
  - Current ETL does not process or emit Group/Intrusion Set nodes.
- **Gaps/Improvements:**
  - If Group is added to the ontology, ETL must be extended to map `intrusion-set` objects to `SEC.Group` (or equivalent), with required properties and relationships (e.g., uses, attributed-to).

#### 8.5.2 Software (Tool/Malware)

- **Ontology/SHACL:**
  - Not present in current core ontology or SHACL shapes for ATT&CK.
  - In STIX, represented as `tool` and `malware` objects (collectively "Software" in ATT&CK docs).
- **ETL Handling:**
  - Current ETL does not process or emit Software nodes.
- **Gaps/Improvements:**
  - If Software is added to the ontology, ETL must be extended to map `tool` and `malware` objects to `SEC.Software` (or equivalent), with required properties and relationships (e.g., used-by, implements, targets).

#### 8.5.3 DataSource / DataComponent

- **Ontology/SHACL:**
  - DataSource and DataComponent are referenced in the ontology as properties (e.g., `sec:dataSource`, `sec:dataComponent`), but not as first-class node types/classes.
  - SHACL does not define shapes for DataSource/DataComponent nodes.
- **ETL Handling:**
  - ETL emits `sec:dataSource` and `sec:dataComponent` as string literals attached to Technique/SubTechnique nodes.
- **Gaps/Improvements:**
  - If DataSource/DataComponent are promoted to first-class nodes in the ontology, ETL must be updated to emit nodes and relationships (e.g., Technique → usesDataSource → DataSource).
  - Current approach is property-only, not node-based.

#### 8.5.4 Asset

- **Ontology/SHACL:**
  - Asset is not present as a class in the current ATT&CK core ontology or SHACL shapes.
  - Not directly represented in STIX ATT&CK SDOs.
- **ETL Handling:**
  - No Asset nodes or properties are emitted by the ETL.
- **Gaps/Improvements:**
  - If Asset is added to the ontology (e.g., for mapping to D3FEND or other standards), ETL will need to be extended accordingly.

### 8.6 Summary Table: Coverage of Additional Classes

| Class | STIX Object(s) | Ontology/SHACL Present | ETL Coverage | Gaps/Notes |
| --- | --- | --- | --- | --- |
| Group | intrusion-set | No | No | Add if ontology extended |
| Software | tool, malware | No | No | Add if ontology extended |
| DataSource | (property only) | Property only | As property | Promote to node if needed |
| DataComponent | (property only) | Property only | As property | Promote to node if needed |
| Asset | (not in STIX) | No | No | Add if ontology extended |

### 8.7 Recommendations (Additional Classes)

- Review ontology/SHACL for future inclusion of Group, Software, DataSource, DataComponent, Asset.
- Extend ETL to support these classes if/when added to the ontology.
- For DataSource/DataComponent, consider node-based modeling if richer relationships are needed.

---

# ANNEX: External ATT&CK Schema Analyses

This section will be expanded with detailed analyses and mapping tables for each ATT&CK schema file as reviewed. Each table compares the external schema, KGCS ontology/ETL coverage, and highlights gaps or recommendations for enrichment.

## ATT&CK-STIX Schema Reference

Current ATT&CK Spec Version: [3.3.0](https://github.com/mitre-attack/attack-stix-data/blob/master/CHANGELOG.md)

### STIX Domain Objects

| ATT&CK Concept | STIX Object | Notes |
| -------------- | ----------- | ----- |
| [Analytic](./sdo/analytic.schema.mdx) | `x-mitre-analytic` | |
| [Asset](./sdo/asset.schema.mdx) | `x-mitre-asset` | |
| [Campaign](./sdo/campaign.schema.mdx) | `campaign` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714304), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_pcpvfz4ik6d6)) | |
| [Collection](./sdo/collection.schema.mdx) | `x-mitre-collection` | This type was added in the upgrade to STIX 2.1 and is not available in the [STIX 2.0 dataset](https://github.com/mitre/cti). |
| [Data Component](./sdo/data-component.schema.mdx) | `x-mitre-data-component` | |
| [Data Source](./sdo/data-source.schema.mdx) | `x-mitre-data-source` | |
| [Detection Strategy](./sdo/detection-strategy.schema.mdx) | `x-mitre-detection-strategy` | |
| [Group](./sdo/group.schema.mdx) | `intrusion-set` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714316), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_5ol9xlbbnrdn)) | |
| [Identity](./sdo/identity.schema.mdx) | `identity` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714310), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_wh296fiwpklp)) | Referenced by `created_by_ref` and `x_mitre_modified_by_ref` to convey the creator and most recent modifier of each object |
| [Matrix](./sdo/matrix.schema.mdx) | `x-mitre-matrix` | |
| [Mitigation](./sdo/mitigation.schema.mdx) | `course-of-action` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714307), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_a925mpw39txn)) | |
| [Software](./sdo/software.schema.mdx) | `malware` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714319), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_s5l7katgbp09)) or `tool` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714331), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_z4voa9ndw8v)) | |
| [Tactic](./sdo/tactic.schema.mdx) | `x-mitre-tactic` | |
| [Technique](./sdo/technique.schema.mdx) | `attack-pattern` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714301), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_axjijf603msy)) | |

### STIX Relationship Objects

| ATT&CK Concept | STIX Object | Notes |
| -------------- | ----------- | ----- |
| [Relationship](./sro/relationship.schema.mdx) | `relationship` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part2-stix-objects/stix-v2.0-cs01-part2-stix-objects.html#_Toc496714337), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_cqhkqvhnlgfh)) | ATT&CK uses many relationship types. [Refer to them here](./relationship-types). |

### STIX Meta Objects

| ATT&CK Concept | STIX Object | Notes |
| -------------- | ----------- | ----- |
| [Marking Definition](./smo/marking-definition.schema.mdx) | `marking-definition` ([STIX 2.0](https://docs.oasis-open.org/cti/stix/v2.0/cs01/part1-stix-core/stix-v2.0-cs01-part1-stix-core.html#_Toc496709283), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_k5fndj2c7c1k)) | Referenced in the `object_marking_refs` of all objects to express the MITRE Corporation copyright |

## A.1 Tactic Schema Mapping (version 3.3.0)

| Property | External Schema | KGCS Ontology/ETL | Gap/Notes |
| --- | --- | --- | --- |
| id | Yes (req) | Yes | - |
| type | Yes (req) | Yes | - |
| spec_version | Yes (req) | No | Needs mapping |
| created | Yes (req) | Yes | - |
| modified | Yes (req) | Yes | - |
| created_by_ref | Yes (req) | No | Needs mapping |
| labels | Optional | No | Needs mapping |
| revoked | Optional | No | Needs mapping |
| confidence | Optional | No | Needs mapping |
| lang | Optional | No | Needs mapping |
| external_references | Yes (req) | No | Needs mapping |
| object_marking_refs | Yes (req) | No | Needs mapping |
| granular_markings | Optional | No | Needs mapping |
| extensions | Optional | No | Needs mapping |
| name | Yes (req) | Yes | - |
| x_mitre_attack_spec_version | Yes (req) | No | Needs mapping |
| x_mitre_version | Yes (req) | No | Needs mapping |
| x_mitre_old_attack_id | Optional | No | Needs mapping |
| x_mitre_deprecated | Optional | Yes | - |
| description | Yes (req) | Yes | - |
| x_mitre_domains | Yes (req) | No | Needs mapping |
| x_mitre_shortname | Yes (req) | Yes | - |
| x_mitre_modified_by_ref | Yes (req) | No | Needs mapping |
| x_mitre_contributors | Optional | Yes | - |

**Legend:**

- "Yes (req)": Required in external schema
- "Optional": Optional in external schema
- "Yes": Present in KGCS ontology/ETL
- "No": Not present in KGCS ontology/ETL

---

## A.2 Technique Schema Mapping (version 3.3.0)

| Property | External Schema | KGCS Ontology/ETL | Gap/Notes |
| --- | --- | --- | --- |
| id | Yes (req) | Yes | - |
| type | Yes (req) | Yes | - |
| spec_version | Yes (req) | No | Needs mapping |
| created | Yes (req) | Yes | - |
| modified | Yes (req) | Yes | - |
| created_by_ref | Optional | No | Needs mapping |
| labels | Optional | No | Needs mapping |
| revoked | Optional | No | Needs mapping |
| confidence | Optional | No | Needs mapping |
| lang | Optional | No | Needs mapping |
| external_references | Yes (req) | Partial | Only CAPEC/ATT&CK IDs mapped; full mapping needed |
| object_marking_refs | Optional | No | Needs mapping |
| granular_markings | Optional | No | Needs mapping |
| extensions | Optional | No | Needs mapping |
| name | Yes (req) | No | Needs mapping |
| x_mitre_attack_spec_version | Yes (req) | No | Needs mapping |
| x_mitre_version | Yes (req) | No | Needs mapping |
| x_mitre_old_attack_id | Optional | No | Needs mapping |
| x_mitre_deprecated | Optional | No | Needs mapping |
| kill_chain_phases | Optional | Yes | Used for tactic mapping |
| description | Optional | Yes | - |
| x_mitre_platforms | Optional | Yes | - |
| x_mitre_detection | Deprecated | Yes | Will be removed in v4.0.0; currently mapped |
| x_mitre_is_subtechnique | Yes (req) | Yes | Used to distinguish subtechniques |
| x_mitre_data_sources | Deprecated | Yes | Will be removed in v4.0.0; currently mapped |
| x_mitre_defense_bypassed | Deprecated | No | Needs mapping if required |
| x_mitre_contributors | Optional | No | Needs mapping |
| x_mitre_permissions_required | Deprecated | Yes | Will be removed in v4.0.0; currently mapped |
| x_mitre_remote_support | Deprecated | No | Needs mapping if required |
| x_mitre_system_requirements | Deprecated | No | Needs mapping if required |
| x_mitre_impact_type | Optional | No | Needs mapping if required (for Impact tactic) |
| x_mitre_effective_permissions | Deprecated | Yes | Will be removed in v4.0.0; currently mapped |
| x_mitre_network_requirements | Optional | Yes | - |
| x_mitre_tactic_type | Optional | No | Needs mapping if required (for Mobile domain) |
| x_mitre_domains | Yes (req) | No | Needs mapping |
| x_mitre_modified_by_ref | Optional | No | Needs mapping |

**Legend:**

- "Yes (req)": Required in external schema
- "Optional": Optional in external schema
- "Deprecated": Deprecated in v3.3.0, to be removed in v4.0.0
- "Yes": Present in KGCS ontology/ETL
- "No": Not present in KGCS ontology/ETL
- "Partial": Only some values or subfields mapped

---

## A.3 Mitigation Schema Mapping (version 3.3.0)

| Property | External Schema | KGCS Ontology/ETL | Gap/Notes |
| --- | --- | --- | --- |
| id | Yes (req) | No | Needs mapping |
| type | Yes (req) | No | Needs mapping |
| spec_version | Yes (req) | No | Needs mapping |
| created | Yes (req) | No | Needs mapping |
| modified | Yes (req) | No | Needs mapping |
| created_by_ref | Yes (req) | No | Needs mapping |
| labels | Optional | No | Needs mapping |
| revoked | Optional | No | Needs mapping |
| confidence | Optional | No | Needs mapping |
| lang | Optional | No | Needs mapping |
| external_references | Yes (req) | No | Needs mapping |
| object_marking_refs | Yes (req) | No | Needs mapping |
| granular_markings | Optional | No | Needs mapping |
| extensions | Optional | No | Needs mapping |
| name | Yes (req) | No | Needs mapping |
| x_mitre_attack_spec_version | Yes (req) | No | Needs mapping |
| x_mitre_version | Yes (req) | No | Needs mapping |
| x_mitre_old_attack_id | Optional | No | Needs mapping |
| x_mitre_deprecated | Optional | No | Needs mapping |
| description | Yes (req) | No | Needs mapping |
| x_mitre_domains | Yes (req) | No | Needs mapping |
| x_mitre_modified_by_ref | Yes (req) | No | Needs mapping |
| x_mitre_contributors | Optional | No | Needs mapping |

**Legend:**

- "Yes (req)": Required in external schema
- "Optional": Optional in external schema
- "Deprecated": Deprecated in v3.3.0, to be removed in v4.0.0
- "Yes": Present in KGCS ontology/ETL
- "No": Not present in KGCS ontology/ETL
- "Partial": Only some values or subfields mapped

---

## A.4 Group Schema Mapping (version 3.3.0)

| Property | External Schema | KGCS Ontology/ETL | Gap/Notes |
| --- | --- | --- | --- |
| id | Yes (req) | No | Needs ontology extension and ETL mapping |
| type | Yes (req) | No | Should be 'intrusion-set'; not present in KGCS |
| spec_version | Yes (req) | No | Needs mapping |
| created | Yes (req) | No | Needs mapping |
| modified | Yes (req) | No | Needs mapping |
| created_by_ref | Optional | No | Needs mapping |
| labels | Optional | No | Needs mapping |
| revoked | Optional | No | Needs mapping |
| confidence | Optional | No | Needs mapping |
| lang | Optional | No | Needs mapping |
| external_references | Yes (req) | No | Needs mapping |
| object_marking_refs | Optional | No | Needs mapping |
| granular_markings | Optional | No | Needs mapping |
| extensions | Optional | No | Needs mapping |
| name | Yes (req) | No | Needs mapping |
| x_mitre_attack_spec_version | Yes (req) | No | Needs mapping |
| x_mitre_version | Yes (req) | No | Needs mapping |
| x_mitre_old_attack_id | Optional | No | Needs mapping |
| x_mitre_deprecated | Optional | No | Needs mapping |
| description | Optional | No | Needs mapping |
| x_mitre_domains | Yes (req) | No | Needs mapping |
| x_mitre_contributors | Optional | No | Needs mapping |
| x_mitre_modified_by_ref | Optional | No | Needs mapping |
| aliases | Optional | No | Needs mapping |
| first_seen | Optional | No | Needs mapping |
| last_seen | Optional | No | Needs mapping |
| goals | Optional | No | Needs mapping |
| resource_level | Optional | No | Needs mapping |
| primary_motivation | Optional | No | Needs mapping |
| secondary_motivations | Optional | No | Needs mapping |

**Legend:**

- "Yes (req)": Required in external schema
- "Optional": Optional in external schema
- "Deprecated": Deprecated in v3.3.0, to be removed in v4.0.0
- "Yes": Present in KGCS ontology/ETL
- "No": Not present in KGCS ontology/ETL
- "Partial": Only some values or subfields mapped

---

## A.5 Software Schema Mapping (version 3.3.0)

ATT&CK Software is modeled as both Malware and Tool STIX objects. The table below covers all properties for both types.

| Property | External Schema | KGCS Ontology/ETL | Gap/Notes |
| --- | --- | --- | --- |
| id | Yes (req) | No | Needs ontology extension and ETL mapping |
| type | Yes (req) | No | 'malware' or 'tool'; not present in KGCS |
| spec_version | Yes (req) | No | Needs mapping |
| created | Yes (req) | No | Needs mapping |
| modified | Yes (req) | No | Needs mapping |
| created_by_ref | Yes (req) | No | Needs mapping |
| labels | Optional | No | Needs mapping |
| revoked | Optional | No | Needs mapping |
| confidence | Optional | No | Needs mapping |
| lang | Optional | No | Needs mapping |
| external_references | Yes (req) | No | Needs mapping |
| object_marking_refs | Optional | No | Needs mapping |
| granular_markings | Optional | No | Needs mapping |
| extensions | Optional | No | Needs mapping |
| name | Yes (req) | No | Needs mapping |
| x_mitre_attack_spec_version | Yes (req) | No | Needs mapping |
| x_mitre_version | Yes (req) | No | Needs mapping |
| x_mitre_old_attack_id | Optional | No | Needs mapping |
| x_mitre_deprecated | Optional | No | Needs mapping |
| description | Yes (req) | No | Needs mapping |
| x_mitre_platforms | Optional | No | Needs mapping |
| x_mitre_contributors | Optional | No | Needs mapping |
| x_mitre_aliases | Optional | No | Needs mapping |
| x_mitre_modified_by_ref | Yes (req) | No | Needs mapping |
| x_mitre_domains | Yes (req) | No | Needs mapping |
| aliases | Optional | No | Needs mapping |
| is_family | Malware only | No | Needs mapping |
| malware_types | Malware only | No | Needs mapping |
| kill_chain_phases | Optional | No | Needs mapping |
| first_seen | Optional | No | Needs mapping |
| last_seen | Optional | No | Needs mapping |
| architecture_execution_envs | Malware only | No | Needs mapping |
| implementation_languages | Malware only | No | Needs mapping |
| capabilities | Malware only | No | Needs mapping |
| sample_refs | Malware only | No | Needs mapping |
| operating_system_refs | Malware only | No | Needs mapping |
| tool_types | Tool only | No | Needs mapping |
| tool_version | Tool only | No | Needs mapping |

**Legend:**

- "Yes (req)": Required in external schema
- "Optional": Optional in external schema
- "Yes": Present in KGCS ontology/ETL
- "No": Not present in KGCS ontology/ETL

## A.6 Relationship Types Schema Mapping (version 3.3.0)

| Relationship Type | Source Type(s) | Target Type(s) | Custom Type? | External Schema | KGCS Ontology/ETL | Gap/Notes |
| - | - | - | - | - | - | - |
| uses | intrusion-set, malware, tool, campaign | attack-pattern, malware, tool | No | Yes | Partial | Only some uses relationships mapped; transitive logic not modeled |
| mitigates | course-of-action | attack-pattern | No | Yes | No | Not mapped; needs ontology/ETL extension |
| subtechnique-of | attack-pattern (subtechnique) | attack-pattern (parent) | Yes | Yes | Yes | Mapped as sec:subtechnique_of |
| detects | x-mitre-data-component, x-mitre-detection-strategy | attack-pattern | Yes | Yes (deprecated) | No | Deprecated; not mapped in KGCS |
| attributed-to | campaign | intrusion-set | No | Yes | No | Not mapped; needs ontology/ETL extension |
| targets | attack-pattern | x-mitre-asset | Yes | Yes | No | Not mapped; asset not present in KGCS |
| revoked-by | any type | any type | Yes | Yes | No | Not mapped; could be used for versioning/revocation |

**Legend:**

- "Yes": Present in external schema
- "No": Not present in KGCS ontology/ETL
- "Partial": Only some values or subfields mapped

**Notes:**

- Some relationships (e.g., uses) are only partially mapped in KGCS, and transitive relationships (e.g., group uses software uses technique) are not explicitly modeled.
- The detects relationship is deprecated as of ATT&CK 3.3.0 and will be removed in 4.0.0.
- Asset and detection-strategy objects are not present in KGCS ontology/ETL.
- Custom types (e.g., subtechnique-of, detects, targets, revoked-by) require explicit ontology/ETL support if needed.
