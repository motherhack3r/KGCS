# D3FEND Ontology v1.0: Field-by-Field Mapping

## Core Classes & Properties

| Ontology Field            | D3FEND JSON Field(s)       | Notes / Example Value                   |
| ------------------------- | -------------------------- | --------------------------------------- |
| `sec:DefensiveTechnique`  | DefensiveTechniques        | Main node for each D3FEND technique     |
| `sec:d3fendId`            | ID                         | "D3FEND-001"                            |
| `rdfs:label`              | Name                       | "Process Hollowing Mitigation"          |
| `sec:description`         | Description                | Text                                    |
| `sec:status`              | Status                     | "Stable", "Beta", etc.                  |
| `sec:tag`                 | Tags                       | List of tags/keywords                   |

## Relationships

| Ontology Property        | D3FEND JSON Field(s)      | Notes                                  |
|--------------------------|---------------------------|----------------------------------------|
| `sec:childOf`            | ParentID                  | Hierarchy (child → parent)             |
| `sec:parentOf`           | ParentID                  | Hierarchy (parent → child, inverse)    |
| `sec:mitigates`          | MitigatesTechniques       | Links to ATT&CK Technique (Txxxx)      |
| `sec:references`         | References                | List of reference nodes                |

## Reference Node Properties

| Ontology Class          | D3FEND JSON Field(s)      | Properties                             |
|-------------------------|---------------------------|----------------------------------------|
| `sec:Reference`         | References                | `url`, `referenceType`                 |

## Notes

- The ETL should emit all required D3FEND fields and relationships as RDF triples.
- Handles both MITRE JSON and JSON-LD (@graph) input formats.
- Each DefensiveTechnique is uniquely identified and linked to mitigated ATT&CK techniques, parent/child techniques, and references.
- Tags and status should be emitted as properties if present.

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix d3f: <http://example.org/d3fend#> .
@prefix attck: <http://example.org/attck#> .

d3f:DefensiveTechniqueShape a sh:NodeShape ;
  sh:targetClass d3f:DefensiveTechnique ;
  sh:property [ sh:path d3f:mitigates ; sh:class attck:Technique ] .
```

## Example Instance

```turtle
d3f:D3FEND-001 a d3f:DefensiveTechnique ;
  rdfs:label "Firewall Rule" ;
  d3f:mitigates attck:T1059 .
```

## References

- <https://d3fend.mitre.org/>

---

## Sources

- **Official D3FEND JSON:** https://raw.githubusercontent.com/d3fend/d3fend/master/d3fend.json
- **SHACL shapes:** [d3fend-shapes.ttl](../shacl/d3fend-shapes.ttl)
- **ETL transformer:** [etl_d3fend.py](../../scripts/etl_d3fend.py)

 - **Local schemas / samples:** `data/d3fend/schemas/`, `data/d3fend/raw/`, `data/d3fend/samples/`

Notes: Use the official D3FEND JSON as the authoritative source; include the commit SHA in snapshot metadata.
