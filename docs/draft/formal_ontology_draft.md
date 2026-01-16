# Formal Ontology for Cybersecurity Data Integration

- [Formal Ontology for Cybersecurity Data Integration](#formal-ontology-for-cybersecurity-data-integration)
  - [1. Formal Ontology Tables](#1-formal-ontology-tables)
    - [Class Table](#class-table)
    - [Edge Table](#edge-table)
  - [2. Mermaid Diagram (Authoritative Core)](#2-mermaid-diagram-authoritative-core)
  - [3. OWL (Turtle) Skeleton](#3-owl-turtle-skeleton)
  - [4. Neo4j Cypher Schema (Node \& Relationship Labels)](#4-neo4j-cypher-schema-node--relationship-labels)

## 1. Formal Ontology Tables  

### Class Table

| **Class** | **Namespace** | **JSON Source** | **Key Properties** | **Notes** |
| --------- | ------------- | --------------- | ------------------ | --------- |
| `Platform` | `sec:Platform` | NVD CPE Dictionary | `cpe_uri`, `part`, `vendor`, `product`, `version`, `deprecated` | 1‑1 mapping |
| `PlatformConfiguration` | `sec:PlatformConfiguration` | NVD CVE `configurations` | `config_id`, `criteria` | Holds logical expressions |
| `Vulnerability` | `sec:Vulnerability` | NVD CVE `cve.id` | `cve_id`, `descriptions`, `published`, `lastModified`, `vulnStatus`, `cisa_*`, `tags` | 1‑1 mapping |
| `VulnerabilityScore` | `sec:VulnerabilityScore` | CVSS metrics | `vectorString`, `baseScore`, `version` | Separate node per CVSS version |
| `Reference` | `sec:Reference` | `cve.references` | `url`, `description`, `source` | 1‑1 mapping |
| `Weakness` | `sec:Weakness` | CWE JSON `ID` | `cwe_id`, `name`, `description`, `status` | 1‑1 mapping |
| `AttackPattern` | `sec:AttackPattern` | CAPEC JSON `ID` | `capec_id`, `name`, `description`, `severity` | 1‑1 mapping |
| `Technique` | `sec:Technique` | ATT&CK STIX `attack-pattern` | `technique_id`, `name`, `description` | 1‑1 mapping |
| `SubTechnique` | `sec:SubTechnique` | ATT&CK STIX `attack-pattern` with `x_mitre_is_subtechnique=true` | `subtechnique_id`, `parent_id` | 1‑1 mapping |
| `Tactic` | `sec:Tactic` | ATT&CK STIX `x-mitre-tactic` | `tactic_id`, `name` | 1‑1 mapping |
| `DefensiveTechnique` | `sec:DefensiveTechnique` | D3FEND STIX `course-of-action` | `deftech_id`, `name` | 1‑1 mapping |
| `DetectionAnalytic` | `sec:DetectionAnalytic` | CAR JSON `id` | `car_id`, `name` | 1‑1 mapping |
| `DeceptionTechnique` | `sec:DeceptionTechnique` | SHIELD STIX `attack-pattern` | `shield_id`, `name` | 1‑1 mapping |
| `EngagementConcept` | `sec:EngagementConcept` | ENGAGE docs | `engage_id`, `name` | 1‑1 mapping |

### Edge Table

| **Edge** | **From** | **To** | **JSON Source** | **Provenance** |
| -------- | -------- | ------ | --------------- | -------------- |
| `affected_by` | `PlatformConfiguration` | `Vulnerability` | `configurations.nodes[].cpeMatch[].criteria` | NVD |
| `affects` | `Vulnerability` | `PlatformConfiguration` | inverse of `affected_by` | NVD |
| `scored_by` | `Vulnerability` | `VulnerabilityScore` | `metrics.cvssMetric*` | CVSS |
| `references` | `Vulnerability` | `Reference` | `cve.references` | NVD |
| `caused_by` | `Vulnerability` | `Weakness` | `cve.weaknesses[].description[].value` | NVD |
| `exploited_by` | `Weakness` | `AttackPattern` | `Related_Weaknesses` | CAPEC |
| `implemented_as` | `AttackPattern` | `Technique` | `CAPEC → ATT&CK` mapping | MITRE |
| `belongs_to` | `Technique` | `Tactic` | `kill_chain_phases.phase_name` | ATT&CK |
| `subtechnique_of` | `SubTechnique` | `Technique` | `x_mitre_is_subtechnique` | ATT&CK |
| `mitigated_by` | `Technique` | `DefensiveTechnique` | `relationship: mitigates` | D3FEND |
| `detected_by` | `Technique` | `DetectionAnalytic` | `techniques[]` in CAR | CAR |
| `countered_by` | `Technique` | `DeceptionTechnique` | SHIELD mapping | SHIELD |
| `targets` | `EngagementConcept` | `Group` | ENGAGE docs | ENGAGE |
| `disrupts` | `EngagementConcept` | `Technique` | ENGAGE docs | ENGAGE |

> **Note**: All edges are *authoritative* – they can be derived directly from the source JSON or STIX relationships.

---

## 2. Mermaid Diagram (Authoritative Core)

```mermaid
graph LR
  %% Classes
  subgraph Platform
    P[Platform]:::class
    PC[PlatformConfiguration]:::class
  end
  subgraph Vulnerability
    V[Vulnerability]:::class
    VS[VulnerabilityScore]:::class
    R[Reference]:::class
  end
  subgraph Weakness
    W[Weakness]:::class
  end
  subgraph AttackPattern
    AP[AttackPattern]:::class
  end
  subgraph Technique
    T[Technique]:::class
    ST[SubTechnique]:::class
    TA[Tactic]:::class
  end
  subgraph Defense
    DT[DefensiveTechnique]:::class
    DA[DetectionAnalytic]:::class
    DTc[DeceptionTechnique]:::class
  end
  subgraph Engagement
    EC[EngagementConcept]:::class
  end

  %% Edges
  PC -->|affected_by| V
  V -->|affects| PC
  V -->|scored_by| VS
  V -->|references| R
  V -->|caused_by| W
  W -->|exploited_by| AP
  AP -->|implemented_as| T
  T -->|belongs_to| TA
  ST -->|subtechnique_of| T
  T -->|mitigated_by| DT
  T -->|detected_by| DA
  T -->|countered_by| DTc
  EC -->|targets| Group
  EC -->|disrupts| T

  classDef class fill:#f9f9f9,stroke:#333,stroke-width:1px;
```

---

## 3. OWL (Turtle) Skeleton

```turtle
@prefix sec: <http://example.org/sec#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

sec:Platform a owl:Class .
sec:PlatformConfiguration a owl:Class .
sec:Vulnerability a owl:Class .
sec:VulnerabilityScore a owl:Class .
sec:Reference a owl:Class .
sec:Weakness a owl:Class .
sec:AttackPattern a owl:Class .
sec:Technique a owl:Class .
sec:SubTechnique a owl:Class .
sec:Tactic a owl:Class .
sec:DefensiveTechnique a owl:Class .
sec:DetectionAnalytic a owl:Class .
sec:DeceptionTechnique a owl:Class .
sec:EngagementConcept a owl:Class .

# Properties
sec:affected_by a owl:ObjectProperty ;
    rdfs:domain sec:PlatformConfiguration ;
    rdfs:range sec:Vulnerability .

sec:affects a owl:ObjectProperty ;
    rdfs:domain sec:Vulnerability ;
    rdfs:range sec:PlatformConfiguration .

sec:scored_by a owl:ObjectProperty ;
    rdfs:domain sec:Vulnerability ;
    rdfs:range sec:VulnerabilityScore .

sec:references a owl:ObjectProperty ;
    rdfs:domain sec:Vulnerability ;
    rdfs:range sec:Reference .

sec:caused_by a owl:ObjectProperty ;
    rdfs:domain sec:Vulnerability ;
    rdfs:range sec:Weakness .

sec:exploited_by a owl:ObjectProperty ;
    rdfs:domain sec:Weakness ;
    rdfs:range sec:AttackPattern .

sec:implemented_as a owl:ObjectProperty ;
    rdfs:domain sec:AttackPattern ;
    rdfs:range sec:Technique .

sec:belongs_to a owl:ObjectProperty ;
    rdfs:domain sec:Technique ;
    rdfs:range sec:Tactic .

sec:subtechnique_of a owl:ObjectProperty ;
    rdfs:domain sec:SubTechnique ;
    rdfs:range sec:Technique .

sec:mitigated_by a owl:ObjectProperty ;
    rdfs:domain sec:Technique ;
    rdfs:range sec:DefensiveTechnique .

sec:detected_by a owl:ObjectProperty ;
    rdfs:domain sec:Technique ;
    rdfs:range sec:DetectionAnalytic .

sec:countered_by a owl:ObjectProperty ;
    rdfs:domain sec:Technique ;
    rdfs:range sec:DeceptionTechnique .

sec:targets a owl:ObjectProperty ;
    rdfs:domain sec:EngagementConcept ;
    rdfs:range sec:Group .

sec:disrupts a owl:ObjectProperty ;
    rdfs:domain sec:EngagementConcept ;
    rdfs:range sec:Technique .
```

---

## 4. Neo4j Cypher Schema (Node & Relationship Labels)

```cypher
// Node labels
CREATE CONSTRAINT ON (p:Platform) ASSERT p.cpe_uri IS UNIQUE;
CREATE CONSTRAINT ON (pc:PlatformConfiguration) ASSERT pc.config_id IS UNIQUE;
CREATE CONSTRAINT ON (v:Vulnerability) ASSERT v.cve_id IS UNIQUE;
CREATE CONSTRAINT ON (vs:VulnerabilityScore) ASSERT vs.vectorString IS UNIQUE;
CREATE CONSTRAINT ON (r:Reference) ASSERT r.url IS UNIQUE;
CREATE CONSTRAINT ON (w:Weakness) ASSERT w.cwe_id IS UNIQUE;
CREATE CONSTRAINT ON (ap:AttackPattern) ASSERT ap.capec_id IS UNIQUE;
CREATE CONSTRAINT ON (t:Technique) ASSERT t.technique_id IS UNIQUE;
CREATE CONSTRAINT ON (st:SubTechnique) ASSERT st.subtechnique_id IS UNIQUE;
CREATE CONSTRAINT ON (ta:Tactic) ASSERT ta.tactic_id IS UNIQUE;
CREATE CONSTRAINT ON (dt:DefensiveTechnique) ASSERT dt.deftech_id IS UNIQUE;
CREATE CONSTRAINT ON (da:DetectionAnalytic) ASSERT da.car_id IS UNIQUE;
CREATE CONSTRAINT ON (dc:DeceptionTechnique) ASSERT dc.shield_id IS UNIQUE;
CREATE CONSTRAINT ON (ec:EngagementConcept) ASSERT ec.engage_id IS UNIQUE;

// Relationship types
// (PlatformConfiguration)-[:AFFECTED_BY]->(Vulnerability)
CREATE CONSTRAINT ON ()-[r:AFFECTED_BY]->() ASSERT exists(r.criteria);

// (Vulnerability)-[:SCORDED_BY]->(VulnerabilityScore)
CREATE CONSTRAINT ON ()-[r:SCORDED_BY]->() ASSERT exists(r.vectorString);

// (Vulnerability)-[:REFERENCES]->(Reference)
CREATE CONSTRAINT ON ()-[r:REFERENCES]->() ASSERT exists(r.url);

// (Vulnerability)-[:CAUSED_BY]->(Weakness)
CREATE CONSTRAINT ON ()-[r:CAUSED_BY]->() ASSERT exists(r.cwe_id);

// (Weakness)-[:EXPLOITED_BY]->(AttackPattern)
CREATE CONSTRAINT ON ()-[r:EXPLOITED_BY]->() ASSERT exists(r.capec_id);

// (AttackPattern)-[:IMPLEMENTED_AS]->(Technique)
CREATE CONSTRAINT ON ()-[r:IMPLEMENTED_AS]->() ASSERT exists(r.technique_id);

// (Technique)-[:BELONGS_TO]->(Tactic)
CREATE CONSTRAINT ON ()-[r:BELONGS_TO]->() ASSERT exists(r.tactic_id);

// (SubTechnique)-[:SUBTECHNIQUE_OF]->(Technique)
CREATE CONSTRAINT ON ()-[r:SUBTECHNIQUE_OF]->() ASSERT exists(r.technique_id);

// (Technique)-[:MITIGATED_BY]->(DefensiveTechnique)
CREATE CONSTRAINT ON ()-[r:MITIGATED_BY]->() ASSERT exists(r.deftech_id);

// (Technique)-[:DETECTED_BY]->(DetectionAnalytic)
CREATE CONSTRAINT ON ()-[r:DETECTED_BY]->() ASSERT exists(r.car_id);

// (Technique)-[:COUNTERED_BY]->(DeceptionTechnique)
CREATE CONSTRAINT ON ()-[r:COUNTERED_BY]->() ASSERT exists(r.shield_id);

// (EngagementConcept)-[:TARGETS]->(Group)
CREATE CONSTRAINT ON ()-[r:TARGETS]->() ASSERT exists(r.group_id);

// (EngagementConcept)-[:DISRUPTS]->(Technique)
CREATE CONSTRAINT ON ()-[r:DISRUPTS]->() ASSERT exists(r.technique_id);
```

---

