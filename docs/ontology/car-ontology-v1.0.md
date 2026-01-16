# CAR (Cyber Attack Response) Ontology v1.0

**Scope**: Core CAR entities and relationships as defined by the CAR framework. This ontology is a *frozen* representation of the CAR data model, suitable for knowledge graphs, RAG, and reasoning.

---

## 1. Classes

| Class | Description | Source | Notes |
|-------|-------------|--------|-------|
| `ResponseHub` | Central hub for a response activity (e.g., Incident Response Team, Containment Protocol). | CAR | Identified by a unique CAR ID (e.g., `CAR-001`). |
| `IncidentResponseTeam` | Team responsible for orchestrating response phases. | CAR | Subclass of `ResponseHub`. |
| `ContainmentProtocol` | Procedure to limit spread of an incident. | CAR | Subclass of `ResponseHub`. |
| `EradicationProcedure` | Steps to remove threat from the environment. | CAR | Subclass of `ResponseHub`. |
| `RecoveryProcedure` | Actions to restore services. | CAR | Subclass of `ResponseHub`. |
| `PostIncidentAnalysis` | Review and lessons learned. | CAR | Subclass of `ResponseHub`. |
| `DefenseTechnique` | Defensive measure from D3FEND that can be triggered by a CAR. | CAR | Subclass of `DefenseTechnique` from D3FEND ontology. |
| `AttackPattern` | ATT&CK technique that the CAR addresses. | CAR | Subclass of `Technique` from ATT&CK ontology. |
| `Vulnerability` | CVE that may trigger a CAR. | CAR | Subclass of `Vulnerability` from Core ontology. |
| `Asset` | Targeted system or asset. | CAR | Subclass of `Asset` from Core ontology. |

---

## 2. Relationships

| Relationship | Source | Target | STIX Type | Notes |
|--------------|--------|--------|-----------|-------|
| `triggers` | `ResponseHub` | `DefenseTechnique` | `relationship` (`triggers`) | Indicates that executing the response hub activates a defensive technique. |
| `addresses` | `ResponseHub` | `AttackPattern` | `relationship` (`addresses`) | Response hub mitigates or detects a specific ATT&CK technique. |
| `targets` | `ResponseHub` | `Asset` | `relationship` (`targets`) | Response hub is applied to a particular asset. |
| `responds_to` | `ResponseHub` | `Vulnerability` | `relationship` (`responds_to`) | Response hub is triggered by a vulnerability. |
| `has_mass` | `ResponseHub` | `float` | `property` | Mass value representing urgency. |
| `has_energy` | `ResponseHub` | `float` | `property` | Energy value representing resource cost. |
| `maps_to` | `ResponseHub` | `DefenseTechnique` | `relationship` (`maps_to`) | Explicit mapping between CAR and D3FEND. |
| `maps_to` | `ResponseHub` | `AttackPattern` | `relationship` (`maps_to`) | Explicit mapping between CAR and ATT&CK. |

---

## 3. SHACL Constraints (High‑level)

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix car: <http://example.org/car#> .

car:ResponseHubShape a sh:NodeShape ;
    sh:targetClass car:ResponseHub ;
    sh:property [
        sh:path car:has_mass ;
        sh:datatype xsd:float ;
        sh:minInclusive 0 ;
    ] ;
    sh:property [
        sh:path car:has_energy ;
        sh:datatype xsd:float ;
        sh:minInclusive 0 ;
    ] .

car:ContainmentProtocolShape a sh:NodeShape ;
    sh:targetClass car:ContainmentProtocol ;
    sh:property [
        sh:path car:triggers ;
        sh:class car:DefenseTechnique ;
    ] .
```

---

## 4. Example Instance (Turtle)

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

## 5. Usage Notes

* This ontology is **frozen**; new CAR versions should be added as new classes or instances, not by modifying existing ones.
* All identifiers should be the official CAR IDs (e.g., `CAR-001`).
* The ontology intentionally omits temporal, probabilistic, or confidence attributes; those belong in extensions.

---

## 6. References

* CAR Framework: https://example.org/car
* D3FEND: https://d3fend.mitre.org/
* ATT&CK: https://attack.mitre.org/
* STIX 2.1: https://docs.oasis-open.org/cti/stix/v2.1/overview.html

