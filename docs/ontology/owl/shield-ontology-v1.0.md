# SHIELD Ontology v1.0: Field-by-Field Mapping

## Core Classes & Properties

| Ontology Field           | SHIELD JSON Field(s)      | Notes / Example Value                  |
|--------------------------|---------------------------|----------------------------------------|
| `sec:DeceptionTechnique` | DeceptionTechniques       | Main node for each SHIELD technique    |
| `sec:shieldId`           | ID                        | "SHIELD-001"                           |
| `rdfs:label`             | Name                      | "Fake Account Indicators"              |
| `sec:description`        | Description               | Text                                   |
| `sec:operationalImpact`  | OperationalImpact         | "Detect", "Disrupt", etc.              |
| `sec:easeOfEmployment`   | EaseOfEmployment          | "Low", "Medium", "High"                |

## Relationships

| Ontology Property        | SHIELD JSON Field(s)      | Notes                                  |
|--------------------------|---------------------------|----------------------------------------|
| `sec:counters`           | CountersTechniques        | Links to ATT&CK Technique (Txxxx)      |

## Notes

- The ETL should emit all required SHIELD fields and relationships as RDF triples.
- Each DeceptionTechnique is uniquely identified and linked to countered ATT&CK techniques.
- OperationalImpact and EaseOfEmployment should be emitted as properties if present.

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix shld: <http://example.org/shield#> .
@prefix attck: <http://example.org/attck#> .

shld:DeceptionTechniqueShape a sh:NodeShape ;
  sh:targetClass shld:DeceptionTechnique ;
  sh:property [ sh:path shld:counters ; sh:class attck:Technique ] .
```

## Example Instance

```turtle
shld:SHIELD-001 a shld:DeceptionTechnique ;
  rdfs:label "Fake Account Indicators" ;
  shld:counters attck:T1566 .
```

## References

- <https://shield.mitre.org/>

---

## Sources

- **Official SHIELD data:** <https://github.com/MITRECND/mitrecnd.github.io/tree/master/_data/>
- **SHACL shapes:** [shield-shapes.ttl](../shacl/shield-shapes.ttl)
- **ETL transformer:** [etl_shield.py](../../scripts/etl_shield.py)


- **Local schemas / samples:** `data/shield/schemas/`, `data/shield/raw/`, `data/shield/samples/`

Notes: Use the ATT&CK/STIX repo for the canonical SHIELD dataset; include commit SHA in snapshot metadata.
