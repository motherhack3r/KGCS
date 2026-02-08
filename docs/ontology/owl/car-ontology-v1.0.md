# CAR Ontology v1.0 — Consolidated Documentation

This file consolidates the high-level ontology description and the field-by-field ETL mapping for CAR (Cyber Attack Response) used in KGCS.

## Overview

Scope: Core CAR entities and relationships as defined by the CAR framework. The ontology is frozen and intended for knowledge graphs and ETL emission.

## Core Classes

| Class | Description |
| ----- | ----------- |
| `ResponseHub` | Central hub for a response activity (e.g., Incident Response Team). |
| `ContainmentProtocol` | Procedure to limit spread of an incident. |
| `EradicationProcedure` | Steps to remove threat. |
| `RecoveryProcedure` | Actions to restore services. |
| `PostIncidentAnalysis` | Review and lessons learned. |
| `DefenseTechnique` | Defensive measure from D3FEND. |
| `AttackPattern` | ATT&CK technique addressed by CAR. |
| `Vulnerability` | CVE that may trigger a CAR. |
| `Asset` | Targeted system or asset. |

## Relationships (Ontology)

| Relationship | Source | Target | Notes |
| ------------ | ------ | ------ | ----- |
| `triggers` | ResponseHub | DefenseTechnique | Activates defensive technique |
| `addresses` | ResponseHub | AttackPattern | Mitigates or detects an ATT&CK technique |
| `targets` | ResponseHub | Asset | Applied to particular asset |
| `responds_to` | ResponseHub | Vulnerability | Triggered by a vulnerability |

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix car: <http://example.org/car#> .

car:ResponseHubShape a sh:NodeShape ;
    sh:targetClass car:ResponseHub ;
    sh:property [ sh:path car:has_mass ; sh:datatype xsd:float ; sh:minInclusive 0 ] ;
    sh:property [ sh:path car:has_energy ; sh:datatype xsd:float ; sh:minInclusive 0 ] .

car:ContainmentProtocolShape a sh:NodeShape ;
    sh:targetClass car:ContainmentProtocol ;
    sh:property [ sh:path car:triggers ; sh:class car:DefenseTechnique ] .
```

## Field-by-Field Mapping (ETL)

| Ontology Field | CAR YAML Field(s) | Notes |
| -------------- | ----------------- | ----- |
| `sec:DetectionAnalytic` | DetectionAnalytics/analytics | Main node for each CAR analytic |
| `sec:carId` | id, ID, carId, analytic_id | Unique ID |
| `rdfs:label` | name, title | |
| `sec:description` | description, summary | |
| `sec:status` | status | |
| `sec:tag` | tags | |
| `sec:platform` | platform | |

## Relationships (ETL)

| Ontology Property | CAR YAML Field(s) |
| ----------------- | ---------------- |
| `sec:detects` | techniques, DetectsTechniques |
| `sec:requires` | data_sources, DataSources |
| `sec:reference` | references |

## Example Instance

```turtle
car:CAR-001 a car:ContainmentProtocol ;
    car:has_mass 0.8 ;
    car:has_energy 1.2 ;
    car:triggers d3f:FirewallRule ;
    car:addresses attck:T1059 ;
    car:targets ex:WindowsServer ;
    car:responds_to cve:2025-1234 .
```

---

## References

* CAR Framework
* D3FEND: <https://d3fend.mitre.org/>
* ATT&CK: <https://attack.mitre.org/>

---

## Sources

* **Official CAR JSON (latest):** <https://car.mitre.org/data/car_latest.json>
* **SHACL shapes:** [car-shapes.ttl](../shacl/car-shapes.ttl)
* **ETL transformer:** [etl_car.py](../../scripts/etl_car.py)

Notes: CAR authoritative feed should be snapshot-pinned; include feed version in `.meta.json`.

- **Local schemas / samples:** `data/car/schemas/`, `data/car/raw/`, `data/car/samples/`
