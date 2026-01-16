# CAPEC (Common Attack Pattern Enumeration and Classification) Ontology v1.0

**Scope**: Core CAPEC entities and relationships as defined by the CAPEC standard. This ontology is a *frozen* representation of the CAPEC data model, suitable for knowledge graphs, RAG, and reasoning.

---

## 1. Classes

| Class | Description | Source | Notes |
| ------- | ------------- | -------- | ------- |
| `AttackPattern` | Individual attack pattern (e.g., CAPEC‑130). | CAPEC | Identified by a unique CAPEC ID (e.g., `CAPEC-130`). |
| `Category` | Grouping of attack patterns based on common characteristics. | CAPEC | Subclass of `AttackPattern` hierarchy. |
| `View` | Perspective or slice of the CAPEC catalog (e.g., graph view). | CAPEC | Subclass of `AttackPattern` hierarchy. |
| `ExternalReference` | External resource that provides additional information about an attack pattern. | CAPEC | Subclass of `AttackPattern` hierarchy. |
| `Weakness` | CWE weakness that is related to an attack pattern. | CAPEC | Relationship `relatedWeakness`. |
| `Technique` | ATT&CK technique that an attack pattern can map to. | CAPEC | Relationship `mapsTo`. |

---

## 2. Relationships

| Relationship | Source | Target | Notes |
| ------------ | ------ | ------ | ----- |
| `childOf` | `AttackPattern` | `AttackPattern` | Hierarchical relationship (more specific → more general). |
| `parentOf` | `AttackPattern` | `AttackPattern` | Inverse of `childOf`. |
| `peerOf` | `AttackPattern` | `AttackPattern` | Same abstraction level. |
| `canPrecede` | `AttackPattern` | `AttackPattern` | Sequential relationship. |
| `canFollow` | `AttackPattern` | `AttackPattern` | Sequential relationship. |
| `canAlsoBe` | `AttackPattern` | `AttackPattern` | Alternative classification. |
| `mapsTo` | `AttackPattern` | `Technique` | Maps an attack pattern to an ATT&CK technique. |
| `mapsTo` | `AttackPattern` | `Weakness` | Maps an attack pattern to a CWE weakness. |
| `hasExternalReference` | `AttackPattern` | `ExternalReference` | Link to external documentation. |
| `hasCategory` | `AttackPattern` | `Category` | Membership in a category. |
| `hasView` | `AttackPattern` | `View` | Membership in a view. |
| `hasRelatedWeakness` | `AttackPattern` | `Weakness` | Indicates a weakness that can be exploited by the pattern. |

---

## 3. SHACL Constraints (High‑level)

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix capec: <http://example.org/capec#> .

capec:AttackPatternShape a sh:NodeShape ;
    sh:targetClass capec:AttackPattern ;
    sh:property [
        sh:path capec:childOf ;
        sh:class capec:AttackPattern ;
    ] ;
    sh:property [
        sh:path capec:mapsTo ;
        sh:class capec:Technique ;
    ] ;
    sh:property [
        sh:path capec:hasExternalReference ;
        sh:class capec:ExternalReference ;
    ] .

capec:CategoryShape a sh:NodeShape ;
    sh:targetClass capec:Category ;
    sh:property [
        sh:path capec:hasMember ;
        sh:class capec:AttackPattern ;
    ] .
```

---

## 4. Example Instance (Turtle)

```turtle
capec:CAPEC-130 a capec:AttackPattern ;
    capec:childOf capec:CAPEC-100 ;
    capec:mapsTo attck:T1059 ;
    capec:hasExternalReference capec:ExtRef-001 ;
    capec:hasCategory capec:Cat-01 ;
    capec:hasView capec:View-Graph ;
    capec:hasRelatedWeakness cwe:CWE-787 .

capec:Cat-01 a capec:Category ;
    capec:hasMember capec:CAPEC-130 .

capec:View-Graph a capec:View ;
    capec:hasMember capec:CAPEC-130 .

capec:ExtRef-001 a capec:ExternalReference ;
    capec:hasTitle "CAPEC 130 – Excessive Allocation" ;
    capec:hasURL "https://capec.mitre.org/data/definitions/130.html" .
```

---

## 5. Usage Notes

* This ontology is **frozen**; new CAPEC entries should be added as new instances, not by modifying existing ones.
* All identifiers should be the official CAPEC IDs (e.g., `CAPEC-130`).
* The ontology intentionally omits temporal, probabilistic, or confidence attributes; those belong in extensions.

---

## 6. References

* CAPEC: <https://capec.mitre.org/>
* ATT&CK: <https://attack.mitre.org/>
* CWE: <https://cwe.mitre.org/>
