Below is the **formalized ThreatActor Extension**, designed to support **attribution, intelligence, and adversary context** while **guaranteeing zero pollution of Core Ontology v1.0**.

This extension is where **attribution is allowed**—but **never asserted as fact**, only as *claims with provenance*.

---

# 🎭 ThreatActor Ontology Extension v1.0

**(Attribution Without Pollution)**

**Status:** Stable
**Depends on:** Core Ontology v1.0
**Temporal:** YES
**Confidence-aware:** YES
**Speculative:** Explicitly contained

---

## 1. Purpose & Design Contract

### What this extension exists for

* Represent **who may be behind activity**
* Model **threat intelligence claims**
* Track **tools, malware, and capabilities**
* Enable **intelligence-driven prioritization**

### What it never does

* Never asserts ground truth
* Never alters Core techniques or vulnerabilities
* Never introduces implicit causality
* Never mixes observation with attribution

> **Golden Rule**
> Attribution is a **claim**, not a fact.
> Claims require **confidence and provenance**.

---

## 2. Conceptual Boundary

```
Core Ontology     → “What exists”
Incident Ext     → “What happened”
ThreatActor Ext  → “Who might be responsible”
Risk Ext         → “What should we do”
```

No other extension is allowed to answer *“who did it?”*

---

## 3. Core Classes (ThreatActor Extension)

### 3.1 ThreatActor

> Abstract adversarial entity

| Property     | Type   | Notes                                |
| ------------ | ------ | ------------------------------------ |
| `actor_id`   | string | Stable identifier                    |
| `name`       | string | Canonical or alias                   |
| `actor_type` | enum   | GROUP / INDIVIDUAL / STATE / UNKNOWN |
| `status`     | enum   | ACTIVE / DORMANT / DISBANDED         |
| `first_seen` | date   | Optional                             |
| `last_seen`  | date   | Optional                             |

---

### 3.2 AttributionClaim

> **Critical class** — prevents attribution leakage

| Property           | Type   | Notes               |
| ------------------ | ------ | ------------------- |
| `claim_id`         | string | Unique              |
| `confidence`       | enum   | LOW / MEDIUM / HIGH |
| `confidence_score` | float  | Optional (0–1)      |
| `asserted_by`      | string | Vendor / analyst    |
| `asserted_on`      | date   | Required            |
| `rationale`        | string | Mandatory           |

---

### 3.3 Capability

| Property        | Type   | Notes               |
| --------------- | ------ | ------------------- |
| `capability_id` | string | Unique              |
| `description`   | string | Free text           |
| `maturity`      | enum   | LOW / MEDIUM / HIGH |

---

### 3.4 Tool

| Property        | Type    | Notes             |
| --------------- | ------- | ----------------- |
| `tool_id`       | string  | MITRE Software ID |
| `name`          | string  | Canonical         |
| `tool_type`     | enum    | TOOL / FRAMEWORK  |
| `is_legitimate` | boolean | Dual-use flag     |

---

### 3.5 Malware

| Property       | Type   | Notes                     |
| -------------- | ------ | ------------------------- |
| `malware_id`   | string | MITRE Software ID         |
| `name`         | string | Canonical                 |
| `malware_type` | enum   | RAT / LOADER / RANSOMWARE |
| `platforms`    | list   | Optional                  |

---

## 4. Authoritative Relationships

### 4.1 Actor Structure

```
ThreatActor ── has_capability ──▶ Capability
ThreatActor ── operates ──▶ Tool
ThreatActor ── deploys ──▶ Malware
```

---

### 4.2 Technique Usage (Anchored to Core)

```
ThreatActor ── uses ──▶ Technique   (Core)
Tool ── implements ──▶ Technique    (Core)
Malware ── implements ──▶ Technique (Core)
```

> Threat actors **never exploit vulnerabilities directly**
> They operate *only* through techniques.

---

### 4.3 Attribution (Claim-Based Only)

```
AttributionClaim ── attributes ──▶ ThreatActor
AttributionClaim ── based_on ──▶ Incident
AttributionClaim ── references ──▶ Evidence
```

> ❗ This is the **only legal path** from Incident → ThreatActor

---

## 5. Explicitly Forbidden Edges

❌ `Incident → ThreatActor` (direct)
❌ `ThreatActor → Vulnerability`
❌ `ThreatActor → Weakness`
❌ `AttributionClaim → modifies Incident`
❌ Any confidence-less attribution

---

## 6. Canonical Intelligence Traversals (RAG-safe)

### Attribution Reasoning

```
Incident
 → AttributionClaim
 → ThreatActor
```

### Technique-Based Profiling

```
Technique
 → ThreatActor
 → Tool / Malware
```

### Defensive Planning

```
ThreatActor
 → uses Technique
 → mitigated_by DefensiveTechnique
```

---

## 7. OWL (Turtle) – ThreatActor Extension

```turtle
@prefix sec: <http://example.org/sec#> .
@prefix ta: <http://example.org/threatactor#> .
@prefix inc: <http://example.org/incident#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

ta:ThreatActor a owl:Class .
ta:AttributionClaim a owl:Class .
ta:Capability a owl:Class .
ta:Tool a owl:Class .
ta:Malware a owl:Class .

ta:uses a owl:ObjectProperty ;
  rdfs:domain ta:ThreatActor ;
  rdfs:range sec:Technique .

ta:implements a owl:ObjectProperty ;
  rdfs:domain ta:Tool ;
  rdfs:range sec:Technique .

ta:attributes a owl:ObjectProperty ;
  rdfs:domain ta:AttributionClaim ;
  rdfs:range ta:ThreatActor .

ta:based_on a owl:ObjectProperty ;
  rdfs:domain ta:AttributionClaim ;
  rdfs:range inc:Incident .
```

---

## 8. Neo4j Schema (ThreatActor Extension)

```cypher
CREATE CONSTRAINT actor_id IF NOT EXISTS
FOR (a:ThreatActor) REQUIRE a.actor_id IS UNIQUE;

CREATE CONSTRAINT claim_id IF NOT EXISTS
FOR (c:AttributionClaim) REQUIRE c.claim_id IS UNIQUE;

// Relationships
(:ThreatActor)-[:USES]->(:Technique)
(:Tool)-[:IMPLEMENTS]->(:Technique)
(:Malware)-[:IMPLEMENTS]->(:Technique)

(:AttributionClaim)-[:ATTRIBUTES]->(:ThreatActor)
(:AttributionClaim)-[:BASED_ON]->(:Incident)
(:AttributionClaim)-[:REFERENCES]->(:Evidence)
```

---

## 9. Governance Rules (Hard Constraints)

1. Attribution **must be claim-based**
2. Every claim **must include confidence and rationale**
3. Multiple conflicting claims are allowed
4. Removing attribution **never affects Incidents**
5. Threat actors do not exist without evidence-backed claims

---

## 10. Why This Extension Is Correct

| Requirement                       | Met |
| --------------------------------- | --- |
| Attribution without hallucination | ✅   |
| Intelligence provenance           | ✅   |
| Core purity                       | ✅   |
| RAG safety                        | ✅   |
| Analyst trust                     | ✅   |

---

