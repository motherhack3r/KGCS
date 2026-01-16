Below is the **formalized Incident Extension**, strictly layered **on top of Core Ontology v1.0**, aligned with your drafts and normalized to be **RAG-safe, time-aware, and non-polluting**.

This is a **production-grade specification** (not conceptual), designed to plug directly into the Core you froze earlier.

> Source alignment and terminology are grounded in your uploaded drafts  

---

# 🚨 Incident Ontology Extension v1.0

**Status:** Stable
**Depends on:** Core Ontology v1.0
**Temporal:** YES
**Authoritativeness:** Observational only

---

## 1. Purpose & Design Guarantees

### What this extension does

* Models **what actually happened**
* Captures **observed use of techniques**
* Preserves **time, evidence, and assets**
* Enables **forensic & RAG reasoning**

### What it never does

* Never alters Core semantics
* Never creates new vulnerabilities, techniques, or weaknesses
* Never infers causality beyond observation

> **Golden Rule**
> Incidents **instantiate** Core concepts — they do not redefine them.

---

## 2. Core Classes (Incident Extension)

### 2.1 Incident

| Property      | Type     | Notes                     |
| ------------- | -------- | ------------------------- |
| `incident_id` | string   | Globally unique           |
| `start_time`  | datetime | Optional                  |
| `end_time`    | datetime | Optional                  |
| `status`      | enum     | OPEN / CONTAINED / CLOSED |
| `description` | string   | Human-readable            |
| `source`      | string   | SOC, SIEM, MDR            |

---

### 2.2 ObservedTechnique

> **Critical class** — this is the *bridge* between time and abstraction.

| Property           | Type     | Notes                  |
| ------------------ | -------- | ---------------------- |
| `observation_id`   | string   | Unique                 |
| `first_seen`       | datetime | Required               |
| `last_seen`        | datetime | Optional               |
| `confidence`       | enum     | LOW / MEDIUM / HIGH    |
| `observation_type` | enum     | ALERT / FORENSIC / LOG |

---

### 2.3 DetectionEvent

| Property       | Type     | Notes          |
| -------------- | -------- | -------------- |
| `detection_id` | string   | Unique         |
| `timestamp`    | datetime | Required       |
| `detector`     | string   | SIEM, EDR, NDR |
| `rule_id`      | string   | Optional       |

---

### 2.4 Evidence

| Property        | Type   | Notes                      |
| --------------- | ------ | -------------------------- |
| `evidence_id`   | string | Unique                     |
| `evidence_type` | enum   | LOG / FILE / MEMORY / PCAP |
| `hash`          | string | Optional                   |
| `location`      | uri    | Storage pointer            |

---

### 2.5 AffectedAsset

| Property     | Type   | Notes                   |
| ------------ | ------ | ----------------------- |
| `asset_id`   | string | External reference      |
| `asset_role` | enum   | TARGET / PIVOT / VICTIM |

---

## 3. Authoritative Relationships

### 3.1 Incident Structure

```
Incident ── involves ──▶ AffectedAsset
Incident ── observed ──▶ ObservedTechnique
Incident ── supported_by ──▶ Evidence
```

---

### 3.2 Observation Binding (Critical)

```
ObservedTechnique ── instance_of ──▶ Technique   (Core)
```

> This edge is **mandatory**
> No observed behavior exists without a Core Technique anchor.

---

### 3.3 Detection & Evidence Chain

```
DetectionEvent ── detects ──▶ ObservedTechnique
DetectionEvent ── supported_by ──▶ Evidence
ObservedTechnique ── evidenced_by ──▶ Evidence
```

---

## 4. What Is Explicitly Forbidden

❌ `Incident → Vulnerability` (direct)
❌ `ObservedTechnique → Weakness`
❌ `Incident → ThreatActor` (handled in ThreatActor extension)
❌ Any probabilistic causation edges

> If analysts *believe* a vulnerability was exploited, that belief belongs in **Risk or ThreatActor extensions**, not here.

---

## 5. Canonical Incident Traversal (RAG-safe)

**Question:**

> “What defensive techniques are relevant to this incident?”

```
Incident
 → ObservedTechnique
 → Technique
 → DefensiveTechnique
```

**Question:**

> “What detections fired during this incident?”

```
Incident
 → ObservedTechnique
 → DetectionEvent
 → Evidence
```

---

## 6. OWL (Turtle) – Incident Extension

```turtle
@prefix sec: <http://example.org/sec#> .
@prefix inc: <http://example.org/incident#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

inc:Incident a owl:Class .
inc:ObservedTechnique a owl:Class .
inc:DetectionEvent a owl:Class .
inc:Evidence a owl:Class .
inc:AffectedAsset a owl:Class .

inc:observed a owl:ObjectProperty ;
  rdfs:domain inc:Incident ;
  rdfs:range inc:ObservedTechnique .

inc:instance_of a owl:ObjectProperty ;
  rdfs:domain inc:ObservedTechnique ;
  rdfs:range sec:Technique .

inc:detects a owl:ObjectProperty ;
  rdfs:domain inc:DetectionEvent ;
  rdfs:range inc:ObservedTechnique .

inc:supported_by a owl:ObjectProperty ;
  rdfs:domain inc:DetectionEvent ;
  rdfs:range inc:Evidence .
```

---

## 7. Neo4j Schema (Incident Extension)

```cypher
CREATE CONSTRAINT incident_id IF NOT EXISTS
FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE;

CREATE CONSTRAINT observation_id IF NOT EXISTS
FOR (o:ObservedTechnique) REQUIRE o.observation_id IS UNIQUE;

CREATE CONSTRAINT detection_id IF NOT EXISTS
FOR (d:DetectionEvent) REQUIRE d.detection_id IS UNIQUE;

CREATE CONSTRAINT evidence_id IF NOT EXISTS
FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE;

// Relationships
(:Incident)-[:OBSERVED]->(:ObservedTechnique)
(:ObservedTechnique)-[:INSTANCE_OF]->(:Technique)
(:DetectionEvent)-[:DETECTS]->(:ObservedTechnique)
(:DetectionEvent)-[:SUPPORTED_BY]->(:Evidence)
```

---

## 8. Governance Rules (Non-Negotiable)

1. Every `ObservedTechnique` **must** map to exactly one Core `Technique`
2. No Incident object can exist without a timestamp
3. Evidence must be immutable once linked
4. Deleting an Incident **never deletes Core nodes**

---

## 9. Why This Works

| Requirement        | Satisfied |
| ------------------ | --------- |
| RAG safety         | ✅         |
| Temporal reasoning | ✅         |
| Explainability     | ✅         |
| SOC usability      | ✅         |
| Core purity        | ✅         |

---

## 🔜 Recommended Next Step

The next *high-leverage* options are:

1. 🔗 **Formalize ThreatActor Extension** (attribution without pollution)
2. ⚖️ **Formalize Risk Extension** (decision & prioritization)
3. 🧠 **Define RAG traversal templates** per extension
4. 🛡️ **SHACL constraints** for incident data quality

