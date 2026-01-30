# ATT&CK Ontology v1.0 — Field-by-Field Mapping

This document summarizes the mapping between MITRE ATT&CK STIX 2.1 fields and the KGCS ontology for ATT&CK, as required for ETL emission and SHACL validation.

## Core Entity Types

- **Technique** (attack-pattern)
- **SubTechnique** (attack-pattern, with x_mitre_is_subtechnique=true)
- **Tactic** (x-mitre-tactic)
- **Group** (intrusion-set)
- **Software** (malware/tool)
- **DataSource** (x-mitre-data-source)
- **DataComponent** (x-mitre-data-component)
- **Mitigation** (course-of-action)

## Field-by-Field Mapping

| STIX Field / Property             | Ontology Property / Node           | Notes                                            |
|-----------------------------------|------------------------------------|--------------------------------------------------|
| id (e.g., attack-pattern--*)      | attackId                           | Always present; Txxxx or Sxxxx for subtechniques |
| name                              | rdfs:label                         |                                                  |
| description                       | dct:description                    |                                                  |
| x_mitre_tactic_type               | kgcs:tacticType                    | For tactics only                                 |
| x_mitre_is_subtechnique           | kgcs:isSubtechnique                | Boolean; true for subtechniques                  |
| x_mitre_platforms                 | kgcs:platform                      | List of platforms                                |
| x_mitre_data_sources              | kgcs:dataSource                    | List; links to DataSource nodes                  |
| x_mitre_data_components           | kgcs:dataComponent                 | List; links to DataComponent nodes               |
| x_mitre_version                   | kgcs:version                       |                                                  |
| x_mitre_detection                 | kgcs:detection                     | Free text detection guidance                     |
| x_mitre_permissions_required      | kgcs:permissionsRequired           | List                                             |
| x_mitre_effective_permissions     | kgcs:effectivePermissions          | List                                             |
| x_mitre_network_requirements      | kgcs:networkRequirements           | List                                             |
| x_mitre_contributors              | kgcs:contributor                   | List                                             |
| x_mitre_deprecated                | kgcs:deprecated                    | Boolean                                          |
| created                           | dct:created                        | Timestamp                                        |
| modified                          | dct:modified                       | Timestamp                                        |
| external_references[].external_id | attackId (Txxxx/Sxxxx/Gxxxx/Mxxxx) | Used for stable IDs                              |
| kill_chain_phases[].phase_name    | kgcs:tactic                        | Maps to Tactic node                              |
| object_marking_refs               | kgcs:markingRef                    | List                                             |
| revoked                           | kgcs:revoked                       | Boolean                                          |

## Relationships

| STIX Relationship Type     | Ontology Edge           | Source → Target                      |
| -------------------------  | ----------------------- | ------------------------------------ |  
| subtechnique-of            | kgcs:subtechniqueOf     | SubTechnique → Technique             |
| part-of (tactic)           | kgcs:partOf             | Technique → Tactic                   |
| uses (group/software)      | kgcs:usedBy             | Technique → Group/Software           |
| mitigates                  | kgcs:mitigatedBy        | Technique → Mitigation               |
| detected-by                | kgcs:detectedBy         | Technique → DataSource/DataComponent |
| requires                   | kgcs:requires           | Technique → DataSource/DataComponent |
| related-to                 | kgcs:related            | Technique ↔ Technique                |

## Node Types and IDs

- **Technique**: attack-pattern, external_id = Txxxx
- **SubTechnique**: attack-pattern, x_mitre_is_subtechnique=true, external_id = Txxxx.y
- **Tactic**: x-mitre-tactic, external_id = TAxxxx
- **Group**: intrusion-set, external_id = Gxxxx
- **Software**: malware/tool, external_id = Sxxxx/Mxxxx
- **Mitigation**: course-of-action, external_id = Mxxxx
- **DataSource**: x-mitre-data-source, external_id = DSxxxx
- **DataComponent**: x-mitre-data-component, external_id = DCxxxx

## Required for ETL Emission

- All above fields and relationships must be emitted as RDF triples
- All IDs must be preserved (attackId, tacticId, groupId, etc.)
- Relationships must use correct ontology edge (see above)
- Subtechnique/technique/tactic hierarchy must be preserved
- DataSource/DataComponent links must be explicit
- Deprecated/revoked/markingRef must be handled

## Example: Technique Node

- attackId: T1059
- rdfs:label: "Command and Scripting Interpreter"
- dct:description: "Adversaries may abuse command and script interpreters..."
- kgcs:platform: ["Windows", "Linux", ...]
- kgcs:partOf: TA0002 (Execution)
- kgcs:subtechniqueOf: T1059 (if subtechnique)
- kgcs:mitigatedBy: M1047 (Mitigation)
- kgcs:detectedBy: DS0017 (DataSource)
- kgcs:usedBy: G0010 (Group)

## Example: Relationships

- T1059 kgcs:partOf TA0002
- T1059.001 kgcs:subtechniqueOf T1059
- T1059 kgcs:mitigatedBy M1047
- T1059 kgcs:detectedBy DS0017
- T1059 kgcs:usedBy G0010

---

This mapping should be used to audit and patch src/etl/etl_attack.py for full ontology conformance.
