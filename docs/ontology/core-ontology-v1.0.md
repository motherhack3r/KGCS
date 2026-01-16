Below is a **normalized, frozen, implementation-agnostic *Core Ontology v1.0*** derived from your drafts.
This is **not a redesign**: it is a **canonical consolidation** with explicit scope boundaries, invariants, and guarantees.

You can treat this as the **constitution** of the cybersecurity knowledge graph. Everything else (risk, incidents, threat actors, predictions, SOC logic, business impact) must sit **on top of this**, never inside it.

---

# 🔐 Cybersecurity Core Ontology v1.0

**Status:** Stable
**Scope:** Authoritative security knowledge only
**Design Goal:** Lossless integration of security standards with zero invented semantics
**Primary Use:** Knowledge graphs, RAG, reasoning, explainability

---

## 1. Ontology Scope (Hard Boundary)

### ✅ Included

* Standards-backed facts
* Canonical identifiers
* Structural relationships explicitly defined by standards
* Multi-version coexistence (CVSS, ATT&CK, etc.)

### ❌ Explicitly Excluded

* Incidents, alerts, detections-in-time
* Threat actor behavior inference
* Risk scoring, business impact
* Probabilistic or predictive edges
* SOAR / SOC logic

> **Rule:**
> If it cannot be traced to an external standard **with a stable ID**, it is **not Core Ontology**.

---

## 2. Core Ontology Layers

```
┌─────────────────────────────┐
│ Engagement & Strategy       │  (ENGAGE)
├─────────────────────────────┤
│ Defense / Detection         │  (D3FEND / CAR / SHIELD)
├─────────────────────────────┤
│ Adversary Tradecraft        │  (ATT&CK)
├─────────────────────────────┤
│ Attack Abstraction          │  (CAPEC)
├─────────────────────────────┤
│ Weakness                    │  (CWE)
├─────────────────────────────┤
│ Vulnerability               │  (CVE / CVSS)
├─────────────────────────────┤
│ Exposure & Configuration    │  (CPE / NVD)
└─────────────────────────────┘
```

Layers are **conceptual only**.
No inheritance or leakage of semantics across layers.

---

## 3. Core Classes (Frozen)

### 3.1 Exposure & Configuration

| Class                   | Description                         | Source  |
| ----------------------- | ----------------------------------- | ------- |
| `Platform`              | Atomic software / hardware identity | CPE     |
| `PlatformConfiguration` | Logical exposure expression         | NVD CVE |

**Invariant**

* Vulnerabilities affect **configurations**, not platforms directly.

---

### 3.2 Vulnerability

| Class                | Description               | Source      |
| -------------------- | ------------------------- | ----------- |
| `Vulnerability`      | Publicly disclosed flaw   | CVE         |
| `VulnerabilityScore` | Severity scoring instance | CVSS        |
| `Reference`          | Supporting evidence       | NVD / MITRE |

**Invariant**

* Each CVSS version = separate `VulnerabilityScore`
* Scores never overwrite each other

---

### 3.3 Weakness & Attack Abstraction

| Class           | Description                   | Source |
| --------------- | ----------------------------- | ------ |
| `Weakness`      | Root cause category           | CWE    |
| `AttackPattern` | Abstract exploitation pattern | CAPEC  |

**Invariant**

* Weakness ≠ Vulnerability
* AttackPattern ≠ Technique

---

### 3.4 Adversary Tradecraft

| Class          | Description                 | Source |
| -------------- | --------------------------- | ------ |
| `Technique`    | Concrete adversary behavior | ATT&CK |
| `SubTechnique` | Specialized technique       | ATT&CK |
| `Tactic`       | Operational objective       | ATT&CK |

**Invariant**

* Tactics classify intent, not execution
* SubTechniques always belong to exactly one Technique

---

### 3.5 Defense, Detection & Deception

| Class                | Description            | Source |
| -------------------- | ---------------------- | ------ |
| `DefensiveTechnique` | Mitigation / denial    | D3FEND |
| `DetectionAnalytic`  | Detection logic        | CAR    |
| `DeceptionTechnique` | Adversary manipulation | SHIELD |

**Invariant**

* Defense ≠ Detection ≠ Deception
* Each mapped independently to ATT&CK

---

### 3.6 Engagement & Strategy

| Class               | Description                     | Source |
| ------------------- | ------------------------------- | ------ |
| `EngagementConcept` | Strategic adversary interaction | ENGAGE |

**Invariant**

* Engagement operates on **techniques**, not vulnerabilities

---

## 4. Core Relationships (Authoritative Only)

### 4.1 Exposure & Vulnerability

```
PlatformConfiguration ── affected_by ──▶ Vulnerability
Vulnerability ── scored_by ──▶ VulnerabilityScore
Vulnerability ── references ──▶ Reference
```

---

### 4.2 Causality Chain (Non-negotiable)

```
Vulnerability ── caused_by ──▶ Weakness
Weakness ── exploited_by ──▶ AttackPattern
AttackPattern ── implemented_as ──▶ Technique
```

> This is the **causal backbone** of the ontology.

---

### 4.3 Adversary Structure

```
Technique ── belongs_to ──▶ Tactic
SubTechnique ── subtechnique_of ──▶ Technique
```

---

### 4.4 Defense & Response

```
Technique ── mitigated_by ──▶ DefensiveTechnique
Technique ── detected_by ──▶ DetectionAnalytic
Technique ── countered_by ──▶ DeceptionTechnique
```

---

### 4.5 Engagement

```
EngagementConcept ── disrupts ──▶ Technique
EngagementConcept ── targets ──▶ Group   (external)
```

---

## 5. Global Ontology Rules (Hard Guarantees)

1. **Every node has an external ID**
2. **Every edge has a standard provenance**
3. **No temporal semantics**
4. **No probability, likelihood, or confidence**
5. **No “uses”, “leads to”, or “prevents” edges**
6. **No threat actors in Core**
7. **No incidents in Core**

If a rule is violated → **it is not Core Ontology**.

---

## 6. What This Ontology Guarantees

### ✅ RAG-safe traversal

No hallucinated causality.

### ✅ Explainability

Every answer can be traced to:

* a standard
* an ID
* an edge type

### ✅ Extensibility

You can add:

* Incident ontology
* Risk ontology
* Business ontology
* Threat actor ontology

…without changing Core v1.0.

---

## 7. Canonical Traversal Example

**Question:**

> “How can we detect and mitigate a vulnerability affecting this asset?”

**Guaranteed traversal path:**

```
Asset
 → PlatformConfiguration
 → Vulnerability
 → Weakness
 → AttackPattern
 → Technique
 → (DetectionAnalytic / DefensiveTechnique)
```

No shortcuts. No invented steps.

---

## 8. Versioning Policy

* **Core Ontology v1.0**: frozen
* New standards → **v1.1 / v2.0**
* New use cases → **extensions, not mutations**

---

## 9. Ready for Next Step

From here, the **correct next moves** are:

1. 🔒 Freeze this as `core-ontology-v1.0`
2. 📦 Split extensions (Incident, Risk, ThreatActor)
3. 🧠 Define RAG traversal templates
4. 🦉 Formalize OWL DL constraints
5. 🗺️ Generate Neo4j / RDF schemas

