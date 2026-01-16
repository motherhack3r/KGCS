# Copilot Instructions for KGCS

**KGCS** (Cybersecurity Knowledge Graph) is a **frozen, standards-backed knowledge graph** that integrates 9 MITRE security taxonomies (CVE, CWE, CPE, CVSS, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE) with strict semantic boundaries for safe, hallucination-free AI reasoning.

**Core Principle:** External standards = authoritative truth. Inferred or temporal data = extension layers only.

---

## Architecture at a Glance

### Four Immutable Layers

1. **Core Ontology** (`docs/ontology/core-ontology-v1.0.md`)
   - Frozen, standards-backed classes: `Platform` (CPE), `Vulnerability` (CVE), `Weakness` (CWE), `Technique` (ATT&CK), `DefensiveTechnique` (D3FEND), `DetectionAnalytic` (CAR), etc.
   - No inheritance between classes; no temporal properties
   - Critical invariant: vulnerabilities affect *configurations*, not platforms directly
   - Each CVSS version = separate node (never overwrite)

2. **Incident Extension** (`docs/ontology/incident-ontology-extension-v1.0.md`)
   - Temporal, observational layer: `Incident`, `ObservedTechnique`, `DetectionEvent`, `Evidence`
   - Instantiates Core concepts without altering their semantics
   - Always carries: timestamp, confidence level, source system

3. **Risk Extension** (`docs/ontology/risk-ontology-extension-v1.0.md`)
   - Decision layer: `RiskAssessment`, `RiskScenario` with decisions (ACCEPT/MITIGATE/TRANSFER/AVOID)
   - Only place where subjectivity is allowed

4. **ThreatActor Extension** (`docs/ontology/threatactor-ontology-extension-v1.0.md`)
   - Attribution claims only; always includes confidence level
   - Never asserts ground truth

---

## Critical Patterns

### Pattern 1: Standards-Backed Data Only in Core

**Rule:** If it cannot be traced to an external standard with a stable ID, it is **not Core Ontology**.

**Examples:**
- ✅ `Vulnerability` → CVE ID is stable
- ✅ `AttackPattern` → CAPEC ID is stable
- ❌ Business impact scoring → Risk extension only
- ❌ Temporal observations → Incident extension only

### Pattern 2: RAG Must Use Pre-Approved Traversal Templates

**Location:** `docs/ontology/rag/RAG-travesal-templates-extension.md`

LLMs **never reason freely** over the graph. Instead:
1. Use only approved traversal templates (e.g., `T-CORE-01`)
2. Never skip layers
3. Never cross extensions unless explicitly allowed
4. Always terminate on authoritative Core nodes for explanations

**Example allowed path:**
```
Vulnerability → Weakness → AttackPattern → Technique → DefensiveTechnique
```

**Example forbidden path:**
```
CVE → ThreatActor (direct) 
→ Must go through Incident extension first
```

### Pattern 3: SHACL Validation at Three Gates

**Locations:** `docs/ontology/shacl/SHACL-constraints.md`, `docs/ontology/shacl/SHACL-profiles.md`

Data must pass SHACL validation at:
1. **Ingest time** (ETL/pipeline): enforce schema purity
2. **Pre-RAG index build**: ensure no hallucination surfaces
3. **Pre-query execution** (optional): runtime safeguards

**Three trust profiles** control what semantics survive:
- **SOC profile:** observational truth only; evidence mandatory
- **EXEC profile:** decision clarity; allows aggregation
- **AI profile:** hallucination safety (strictest)

If SHACL fails → reject or downgrade confidence.

### Pattern 4: Extension Boundaries Are Immutable

**Core never receives inputs from extensions.**

- Extensions **reference** Core concepts
- Extensions **never** add properties to Core classes
- If you need a hybrid concept, create it in the extension layer (e.g., `ObservedTechnique` references `Technique` but adds temporal properties)

### Pattern 5: Evidence & Provenance Non-Negotiable

Every Incident and Attribution claim must track:
```json
{
  "claim_id": "claim-123",
  "source_system": "EDR-X",
  "timestamp": "2025-01-15T10:30:00Z",
  "confidence": "HIGH",  // LOW | MEDIUM | HIGH
  "evidence_ids": ["evt-001", "evt-002"]
}
```

This enables explainable RAG: "Here's what we think, here's why."

---

## File Map & Responsibilities

| File | Purpose |
|------|---------|
| `docs/ontology/core-ontology-v1.0.md` | Authoritative class/edge definitions; read first |
| `docs/ontology/formal_ontology_draft.md` | Class/edge tables in tabular form; Mermaid diagrams |
| `docs/ontology/incident-ontology-extension-v1.0.md` | Temporal, observational modeling |
| `docs/ontology/risk-ontology-extension-v1.0.md` | Decision/prioritization modeling |
| `docs/ontology/threatactor-ontology-extension-v1.0.md` | Attribution claims with confidence |
| `docs/ontology/rag/RAG-travesal-templates-extension.md` | Approved query paths for safe AI reasoning |
| `docs/ontology/shacl/SHACL-constraints.md` | Data validation rules (enforce purity) |
| `docs/ontology/shacl/SHACL-profiles.md` | Trust-level filtering (SOC/EXEC/AI) |
| `docs/ontology/owl/` | OWL/Turtle formal definitions |
| `data/{cve,cwe,capec,cpe,attack,cti-stix}/` | Standard sample data and JSON schemas |

---

## Decision Tree for New Work

1. **Is this fact in an external standard with a stable ID?**
   - Yes → Core Ontology
   - No → go to (2)

2. **Does this fact have a timestamp?**
   - Yes → Incident extension
   - No → go to (3)

3. **Is this a "should we do this?" decision?**
   - Yes → Risk extension
   - No → go to (4)

4. **Is this an attribution claim?**
   - Yes → ThreatActor extension (always with confidence)
   - No → Likely not in scope or needs new extension

---

## Project Conventions

1. **Identifiers** are always external: `cve_id`, `cwe_id`, `capec_id`, `technique_id`, `actor_id`. Never invent new IDs.

2. **Relationships are immutable.** Before implementing a new edge, add it to `formal_ontology_draft.md` first.

3. **No temporal properties in Core.** Incidents, observations, and assessments add `first_seen`, `last_seen`, `timestamp`, `confidence`. Core classes have none.

4. **SHACL before deployment.** Always validate new data or schema changes against the applicable profile (SOC/EXEC/AI).

5. **No inheritance in Core.** If two classes need shared properties, document the pattern in Core, don't inherit.

6. **Extension isolation.** When adding to an extension, verify it doesn't reference or modify Core class properties.

---

## Common Pitfalls to Avoid

- ❌ Adding temporal fields to Core classes (they belong in Incident extension)
- ❌ Creating edges that skip ontology layers (e.g., CVE directly to Technique)
- ❌ Forgetting SHACL validation when loading new standard data
- ❌ Using confidence levels in Core (they belong in extension claims only)
- ❌ Altering MITRE semantics to fit a use case (extend instead; never replace)
