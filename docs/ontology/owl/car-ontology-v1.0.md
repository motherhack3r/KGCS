# CAR Ontology v1.0: Field-by-Field Mapping

## Core Classes & Properties

| Ontology Field           | CAR YAML Field(s)         | Notes / Example Value                  |
|-------------------------|---------------------------|----------------------------------------|
| `sec:DetectionAnalytic` | DetectionAnalytics/analytics | Main node for each CAR analytic     |
| `sec:carId`             | id, ID, carId, car_id, analytic_id, analyticId | "CAR-2013-10-002" |
| `rdfs:label`            | name, Name, title, Title  | "Create Remote Process"                |
| `sec:description`       | description, Description, summary, Summary | Text                    |
| `sec:status`            | status, Status            | "Stable", "Beta", etc.                |
| `sec:tag`               | tags, Tags                | List of tags/keywords                  |
| `sec:platform`          | platform, Platform        | "Windows", "Linux", etc.               |

## Relationships

| Ontology Property        | CAR YAML Field(s)         | Notes                                  |
|-------------------------|---------------------------|----------------------------------------|
| `sec:detects`           | techniques, DetectsTechniques, detects_techniques, etc. | Links to ATT&CK Technique (Txxxx) |
| `sec:requires`          | data_sources, DataSources, dataSources, dataSource | Links to DataSource node         |
| `sec:reference`         | references, References    | List of reference nodes                |

## Reference Node Properties

| Ontology Class          | CAR YAML Field(s)         | Properties                             |
|------------------------|---------------------------|----------------------------------------|
| `sec:Reference`        | references, References    | `url`, `referenceType`                 |

## Notes
- The ETL should emit all required CAR fields and relationships as RDF triples.
- Handles multiple field name variants and YAML input structures.
- Each DetectionAnalytic is uniquely identified and linked to detected ATT&CK techniques, required data sources, platforms, tags, status, and references.
- Tags and status should be emitted as properties if present.
