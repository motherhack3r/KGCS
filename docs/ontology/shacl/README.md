KGCS SHACL shapes
==================

This folder contains SHACL shapes that validate critical invariants derived from the Core Ontology v1.0 and its extensions. Use `kgcs-shapes.ttl` as the canonical shape bundle for CI and local validation.

Key invariants enforced (non-exhaustive):

- `Vulnerability` must have a `cveId`.

- `VulnerabilityScore` must have a `cvssVersion` and `baseScore`.

- `Platform` must have a `cpeNameId`.

- `PlatformConfiguration` must have a `matchCriteriaId`.

- `Technique` must link to at least one `Tactic` via `belongs_to`.

- `SubTechnique` must have a `subtechnique_of` parent.

Run validator (example):

```bash
python -m src.cli.validate --shapes docs/ontology/shacl/kgcs-shapes.ttl --data data/samples/example.ttl
```

Or using the CLI wrapper:

```bash
python scripts/validate_shacl_cli.py --shapes docs/ontology/shacl/kgcs-shapes.ttl --data data/samples/example.ttl
```

See `rag-to-shacl.md` for how RAG templates map to shape groups.
