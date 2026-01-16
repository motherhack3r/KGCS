# CWE (Common Weakness Enumeration) Ontology v1.0

**Scope**: Core CWE entities and relationships as defined by the CWE standard. This ontology is a *frozen* representation of the CWE data model, suitable for knowledge graphs, RAG, and reasoning.

---

## 1. Classes

| Class | Description | Source | Notes |
|-------|-------------|--------|-------|
| `Weakness` | Individual weakness entry (e.g., CWE‑121). | CWE | Identified by a unique CWE ID (e.g., `CWE-121`). |
| `Category` | Grouping of weaknesses (e.g., `Buffer Overflows`). | CWE | Subclass of `Weakness` hierarchy. |
| `View` | Perspective or taxonomy view of weaknesses (e.g., `OWASP Top 10`). | CWE | Subclass of `Weakness` hierarchy. |
| `Platform` | Target platform for a weakness (e.g., Windows, Linux). | CWE | Subclass of `Weakness` hierarchy. |
| `DetectionMethod` | Technique used to detect a weakness. | CWE | Subclass of `Weakness` hierarchy. |
| `Mitigation` | Recommended mitigation for a weakness. | CWE | Subclass of `Weakness` hierarchy. |
| `Consequence` | Impact of exploiting a weakness. | CWE | Subclass of `Weakness` hierarchy. |

---

## 2. Relationships

| Relationship | Source | Target | Notes |
|--------------|--------|--------|-------|
| `childOf` | `Weakness` | `Weakness` | Hierarchical relationship (more specific → more general). |
| `parentOf` | `Weakness` | `Weakness` | Inverse of `childOf`. |
| `peerOf` | `Weakness` | `Weakness` | Same abstraction level. |
| `canPrecede` | `Weakness` | `Weakness` | Sequential relationship. |
| `canFollow` | `Weakness` | `Weakness` | Sequential relationship. |
| `requiredBy` | `Weakness` | `Weakness` | Compositional relationship. |
| `requires` | `Weakness` | `Weakness` | Compositional relationship. |
| `canAlsoBe` | `Weakness` | `Weakness` | Alternative classification. |
| `startsWith` | `Weakness` | `Weakness` | Sequential relationship. |
| `mapsTo` | `Weakness` | `CAPEC` | Taxonomy mapping. |
| `mapsTo` | `Weakness` | `WASC` | Taxonomy mapping. |
| `mapsTo` | `Weakness` | `OWASP` | Taxonomy mapping. |
| `mapsTo` | `Weakness` | `CERT` | Taxonomy mapping. |
| `mapsTo` | `Weakness` | `PCI` | Taxonomy mapping. |
| `mapsTo` | `Weakness` | `NVD` | Taxonomy mapping. |
| `mapsTo` | `Weakness` | `CISQ` | Taxonomy mapping. |
| `hasConsequence` | `Weakness` | `Consequence` | Impact of exploitation. |
| `hasDetectionMethod` | `Weakness` | `DetectionMethod` | How to detect. |
| `hasMitigation` | `Weakness` | `Mitigation` | How to mitigate. |
| `appliesTo` | `Mitigation` | `Phase` | Development lifecycle phase. |
| `hasPlatform` | `Weakness` | `Platform` | Target platform. |
| `hasReference` | `Weakness` | `Reference` | External reference. |

---

## 3. SHACL Constraints (High‑level)

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix cwe: <http://example.org/cwe#> .

cwe:WeaknessShape a sh:NodeShape ;
    sh:targetClass cwe:Weakness ;
    sh:property [
        sh:path cwe:hasConsequence ;
        sh:class cwe:Consequence ;
    ] ;
    sh:property [
        sh:path cwe:hasDetectionMethod ;
        sh:class cwe:DetectionMethod ;
    ] ;
    sh:property [
        sh:path cwe:hasMitigation ;
        sh:class cwe:Mitigation ;
    ] .

cwe:CategoryShape a sh:NodeShape ;
    sh:targetClass cwe:Category ;
    sh:property [
        sh:path cwe:childOf ;
        sh:class cwe:Category ;
    ] .
```

---

## 4. Example Instance (Turtle)

```turtle
cwe:CWE-121 a cwe:Weakness ;
    cwe:childOf cwe:CWE-787 ;
    cwe:hasConsequence cwe:ConfidentialityImpact ;
    cwe:hasDetectionMethod cwe:StaticAnalysis ;
    cwe:hasMitigation cwe:BoundsChecking ;
    cwe:appliesTo cwe:Implementation ;
    cwe:hasPlatform cwe:Windows ;
    cwe:hasReference cwe:Ref-12345 .

cwe:ConfidentialityImpact a cwe:Consequence ;
    cwe:scope "Confidentiality" ;
    cwe:impact "High" .

cwe:StaticAnalysis a cwe:DetectionMethod ;
    cwe:method "Static Code Analysis" ;
    cwe:effectiveness "High" .

cwe:BoundsChecking a cwe:Mitigation ;
    cwe:strategy "Bounds Checking" ;
    cwe:effectiveness "High" .
```

---

## 5. Usage Notes

* This ontology is **frozen**; new CWE entries should be added as new instances, not by modifying existing ones.
* All identifiers should be the official CWE IDs (e.g., `CWE-121`).
* The ontology intentionally omits temporal, probabilistic, or confidence attributes; those belong in extensions.

---

## 6. References

* CWE: https://cwe.mitre.org/
* CAPEC: https://capec.mitre.org/
* WASC: https://wasc.org/
* OWASP Top 10: https://owasp.org/www-project-top-10/
* CERT: https://cert.org/
* PCI DSS: https://www.pcisecuritystandards.org/
* NVD: https://nvd.nist.gov/
* CISQ: https://www.cisq.org/

