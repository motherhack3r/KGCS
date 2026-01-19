RAG template → SHACL shape mapping
=================================

This file maps each RAG traversal template to the primary SHACL shapes that should be validated or enforced before using the template for reasoning or RAG responses.

- Template T1 (Vulnerability Impact Explanation):
  - Validate: `ex:VulnerabilityShape`, `ex:WeaknessShape`, `ex:AttackPatternShape`, `ex:TechniqueShape`, `ex:TacticShape`

- Template T2 (Severity & Scoring Explanation):
  - Validate: `ex:VulnerabilityShape`, `ex:VulnerabilityScoreShape`

- Template T3 (Detection-Centric Reasoning):
  - Validate: `ex:TechniqueShape`, `ex:DetectionAnalyticShape`

- Template T4 (Mitigation-Centric Reasoning):
  - Validate: `ex:TechniqueShape` and any `ex:DefensiveTechnique` shapes (if created)

- Template T5 (Deception & Adversary Disruption):
  - Validate: `ex:TechniqueShape`, `ex:TacticShape`, and SHACL shapes for deception artifacts (future)

- Template T6 (Reference & Evidence Grounding):
  - Validate: `ex:VulnerabilityShape` and `ex:Reference` presence (via `ex:references` property)

- Template T7 (End-to-End Defensive Reasoning):
  - Validate: all shapes from T1 + detection + mitigation shapes (`ex:DetectionAnalyticShape`, `ex:VulnerabilityScoreShape`)

Notes:

- The SHACL bundle `kgcs-shapes.ttl` provides core coverage; project teams should extend it with additional shapes for `DefensiveTechnique`, `Reference`, `DeceptionTechnique`, and extension-specific constraints as needed.

- CI should run the relevant shape subset for the RAG path being used in retrieval/response.
