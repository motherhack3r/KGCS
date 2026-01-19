SHACL Constraints — Changes & Review Checklist
===========================================

Date: 2026-01-19

Purpose: concise summary of SHACL constraints added or updated for Phase 2, and a short checklist to validate changes.

- Summary of files added/updated

- `kgcs-shapes.ttl` — canonical bundle: core invariants (Vulnerability `cveId`, VulnerabilityScore `cvssVersion`/`baseScore`, Platform `cpeNameId`, PlatformConfiguration `matchCriteriaId`, Technique→Tactic linkage, SubTechnique parent).

- Per-OWL bundles (identifier-focused):

  - `cpe-shapes.ttl`: `cpeNameId`, `matchCriteriaId`

  - `cve-shapes.ttl`: `cveId`, `cvssVersion`, `baseScore`

  - `cwe-shapes.ttl`: `cweId`

  - `capec-shapes.ttl`: `capecId`

  - `attck-shapes.ttl`: `technique_id`, `tacticId`, `subtechnique_of` parent

  - `d3fend-shapes.ttl`: `d3fendId`

  - `car-shapes.ttl`: `carId`

  - `shield-shapes.ttl`: `shieldId`

  - `engage-shapes.ttl`: `engageId`
- `core-extended-shapes.ttl` — cross-module consistency checks
- `manifest.md` — mapping OWL filenames → per-OWL shape bundles
- `rag-to-shacl.md` — mapping RAG templates → primary shapes

Key constraint categories (why they matter)

- Identifier presence: every Core/Standard node must include its canonical external ID (cveId, cweId, capecId, carId, etc.). This guarantees traceability.

- Structural invariants: Technique → belongs_to → Tactic; SubTechnique → subtechnique_of → Technique; Vulnerability → caused_by → Weakness (if present) — these preserve the causal backbone.

- Configuration semantics: Vulnerabilities affect PlatformConfiguration, not Platform; PlatformConfiguration must reference Platform via `matchesPlatform`.

Short checklist for reviewers (manual/CI validation)

- [ ] Confirm `docs/ontology/shacl/kgcs-shapes.ttl` loads in `rdflib`/`pyshacl` without parse errors.

- [ ] Confirm per-OWL bundles listed in `docs/ontology/shacl/manifest.md` load without parse errors.

- [ ] Run validator locally on a positive sample: `python scripts/validate_shacl.py --data data/shacl-samples/t1_good.ttl --owl attck-ontology-v1.0.owl` and expect `CONFORMS` (or report generated).

- [ ] Run validator locally on a negative sample: `python scripts/validate_shacl.py --data data/shacl-samples/t1_bad.ttl --owl attck-ontology-v1.0.owl` and confirm failures are reported for expected constraints.

- [ ] Verify `scripts/validate_shacl.py --template T1` extracts the expected subset from the canonical bundle and validates accordingly.

- [ ] Inspect `docs/ontology/shacl/manifest.md` and ensure every OWL in `docs/ontology/owl/` has an entry (or intentionally omitted).

- [ ] Confirm CI run produces artifacts in `artifacts/` and that changed-OWL detection triggers per-OWL validation in `.github/workflows/shacl-validation.yml`.

Notes / next actions

- Add per-OWL positive/negative samples under `data/shacl-samples/` (e.g., `attck-t1_good.ttl`, `attck-t1_bad.ttl`) to fully exercise each bundle.

- Consider replacing `manifest.md` with a machine-parsable `manifest.json` for more robust CI usage.

- Add governance metadata into each SHACL constraint: stable rule ID, short machine-friendly code, and human message (this is currently a remaining Phase 2 task).

Contact: KGCS architecture team (add owners in governance doc when ready).
