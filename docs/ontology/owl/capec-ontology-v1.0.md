# CAPEC Ontology v1.0 — Field-by-Field Mapping

This document summarizes the mapping between MITRE CAPEC JSON fields and the KGCS ontology for CAPEC, as required for ETL emission and SHACL validation.

## Core Entity Types
- **AttackPattern** (CAPEC)
- **Category** (CAPEC Category)

## Field-by-Field Mapping

| CAPEC Field / Property         | Ontology Property / Node         | Notes |
|-------------------------------|-----------------------------------|-------|
| id                            | capecId                           | Always present; CAPEC-xxxx |
| name                          | rdfs:label                        | |
| description                   | dct:description                   | |
| likelihood_of_attack          | kgcs:likelihood                   | |
| severity                      | kgcs:severity                     | |
| prerequisites                 | kgcs:prerequisite                 | List |
| skills_required               | kgcs:skillsRequired                | List |
| typical_severity              | kgcs:typicalSeverity               | |
| related_weaknesses            | kgcs:exploits                      | List of CWE IDs |
| related_attack_patterns       | kgcs:related                       | List of CAPEC IDs |
| consequences                  | kgcs:consequence                   | List |
| mitigations                   | kgcs:mitigation                    | List |
| example_instances             | kgcs:example                       | List |
| references                    | kgcs:reference                     | List |
| status                        | kgcs:status                        | |
| abstraction                   | kgcs:abstraction                   | |
| parent_of                     | kgcs:parentOf                      | List of CAPEC IDs |
| child_of                      | kgcs:childOf                       | List of CAPEC IDs |
| peer_of                       | kgcs:peerOf                        | List of CAPEC IDs |
| related_categories            | kgcs:relatedCategory                | List of Category IDs |
| category                      | kgcs:category                      | CAPEC Category node |
| created_date                  | dct:created                        | Timestamp |
| modified_date                 | dct:modified                       | Timestamp |
| deprecated                    | kgcs:deprecated                    | Boolean |

## Relationships

| CAPEC Relationship Type      | Ontology Edge           | Source → Target |
|-----------------------------|-------------------------|-----------------|
| exploits                    | kgcs:exploits           | AttackPattern → CWE |
| related                     | kgcs:related            | AttackPattern ↔ AttackPattern |
| parentOf                    | kgcs:parentOf           | AttackPattern → AttackPattern |
| childOf                     | kgcs:childOf            | AttackPattern → AttackPattern |
| peerOf                      | kgcs:peerOf             | AttackPattern ↔ AttackPattern |
| relatedCategory             | kgcs:relatedCategory    | AttackPattern → Category |
| category                    | kgcs:category           | AttackPattern → Category |

## Node Types and IDs
- **AttackPattern**: CAPEC entry, id = CAPEC-xxxx
- **Category**: CAPEC Category, id = Category-xxxx

## Required for ETL Emission
- All above fields and relationships must be emitted as RDF triples
- All IDs must be preserved (capecId, categoryId, etc.)
- Relationships must use correct ontology edge (see above)
- Hierarchy (parentOf, childOf, peerOf, category) must be preserved
- Deprecated/status/abstraction must be handled

## Example: AttackPattern Node
- capecId: CAPEC-242
- rdfs:label: "Code Injection"
- dct:description: "An adversary exploits improper input validation..."
- kgcs:likelihood: "High"
- kgcs:severity: "Critical"
- kgcs:prerequisite: ["User input is not sanitized"]
- kgcs:exploits: CWE-94
- kgcs:related: CAPEC-100
- kgcs:consequence: ["Data loss"]
- kgcs:mitigation: ["Input validation"]
- kgcs:example: ["Example 1"]
- kgcs:reference: ["https://capec.mitre.org/data/definitions/242.html"]
- kgcs:status: "Draft"
- kgcs:abstraction: "Class"
- kgcs:parentOf: CAPEC-100
- kgcs:category: Category-123
- dct:created: "2022-01-01T00:00:00Z"
- dct:modified: "2023-01-01T00:00:00Z"
- kgcs:deprecated: false

---

This mapping should be used to audit and patch src/etl/etl_capec.py for full ontology conformance.
