# D3FEND Safe Expansion Set (Ontology-Safe, Governance-First)

Date: 2026-02-13

## 1) Evidence Snapshot

From raw ontology/data profiling:

- d3fend.owl breadth:
  - Classes: 4281
  - Object properties: 214
  - Datatype properties: 42
  - Named individuals: 2466
- Current Stage 5 emitted graph:
  - Node types: DefensiveTechnique only
  - Relationship predicates: mitigates only
- d3fend.json signals:
  - subjects with d3fend-id: 493
  - subjects with attack-id: 1454
  - subjects with cwe-id: 943
  - most frequent object-like D3FEND predicates include: kb-reference, narrower/broader, modifies, invokes, contains, produces, analyzes, accesses, enables, hardens.

Conclusion: current pipeline is an MVP slice of a much larger standard.

## 2) Sincere Opinion

Your concern is correct.

Expanding D3FEND is high value, but should be done in a strict staged way. Most OWL content is schema-level semantics (class definitions, restrictions, subProperty chains), while KGCS ETL should serialize source assertions only. If we ingest schema-level triples naively, we risk semantic duplication, ontology drift, and noisy graph structure.

Best path: expand with assertion-level, source-backed relations and selected node families first; keep ontology-level semantics in OWL modules, not ETL inference.

## 3) Safe Expansion Set (Recommended)

### Phase A — Low-risk, high-value (implement first)

Keep current DefensiveTechnique nodes, add richer assertion properties and explicit provenance:

- DefensiveTechnique properties:
  - d3fendId
  - label
  - description/definition
  - status
  - kb-article
  - synonym(s)
  - seeAlso / source URI
- Reference nodes (typed):
  - map kb-reference and kb-reference-of into explicit reference entities
  - preserve author, title, organization, publish time, URL

Add these relation families only when present as explicit source assertions:

1. mitigates (already)
2. analyzes
3. monitors
4. hardens
5. filters
6. isolates
7. restricts
8. enables

Reason: these are frequent enough to matter and semantically aligned with defensive behavior.

### Phase B — Controlled graph-structure enrichment

Add taxonomy/context edges that are explicitly asserted:

- broader / narrower (as explicit hierarchical links)
- modifies
- invokes
- contains / produces / accesses

Guardrail: do not materialize transitive closure; only emit asserted triples.

### Phase C — Additional node families (optional, extension-scoped)

Add only if SHACL + extension ontology are updated first:

- D3FEND Reference subclasses (PatentReference, GuidelineReference, AcademicPaperReference, etc.)
- Control entities (CCIControl, NISTControl)
- Tactic-like entities that are explicitly represented in D3FEND payload

Important: keep these extension-scoped and avoid conflating with ATT&CK/CWE core classes without explicit source mapping.

## 4) What NOT to ingest directly from OWL into ETL

Do not serialize these as operational graph assertions unless explicitly required by an approved template:

- owl:Restriction structures
- schema-only class axioms and blank-node restrictions
- inferred inverse/transitive edges not present in source assertions
- any edge that requires interpretation beyond source data

## 5) Governance and SHACL Requirements

Before each phase:

1. Define/extend allowed classes and predicates in extension OWL (non-invasive to frozen core).
2. Add SHACL shapes for required IDs and allowed edge targets.
3. Validate on Stage 5 output before Neo4j load.
4. Verify counts with focused Cypher checks and snapshot artifacts.

## 6) Suggested Acceptance Checks

- No fabricated edges (all edges traceable to source item IDs/fields).
- DefensiveTechnique count remains stable unless source changed.
- New predicates appear with non-zero counts and valid endpoint labels.
- SHACL conformance remains true.
- Cross-standard links (to ATT&CK/CWE) increase only where source explicitly supports them.

## 7) Bottom Line

Yes — D3FEND should be represented by more than only DefensiveTechnique+mitigates.

But the right implementation is incremental, assertion-first, SHACL-gated, and extension-scoped, not a bulk OWL dump into Neo4j.
