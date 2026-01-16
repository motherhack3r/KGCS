Below is the **formalized Risk Extension**, designed specifically for **decision-making and prioritization**, while **preserving the immutability and objectivity of Core Ontology v1.0**.

This extension is **where subjectivity is allowed**—but *only here*.

---

# ⚖️ Risk Ontology Extension v1.0

**(Decision & Prioritization Layer)**

**Status:** Stable
**Depends on:** Core Ontology v1.0
**Temporal:** YES
**Subjective:** YES (explicitly contained)
**Audience:** GRC, security leadership, risk committees, automated prioritization engines

---

## 1. Purpose & Design Contract

### What this extension exists for

* Decide **what matters most**
* Compare **security options**
* Support **accept / mitigate / transfer / avoid** decisions
* Contextualize Core facts with **business reality**

### What it never does

* Never alters CVSS, CWE, or ATT&CK semantics
* Never overwrites Core severity
* Never claims factual truth—only *assessment*

> **Golden Rule**
> Risk is **contextual and opinionated**.
> Core knowledge is **absolute and factual**.

---

## 2. Conceptual Boundary

```
Core Ontology  →  “What exists”
Incident Ext  →  “What happened”
Risk Ext      →  “What should we do”
```

No other extension is allowed to answer *“what should we do?”*

---

## 3. Core Classes (Risk Extension)

### 3.1 RiskAssessment

> Top-level decision artifact

| Property          | Type     | Notes                                |
| ----------------- | -------- | ------------------------------------ |
| `risk_id`         | string   | Unique                               |
| `assessment_date` | datetime | Required                             |
| `scope`           | string   | Asset / system / org                 |
| `assessor`        | string   | Human or system                      |
| `methodology`     | enum     | FAIR / ISO27005 / CUSTOM             |
| `decision`        | enum     | ACCEPT / MITIGATE / TRANSFER / AVOID |
| `review_date`     | datetime | Optional                             |

---

### 3.2 RiskScenario

> **Atomic unit of reasoning**

| Property           | Type   | Notes                 |
| ------------------ | ------ | --------------------- |
| `scenario_id`      | string | Unique                |
| `description`      | string | Human-readable        |
| `assumption_level` | enum   | LOW / MEDIUM / HIGH   |
| `time_horizon`     | enum   | SHORT / MEDIUM / LONG |

---

### 3.3 Likelihood

| Property        | Type   | Notes                       |
| --------------- | ------ | --------------------------- |
| `likelihood_id` | string | Unique                      |
| `value`         | float  | Normalized (0–1)            |
| `scale`         | string | Qualitative or quantitative |
| `rationale`     | string | Mandatory                   |

---

### 3.4 Impact

| Property    | Type   | Notes                                          |
| ----------- | ------ | ---------------------------------------------- |
| `impact_id` | string | Unique                                         |
| `category`  | enum   | FINANCIAL / OPERATIONAL / LEGAL / REPUTATIONAL |
| `value`     | float  | Normalized                                     |
| `unit`      | string | $, hours, score                                |
| `rationale` | string | Mandatory                                      |

---

### 3.5 RiskScore

> **Derived, not authoritative**

| Property        | Type   | Notes      |
| --------------- | ------ | ---------- |
| `score_id`      | string | Unique     |
| `formula`       | string | e.g. L × I |
| `value`         | float  | Result     |
| `normalization` | string | Optional   |

---

### 3.6 Control

> Business-facing abstraction of mitigation

| Property        | Type   | Notes                               |
| --------------- | ------ | ----------------------------------- |
| `control_id`    | string | Unique                              |
| `control_type`  | enum   | PREVENTIVE / DETECTIVE / CORRECTIVE |
| `status`        | enum   | PLANNED / IMPLEMENTED / DEFERRED    |
| `cost`          | float  | Optional                            |
| `effectiveness` | enum   | LOW / MEDIUM / HIGH                 |

---

## 4. Authoritative Relationships

### 4.1 Assessment Structure

```
RiskAssessment ── evaluates ──▶ RiskScenario
RiskAssessment ── produces ──▶ RiskScore
```

---

### 4.2 Scenario Composition (Core Anchors)

```
RiskScenario ── involves ──▶ Asset
RiskScenario ── considers ──▶ Vulnerability   (Core)
RiskScenario ── considers ──▶ Technique       (Core)
RiskScenario ── involves ──▶ ThreatActor      (ThreatActor Ext)
```

> All “considers” edges are **non-authoritative references**.

---

### 4.3 Quantification

```
RiskScenario ── estimated_by ──▶ Likelihood
RiskScenario ── results_in ──▶ Impact
Likelihood ── combined_with ──▶ Impact ──▶ RiskScore
```

---

### 4.4 Mitigation & Decision

```
RiskScenario ── mitigated_by ──▶ Control
Control ── maps_to ──▶ DefensiveTechnique   (Core)
RiskAssessment ── recommends ──▶ Control
```

---

## 5. Explicitly Forbidden Edges

❌ `RiskScore → Vulnerability`
❌ `Likelihood → CVSS`
❌ `Impact → Technique`
❌ `RiskAssessment → modifies Core`

> Risk may *reference* Core but never *reshape* it.

---

## 6. Canonical Decision Traversals (RAG-safe)

### Prioritization

```
Asset
 → Vulnerability
 → RiskScenario
 → RiskScore
```

### Mitigation Selection

```
RiskScenario
 → Control
 → DefensiveTechnique
```

### Executive Summary

```
RiskAssessment
 → RiskScore
 → Decision
```

---

## 7. OWL (Turtle) – Risk Extension

```turtle
@prefix sec: <http://example.org/sec#> .
@prefix risk: <http://example.org/risk#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

risk:RiskAssessment a owl:Class .
risk:RiskScenario a owl:Class .
risk:Likelihood a owl:Class .
risk:Impact a owl:Class .
risk:RiskScore a owl:Class .
risk:Control a owl:Class .

risk:evaluates a owl:ObjectProperty ;
  rdfs:domain risk:RiskAssessment ;
  rdfs:range risk:RiskScenario .

risk:considers a owl:ObjectProperty ;
  rdfs:domain risk:RiskScenario ;
  rdfs:range sec:Vulnerability .

risk:estimated_by a owl:ObjectProperty ;
  rdfs:domain risk:RiskScenario ;
  rdfs:range risk:Likelihood .

risk:results_in a owl:ObjectProperty ;
  rdfs:domain risk:RiskScenario ;
  rdfs:range risk:Impact .

risk:maps_to a owl:ObjectProperty ;
  rdfs:domain risk:Control ;
  rdfs:range sec:DefensiveTechnique .
```

---

## 8. Neo4j Schema (Risk Extension)

```cypher
CREATE CONSTRAINT risk_id IF NOT EXISTS
FOR (r:RiskAssessment) REQUIRE r.risk_id IS UNIQUE;

CREATE CONSTRAINT scenario_id IF NOT EXISTS
FOR (s:RiskScenario) REQUIRE s.scenario_id IS UNIQUE;

CREATE CONSTRAINT score_id IF NOT EXISTS
FOR (rs:RiskScore) REQUIRE rs.score_id IS UNIQUE;

// Relationships
(:RiskAssessment)-[:EVALUATES]->(:RiskScenario)
(:RiskScenario)-[:CONSIDERS]->(:Vulnerability)
(:RiskScenario)-[:CONSIDERS]->(:Technique)
(:RiskScenario)-[:ESTIMATED_BY]->(:Likelihood)
(:RiskScenario)-[:RESULTS_IN]->(:Impact)
(:RiskScenario)-[:MITIGATED_BY]->(:Control)
(:Control)-[:MAPS_TO]->(:DefensiveTechnique)
```

---

## 9. Governance Rules (Hard Constraints)

1. Every RiskScenario **must reference at least one Core entity**
2. Likelihood & Impact **require documented rationale**
3. RiskScore **must be reproducible**
4. Risk decisions are **time-bounded**
5. Removing Risk data never affects Core or Incident data

---

## 10. Why This Extension Is Correct

| Requirement              | Met |
| ------------------------ | --- |
| Decision support         | ✅   |
| Executive explainability | ✅   |
| RAG controllability      | ✅   |
| Core purity              | ✅   |
| Regulatory compatibility | ✅   |

---

