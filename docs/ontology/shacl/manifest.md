SHACL manifest (machine)
=========================

The authoritative, machine-readable OWL → SHACL mapping is in
`docs/ontology/shacl/manifest.json`.

Use `manifest.json` for tooling and CI. This markdown file is a short human-facing note and may be updated to reference or document policies; mapping edits should be made in the JSON manifest.
SHACL manifest: OWL → shape bundles
===================================

This manifest maps OWL module files (in `docs/ontology/owl/`) to the recommended SHACL shape bundle(s) that should be validated for that module.

- `cpe-ontology-v1.0.owl` → `docs/ontology/shacl/cpe-shapes.ttl`
- `cve-ontology-v1.0.owl` → `docs/ontology/shacl/cve-shapes.ttl`
- `cwe-ontology-v1.0.owl` → `docs/ontology/shacl/cwe-shapes.ttl`
- `capec-ontology-v1.0.owl` → `docs/ontology/shacl/capec-shapes.ttl`
- `attck-ontology-v1.0.owl` → `docs/ontology/shacl/attck-shapes.ttl`
- `d3fend-ontology-v1.0.owl` → `docs/ontology/shacl/d3fend-shapes.ttl`
- `car-ontology-v1.0.owl` → `docs/ontology/shacl/car-shapes.ttl`
- `shield-ontology-v1.0.owl` → `docs/ontology/shacl/shield-shapes.ttl`
- `engage-ontology-v1.0.owl` → `docs/ontology/shacl/engage-shapes.ttl`
- `core-ontology-extended-v1.0.owl` → `docs/ontology/shacl/core-extended-shapes.ttl`
- `incident-ontology-extension-v1.0.owl` → `docs/ontology/shacl/kgcs-shapes.ttl` (use incident shapes in canonical bundle)
- `risk-ontology-extension-v1.0.owl` → `docs/ontology/shacl/kgcs-shapes.ttl` (use risk shapes in canonical bundle)
- `threatactor-ontology-extension-v1.0.owl` → `docs/ontology/shacl/kgcs-shapes.ttl`

Recommendation: CI should validate the specific bundle(s) for the OWL modules changed by a PR. The canonical bundle `docs/ontology/shacl/kgcs-shapes.ttl` remains the superset for full validation.
