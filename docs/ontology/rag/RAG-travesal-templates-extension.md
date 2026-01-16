Below is a **formal set of RAG traversal templates** designed to be **query-safe, non-hallucinatory, and ontology-governed**, explicitly aligned with:

* **Core Ontology v1.0**
* **Incident Extension**
* **Risk Extension**
* **ThreatActor Extension**

These templates are **not examples** — they are **approved traversal contracts** that an LLM (or agent) is allowed to follow.

They are derived and normalized from your ontology drafts and design principles  .

---

# 🧠 RAG Traversal Templates

**(Query-Safe Paths)**

## 0. Why Traversal Templates Exist (Non-Negotiable)

> **RAG systems must not “reason freely” over graphs**
> They must follow **pre-approved paths** to avoid:

* invented causality
* probabilistic leakage
* attribution hallucination
* business logic pollution

A **Traversal Template** defines:

* allowed **start nodes**
* allowed **edge sequence**
* allowed **end nodes**
* **forbidden shortcuts**

---

## 1. Core Traversal Invariants (Global Rules)

These apply to **all templates**:

1. ❌ Never skip layers (e.g. CVE → Technique directly)
2. ❌ Never cross extensions unless explicitly allowed
3. ❌ Never traverse *into* Core from extensions
4. ❌ Never infer “used”, “caused”, or “exploited” unless edge exists
5. ✅ Always terminate on authoritative Core nodes for explanations

---

## 2. Core Ontology Traversal Templates

### T-CORE-01 — *Vulnerability → Defensive Options*

**Question answered**

> “How can this vulnerability be mitigated or detected?”

**Traversal**

```
Vulnerability
 → Weakness
 → AttackPattern
 → Technique
 → (DefensiveTechnique | DetectionAnalytic | DeceptionTechnique)
```

**Why safe**

* Follows the causal backbone
* No incident or attribution inference

---

### T-CORE-02 — *Asset Exposure Analysis*

**Question answered**

> “What attack techniques are relevant to this asset?”

**Traversal**

```
Asset
 → PlatformConfiguration
 → Vulnerability
 → Weakness
 → AttackPattern
 → Technique
```

**Forbidden**

* ❌ Asset → Technique (direct)

---

### T-CORE-03 — *Technique Context*

**Question answered**

> “What is this technique, and how is it usually handled?”

**Traversal**

```
Technique
 → Tactic
 → DefensiveTechnique
 → DetectionAnalytic
 → DeceptionTechnique
```

---

## 3. Incident Extension Traversal Templates

### T-INC-01 — *Incident → What Happened*

**Question answered**

> “What techniques were observed in this incident?”

**Traversal**

```
Incident
 → ObservedTechnique
 → Technique
```

**Rule**

* `ObservedTechnique` is mandatory (no abstraction jumps)

---

### T-INC-02 — *Incident → Defensive Guidance*

**Question answered**

> “How could this incident have been mitigated?”

**Traversal**

```
Incident
 → ObservedTechnique
 → Technique
 → DefensiveTechnique
```

---

### T-INC-03 — *Evidence Traceability*

**Question answered**

> “Why do we believe this technique was used?”

**Traversal**

```
Incident
 → ObservedTechnique
 → Evidence
```

**Guarantee**

* Every claim can be justified with artifacts

---

## 4. ThreatActor Extension Traversal Templates

(**Attribution Without Pollution**)

### T-TA-01 — *Attribution Reasoning*

**Question answered**

> “Who might be responsible for this incident?”

**Traversal**

```
Incident
 → AttributionClaim
 → ThreatActor
```

**Hard rule**

* ❌ Incident → ThreatActor (direct) is illegal

---

### T-TA-02 — *Threat Actor Profiling*

**Question answered**

> “What techniques is this threat actor known for?”

**Traversal**

```
ThreatActor
 → Technique
 → Tactic
```

---

### T-TA-03 — *Tool-Driven Attribution*

**Question answered**

> “What does this malware typically do?”

**Traversal**

```
Malware
 → Technique
 → DefensiveTechnique
```

---

## 5. Risk Extension Traversal Templates

(**Decision & Prioritization Only**)

### T-RISK-01 — *Risk Prioritization*

**Question answered**

> “Which vulnerabilities should we fix first?”

**Traversal**

```
Asset
 → Vulnerability
 → RiskScenario
 → RiskScore
```

**Rule**

* CVSS is referenced, never overridden

---

### T-RISK-02 — *Mitigation Planning*

**Question answered**

> “What controls reduce this risk?”

**Traversal**

```
RiskScenario
 → Control
 → DefensiveTechnique
```

---

### T-RISK-03 — *Executive Decision Support*

**Question answered**

> “What is the recommended action?”

**Traversal**

```
RiskAssessment
 → RiskScore
 → Decision
```

---

## 6. Cross-Extension (Explicitly Allowed) Templates

### T-X-01 — *Incident → Risk Escalation*

**Question answered**

> “How does this incident affect our risk posture?”

**Traversal**

```
Incident
 → ObservedTechnique
 → Technique
 → RiskScenario
 → RiskScore
```

---

### T-X-02 — *Threat-Informed Risk*

**Question answered**

> “Which risks are influenced by this threat actor?”

**Traversal**

```
ThreatActor
 → Technique
 → RiskScenario
```

---

## 7. Forbidden Traversals (Global Blacklist)

These must be **hard-blocked** in RAG:

❌ CVE → ThreatActor
❌ Incident → Vulnerability
❌ ThreatActor → Weakness
❌ RiskScore → Technique
❌ Detection → ThreatActor
❌ Incident → Decision

If a user asks a question that *requires* one of these paths → **the system must answer with uncertainty**.

---

## 8. How to Enforce This in Practice

### Option A — Static Path Registry

* Encode templates as allowed edge sequences
* Reject queries outside registry

### Option B — Query Planner + Validator

1. LLM proposes traversal
2. Validator checks against template list
3. Only then execute graph query

### Option C — Prompt-Bound RAG

Inject templates directly into system prompt:

> “You may only answer by following one of the approved traversal templates…”

---

## 9. What You Have Achieved

With this, your system now has:

* ✅ **Semantic guardrails**
* ✅ **Explainable answers**
* ✅ **No attribution hallucination**
* ✅ **Regulatory-friendly reasoning**
* ✅ **Composable, future-proof RAG**

---

## 🔜 Natural Next Steps (High Value)

1. 🛡️ **SHACL validation rules** per template
2. 🧠 **Traversal-aware prompt engineering**
3. ⚙️ **Automatic query planner** (LLM → Cypher/SPARQL)
4. 📊 **Decision dashboards driven by Risk templates**


