# CWE Ontology v1.0: Field-by-Field Mapping

## Core Classes & Properties

| Ontology Field            | CWE JSON/XML Field(s)           | Notes / Example Value                        |
| ------------------------- | ------------------------------- | -------------------------------------------- |
| `cwe:Weakness`            | Weakness                        | Main node for each CWE entry                 |
| `cwe:Category`            | Category                        | Grouping node (not always present)           |
| `cwe:View`                | View                            | Taxonomy view (not always present)           |
| `cwe:cwe_id`              | ID                              | "CWE-79"                                     |
| `cwe:name`                | Name                            | "Improper Neutralization of Input..."        |
| `cwe:description`         | Description                     | Text                                         |
| `cwe:abstractionLevel`    | WeaknessAbstraction/Abstraction | "Base", "Class", "Variant", "Pillar"         |
| `cwe:status`              | Status                          | "Stable", "Draft", etc.                      |
| `cwe:hasPlatform`         | ApplicablePlatforms             | List of platforms (OS, language, etc.)       |
| `cwe:hasConsequence`      | Consequences                    | List of consequence nodes                    |
| `cwe:hasDetectionMethod`  | DetectionMethods                | List of detection method nodes               |
| `cwe:hasMitigation`       | PotentialMitigations            | List of mitigation nodes                     |
| `cwe:hasReference`        | References                      | List of reference nodes                      |
| `cwe:memberOf`            | MemberOf                        | Category/View membership                     |

## Relationships

| Ontology Property         | CWE JSON/XML Field(s)         | Notes                                        |
|-------------------------- |------------------------------ |--------------------------------------------- |
| `cwe:childOf`             | RelatedWeaknesses (ChildOf)   | Hierarchy                                    |
| `cwe:parentOf`            | RelatedWeaknesses (ParentOf)  | Hierarchy                                    |
| `cwe:peerOf`              | RelatedWeaknesses (PeerOf)    | Sibling relationship                         |
| `cwe:canPrecede`          | RelatedWeaknesses (CanPrecede)| Sequential                                   |
| `cwe:canFollow`           | RelatedWeaknesses (CanFollow) | Sequential                                   |
| `cwe:requires`            | RelatedWeaknesses (Requires)  | Prerequisite                                 |
| `cwe:requiredBy`          | RelatedWeaknesses (RequiredBy)| Prerequisite                                 |
| `cwe:canAlsoBe`           | RelatedWeaknesses (CanAlsoBe) | Alternative classification                   |
| `cwe:startsWith`          | RelatedWeaknesses (StartsWith)| Sequence start                               |
| `cwe:mapsToCAPEC`         | Related_Attack_Patterns       | CAPEC mappings                               |
| `cwe:mapsToVulnerability` | Related_Vulnerabilities       | CVE mappings                                 |
| `cwe:mapsToWASC`          | Related_Weaknesses (WASC)     | WASC mapping                                 |
| `cwe:mapsToOWASP`         | Related_Weaknesses (OWASP)    | OWASP mapping                                |
| `cwe:mapsToCERT`          | Related_Weaknesses (CERT)     | CERT mapping                                 |
| `cwe:mapsToPCI`           | Related_Weaknesses (PCI)      | PCI mapping                                  |
| `cwe:mapsToNVD`           | Related_Weaknesses (NVD)      | NVD mapping                                  |
| `cwe:mapsToCISQ`          | Related_Weaknesses (CISQ)     | CISQ mapping                                 |

## Node Types for Consequence, Mitigation, DetectionMethod, Reference

| Ontology Class            | CWE JSON/XML Field(s)         | Properties                                   |
|-------------------------- |------------------------------ |--------------------------------------------- |
| `cwe:Consequence`         | Consequences                  | `scope`, `impact`                            |
| `cwe:Mitigation`          | PotentialMitigations          | `strategy`, `effectiveness`, `appliesTo`     |
| `cwe:DetectionMethod`     | DetectionMethods              | `method`, `effectiveness`                    |
| `cwe:Reference`           | References                    | `url`, `referenceType`                       |
