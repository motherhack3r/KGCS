This folder contains SHACL shapes and profiles for KGCS.

Files added:

- `core-shapes.ttl` — Core invariants and incident separation shapes.
- `ai-strict-profile.ttl` — Minimal AI-focused profile that includes core shapes and adds a few stricter rules.

Quick validation (example using pyshacl):

1. Install:

```bash
python -m pip install pyshacl rdflib
```

2. Validate an RDF data file (`data.ttl`) against the shapes:

```bash
pyshacl -s docs/ontology/shacl/core-shapes.ttl -s docs/ontology/shacl/ai-strict-profile.ttl -d data.ttl -f turtle
```

Notes:
- `pyshacl` accepts multiple `-s` shapes files.
- For large validation runs, run shapes as a combined graph and consider streaming or incremental validation.

Next steps I can take:
- Combine shapes into a single profile TTL and add more rules from RAG templates.
- Add example data snippets under `data/` and CI job to run `pyshacl` on push.
