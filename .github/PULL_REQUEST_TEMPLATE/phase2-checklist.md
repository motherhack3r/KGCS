<!-- Phase 2 completion checklist for KGCS: use this template when opening PRs that touch Phase 2 deliverables -->

# KGCS — Phase 2 Completion Checklist

Use this checklist when submitting PRs that complete or modify Phase 2 artifacts. Each checked item should have tests, small example data, and a short rationale in the PR description.

## Quick summary

- **Goal:** Complete SHACL coverage, governance artifacts, and CI gating for Phase 2.

- **Blockers:** SHACL coverage gaps, missing SHACL samples, CI integration.

## Blocking items (must pass before Phase 3 rollout)

- [ ] Expand SHACL coverage to all OWL modules and RAG templates (`docs/ontology/owl/`, `docs/ontology/rag/`) (partial: canonical bundle and per-OWL identifier shapes added)

- [ ] Add or update SHACL constraint docs (`docs/ontology/shacl/`) and a short checklist of constraints changed

- [ ] Add positive/negative SHACL samples under `data/shacl-samples/` and include a validation manifest

- [ ] Ensure `scripts/validate_shacl.py` exposes a stable `run_validator()` entry and is called from `scripts/ingest_pipeline.py` (ETL integration pending; validator CLI added)

- [ ] Finalize CI workflow `.github/workflows/shacl-validation.yml` to run the SHACL validator and fail on violations

- [ ] Add governance artifacts: rule IDs, failure payload schema, and responsible owners in `docs/KGCS.md` or governance doc referenced there

## Recent progress (quick wins)

- [x] Added canonical SHACL bundle: `docs/ontology/shacl/kgcs-shapes.ttl`

- [x] Added RAG→SHACL mapping: `docs/ontology/shacl/rag-to-shacl.md`

- [x] `scripts/validate_shacl.py` updated: CLI supports `--template` to validate shape subsets per RAG template

## Non-blocking / recommended

- [ ] Add unit/integration tests for re-ingestion/versioning behavior (CVSS coexistence, `affected_by` → `PlatformConfiguration` invariant)

- [ ] Add example staging indexing pipeline that runs SHACL pre-index and rejects bad data

- [ ] Provide a short README for `scripts/validate_shacl.py` with example commands

## PR checklist (fill this in for the PR)

- [ ] Title clearly references Phase 2 and list of files changed

- [ ] Description lists which Phase 2 checklist items are completed

- [ ] Added/updated SHACL files are documented and linked in PR description

- [ ] New positive/negative samples included in `data/shacl-samples/` and referenced

- [ ] CI pipeline updated and a sample run (or CI run) attached

- [ ] Reviewer(s): @architecture, @security (adjust as needed)

## How reviewers should validate

1. Run the SHACL validator locally using `scripts/validate_shacl.py` against the new/updated SHACL files and samples.

2. Confirm that positive samples pass and negative samples fail as expected.

3. Inspect CI workflow changes and, if possible, trigger a test run.

4. Verify that `scripts/ingest_pipeline.py` calls the validator before indexing (or provide a short runbook if staged differently).

## References

- Core spec: `docs/ontology/core-ontology-v1.0.md`

- RAG templates: `docs/ontology/rag/RAG-travesal-templates.md`

- Incident/Risk/ThreatActor extensions: `docs/ontology/incident-ontology-extension-v1.0.md`, `docs/ontology/risk-ontology-extension-v1.0.md`, `docs/ontology/threatactor-ontology-extension-v1.0.md`

- Ingest & validation scripts: `scripts/ingest_pipeline.py`, `scripts/validate_shacl.py`

- CI stub: `.github/workflows/shacl-validation.yml`

---

Please update the checklist items you completed in this PR description and mark the remaining items as blockers if not yet addressed.
