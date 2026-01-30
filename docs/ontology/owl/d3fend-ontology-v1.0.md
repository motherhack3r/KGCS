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
