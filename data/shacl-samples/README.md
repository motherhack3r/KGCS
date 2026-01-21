SHACL sample TTLs
==================

This directory contains positive and negative SHACL samples used to test per-OWL and canonical shape bundles.

Files added:

- car-good.ttl / car-bad.ttl
- d3fend-good.ttl / d3fend-bad.ttl
- cwe-good.ttl / cwe-bad.ttl
- capec-good.ttl / capec-bad.ttl
- shield-good.ttl / shield-bad.ttl
- engage-good.ttl / engage-bad.ttl

Quick validation commands (run from the repository root):

PowerShell:

```powershell
python -m pip install --upgrade pip; pip install rdflib pyshacl
foreach ($f in Get-ChildItem -Path 'data/shacl-samples' -Filter '*.ttl') {
  Write-Host "Validating $($f.FullName)";
  python -m src.cli.validate --data $f.FullName --shapes docs/ontology/shacl/kgcs-shapes.ttl
}
```

POSIX shell (linux/mac):

```bash
python -m pip install --upgrade pip
pip install rdflib pyshacl
for f in data/shacl-samples/*.ttl; do
  echo "Validating $f"
  python -m src.cli.validate --data "$f" --shapes docs/ontology/shacl/kgcs-shapes.ttl
done
```

If you'd like these samples validated automatically in CI on every PR, I can update `.github/workflows/shacl-validation.yml` to include a dedicated job that validates all files in this directory and fails the job on any non-conformance.
