# Ontology (OWL) — Canonical Documentation

This folder holds the canonical ontology documentation and OWL modules used by KGCS. When multiple copies of a standard's documentation exist, the canonical location is the markdown file in this folder.

## Documentation

Canonical per-standard documentation (MD):

- `attack-ontology-v1.0.md` — ATT&CK mapping and ETL fields
- `capec-ontology-v1.0.md` — CAPEC mapping and ETL fields
- `car-ontology-v1.0.md` — CAR mapping and ETL fields
- `cve-cpe-cpematch-ontology-v1.0.md` — CVE / CPE / CPEMatch mapping
- `cwe-ontology-v1.0.md` — CWE mapping and ETL fields
- `d3fend-ontology-v1.0.md` — D3FEND mapping and ETL fields
- `engage-ontology-v1.0.md` — ENGAGE mapping and ETL fields
- `shield-ontology-v1.0.md` — SHIELD mapping and ETL fields

OWL modules (RDF/XML/Turtle): these files contain the formal OWL ontologies and are the source for imports and reasoning. Examples in this folder include `core-ontology-v1.0.owl`, `core-ontology-extended-v1.0.owl`, `cpe-ontology-v1.0.owl`, `cve-ontology-v1.0.owl`, etc.

Required sections for each `*-ontology-v1.0.md` (canonical docs):

- **Overview** — scope and purpose
- **Classes** — key class list and descriptions
- **Relationships** — object/data properties and usage
- **SHACL** — high-level shapes or pointer to SHACL files
- **Field-by-Field mapping** — ETL mapping from source fields
- **Example** — small Turtle instance examples
- **References / Usage notes** — provenance and usage guidance

## Naming & versioning conventions

- Use `*-ontology-v1.0.md` for per-standard canonical docs.
- Keep OWL module filenames versioned: `module-name-v1.0.owl`.
- If you add an extension, place its docs and OWL in this folder and follow the same structure.

## Contact / maintenance

Maintainers should ensure each canonical MD is kept in sync with its OWL module; prefer updating the MD and OWL together and run SHACL/ROBOT checks in CI.
