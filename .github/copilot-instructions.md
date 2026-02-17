# Copilot & AI Agent Instructions for KGCS

## Project Overview
- **KGCS** is a standards-backed cybersecurity knowledge graph unifying MITRE/NVD taxonomies (CVE, CWE, CPE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).
- Core ontology is immutable and mapped 1:1 to official schemas; extensions add context but never modify core.
- Data flows: Download → ETL (per standard) → SHACL validation → Neo4j load → Query/Export.
- See [docs/KGCS.md](../docs/KGCS.md) and [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for architecture and design principles.

## Ontology & Governance Rules

**Priority Order (Non-Negotiable):**
1. Ontology correctness (OWL semantics)
2. Governance correctness (SHACL constraints)
3. Causal traceability (authoritative standards)
4. Operational correctness (ETL, pipelines)
5. Developer convenience

**Immutable Rules:**
- **Mandatory causal chain:** CPE → CVEMatch → CVE → CWE → CAPEC → ATT&CK → {D3FEND, CAR, SHIELD, ENGAGE}. Every hop must exist in authoritative NVD or MITRE data. Skipping steps breaks traceability and is forbidden.
- **PlatformConfiguration, not Platform:** Vulnerabilities affect configurations (version bounds, update state), never abstract platforms.
- **CVSS version separation:** CVSS v2.0, v3.1, v4.0 are separate nodes. Never merge, normalize, or overwrite scores.
- **Core ontologies are frozen:** OWL modules in docs/ontology/owl/ are immutable. Extensions must import core without modification.
- **No fabricated edges:** Every relationship must be traceable to source data (IDs, fields, references).

**Ontology Reasoning Contract:**
- Only infer class membership, relationships, and constraints explicitly present in OWL, source standards, or SHACL.
- Never infer threat likelihood, attack success, actor intent, or risk meaning beyond declared scores.
- If not present in NVD or MITRE data, it does not exist.

**Open World vs Closed World:**
- OWL is open-world; SHACL enforces closed-world constraints. ETL must never simulate closed-world logic.

**Responsibility Split:**
| Concern | Location |
|---------|----------|
| Semantic meaning | OWL |
| Allowed graph shapes | SHACL |
| Data correctness | SHACL |
| Performance / batching | ETL |
| RAG safety | SHACL + query templates |

**ETL Transformer Discipline:**
- ETL transformers are dumb serializers: parse authoritative data, emit triples, preserve identifiers and provenance.
- Never interpret meaning, infer relationships, apply heuristics, or collapse abstraction layers.

**Validation Workflow:**
- SHACL validation is mandatory before Neo4j ingestion. If SHACL and OWL disagree, SHACL governs operational behavior; ETL must not work around the conflict.

**RAG Safety Contract:**
- Only use traversal paths explicitly listed in approved templates (docs/ontology/rag/). Each hop must be backed by authoritative data and constrained by SHACL. No traversal may collapse abstraction layers.

**Anti-Patterns (Absolute Prohibitions):**
- Never collapse CPE → CVE → CWE into a single concept.
- Never treat ATT&CK techniques as events that “happen.”
- Never introduce transitive closure without explicit standard backing.
- Never attribute incidents to threat actors by inference.
- Never add helper or shortcut edges for convenience.

**Testing Rules:**
- A test that passes but violates ontology principles is a failed test. Ontology rules validate truth; truth always wins.

**Extension Development:**
- Extensions may add context, never meaning. They must import core ontologies, remain semantically non-invasive, and avoid inference or reinterpretation.

**Mental Model Reminder:**
- KGCS is not an attack simulator, prediction engine, or risk calculator. It is a semantic truth layer. Your job is to protect that truth, even when inconvenient.

## Environment Setup (MANDATORY)

Before running any command, always activate the workspace conda environment:

> (E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
> conda activate E:\DEVEL\LAIA\KGCS\.conda

Ensure you are using the correct terminal type for your OS (PowerShell for Windows). Do not attempt to run bash commands in PowerShell or Python interpreter shells.

---

## Key Workflows

**Authoritative Pipeline Instructions**

> **Always use [docs/PIPELINE_EXECUTION_GUIDE.md](../docs/PIPELINE_EXECUTION_GUIDE.md) as the source of truth for running the KGCS pipeline.**
>
> - The "Quick Commands" section in that file is the most reliable, validated, and up-to-date workflow for end-to-end execution (download → ETL → load → stats).
> - If there is any conflict or ambiguity between documentation files, prefer PIPELINE_EXECUTION_GUIDE.md over the root README or other markdown files.
> - Some other documentation (including the root README) may be outdated; always check the pipeline guide first for operational steps.


**Example (see guide for full details):**

> Replace `<YYYY-MM-DD>` with the current date for your run (e.g., `2026-02-17`).

```powershell
# Activate environment
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\LAIA\KGCS\.conda
cd e:\DEVEL\LAIA\KGCS

# Download
E:/DEVEL/LAIA/KGCS/.conda/python.exe -m src.ingest.download_manager

# Run ETL
E:/DEVEL/LAIA/KGCS/.conda/python.exe scripts/run_all_etl.py

# Load nodes then relationships
.\scripts\load_nodes_all.ps1 -PythonExe E:/DEVEL/LAIA/KGCS/.conda/python.exe -DbVersion <YYYY-MM-DD> -FastParse -ProgressNewline -ParseHeartbeatSeconds 20
.\scripts\load_rels_all.ps1 -PythonExe E:/DEVEL/LAIA/KGCS/.conda/python.exe -DbVersion <YYYY-MM-DD> -FastParse -ProgressNewline -ParseHeartbeatSeconds 20

# Extract stats
python .\scripts\utilities\extract_neo4j_stats.py --db neo4j-<YYYY-MM-DD> --output artifacts/neo4j-stats-<YYYY-MM-DD>.json --pretty
```

- **Full pipeline:** `python scripts/run_all_etl.py` (orchestrates all ETL stages)
- **Iterative/targeted ETL:** `python scripts/run_standard_pipeline.py` (interactive, per-standard)
- **Validation:** `python scripts/validation/validate_all_standards.py` (SHACL for all outputs)
- **Combine outputs:** `python scripts/combine_pipeline.py`
- **Neo4j load:** Use PowerShell scripts or `src/etl/rdf_to_neo4j.py` (see scripts/utilities/README.md)
- **Testing:** `pytest tests/ -v` (unit, integration, data load, utilities)

## Directory Conventions
- **src/etl/**: Per-standard ETL modules (e.g., `etl_capec.py`)
- **data/{standard}/samples/**: Canonical ETL outputs (nodes/relationships TTL)
- **tmp/**: Full per-standard TTLs for debugging/combining
- **artifacts/**: Final outputs, stats, and validation reports
- **scripts/validation/**: SHACL and pipeline validation scripts
- **scripts/utilities/**: Neo4j, export, and admin tools
- **tests/**: Unit, integration, data load, utility, and manual verification scripts

## Project-Specific Patterns
- **ETL outputs**: Always write both full TTL (to `tmp/`) and canonical split files (to `data/{standard}/samples/`). Loaders consume only canonical samples.
- **Loader safety**: Neo4j loader defaults to safe mode (no DB reset, dry-run supported).
- **Predicate naming**: All cross-standard relationships must use canonical predicates in the `SEC` namespace (e.g., `SEC.implemented_as`, `SEC.related_to`). This applies to all standards, not just CAPEC→ATT&CK. If legacy ETLs emit non-canonical predicates, canonicalize via migration or update the ETL to enforce `SEC` predicates. No silent remapping occurs during load.
- **Validation**: SHACL validation is required for all new/changed ontology artifacts; CI enforces this.
- **Testing**: All scripts and ETLs are idempotent and log to `logs/`. Use small sample data for fast tests.
- **Manual verification**: Use scripts in `tests/verification/` for graph inspection (always exit 0).

## Integration & Extensibility
- **Adding standards**: Follow [docs/EXTENDING.md](../docs/EXTENDING.md); add new ETL under `src/etl/`, update pipeline scripts, and provide SHACL shapes.
- **RAG integration**: Use only pre-approved traversal templates in `docs/ontology/rag/`.
- **External data**: Download raw JSON/STIX into `data/{standard}/raw/`.

## References
- [docs/PIPELINE_EXECUTION_GUIDE.md](../docs/PIPELINE_EXECUTION_GUIDE.md): End-to-end pipeline
- [docs/GLOSSARY.md](../docs/GLOSSARY.md): Definitions
- [scripts/README.md](../scripts/README.md): Script usage and conventions
- [tests/README.md](../tests/README.md): Test organization and expectations

---
**Last updated:** 2026-02-17
