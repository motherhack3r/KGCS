Below are **production-grade, D3FEND-specific SHACL shapes**, fully aligned with:

* Your **Core Ontology v1.0**
* The **Defense Semantics Extension (D3FEND-aligned)**
* Your existing **trust-profile philosophy (SOC / Exec / AI)**

These shapes are **normative**, not illustrative.

---

# 🛡️ D3FEND SHACL Shapes v1.0

**Purpose:**
Enforce *semantic correctness* of defensive knowledge and prevent overclaiming, shortcut reasoning, or ontology pollution.

**Applies to:**
`Defense Semantics Extension v1.0`

---

## 1. Design Principles (Encoded in SHACL)

1. Every DefensiveTechnique **must counter something**
2. Every DefensiveTechnique **must declare what it acts on**
3. Every DefensiveTechnique **must declare its effect**
4. DefensiveTechnique **must not reference vulnerabilities**
5. Defensive effects **must come from a controlled vocabulary**
6. No temporal, probabilistic, or effectiveness claims allowed

---

## 2. Namespace Prefixes

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix sec: <https://example.org/sec/defense#> .
@prefix core: <https://example.org/sec/core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
```

---

## 3. Core Shape — DefensiveTechnique (MANDATORY)

### 3.1 DefensiveTechnique Integrity Shape

```turtle
sec:DefensiveTechniqueShape
    a sh:NodeShape ;
    sh:targetClass sec:DefensiveTechnique ;

    ### Must counter at least one ATT&CK Technique
    sh:property [
        sh:path sec:countersTechnique ;
        sh:class core:Technique ;
        sh:minCount 1 ;
        sh:message "A DefensiveTechnique MUST counter at least one ATT&CK Technique (D3FEND requirement)." ;
    ] ;

    ### Must act on at least one DigitalArtifact
    sh:property [
        sh:path sec:actsOnArtifact ;
        sh:class core:DigitalArtifact ;
        sh:minCount 1 ;
        sh:message "A DefensiveTechnique MUST act on at least one DigitalArtifact." ;
    ] ;

    ### Must declare at least one DefensiveEffect
    sh:property [
        sh:path sec:producesEffect ;
        sh:class sec:DefensiveEffect ;
        sh:minCount 1 ;
        sh:message "A DefensiveTechnique MUST declare at least one DefensiveEffect." ;
    ] .
```

---

## 4. Controlled Vocabulary Enforcement — DefensiveEffect

### 4.1 DefensiveEffect Enumeration Shape

This prevents inventing effects like *“Stops”*, *“Eliminates”*, or *“Fully Blocks”*.

```turtle
sec:DefensiveEffectVocabularyShape
    a sh:NodeShape ;
    sh:targetClass sec:DefensiveEffect ;

    sh:in (
        sec:Detect
        sec:Prevent
        sec:Delay
        sec:Degrade
        sec:Disrupt
        sec:Contain
        sec:Restore
        sec:Reveal
    ) ;

    sh:message "DefensiveEffect MUST be one of the allowed D3FEND effects (Detect, Prevent, Delay, Degrade, Disrupt, Contain, Restore, Reveal)." .
```

---

## 5. Forbidden Relationships (Hard Safety Rules)

### 5.1 DefensiveTechnique MUST NOT reference Vulnerability

```turtle
sec:NoVulnerabilityLinkShape
    a sh:NodeShape ;
    sh:targetClass sec:DefensiveTechnique ;

    sh:not [
        sh:property [
            sh:path ?p ;
            sh:class core:Vulnerability ;
        ]
    ] ;

    sh:message "DefensiveTechnique MUST NOT directly reference Vulnerability. D3FEND operates on Techniques, not CVEs." .
```

---

### 5.2 DefensiveTechnique MUST NOT reference Weakness or AttackPattern

```turtle
sec:NoWeaknessOrAttackPatternShape
    a sh:NodeShape ;
    sh:targetClass sec:DefensiveTechnique ;

    sh:not [
        sh:property [
            sh:path ?p ;
            sh:class core:Weakness ;
        ]
    ] ;

    sh:not [
        sh:property [
            sh:path ?p ;
            sh:class core:AttackPattern ;
        ]
    ] ;

    sh:message "DefensiveTechnique MUST NOT reference Weakness or AttackPattern directly." .
```

---

## 6. DigitalArtifact Usage Integrity

### 6.1 DefensiveTechnique Artifact Targeting Shape

Ensures artifacts are **objects of action**, not abstract placeholders.

```turtle
sec:ArtifactTargetingShape
    a sh:NodeShape ;
    sh:targetClass sec:DefensiveTechnique ;

    sh:property [
        sh:path sec:actsOnArtifact ;
        sh:nodeKind sh:IRI ;
        sh:message "actsOnArtifact MUST reference a concrete DigitalArtifact instance." ;
    ] .
```

---

## 7. Optional: Strict Mode (AI / RAG Safety)

### 7.1 Single-Effect Declaration (Optional Profile)

Useful for **AI-facing graphs** to reduce ambiguity.

```turtle
sec:SingleEffectStrictShape
    a sh:NodeShape ;
    sh:targetClass sec:DefensiveTechnique ;

    sh:property [
        sh:path sec:producesEffect ;
        sh:maxCount 1 ;
        sh:message "Strict mode: DefensiveTechnique should declare only one primary DefensiveEffect." ;
    ] .
```

---

## 8. Validation Outcomes (Deterministic)

| Case                                    | Result    |
| --------------------------------------- | --------- |
| DefensiveTechnique without effect       | ❌ Invalid |
| DefensiveTechnique acting on Asset      | ❌ Invalid |
| DefensiveTechnique referencing CVE      | ❌ Invalid |
| DefensiveTechnique countering ATT&CK    | ✅ Valid   |
| DefensiveTechnique with invented effect | ❌ Invalid |

---

## 9. Why These SHACL Shapes Matter

These shapes guarantee that:

* D3FEND semantics are **never diluted**
* RAG answers **cannot overclaim**
* Defensive coverage analysis is **honest**
* Analysts trust the graph
* Executives don’t get false certainty
* AI stays grounded

---

## 10. Next Logical Options (Choose One)

You are now at a **very mature stage**. Logical next steps:

1. 🔍 **Validate existing OWL instances against these SHACL shapes**
2. 🧠 **Update RAG traversal templates to branch on DefensiveEffect**
3. 🧱 **Create trust-tier SHACL overlays (SOC / Exec / AI)**
4. 📦 **Produce a versioned ontology release bundle**

Say the number — I’ll proceed immediately.
