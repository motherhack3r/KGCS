# ATT&CK Ontology v1.0 — Consolidated Documentation

This file consolidates the high-level ontology description and the field-by-field ETL mapping for MITRE ATT&CK used by KGCS.

## Overview

Scope: Core ATT&CK entities and relationships as defined by the MITRE ATT&CK framework. This ontology is a frozen representation of the ATT&CK data model, suitable for knowledge graphs, RAG, and reasoning.

## Ontology — Classes

| Class | Description |
| ----- | ----------- |
| `Tactic` | High‑level objective of an adversary (e.g., Initial Access, Execution). |
| `Technique` | Concrete adversary action that achieves a tactic. |
| `SubTechnique` | Granular variation of a technique. |
| `Group` | Adversary group or intrusion set. |
| `Software` | Malware or tool used by a group. |
| `DataSource` | Source of observable data. |
| `DataComponent` | Specific data element within a data source. |
| `Asset` | Targeted asset or system. |

## Relationships (Ontology)

| Relationship | Source | Target | Notes |
| ------------ | ------ | ------ | ----- |
| `contains` | Tactic | Technique | Tactic contains techniques |
| `subtechnique_of` | SubTechnique | Technique | Subtechnique specialization |
| `uses` | Group/Software | Technique | Usage relationship |
| `detects` | DataComponent | Technique | Detection capability |
| `targets` | Technique | Asset | Targeting relationship |

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/attck#> .

ex:TacticShape a sh:NodeShape ;
    sh:targetClass ex:Tactic ;
    sh:property [ sh:path ex:contains ; sh:class ex:Technique ; sh:minCount 1 ] .

ex:TechniqueShape a sh:NodeShape ;
    sh:targetClass ex:Technique ;
    sh:property [ sh:path ex:subtechnique_of ; sh:class ex:Technique ; sh:maxCount 1 ] .

ex:GroupShape a sh:NodeShape ;
    sh:targetClass ex:Group ;
    sh:property [ sh:path ex:uses ; sh:class ex:Software ] ;
    sh:property [ sh:path ex:uses ; sh:class ex:Technique ] .
```

## Field-by-Field Mapping (ETL)

This section maps STIX/ATT&CK fields to KGCS ontology properties used by the ETL.

| STIX Field / Property | Ontology Property / Node | Notes |
| --------------------- | ------------------------ | ----- |
| id | attackId | attack-pattern id (Txxxx) |
| name | rdfs:label | |
| description | dct:description | |
| x_mitre_tactic_type | kgcs:tacticType | |
| x_mitre_is_subtechnique | kgcs:isSubtechnique | Boolean |
| x_mitre_platforms | kgcs:platform | List |
| x_mitre_data_sources | kgcs:dataSource | Links to DataSource nodes |
| x_mitre_data_components | kgcs:dataComponent | Links to DataComponent nodes |
| x_mitre_detection | kgcs:detection | Free text |
| created / modified | dct:created / dct:modified | Timestamps |

## Node Types and IDs

- Technique: attack-pattern, external_id = Txxxx
- SubTechnique: attack-pattern with x_mitre_is_subtechnique=true
- Tactic: x-mitre-tactic (TAxxxx)
- Group: intrusion-set (Gxxxx)
- Software: malware/tool (Sxxxx/Mxxxx)

## Example Instances

```turtle
ex:TA0001 a ex:Tactic ; ex:contains ex:T1059 .
ex:T1059 a ex:Technique ; ex:subtechnique_of ex:T1059.001 ; ex:targets ex:WindowsServer .
ex:T1059.001 a ex:SubTechnique ; ex:subtechnique_of ex:T1059 .
ex:GroupA a ex:Group ; ex:uses ex:MalwareX , ex:T1059 .
```

## Usage Notes

- Frozen ontology: add instances rather than changing canonical classes.
- Preserve official ATT&CK IDs (Txxxx, TAxxxx).

---

## References

- MITRE ATT&CK: <https://attack.mitre.org/>
- STIX 2.1: <https://docs.oasis-open.org/cti/stix/v2.1/overview.html>

---

## Official Sources

- **MITRE ATT&CK STIX repository (raw):**
  - Enterprise: <https://github.com/mitre/cti/raw/refs/heads/master/enterprise-attack/enterprise-attack.json>
  - Mobile: <https://github.com/mitre/cti/raw/refs/heads/master/mobile-attack/mobile-attack.json>
  - ICS: <https://github.com/mitre/cti/raw/refs/heads/master/ics-attack/ics-attack.json>
  - PRE-ATT&CK: <https://github.com/mitre/cti/raw/refs/heads/master/pre-attack/pre-attack.json>
- **MITRE CTI-STIX JSON SCHEMA:** <https://github.com/oasis-open/cti-stix2-json-schemas/tree/master/schemas>
- **SHACL shapes:** [attack-shapes.ttl](../shacl/attack-shapes.ttl)
- **ETL transformer:** [etl_attck.py](../../scripts/etl_attck.py) (STIX → RDF)

Notes: Use the official ATT&CK STIX repository for canonical IDs and timestamps; snapshots should include the commit SHA in `.meta.json`.
 
- **Local schemas / samples:** `data/attack/schemas/`, `data/attack/raw/`, `data/attack/samples/` (preferred for offline snapshots)
