# KGCS – Executable Agent Checklist

**Purpose:**  
Prevent semantic corruption, unsafe inference, and ontology drift.

This checklist MUST be executed **top to bottom** before:

- proposing a change
- writing ETL code
- modifying OWL / SHACL
- approving RAG traversals
- accepting test results

If any step fails → **STOP**.

---

## PHASE 0 — TASK CLASSIFICATION (MANDATORY)

☐ Identify the task type (choose ONE):

- ☐ Ontology change (OWL)
- ☐ Governance change (SHACL)
- ☐ Data ingestion / ETL
- ☐ Query / RAG traversal
- ☐ Test-only change
- ☐ Documentation only

☐ Confirm whether the task:

- ☐ Affects semantic meaning
- ☐ Affects constraints only
- ☐ Is purely mechanical

If semantic meaning is affected → **extra scrutiny required in all phases**.

---

## PHASE 1 — CORE INVARIANTS CHECK

☐ Does this change violate any of the Five Immutable Rules?

- ☐ Causal chain preserved (`CPE → … → ATT&CK → Defense`)
- ☐ PlatformConfiguration used (not Platform)
- ☐ CVSS versions remain separate
- ☐ Core OWL remains untouched (or explicitly justified)
- ☐ No fabricated edges introduced

If **any** box is unchecked → **STOP. CHANGE INVALID.**

---

## PHASE 2 — ONTOLOGY SAFETY CHECK (OWL)

☐ Does the change:

- ☐ Add new classes?
- ☐ Add new object properties?
- ☐ Add new axioms (domain, range, disjointness, equivalence)?
- ☐ Modify imports?

If YES to any:

☐ Is every class/property:

- ☐ Directly grounded in an authoritative standard?
- ☐ Non-interpretative (factual, not analytical)?

☐ Are you avoiding:

- ☐ Transitivity
- ☐ Equivalence classes
- ☐ Implicit hierarchies
- ☐ Semantic shortcuts

If unsure → **DO NOT PROCEED**.

---

## PHASE 3 — INFERENCE CONTRACT CHECK

☐ Does this change cause the system to infer (explicitly or implicitly):

- ☐ Likelihood
- ☐ Probability
- ☐ Impact
- ☐ Actor intent
- ☐ Temporal causality
- ☐ Strategic meaning

If YES → **STOP. FORBIDDEN INFERENCE.**

☐ Can every inferred fact be traced to:

- ☐ NVD JSON field
- ☐ MITRE STIX object
- ☐ Explicit SHACL rule

If not → **STOP.**

---

## PHASE 4 — SHACL GOVERNANCE CHECK

☐ Is the intended constraint expressed in SHACL (not ETL)?

☐ Are there SHACL shapes that:

- ☐ Explicitly allow the structure
- ☐ Explicitly forbid invalid variants

☐ Does SHACL enforce:

- ☐ Cardinality
- ☐ Required relationships
- ☐ Safe traversal boundaries

If SHACL is missing or weak → **FIX SHACL FIRST**.

---

## PHASE 5 — ETL DISCIPLINE CHECK

☐ Does the ETL code:

- ☐ Only serialize authoritative data?
- ☐ Preserve IDs and provenance?
- ☐ Avoid interpretation or heuristics?

☐ Are you avoiding:

- ☐ Conditional relationship inference
- ☐ Cross-standard reasoning
- ☐ “Helper” edges
- ☐ Performance-driven semantic shortcuts

If ETL logic feels “smart” → **REJECT AND REFACTOR**.

---

## PHASE 6 — RAG SAFETY CHECK (IF APPLICABLE)

☐ Is this traversal explicitly listed in approved templates (T1–T7)?

☐ For each hop:

- ☐ Backed by standard data
- ☐ Constrained by SHACL
- ☐ Not collapsing abstraction layers

☐ Ask explicitly:
> “Could this traversal cause an LLM to over-interpret meaning?”

If YES → **REJECT TRAVERSAL**.

---

## PHASE 7 — VALIDATION & TESTING CHECK

☐ SHACL validation executed?

- ☐ PASS with zero violations

☐ Manual verification scripts run?

- ☐ Causal chain visually confirmed

☐ Automated tests executed?

- ☐ All pass

☐ Final question:
> “Could this change be *technically correct* but *semantically wrong*?”

If YES → **DO NOT MERGE**.

---

## PHASE 8 — FINAL ACCEPTANCE GATE

☐ Can every new node and edge be explained as:
> “This exists because the standard explicitly says so.”

☐ Can you explain the change to a third party **without using intuition or assumptions**?

☐ Does the graph remain a **truth layer**, not an analysis engine?

If ALL are YES → **CHANGE APPROVED**  
If ANY are NO → **CHANGE REJECTED**

---

## REMINDER (NON-NEGOTIABLE)

KGCS is not optimized for:

- convenience
- cleverness
- expressiveness

It is optimized for:

- correctness
- traceability
- reasoning safety

REMEMBER: **Truth > Usefulness > Convenience**

---
