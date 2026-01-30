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
