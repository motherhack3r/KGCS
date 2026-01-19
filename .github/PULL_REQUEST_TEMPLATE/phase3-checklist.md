<!-- Phase 3 ingestion checklist for KGCS: use this template when opening PRs that implement or modify Phase 3 ETL components -->

# KGCS — Phase 3 Ingestion Checklist

Use this checklist when submitting PRs that add or change ingestion code, infra, or CI for Phase 3. Each checked item should include tests, example data, and a short rationale in the PR description.

## Quick summary

- **Goal:** Build a repeatable, auditable ETL that ingests NVD/MITRE sources, validates via SHACL, preserves provenance/versioning, and writes canonical KG nodes/edges.
- **Blockers:** DB networking/credentials, large sample data, rule‑ID fail policy for CI.

## Blocking items (must pass before Phase 4 rollout)

- [ ] Add `requirements.txt` with core runtime deps (rdflib, pyshacl, stix2, requests, python-dateutil, neo4j-driver)
- [ ] Provide `infra/docker-compose.yml` (Neo4j or a triple store) and local startup script (`scripts/setup_env.*`)
- [ ] Implement `scripts/ingest_nvd_cve.py` and `scripts/ingest_cpe.py` (MVP ingest)
- [ ] Integrate `run_validator()` into `scripts/ingest_pipeline.py` (pre-ingest validation)
- [ ] Provide failure payloads that conform to `docs/ontology/shacl/failure_payload_schema.json`
- [ ] Add deterministic upsert semantics + `ingest_metadata` (source_hash, ingest_job_id, ingest_time)

## Recommended incremental work (MVP → Full)

- [ ] MVP: CPE/CVE/CVSS ingest + SHACL pre-ingest + dry-run CI job
- [ ] STIX ingest: `scripts/ingest_stix.py` for ATT&CK, D3FEND, SHIELD
- [ ] CAPEC/CWE/CAR loaders and mapping to the causal chain
- [ ] Tests: unit tests for parsers + integration tests using `data/*/samples`
- [ ] CI: `.github/workflows/ingest-and-validate.yml` that runs validator and a dry-run ingest; publish `artifacts/`
- [ ] Fail-on-rule: configure which `rule_id` values cause CI failure vs. collect-only
- [ ] Performance tests & benchmark scripts for large ingests

## Acceptance criteria (for this PR)

- [ ] The PR includes tests or sample data exercised by tests
- [ ] The PR updates `docs/PHASE3.md` or `docs/README.md` with run instructions
- [ ] `scripts/ingest_pipeline.py --dry-run` completes without writing to the DB and produces `artifacts/*` reports
- [ ] If implementing a loader, ingested sample nodes include `source_uri`, `source_hash`, and `ingest_time`
- [ ] New CLI scripts include `--dry-run` and `--verbose` flags

## PR checklist (fill this in for the PR)

- [ ] Title clearly references Phase 3 and list of files changed
- [ ] Description lists which Phase 3 checklist items are completed
- [ ] New files are added under `scripts/`, `infra/`, `tests/` (as applicable)
- [ ] Example sample data included in `data/*/samples/` and referenced
- [ ] CI workflow updated to run the new dry-run job and publish artifacts
- [ ] Reviewer(s): @architecture, @data-team, @security (adjust as needed)

## How reviewers should validate

1. Follow `scripts/setup_env.*` to start local services (or use CI artifacts if available).
2. Run `python scripts/ingest_pipeline.py --dry-run --data data/shacl-samples/<example>` and check `artifacts/` for reports.
3. Run unit tests: `pytest tests/ingest` and confirm all new tests pass.
4. Inspect produced nodes/edges in the DB (if not dry-run) for provenance fields.

## Notes & run commands

- Local dev bootstrap (PowerShell):

```powershell
python -m pip install -r requirements.txt
docker-compose -f infra/docker-compose.yml up -d
```

- Dry-run ingestion (example):

```bash
python scripts/ingest_pipeline.py --dry-run --input data/cve/samples/sample_cve.json
```

- Publish artifacts in CI: ensure `artifacts/` is archived as job output and that the failure payload schema is validated.

---

Please update the checklist items you completed in this PR description and mark the remaining items as blockers if not yet addressed.
