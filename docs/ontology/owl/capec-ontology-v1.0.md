# CAPEC Ontology v1.0 — Consolidated Documentation

This file consolidates the high-level ontology description and the field-by-field ETL mapping for MITRE CAPEC as used by KGCS.

## Overview

Scope: Core CAPEC entities and relationships as defined by the CAPEC standard. This ontology is a frozen representation of the CAPEC data model, suitable for knowledge graphs, RAG, and reasoning.

## Ontology — Classes

| Class | Description | Source | Notes |
| ----- | ----------- | ------ | ----- |
| `AttackPattern` | Individual attack pattern (e.g., CAPEC‑130). | CAPEC | |
| `Category` | Grouping of attack patterns. | CAPEC | |
| `View` | Perspective or slice of the CAPEC catalog. | CAPEC | |
| `ExternalReference` | External resource for an attack pattern. | CAPEC | |
| `Weakness` | CWE weakness related to an attack pattern. | CAPEC | |
| `Technique` | ATT&CK technique that an attack pattern can map to. | CAPEC | |

## Ontology — Relationships

| Relationship | Source | Target | Notes |
| ------------ | ------ | ------ | ----- |
| `childOf` | AttackPattern | AttackPattern | Hierarchy |
| `parentOf` | AttackPattern | AttackPattern | Inverse |
| `peerOf` | AttackPattern | AttackPattern | Sibling |
| `mapsTo` | AttackPattern | Technique / Weakness | Mapping to ATT&CK or CWE |
| `hasExternalReference` | AttackPattern | ExternalReference | External docs |
| `hasCategory` | AttackPattern | Category | Membership |

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix capec: <http://example.org/capec#> .

capec:AttackPatternShape a sh:NodeShape ;
    sh:targetClass capec:AttackPattern ;
    sh:property [ sh:path capec:childOf ; sh:class capec:AttackPattern ] ;
    sh:property [ sh:path capec:mapsTo ; sh:class capec:Technique ] ;
    sh:property [ sh:path capec:hasExternalReference ; sh:class capec:ExternalReference ] .

capec:CategoryShape a sh:NodeShape ;
    sh:targetClass capec:Category ;
    sh:property [ sh:path capec:hasMember ; sh:class capec:AttackPattern ] .
```

## Field-by-Field Mapping (ETL)

| CAPEC Field / Property | Ontology Property / Node | Notes |
| ---------------------- | ------------------------ | ----- |
| id | capecId | CAPEC-xxxx |
| name | rdfs:label | |
| description | dct:description | |
| likelihood_of_attack | kgcs:likelihood | |
| severity | kgcs:severity | |
| prerequisites | kgcs:prerequisite | List |
| skills_required | kgcs:skillsRequired | List |
| related_weaknesses | kgcs:exploits | List of CWE IDs |
| related_attack_patterns | kgcs:related | List of CAPEC IDs |
| mitigations | kgcs:mitigation | List |
| example_instances | kgcs:example | List |
| references | kgcs:reference | List |
| status | kgcs:status | |
| parent_of / child_of / peer_of | kgcs:parentOf / kgcs:childOf / kgcs:peerOf | Hierarchy relationships |

## Example Instance

```turtle
capec:CAPEC-130 a capec:AttackPattern ;
    capec:childOf capec:CAPEC-100 ;
    capec:mapsTo attack:T1059 ;
    capec:hasExternalReference capec:ExtRef-001 ;
    capec:hasCategory capec:Cat-01 ;
    capec:hasView capec:View-Graph ;
    capec:hasRelatedWeakness cwe:CWE-787 .
```

## Usage Notes

* Frozen ontology: prefer adding instances over modifying existing canonical classes.
* Use official CAPEC identifiers.

---

## References

* <https://capec.mitre.org/>
* <https://attack.mitre.org/>
* <https://cwe.mitre.org/>

---

## Sources

* **MITRE CAPEC XML:** <https://capec.mitre.org/data/xml/capec_latest.xml>
* **MITRE CAPEC XSD:** <https://capec.mitre.org/data/xsd/ap_schema_latest.xsd>

* **MITRE CTI CAPEC JSON (STIX 2.1):** <https://raw.githubusercontent.com/mitre/cti/refs/heads/master/capec/2.1/stix-capec.json>
* **MITRE CTI-STIX JSON SCHEMA:** <https://github.com/oasis-open/cti-stix2-json-schemas/tree/master/schemas>

* **SHACL shapes:** [capec-shapes.ttl](../shacl/capec-shapes.ttl)
* **ETL transformer:** [etl_capec.py](../../scripts/etl_capec.py)

Notes: Use the CAPEC JSON feed for authoritative IDs; include the feed version or timestamp in snapshot metadata.

- **Local schemas / samples:** `data/capec/schemas/`, `data/capec/raw/`, `data/capec/samples/`
