Excellent—this is the **last missing governance layer**.
Below is a **tiered SHACL profile system** that lets you expose *the same graph* to different consumers **without changing the data**, only the **validation contract**.

Think of it as **semantic zero-trust**.

---

# 🛡️ SHACL Profiles per Trust Level

**(SOC / Exec / AI)**

## Design Principle

> **Trust level ≠ data visibility**
> **Trust level = which semantics are allowed to survive validation**

Each profile:

* ⛔ forbids certain edges/classes
* ✅ enforces different minimum guarantees
* 🔎 controls what *kind* of reasoning is possible

---

## 0. Trust Levels Overview

| Profile  | Audience            | Goal                 | Risk Tolerance |
| -------- | ------------------- | -------------------- | -------------- |
| **SOC**  | Analysts, IR, DFIR  | Tactical accuracy    | 🔴 Zero        |
| **EXEC** | CISO, Board, GRC    | Decision clarity     | 🟠 Low         |
| **AI**   | RAG / Agents / LLMs | Hallucination safety | 🔴 Zero        |

> ⚠️ **AI and SOC are stricter than EXEC**, but in *different ways*.

---

# 🔴 TRUST PROFILE: SOC

**“Only what we can prove”**

## SOC Profile Philosophy

* Observational truth only
* No speculation
* No aggregation shortcuts
* Evidence is mandatory

---

## SH-SOC-01 — Incidents Must Be Evidence-Backed

```turtle
inc:SOCIncidentEvidenceShape
  a sh:NodeShape ;
  sh:targetClass inc:Incident ;
  sh:property [
    sh:path inc:observed ;
    sh:minCount 1 ;
  ] ;
  sh:property [
    sh:path inc:supported_by ;
    sh:minCount 1 ;
    sh:message "SOC incidents must be supported by evidence." ;
  ] .
```

---

## SH-SOC-02 — Observed Techniques Require High Confidence

```turtle
inc:SOCObservedTechniqueConfidenceShape
  a sh:NodeShape ;
  sh:targetClass inc:ObservedTechnique ;
  sh:property [
    sh:path inc:confidence ;
    sh:in ("HIGH") ;
    sh:message "SOC view requires HIGH confidence observations only." ;
  ] .
```

---

## SH-SOC-03 — No Risk or Attribution Allowed

```turtle
soc:NoRiskOrAttributionShape
  a sh:NodeShape ;
  sh:targetClass inc:Incident ;
  sh:not [
    sh:or (
      [ sh:path risk:evaluates ; sh:minCount 1 ]
      [ sh:path ta:attributes ; sh:minCount 1 ]
    )
  ] ;
  sh:message "SOC view must not include Risk or Attribution." .
```

---

## ✅ SOC Guarantees

* Court-defensible
* DFIR-safe
* Zero speculation

---

# 🟠 TRUST PROFILE: EXEC

**“Enough truth to decide”**

## EXEC Profile Philosophy

* Aggregation allowed
* Subjectivity allowed (explicit)
* Attribution allowed (summarized)
* Evidence optional

---

## SH-EXEC-01 — Risk Required for Exposure

```turtle
risk:ExecRiskRequiredShape
  a sh:NodeShape ;
  sh:targetClass sec:Vulnerability ;
  sh:property [
    sh:path risk:considered_in ;
    sh:minCount 1 ;
    sh:message "Exec view requires Vulnerabilities to be contextualized by Risk." ;
  ] .
```

---

## SH-EXEC-02 — Attribution Must Be Abstracted

```turtle
exec:AbstractAttributionOnlyShape
  a sh:NodeShape ;
  sh:targetClass ta:ThreatActor ;
  sh:property [
    sh:path ta:actor_type ;
    sh:in ("GROUP" "STATE" "UNKNOWN") ;
    sh:message "Exec attribution must be abstracted (no individual actors)." ;
  ] .
```

---

## SH-EXEC-03 — Evidence Optional, Rationale Mandatory

```turtle
risk:ExecRationaleShape
  a sh:NodeShape ;
  sh:targetClass risk:RiskAssessment ;
  sh:property [
    sh:path risk:rationale ;
    sh:minCount 1 ;
    sh:message "Exec decisions require rationale." ;
  ] .
```

---

## ✅ EXEC Guarantees

* Decision-focused
* Board-safe
* No technical overload

---

# 🔴 TRUST PROFILE: AI (RAG / Agents)

**“Nothing that can hallucinate”**

## AI Profile Philosophy

* Deterministic traversal only
* No subjective nodes without anchors
* No unbounded fan-out
* No implicit joins

---

## SH-AI-01 — Only Approved Traversal Anchors

```turtle
ai:ApprovedAnchorsShape
  a sh:NodeShape ;
  sh:targetClass sec:Technique ;
  sh:property [
    sh:path sec:belongs_to ;
    sh:minCount 1 ;
  ] ;
  sh:property [
    sh:path sec:mitigated_by ;
    sh:minCount 1 ;
    sh:message "AI queries require Technique anchors with mitigation context." ;
  ] .
```

---

## SH-AI-02 — No Direct Cross-Extension Jumps

```turtle
ai:NoCrossExtensionJumpShape
  a sh:NodeShape ;
  sh:targetClass inc:Incident ;
  sh:not [
    sh:property [
      sh:path risk:evaluates ;
      sh:minCount 1 ;
    ]
  ] ;
  sh:message "AI must not traverse Incident → Risk directly." .
```

---

## SH-AI-03 — Attribution Requires Confidence Threshold

```turtle
ai:AttributionConfidenceThresholdShape
  a sh:NodeShape ;
  sh:targetClass ta:AttributionClaim ;
  sh:property [
    sh:path ta:confidence_score ;
    sh:minInclusive 0.7 ;
    sh:message "AI attribution requires confidence ≥ 0.7." ;
  ] .
```

---

## SH-AI-04 — No Unanchored Risk

```turtle
ai:AnchoredRiskOnlyShape
  a sh:NodeShape ;
  sh:targetClass risk:RiskScenario ;
  sh:property [
    sh:path risk:considers ;
    sh:class sec:Technique ;
    sh:minCount 1 ;
    sh:message "AI risk reasoning must anchor to Core Technique." ;
  ] .
```

---

## ✅ AI Guarantees

* Hallucination-resistant
* Deterministic answers
* Auditable reasoning paths

---

# 🧩 How to Deploy This (Recommended)

### 1. One Graph, Multiple SHACL Sets

```
/shacl/
 ├── core.ttl
 ├── incident.ttl
 ├── risk.ttl
 ├── threatactor.ttl
 ├── trust-soc.ttl
 ├── trust-exec.ttl
 └── trust-ai.ttl
```

### 2. Validate by Context

* SOC UI → `core + incident + trust-soc`
* Exec Dashboard → `core + risk + trust-exec`
* RAG Pipeline → `core + all + trust-ai`

---

## 🧠 Why This Is Powerful (and Rare)

Most orgs try to do this with **access control**.
With **ontology law** you achieve:

* 🔐 **Semantic zero trust**
* 🧠 **AI-safe knowledge exposure**
* ⚖️ **Role-based truth**
* 📜 **Audit-grade explainability**



---

