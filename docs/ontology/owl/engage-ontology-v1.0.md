# ENGAGE Ontology v1.0: Field-by-Field Mapping

## Core Classes & Properties

| Ontology Field         | ENGAGE JSON Field(s)      | Notes / Example Value                  |
|-----------------------|---------------------------|----------------------------------------|
| `sec:EngagementConcept` | EngagementConcepts        | Main node for each ENGAGE concept      |
| `sec:engageId`        | ID                        | "ENGAGE-001"                          |
| `rdfs:label`          | Name                      | "Coordinated Public Attribution"      |
| `sec:description`     | Description               | Text                                   |
| `sec:strategicValue`  | StrategicValue            | "Disrupt adversary operations"        |
| `sec:category`        | Category                  | "Attribution", "Disruption"           |

## Relationships

| Ontology Property      | ENGAGE JSON Field(s)      | Notes                                  |
|-----------------------|---------------------------|----------------------------------------|
| `sec:disrupts`        | DisruptsTechniques        | Links to ATT&CK Technique (Txxxx)      |

## Notes
- The ETL emits all required ENGAGE fields and relationships as RDF triples.
- Handles both direct JSON and activities.json directory input.
- Each EngagementConcept is uniquely identified and linked to disrupted ATT&CK techniques.
