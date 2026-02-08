# ENGAGE Ontology v1.0: Field-by-Field Mapping

## Core Classes & Properties

| Ontology Field | ENGAGE JSON Field(s) | Notes / Example Value |
| --- | --- | --- |
| `sec:EngagementConcept` | EngagementConcepts | Main node for each ENGAGE concept |
| `sec:engageId` | ID | "ENGAGE-001" |
| `rdfs:label` | Name | "Coordinated Public Attribution" |
| `sec:description` | Description | Text |
| `sec:strategicValue` | StrategicValue | "Disrupt adversary operations" |
| `sec:category` | Category | "Attribution", "Disruption" |

## Relationships

| Ontology Property | ENGAGE JSON Field(s) | Notes |
| --- | --- | --- |
| `sec:disrupts` | DisruptsTechniques | Links to ATT&CK Technique (Txxxx) |

## Notes

- The ETL emits all required ENGAGE fields and relationships as RDF triples.
- Handles both direct JSON and activities.json directory input.
- Each EngagementConcept is uniquely identified and linked to disrupted ATT&CK techniques.

## SHACL — High Level

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix eng: <http://example.org/engage#> .
@prefix attck: <http://example.org/attck#> .

eng:EngagementConceptShape a sh:NodeShape ;
  sh:targetClass eng:EngagementConcept ;
  sh:property [ sh:path eng:disrupts ; sh:class attck:Technique ] .
```

## Example Instance

```turtle
eng:ENGAGE-001 a eng:EngagementConcept ;
  rdfs:label "Coordinated Public Attribution" ;
  eng:disrupts attck:T1059 .
```

## References

- <https://example.org/engage>

---

## Sources

- **Official ENGAGE JSON:** <https://github.com/mitre/engage/tree/main/Data/json/>
- **SHACL shapes:** [engage-shapes.ttl](../shacl/engage-shapes.ttl)
- **ETL transformer:** [etl_engage.py](../../scripts/etl_engage.py)

- **Local schemas / samples:** `data/engage/schemas/`, `data/engage/raw/`, `data/engage/samples/`

Notes: Use the ENGAGE feed for canonical IDs; include feed version in `.meta.json` snapshots.
