# AI Coding Agent Instructions for KGCS

## Project Overview: Knowledge Graph for Cybersecurity (KGCS)

**KGCS** is a **frozen, authoritative cybersecurity knowledge graph** built on standards-backed data (CVE, CWE, CPE, CVSS, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE). The architecture enforces **strict semantic boundaries** to enable safe, hallucination-free RAG and AI reasoning.

**Not in scope:** business logic, incidents, risk assessments, or threat actor attribution—these are separate *extensions* that layer on top without polluting the core.

---

## Architecture: Four Canonical Layers

### 1. **Core Ontology v1.0** (`docs/ontology/core-ontology-v1.0.md`)

**Golden Rule:** If it cannot be traced to an external standard with a stable ID, it is **not Core**.

**Frozen classes:** `Platform` (CPE), `Vulnerability` (CVE), `VulnerabilityScore` (CVSS), `Weakness` (CWE), `AttackPattern` (CAPEC), `Technique` (ATT&CK), `Tactic`, `SubTechnique`, `DefensiveTechnique` (D3FEND), `DetectionAnalytic` (CAR), `DeceptionTechnique` (SHIELD), `EngagementConcept` (ENGAGE).

**Critical invariants:**
- Vulnerabilities affect **configurations**, not platforms directly
- Each CVSS version = separate `VulnerabilityScore` node (never overwrite)
- No inheritance or semantic leakage between layers
- No temporal properties (core facts are timeless)

### 2. **Incident Extension** (`docs/ontology/incident-ontology-extension-v1.0.md`)

Models **what actually happened**: observations, detections, evidence, time, assets. **Never alters Core semantics.**

Key classes: `Incident`, `ObservedTechnique`, `DetectionEvent`, `Evidence`, `AffectedAsset`.

**Golden Rule:** Incidents **instantiate** Core concepts—they don't redefine them.

### 3. **Risk Extension** (`docs/ontology/risk-ontology-extension-v1.0.md`)

Answers "what should we do?" for prioritization and decisions. **Explicitly allows subjectivity here only.**

Key classes: `RiskAssessment`, `RiskScenario`, decisions (ACCEPT/MITIGATE/TRANSFER/AVOID).

### 4. **ThreatActor Extension** (`docs/ontology/threatactor-ontology-extension-v1.0.md`)

Represents attribution claims **with provenance and confidence**. Never asserts ground truth.

Key classes: `ThreatActor`, `AttributionClaim` (always includes confidence level).

---

## Critical Developer Patterns

### Pattern 1: RAG Must Follow Pre-Approved Traversal Templates

**Location:** `docs/ontology/RAG-travesal-templates-extension.md`

RAG systems must **never reason freely** over the graph. Instead:
1. Use only approved traversal templates (e.g., `T-CORE-01`, `T-TA-02`)
2. Never skip layers (e.g., CVE → Technique directly is forbidden)
3. Never cross extensions unless explicitly allowed
4. Always terminate on authoritative Core nodes for explanations

**Example allowed traversal:**
```
Vulnerability → Weakness → AttackPattern → Technique → DefensiveTechnique
```

**Example forbidden:**
```
CVE → ThreatActor (direct) — must go through Incident extension
Incident → Weakness (crosses backward into Core) — illegal
```

### Pattern 2: SHACL Validation as Data Quality Gate

**Locations:** `docs/ontology/SHACL-constraints.md`, `docs/ontology/SHACL-profiles.md`

Data must pass SHACL validation at **three points:**
1. **Ingest time** (ETL/pipeline)
2. **Pre-RAG index build**
3. **Pre-query execution** (optional but recommended)

**Three trust profiles** control which semantics survive:
- **SOC profile:** observational truth only, no speculation, evidence mandatory
- **EXEC profile:** decision clarity, allows aggregation
- **AI profile:** hallucination safety (strictest, same as SOC in different ways)

If SHACL fails → reject or downgrade confidence.

### Pattern 3: Evidence Provenance is Non-Negotiable

Every Incident and Attribution claim must track:
- Source system (SIEM, EDR, MDR, analyst)
- Timestamp or time range
- Confidence level (LOW/MEDIUM/HIGH)
- Supporting evidence IDs

This enables explainable RAG answers: "Here's what we think, here's why."

### Pattern 4: Extension Boundaries Are Immutable

**Core never receives inputs from extensions.** Instead:
- Core defines classes and relationships
- Extensions reference Core concepts
- Extensions never add properties to Core classes
- If you need a hybrid concept, create it in the extension layer

Example: `ObservedTechnique` in Incident extension references `Technique` from Core, but adds temporal and confidence properties.

---

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| `docs/ontology/core-ontology-v1.0.md` | Authoritative class/edge definitions; read first |
| `docs/ontology/formal_ontology_draft.md` | Class/edge tables; Mermaid diagrams |
| `docs/ontology/RAG-travesal-templates-extension.md` | Approved query paths for safe reasoning |
| `docs/ontology/incident-ontology-extension-v1.0.md` | Temporal, observational layer |
| `docs/ontology/risk-ontology-extension-v1.0.md` | Decision/prioritization layer |
| `docs/ontology/threatactor-ontology-extension-v1.0.md` | Attribution claims with confidence |
| `docs/ontology/SHACL-constraints.md` | Data validation rules (enforce ontology purity) |
| `docs/ontology/SHACL-profiles.md` | Trust-level filtering (SOC/EXEC/AI) |
| `docs/ontology/owl/` | OWL/Turtle formal definitions |
| `data/cve/`, `data/cwe/`, `data/capec/`, `data/cpe/` | Standard sample data and JSON schemas |

---

## When Working on Code or Modeling

### Question 1: Is this fact in an external standard?
- **Yes** → put it in Core Ontology
- **No** → determine which extension (Incident/Risk/ThreatActor) or reject it

### Question 2: Does this fact have a timestamp?
- **Yes** → it belongs in Incident extension
- **No** → it belongs in Core

### Question 3: Does this involve "should we do this?" reasoning?
- **Yes** → Risk extension only
- **No** → likely Core or Incident

### Question 4: Does this involve attribution or threat actor claims?
- **Yes** → ThreatActor extension, always with confidence
- **No** → not attribution

### Question 5: Will an LLM traverse this path during RAG?
- **Yes** → check `RAG-travesal-templates-extension.md` for approval
- **No** → document why it's internal-only

---

## Conventions Specific to This Project

1. **Identifiers** are always traced to external standards: `cve_id`, `cwe_id`, `capec_id`, `technique_id`, `actor_id`, etc. Never invent new IDs.

2. **Relationships are immutable once documented.** If you need a new edge, add it to the formal ontology first, then implement.

3. **Confidence/Provenance in Extensions:** Every claim in Incident, Risk, or ThreatActor must declare source and confidence. Example:
   ```
   {
     "observation_id": "obs-123",
     "technique_id": "T1234",
     "confidence": "HIGH",
     "asserted_by": "EDR-system-X",
     "first_seen": "2025-01-15T10:30:00Z"
   }
   ```

4. **No temporal properties in Core.** Incidents and observations add `first_seen`, `last_seen`, `timestamp`. Core classes have none.

5. **SHACL before deployment.** Always validate new data or schema changes against the applicable profile (SOC/EXEC/AI).

---

