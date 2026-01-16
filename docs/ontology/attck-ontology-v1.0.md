# ATT&CK Ontology v1.0

**Scope**: Core ATT&CK entities and relationships as defined by the MITRE ATT&CK framework. This ontology is intended to be a *frozen* representation of the ATT&CK data model, suitable for use in knowledge graphs, RAG, and reasoning.

---

## 1. Classes

| Class | Description | Source | Notes |
|-------|-------------|--------|-------|
| `Tactic` | High‑level objective of an adversary (e.g., Initial Access, Execution). | ATT&CK | Identified by `x-mitre-tactic` STIX objects. |
| `Technique` | Concrete adversary action that achieves a tactic. | ATT&CK | Represented by `attack-pattern` STIX objects where `x_mitre_is_subtechnique = false`. |
| `SubTechnique` | Granular variation of a technique. | ATT&CK | Represented by `attack-pattern` STIX objects where `x_mitre_is_subtechnique = true`. |
| `Group` | Adversary group or intrusion set. | ATT&CK | Represented by `intrusion-set` STIX objects. |
| `Software` | Malware or tool used by a group. | ATT&CK | Represented by `malware` or `tool` STIX objects. |
| `DataSource` | Source of observable data (e.g., Windows Event Log). | ATT&CK | Represented by `x-mitre-data-source` STIX objects. |
| `DataComponent` | Specific data element within a data source. | ATT&CK | Represented by `x-mitre-data-component` STIX objects. |
| `Asset` | Targeted asset or system. | ATT&CK | Represented by `x-mitre-asset` STIX objects. |

---

## 2. Relationships

| Relationship | Source | Target | STIX Type | Notes |
|--------------|--------|--------|-----------|-------|
| `contains` | `Tactic` | `Technique` | `relationship` (`tactic-contains`) | Indicates that a tactic includes one or more techniques. |
| `subtechnique_of` | `SubTechnique` | `Technique` | `relationship` (`subtechnique-of`) | Indicates that a sub‑technique is a specialization of a technique. |
| `uses` | `Group` | `Software` | `relationship` (`uses`) | Group uses a software. |
| `uses` | `Group` | `Technique` | `relationship` (`uses`) | Group uses a technique. |
| `uses` | `Software` | `Technique` | `relationship` (`uses`) | Software uses a technique. |
| `detects` | `DataComponent` | `Technique` | `relationship` (`detects`) | Data component can detect a technique. |
| `targets` | `Technique` | `Asset` | `relationship` (`targets`) | Technique targets an asset. |
| `has_data_source` | `Technique` | `DataSource` | `relationship` (`has-data-source`) | Technique can be detected using a data source. |
| `has_data_component` | `Technique` | `DataComponent` | `relationship` (`has-data-component`) | Technique can be detected using a data component. |

---

## 3. SHACL Constraints (High‑level)

The following SHACL shapes enforce core constraints on the ATT&CK ontology. They are expressed in Turtle syntax and can be used with any SHACL validator.

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/attck#> .

ex:TacticShape a sh:NodeShape ;
    sh:targetClass ex:Tactic ;
    sh:property [
        sh:path ex:contains ;
        sh:class ex:Technique ;
        sh:minCount 1 ;
    ] .

ex:TechniqueShape a sh:NodeShape ;
    sh:targetClass ex:Technique ;
    sh:property [
        sh:path ex:subtechnique_of ;
        sh:class ex:Technique ;
        sh:maxCount 1 ;
    ] .

ex:GroupShape a sh:NodeShape ;
    sh:targetClass ex:Group ;
    sh:property [
        sh:path ex:uses ;
        sh:class ex:Software ;
    ] ;
    sh:property [
        sh:path ex:uses ;
        sh:class ex:Technique ;
    ] .
```

---

## 4. Example Instance (Turtle)

```turtle
ex:TA0001 a ex:Tactic ;
    ex:contains ex:T1059 .

ex:T1059 a ex:Technique ;
    ex:subtechnique_of ex:T1059.001 ;
    ex:targets ex:WindowsServer .

ex:T1059.001 a ex:SubTechnique ;
    ex:subtechnique_of ex:T1059 .

ex:GroupA a ex:Group ;
    ex:uses ex:MalwareX , ex:T1059 .
```

---

## 5. Usage Notes

* This ontology is **frozen**; new ATT&CK versions should be added as new classes or instances, not by modifying existing ones.
* All identifiers should be the official ATT&CK IDs (e.g., `T1059`, `TA0001`).
* The ontology intentionally omits temporal, probabilistic, or confidence attributes; those belong in extensions.

---

## 6. References

* MITRE ATT&CK: https://attack.mitre.org/
* STIX 2.1: https://docs.oasis-open.org/cti/stix/v2.1/overview.html

