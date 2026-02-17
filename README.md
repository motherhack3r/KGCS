# KGCS – Cybersecurity Knowledge Graph

**Version:** 1.0  
**Date:** January 2026  

---

## 📌 Overview

KGCS (Cybersecurity Knowledge Graph) is a frozen, standards‑backed ontology that unifies nine MITRE security taxonomies (CVE, CWE, CPE, CVSS, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).
It provides a single source of truth for AI systems to reason about vulnerabilities, attacks, defenses, and threat intelligence without hallucination.

**Current Status:**

- **Phase 1:** Core ontologies complete and frozen
- **Phase 2:** SHACL validation framework complete
- **Phase 3:** MVP data ingestion and Neo4j loader operational (see [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md))
- **Phase 4–5:** Extensions and RAG integration designed, not yet implemented

For a full technical and architectural overview, see [docs/KGCS.md](docs/KGCS.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🏗️ Architecture

```text
┌───────────────────────┐
│  Extension Layer (L4)  │  (Incident, Risk, ThreatActor)
├───────────────────────┤
│  Core Ontology (L3)    │  (CPE → CVE → CWE → CAPEC → ATT&CK → D3FEND/CAR/SHIELD/ENGAGE)
├───────────────────────┤
│  Modular Ontologies    │  (one OWL file per standard)
├───────────────────────┤
│  External Standards    │  (NVD, MITRE)
└───────────────────────┘
```

- **Core** is immutable and 1:1 mapped to official JSON/STIX schemas.  
- **Extensions** add temporal, contextual, or subjective data without polluting the core.

---

## 🔑 Core Invariants

| Invariant | Description |
| ----------- | ------------- |
| Authoritative alignment | Every class/property maps to a stable ID in NVD or MITRE. |
| Explicit provenance | Every edge is traceable to a source field. |
| No invented semantics | The ontology is a lens, not a replacement for the standards. |
| Extensions never modify core | Incident, Risk, ThreatActor layers reference core only. |

---

## 🚀 Getting Started

1. **Clone the repo**  

   ```bash
   git clone https://github.com/yourorg/kgcs.git
   cd kgcs
   ```

2. **Load data**  
   - Download NVD and MITRE JSON/STIX files into data.  
   - Run the ingestion script (Python/Neo4j or RDF).  
  
   Tip: For interactive, single-standard runs use the guided helper:

   ```bash
   python scripts/run_standard_pipeline.py
   # choose a standard (e.g. capec) and a single step (download|etl|shacl|load-nodes|load-rels|stats)
   ```

3. **Query the graph**
   - Use Neo4j Cypher or SPARQL.  
   - Example:  

     ```cypher
     MATCH (cve:Vulnerability {cveId:'CVE-2025-1234'})
     MATCH (cve)-[:caused_by]->(cwe:CWE)
     RETURN cve, cwe
     ```

4. **Integrate with RAG**
   - Use the pre‑approved traversal templates in rag.  
   - Ensure LLM queries follow a template; otherwise reject.

---

## 📚 Documentation

| File | Purpose |
| ------ | --------- |
| KGCS.md | Executive summary & architecture |
| core-ontology-v1.0.md | Core class & edge definitions |
| RAG-travesal-templates.md | Safe traversal contracts |
| incident-ontology-extension-v1.0.md | Incident extension spec |
| risk-ontology-extension-v1.0.md | Risk extension spec |
| threatactor-ontology-extension-v1.0.md | Threat‑actor extension spec |

---

## 📦 Extensions

- **Incident** – Observed techniques, detections, evidence.  
- **Risk** – Assessments, scenarios, decisions.  
- **ThreatActor** – Attribution claims, capabilities, tools.

Each extension lives in its own OWL file and imports the core ontology.

---

## 📈 Future Work

- Short-term (now): stabilize CI SHACL gating, add per-OWL positive/negative samples, and automate validator runs in CI for changed OWL/SHACL artifacts.
- Near-term (next 3 months): harden ETL + loader operational contracts (per-standard ETL modules, guided CLI, tmp full-TTL outputs), canonical predicate policy for cross-standard links, and small migration utilities for existing DBs.
- Mid-term (3–9 months): expand modular OWL coverage, add robust integration tests for ingestion + load, and produce more example traversal templates for RAG safety.
- Long-term (9–18 months): optional UI for traversal visualization and explainable query interfaces.

## 🧰 Operational Scripts

- `scripts/db/` holds the Phase 4 helpers (`create_cpe_cve_relationships.py`, `verify_phase4_complete.py`, the `check_*` utilities, etc.) that interact with Neo4j for reproduction or diagnostics.  
- `scripts/legacy/phase4/` archives the one-off repair/verification scripts (`repair_cpe_properties.py`, `diagnose_cpe_mismatch.py`, `check_buggy_pattern.py`, etc.) that were needed during the CPE parsing fix but are no longer part of normal ingestion.

Key operational scripts and conventions

- `scripts/run_standard_pipeline.py`: interactive helper to run a single standard + step (download, etl, shacl, load-nodes, load-rels, stats). Use for iterative development.
- Per-standard ETL modules under `src/etl/` can be invoked directly: `python -m src.etl.etl_capec --input data/capec/raw --output data/capec/samples/pipeline-stage6-capec.ttl`.
- `scripts/run_all_etl.py` remains as the full orchestrator for end‑to‑end runs; prefer per-standard ETL for targeted runs during development.

Notes about ETL outputs and loader behavior

- All ETLs now write a full per-standard TTL file into `tmp/` (useful for combined-file workflows and debugging).
- Per-standard split outputs (nodes + rels) live under `data/{standard}/samples/` and are the canonical source for the loaders.
- The loader defaults to safe behavior: it will not reset the target database unless `--reset-db` is passed. Use `--dry-run` to verify parse + counts without writes.

Predicate naming and CAPEC→ATT&CK mappings

- Historically some ETLs emitted different predicate names for CAPEC→ATT&CK mappings (`implements` vs `implemented_as`). The current CAPEC ETL emits `SEC.implemented_as` and the loader preserves predicate names on ingest to avoid silent remapping.
- If you prefer a canonical relationship across the DB, run a one-time migration (Cypher) or canonicalize at ETL time. See `docs/PIPELINE_EXECUTION_GUIDE.md` Appendix for recommended commands.
- Regression and integration suites now live under `tests/` so the repository root stays focused on documentation, configuration, and operational scripts.

CI and testing

- GitHub Actions contains a Phase 3 ingestion smoke workflow (`.github/workflows/phase3-ingest-smoke.yml`) that runs the integration test suite and optional validation steps.
- Unit and integration tests live under `tests/` and are used by CI to exercise ETL transformers and loader compatibility (`tests/integration/test_phase3_comprehensive.py`, `tests/unit/test_etl_loader_compat.py`).

### Verification Utilities (RDF/Turtle)

- [tests/verification/verify_causal_chain.py](tests/verification/verify_causal_chain.py) — offline sanity check of CWE→CAPEC→Technique→Tactic using the pipeline Turtle outputs in tmp.
- [tests/verification/verify_defense_layers.py](tests/verification/verify_defense_layers.py) — offline sanity check of defense-layer links (D3FEND/CAR/SHIELD/ENGAGE) against ATT&CK using the pipeline Turtle outputs in tmp.

These are manual verification utilities (not pytest tests) and expect the corresponding tmp/pipeline-stage*.ttl files to exist.

---

## 🤝 Contributing

Pull requests are welcome. Please follow the style guidelines in ontology and keep the core immutable.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## **Roadmap**

- **Short-term (0-3 months):** Complete CI SHACL gating, add missing per-OWL positive/negative samples, and automate validator runs in `src/core/`.
- **Mid-term (3-9 months):** Expand modular OWL coverage (additional standards), automate ingestion pipelines, add RAG enforcement hooks, and produce more example traversal templates.
- **Long-term (9-18 months):** Build a web UI for traversal visualization, full CI enforcement for OWL/SHACL changes, and integrate explainable LLM-backed query interfaces.

## **Current Status**

- **Core Ontology:** Modular OWL files and core invariants are implemented under `docs/ontology/` and treated as frozen for Phase 3.
- **SHACL Validation:** `src/core/validation.py` and validator CLI exist; machine-readable reports are emitted to `artifacts/`; CI SHACL gating is scaffolded and being stabilized.
- **Ingestion:** Per-standard ETL transformers exist under `src/etl/`. ETLs now write a full per-standard TTL into `tmp/` plus canonical nodes/rels into `data/{standard}/samples/` (canonical loaders consume the samples folder).
- **Loader:** `src/etl/rdf_to_neo4j.py` supports nodes-only / rels-only loads, fast streaming parse, and safe defaults (`--dry-run`, `--reset-db` optional). Loader preserves existing predicates by default to avoid silent remapping; see Appendix for migration guidance.
- **Stats & Verification:** `scripts/utilities/extract_neo4j_stats.py` reports causal-chain metrics including CAPEC→Technique breakdown (Technique vs SubTechnique) and sample mappings, written to `artifacts/neo4j-stats-<db>.json`.
- **Tests & CI:** Unit and integration tests exercise ETLs and loader compatibility; the Phase 3 ingest smoke workflow runs tests and optional validation in CI.
- **Integrations & UI:** Neo4j loader and sample data are present; a production UI is planned but not yet implemented.

_For detailed technical documentation, please refer to the files in the `docs/` directory._
_The document KGCS.md provides a comprehensive overview of the architecture and design principles._
