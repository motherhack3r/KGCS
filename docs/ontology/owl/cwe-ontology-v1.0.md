# CWE Ontology v1.0 — Consolidated Documentation

This document merges the high-level CWE ontology description with the ETL field mapping required by KGCS.

## Overview

Scope: Core CWE entities and relationships as defined by the CWE standard. Frozen ontology for KGCS use.

## Classes

| Class | Description |
| ----- | ----------- |
| `Weakness` | Individual weakness (e.g., CWE-121) |
| `Category` | Grouping of weaknesses |
| `View` | Taxonomy view |
| `Platform` | Target platform |
| `DetectionMethod` | Technique used to detect a weakness |
| `Mitigation` | Recommended mitigation |
| `Consequence` | Impact of exploitation |

## Relationships

| Relationship | Source | Target |
| ------------ | ------ | ------ |
| `childOf` | Weakness | Weakness |
| `parentOf` | Weakness | Weakness |
| `peerOf` | Weakness | Weakness |
| `mapsTo` | Weakness | CAPEC/CVE/OWASP/etc. |
| `hasMitigation` | Weakness | Mitigation |

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix cwe: <http://example.org/cwe#> .

cwe:WeaknessShape a sh:NodeShape ;
    sh:targetClass cwe:Weakness ;
    sh:property [ sh:path cwe:hasConsequence ; sh:class cwe:Consequence ] ;
    sh:property [ sh:path cwe:hasDetectionMethod ; sh:class cwe:DetectionMethod ] ;
    sh:property [ sh:path cwe:hasMitigation ; sh:class cwe:Mitigation ] .

cwe:CategoryShape a sh:NodeShape ;
    sh:targetClass cwe:Category ;
    sh:property [ sh:path cwe:childOf ; sh:class cwe:Category ] .
```

## Field Mapping (ETL)

| Ontology Field | CWE Field(s) |
| --------------- | ------------- |
| `cwe:cwe_id` | ID (e.g., CWE-79) |
| `cwe:name` | Name |
| `cwe:description` | Description |
| `cwe:abstractionLevel` | WeaknessAbstraction |
| `cwe:status` | Status |
| `cwe:hasPlatform` | ApplicablePlatforms |
| `cwe:hasConsequence` | Consequences |
| `cwe:hasDetectionMethod` | DetectionMethods |
| `cwe:hasMitigation` | PotentialMitigations |

## Example Instance

```turtle
cwe:CWE-121 a cwe:Weakness ;
    cwe:childOf cwe:CWE-787 ;
    cwe:hasConsequence cwe:ConfidentialityImpact ;
    cwe:hasDetectionMethod cwe:StaticAnalysis ;
    cwe:hasMitigation cwe:BoundsChecking ;
    cwe:appliesTo cwe:Implementation ;
    cwe:hasPlatform cwe:Windows ;
    cwe:hasReference cwe:Ref-12345 .
```

---

## References

* <https://cwe.mitre.org/>

---

## Sources

* **MITRE CWE XML (cwec_v4.19.1.xml zipped):** <https://cwe.mitre.org/data/xml/cwec_latest.xml.zip>
* **MITRE CWE SCHEMA:** <https://cwe.mitre.org/data/xsd/cwe_schema_latest.xsd>
* **SHACL shapes:** [cwe-shapes.ttl](../shacl/cwe-shapes.ttl)
* **ETL transformer:** [etl_cwe.py](../../scripts/etl_cwe.py)

* **Local schemas / samples:** `data/cwe/schemas/` (e.g. `cwe_schema_latest.xsd`), `data/cwe/raw/`, `data/cwe/samples/`

Notes: Use the official CWE XML/JSON feed and capture feed version in snapshot metadata.
