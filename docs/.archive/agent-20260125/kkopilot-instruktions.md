# AI Coding Instructions for KGCS

**Project:** KGCS (Cybersecurity Knowledge Graph) — A frozen, standards-backed knowledge graph integrating 9 MITRE security taxonomies with strict semantic boundaries for hallucination-free AI reasoning.

**Core Invariant:** External standards (NVD, MITRE) = authoritative truth; inferred/temporal data = extension layers only.

---

## Architecture Overview

### Four Immutable Layers (No Cross-Pollution)

```
Layer 4: Extensions          → Incident, Risk, ThreatActor (contextual, temporal, inferred)
Layer 3: Core Ontology      → CPE, CVE, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE (frozen facts)
Layer 2: Modular Ontologies → 9 independent OWL files (cpe, cve, cwe, capec, attck, d3fend, car, shield, engage)
Layer 1: External Standards → NVD APIs, MITRE STIX/JSON/XML (sources of truth, never modified)
```

**Key Rule:** If a concept cannot be traced to an external standard with a stable ID, it belongs in an extension, never Core.

---

## Critical Patterns & Rules

### Pattern 1: The Vulnerability Causality Chain (Core Only)

The canonical reasoning path **must follow this exact sequence**:

```
CPE (Platform) → CVE (Vulnerability) → CVSS (Score) → CWE (Weakness)
                                      → CAPEC (Pattern) → ATT&CK Technique → {D3FEND, CAR, SHIELD, ENGAGE}
```

- ✅ Every edge exists in authoritative JSON/STIX
- ✅ Every step is independently verifiable
- ❌ No shortcuts (e.g., CVE → Technique directly skips essential context)
- ❌ No invented edges between standards

**Location:** [../docs/ontology/rag/RAG-travesal-templates.md](../docs/ontology/rag/RAG-travesal-templates.md) defines allowed traversal templates.

### Pattern 2: Vulnerability Affects Configurations, Not Platforms

**Critical Invariant:** `affected_by` relationships point to `PlatformConfiguration`, not `Platform`.

- A CVE affects **specific versions/updates** of software (configuration)
- A Platform (CPE) is the atomic identifier; vulnerabilities don't affect all versions equally
- `PlatformConfiguration` models NVD's affected version ranges

**Example:** CVE-2025-1234 affects Apache 2.4.41 running on Linux x86-64, not "Apache" in general.

### Pattern 3: CVSS Versioning (Never Overwrite)

Each CVSS version is a **separate ontology node**:
- `VulnerabilityScore_v2.0`
- `VulnerabilityScore_v3.1`
- `VulnerabilityScore_v4.0`

Never merge or update; add new versions alongside existing ones. Extensions may reason about which version to use in specific contexts.

### Pattern 4: RAG Uses Pre-Approved Traversal Templates Only

Located: [../docs/ontology/rag/RAG-travesal-templates.md](../docs/ontology/rag/RAG-travesal-templates.md)

LLMs must **not reason freely** over the graph. Instead:
- Select a template matching the intent (e.g., T1: Vulnerability Impact, T3: Defense Coverage)
- Follow the exact edge sequence
- Stop at explicit boundaries
- Reject the query if no template matches

**Example:** "Explain CVE-2025-1234" → Use Template T1, traverse: CVE → CWE → CAPEC → Technique → Tactic. Stop. Do not add Risk Assessment or business impact (that's T-Risk-1, a separate template).

### Pattern 5: Standards Alignment (1:1 Mapping Rule)

Every ontology class has a **direct, lossless correspondence** to one standard:

| Class | Standard | Source | Unique ID |
|-------|----------|--------|-----------|
| `Platform` | CPE 2.3 | NVD CPE API | `cpeUri` |
| `Vulnerability` | CVE | NVD CVE API 2.0 | `cveId` |
| `VulnerabilityScore` | CVSS | NVD CVSS JSON | `cveId` + version |
| `Weakness` | CWE | MITRE CWE JSON | `cweId` |
| `AttackPattern` | CAPEC | MITRE CAPEC JSON | `capecId` |
| `Technique` / `Tactic` | ATT&CK | MITRE ATT&CK STIX 2.1 | `attackTechnique_id` / `tacticId` |
| `DefensiveTechnique` | D3FEND | MITRE D3FEND STIX | `d3fendId` |
| `DetectionAnalytic` | CAR | MITRE CAR JSON | `carId` |
| `DeceptionTechnique` | SHIELD | MITRE SHIELD STIX | `shieldId` |
| `EngagementConcept` | ENGAGE | MITRE ENGAGE Framework | `engageId` |

**Enforcement:** Every ontology property must derive from source JSON/XML fields. If the source doesn't have it, the class doesn't have it.

---

## Modular Ontology Structure

Located: [../docs/ontology/owl/](../docs/ontology/owl/)

### Independence Without Isolation

Each standard = independent OWL module, **no circular imports**:

```
cpe-ontology-v1.0.owl          (standalone)
cve-ontology-v1.0.owl          (imports: cpe)
cwe-ontology-v1.0.owl          (standalone)
capec-ontology-v1.0.owl        (imports: cwe)
attck-ontology-v1.0.owl        (standalone)
d3fend-ontology-v1.0.owl       (imports: core for linking)
car-ontology-v1.0.owl          (imports: core for linking)
shield-ontology-v1.0.owl       (imports: core for linking)
engage-ontology-v1.0.owl       (imports: core for linking)
core-ontology-extended-v1.0.owl (integrates all + defines causal chain)

Extensions (always import Core, never Core imports Extensions):
  incident-ontology-extension-v1.0.owl
  risk-ontology-extension-v1.0.owl
  threatactor-ontology-extension-v1.0.owl
```

**When adding a new standard or extension:**
1. Create the module file in `../docs/ontology/owl/`
2. Define classes 1:1 with source schema
3. Add to corresponding markdown in `../docs/ontology/` (e.g., `capec-ontology-v1.0.md`)
4. Update `core-ontology-extended-v1.0.owl` to import if it's in Core
5. Update RAG traversal templates if it introduces new reasoning paths

---

## Extension Layers (Non-Core Semantics)

### Layer 4A: Incident Extension

Located: [../docs/ontology/incident-ontology-extension-v1.0.md](../docs/ontology/incident-ontology-extension-v1.0.md)

**What it models:** Observational reality — what actually happened.

**Key classes:** `Incident`, `ObservedTechnique`, `DetectionEvent`, `Evidence`, `AffectedAsset`

**Critical invariant:** Incidents **instantiate** Core concepts (e.g., ObservedTechnique points to ATT&CK Technique), they do **not redefine** them.

**Properties:** Always temporal (`timestamp`, `first_seen`, `last_seen`) + confidence level.

### Layer 4B: Risk Extension

Located: [../docs/ontology/risk-ontology-extension-v1.0.md](../docs/ontology/risk-ontology-extension-v1.0.md)

**What it models:** Decision context — risk assessments, scenarios, remediation choices.

**Key classes:** `RiskAssessment`, `RiskScenario`

**Critical rule:** Only place where subjectivity (probability, business impact) is allowed. Links to Core concepts but does not alter them.

### Layer 4C: ThreatActor Extension

Located: [../docs/ontology/threatactor-ontology-extension-v1.0.md](../docs/ontology/threatactor-ontology-extension-v1.0.md)

**What it models:** Attribution claims, group capabilities, tools/malware used.

**Key classes:** `ThreatActor`, `AttributionClaim`, `Capability`, `Tool`, `Malware`

**Critical rule:** Attribution is **always confidence-qualified**; never asserts ground truth. Links to Core techniques/TTPs but does not invent new ones.

---

## Data Organization

Located: [../data/](../data/) — mirrors standard structure:

```
data/
  cpe/          CPE platform identifiers (NVD)
  cve/          CVE vulnerability disclosures (NVD)
  cwe/          CWE weakness taxonomy (MITRE)
  capec/        CAPEC attack patterns (MITRE)
  attack/       ATT&CK techniques & tactics (MITRE)
  d3fend/       D3FEND defensive techniques (MITRE)
  cti-stix/     STIX bundles (ATT&CK, D3FEND in STIX 2.1 format)
  
Each contains:
  raw/          Original NVD/MITRE JSON/XML/STIX (read-only)
  samples/      Annotated examples for testing/documentation
  schemas/      JSON Schemas, XSD, or SHACL validation rules
```

**Pattern:** Never commit modified external data; if you need to adjust mappings, do it in the ontology class definitions, not the raw data files.

---

## Documentation Structure

Located: [../docs/](../docs/)

- [../KGCS.md](../KGCS.md) — Executive summary + architecture overview (start here)
- [../docs/KGCS-draft.md](../docs/KGCS-draft.md) — Detailed specification with examples
- [../docs/ontology/](../docs/ontology/) — Formal ontology definitions
  - `core-ontology-v1.0.md` — Core classes, properties, invariants
  - `*-ontology-v1.0.md` — Per-standard mappings
  - `*-ontology-extension-v1.0.md` — Extensions (incident, risk, threat actor)
  - `owl/` — OWL 2.0 formal definitions
  - `rag/` — RAG traversal templates & safety constraints
  - `shacl/` — SHACL constraints for validation

**When implementing features:** Read the corresponding markdown first, then the OWL formalization. The markdown is the human-readable spec; OWL is the formal constraint.

---

## Common Tasks & Patterns

### Task: Add a New Relationship Between Standards

**Example:** "D3FEND technique D3-XYZ now mitigates CAPEC-123"

1. **Verify the relationship exists** in source data (D3FEND JSON or MITRE documentation)
2. **Find the edge definition** in [../docs/ontology/core-ontology-v1.0.md](../docs/ontology/core-ontology-v1.0.md)
3. **Add the OWL axiom** to [../docs/ontology/owl/core-ontology-extended-v1.0.owl](../docs/ontology/owl/core-ontology-extended-v1.0.owl)
4. **Update RAG templates** in [../docs/ontology/rag/](../docs/ontology/rag/) if it opens a new reasoning path
5. **Test with samples:** Ensure sample data in [../data/](../data/) still validates

### Task: Ingest New Standard Version (e.g., CPE 3.0)

1. **Check scope:** Does CPE 3.0 introduce new classes/properties?
2. **Create versioned module:** `cpe-ontology-v3.0.owl` (keep v2.3 for backward compatibility)
3. **Update mappings:** Add to [../docs/ontology/](../docs/ontology/) with migration guide
4. **Update Core imports:** Decide if v3.0 replaces v2.3 or coexists
5. **Do not break existing data:** Ensure old CPE URIs still resolve

### Task: Support a New Use Case (e.g., Incident Investigation)

1. **Check if it's Core or Extension:** Does it require temporal/contextual data?
   - Temporal or observational? → Incident Extension
   - Risk decisions? → Risk Extension
   - Attribution claims? → ThreatActor Extension
   - Authoritative mapping to a standard? → Core Ontology
2. **Create/extend appropriate layer** (never modify Core for use cases)
3. **Define traversal templates** in [../docs/ontology/rag/](../docs/ontology/rag/) for safe RAG paths
4. **Add SHACL constraints** in [../docs/ontology/shacl/](../docs/ontology/shacl/) to validate instance data

---

## Validation & Testing

No automated test suite is present; validation is **formal and manual**:

- **Syntax:** OWL 2.0 files must parse in Protégé or similar
- **Schema compliance:** JSON samples must validate against `.schema` files in [../data/](../data/)
- **Alignment:** Every ontology property must be traceable to source standard
- **No pollution:** Extensions must never reference Core in ways that would break it if extended independently
- **Circular imports:** Check that [../docs/ontology/owl/](../docs/ontology/owl/) has no cycles

**Before committing changes:**
1. Verify ontology markdown matches OWL
2. Check that edge sequences in RAG templates exist in core-ontology-extended
3. Validate sample data against schema files
4. Ensure no new Core properties without source standard justification

---

## Key Files to Read First

1. [../KGCS.md](../KGCS.md) (897 lines) — Architecture, causality chain, coverage model
2. [../docs/ontology/core-ontology-v1.0.md](../docs/ontology/core-ontology-v1.0.md) (283 lines) — Core classes, invariants
3. [../docs/KGCS-draft.md](../docs/KGCS-draft.md) (1989 lines) — Detailed spec with alignment rules
4. [../docs/ontology/rag/RAG-travesal-templates.md](../docs/ontology/rag/RAG-travesal-templates.md) (385 lines) — Safe reasoning boundaries

---

## Golden Rules

1. **External standards are authoritative.** If MITRE/NVD say it, we model it. If they don't, it's an extension.
2. **Frozen Core, flowing Extensions.** Core Ontology v1.0 should rarely change; extensions are where complexity grows.
3. **RAG is templated, not freeform.** LLM reasoning must follow pre-approved traversal patterns.
4. **Trace everything back.** Every statement must be traceable to a source with a stable ID.
5. **One-way import flow.** Core is never polluted by extensions; extensions always reference Core.
6. **CVSS versions coexist.** New scoring versions don't replace old ones; they expand the graph.
7. **No circular dependencies.** Ontology modules form a DAG; circular reasoning paths are forbidden.
