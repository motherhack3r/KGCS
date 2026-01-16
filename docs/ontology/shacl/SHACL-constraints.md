Perfect choice.
Below are **production-grade SHACL validation profiles** that **enforce ontology purity, extension boundaries, and RAG-safe traversals**.

These shapes are **not descriptive** — they are **guardrails**.
If data passes SHACL, it is *safe to reason over*.

---

# 🛡️ SHACL Validation Profiles

**(Cybersecurity Ontology Governance Layer)**

**Applies to:**

* 🔐 Core Ontology v1.0
* 🚨 Incident Extension
* ⚖️ Risk Extension
* 🎭 ThreatActor Extension

**Design goal:**

> ❌ Block invalid facts
> ❌ Block semantic pollution
> ❌ Block hallucination-enabling shortcuts

---

## 0. SHACL Strategy (How to Use This)

You should run SHACL validation at **three points**:

1. **Ingest time** (ETL / pipeline)
2. **Pre-RAG index build**
3. **Pre-query execution** (optional but powerful)

If a shape fails →
➡️ *reject data* or *downgrade confidence*

---

## 1. Core Ontology SHACL Profiles

### SH-CORE-01 — Vulnerability Must Have Weakness

> Enforces the causal backbone
> No CVE without a root cause

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix sec: <http://example.org/sec#> .

sec:VulnerabilityShape
  a sh:NodeShape ;
  sh:targetClass sec:Vulnerability ;
  sh:property [
    sh:path sec:caused_by ;
    sh:minCount 1 ;
    sh:message "Every Vulnerability must be linked to at least one Weakness (CWE)." ;
  ] .
```

---

### SH-CORE-02 — No CVE → Technique Shortcut

```turtle
sec:NoDirectVulnTechniqueShape
  a sh:NodeShape ;
  sh:targetClass sec:Vulnerability ;
  sh:not [
    sh:property [
      sh:path sec:implemented_as ;
      sh:minCount 1 ;
    ]
  ] ;
  sh:message "Vulnerability must not directly link to Technique." .
```

---

### SH-CORE-03 — Technique Must Belong to a Tactic

```turtle
sec:TechniqueTacticShape
  a sh:NodeShape ;
  sh:targetClass sec:Technique ;
  sh:property [
    sh:path sec:belongs_to ;
    sh:minCount 1 ;
    sh:message "Every Technique must belong to at least one Tactic." ;
  ] .
```

---

## 2. Incident Extension SHACL Profiles

### SH-INC-01 — Incident Must Have Observations

```turtle
@prefix inc: <http://example.org/incident#> .

inc:IncidentObservationShape
  a sh:NodeShape ;
  sh:targetClass inc:Incident ;
  sh:property [
    sh:path inc:observed ;
    sh:minCount 1 ;
    sh:message "Incident must include at least one ObservedTechnique." ;
  ] .
```

---

### SH-INC-02 — ObservedTechnique Must Anchor to Core

> Prevents fabricated behavior

```turtle
inc:ObservedTechniqueAnchorShape
  a sh:NodeShape ;
  sh:targetClass inc:ObservedTechnique ;
  sh:property [
    sh:path inc:instance_of ;
    sh:class sec:Technique ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
    sh:message "ObservedTechnique must reference exactly one Core Technique." ;
  ] .
```

---

### SH-INC-03 — No Incident → Vulnerability Link

```turtle
inc:NoIncidentVulnerabilityShape
  a sh:NodeShape ;
  sh:targetClass inc:Incident ;
  sh:not [
    sh:property [
      sh:path sec:affected_by ;
      sh:minCount 1 ;
    ]
  ] ;
  sh:message "Incident must not directly reference Vulnerability." .
```

---

## 3. ThreatActor Extension SHACL Profiles

(**Attribution Without Pollution**)

### SH-TA-01 — Attribution Must Be Claim-Based

```turtle
@prefix ta: <http://example.org/threatactor#> .

ta:AttributionClaimShape
  a sh:NodeShape ;
  sh:targetClass ta:AttributionClaim ;
  sh:property [
    sh:path ta:attributes ;
    sh:minCount 1 ;
    sh:message "AttributionClaim must reference a ThreatActor." ;
  ] ;
  sh:property [
    sh:path ta:based_on ;
    sh:minCount 1 ;
    sh:message "AttributionClaim must be based on an Incident." ;
  ] ;
  sh:property [
    sh:path ta:confidence ;
    sh:minCount 1 ;
    sh:message "AttributionClaim must include confidence." ;
  ] .
```

---

### SH-TA-02 — No Direct Incident → ThreatActor

```turtle
ta:NoDirectIncidentActorShape
  a sh:NodeShape ;
  sh:targetClass inc:Incident ;
  sh:not [
    sh:property [
      sh:path ta:attributes ;
      sh:minCount 1 ;
    ]
  ] ;
  sh:message "Incident must not directly reference ThreatActor." .
```

---

### SH-TA-03 — ThreatActors Operate Only via Techniques

```turtle
ta:ThreatActorTechniqueOnlyShape
  a sh:NodeShape ;
  sh:targetClass ta:ThreatActor ;
  sh:not [
    sh:property [
      sh:path sec:caused_by ;
      sh:minCount 1 ;
    ]
  ] ;
  sh:message "ThreatActor must not reference Weakness or Vulnerability directly." .
```

---

## 4. Risk Extension SHACL Profiles

(**Decision Discipline**)

### SH-RISK-01 — RiskScenario Must Anchor to Core

```turtle
@prefix risk: <http://example.org/risk#> .

risk:RiskScenarioAnchorShape
  a sh:NodeShape ;
  sh:targetClass risk:RiskScenario ;
  sh:property [
    sh:path risk:considers ;
    sh:minCount 1 ;
    sh:message "RiskScenario must consider at least one Core entity." ;
  ] .
```

---

### SH-RISK-02 — Likelihood Requires Rationale

```turtle
risk:LikelihoodRationaleShape
  a sh:NodeShape ;
  sh:targetClass risk:Likelihood ;
  sh:property [
    sh:path risk:rationale ;
    sh:minCount 1 ;
    sh:datatype xsd:string ;
    sh:message "Likelihood must include rationale." ;
  ] .
```

---

### SH-RISK-03 — Risk Must Not Override Core Severity

```turtle
risk:NoCVSSOverrideShape
  a sh:NodeShape ;
  sh:targetClass risk:RiskScore ;
  sh:not [
    sh:property [
      sh:path sec:scored_by ;
      sh:minCount 1 ;
    ]
  ] ;
  sh:message "RiskScore must not modify CVSS or Core severity." .
```

---

## 5. RAG-Specific Guardrail Shapes

### SH-RAG-01 — No Forbidden Shortcuts

```turtle
sec:NoForbiddenEdgesShape
  a sh:NodeShape ;
  sh:targetSubjectsOf sec:affected_by ;
  sh:not [
    sh:class ta:ThreatActor ;
  ] ;
  sh:message "Forbidden traversal detected: Vulnerability → ThreatActor." .
```

---

### SH-RAG-02 — Observations Must Be Evidence-Backed

```turtle
inc:ObservationEvidenceShape
  a sh:NodeShape ;
  sh:targetClass inc:ObservedTechnique ;
  sh:property [
    sh:path inc:evidenced_by ;
    sh:minCount 1 ;
    sh:message "ObservedTechnique must be supported by Evidence." ;
  ] .
```

---

## 6. Enforcement Levels (Recommended)

| Level        | When        | Action             |
| ------------ | ----------- | ------------------ |
| **STRICT**   | Ingest      | Reject data        |
| **STANDARD** | Pre-RAG     | Exclude nodes      |
| **LENIENT**  | Exploration | Flag with warnings |

---

## 7. What These SHACL Profiles Guarantee

✅ No hallucinated causality
✅ No attribution leakage
✅ No risk subjectivity in Core
✅ No unsafe RAG traversal
✅ Audit-ready reasoning

---

## 🔜 High-Impact Next Steps

1. ⚙️ **Translate SHACL → Neo4j constraints**
2. 🧠 **Auto-generate SHACL from traversal templates**
3. 🔍 **SHACL-aware RAG validator**
4. 📦 **SHACL profiles per trust level (SOC / Exec / AI)**

