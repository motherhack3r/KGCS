#!/usr/bin/env python3
"""
validate_all_standards.py

Runs SHACL validation for all KGCS standards, automatically choosing the optimal validation script and arguments for each TTL file based on file size and standard.

- Large files (CPE, CPEMatch, CVE): use validate_shacl_stream.py with chunking.
- Medium/small files (others): use validate_shacl_parallel.py for batch validation.
- Ensures all standards are validated and reports results.
"""
import os
import subprocess
import sys
from pathlib import Path

# Map of standard to (ttl_path, shapes_path, validation_script, extra_args)
STANDARDS = [
    # (standard, ttl_path, shapes_path, script, extra_args)
    ("cpe", "tmp/pipeline-stage1-cpe.ttl", "docs/ontology/shacl/cpe-shapes.ttl", "stream", ["--chunk-size", "500000","--workers","8"]),
    ("cpematch", "tmp/pipeline-stage2-cpematch.ttl", "docs/ontology/shacl/cpematch-shapes.ttl", "stream", ["--chunk-size", "500000","--workers","8"]),
    ("cve", "tmp/pipeline-stage3-cve.ttl", "docs/ontology/shacl/cve-shapes.ttl", "stream", ["--chunk-size", "50000","--workers","8"]),
    ("attack", "tmp/pipeline-stage4-attack.ttl", "docs/ontology/shacl/attack-shapes.ttl", "parallel", []),
    ("d3fend", "tmp/pipeline-stage5-d3fend.ttl", "docs/ontology/shacl/d3fend-shapes.ttl", "parallel", []),
    ("capec", "tmp/pipeline-stage6-capec.ttl", "docs/ontology/shacl/capec-shapes.ttl", "parallel", []),
    ("cwe", "tmp/pipeline-stage7-cwe.ttl", "docs/ontology/shacl/cwe-shapes.ttl", "parallel", []),
    ("car", "tmp/pipeline-stage8-car.ttl", "docs/ontology/shacl/car-shapes.ttl", "parallel", []),
    ("shield", "tmp/pipeline-stage9-shield.ttl", "docs/ontology/shacl/shield-shapes.ttl", "parallel", []),
    ("engage", "tmp/pipeline-stage10-engage.ttl", "docs/ontology/shacl/engage-shapes.ttl", "parallel", []),
]

STREAM_SCRIPT = "scripts/validation/validate_shacl_stream.py"
PARALLEL_SCRIPT = "scripts/validation/validate_shacl_parallel.py"


def validate_standard(standard, ttl_path, shapes_path, script_type, extra_args):
    if not Path(ttl_path).exists():
        print(f"[ERROR] TTL file missing for {standard}: {ttl_path}")
        return False
    if not Path(shapes_path).exists():
        print(f"[ERROR] SHACL shapes file missing for {standard}: {shapes_path}")
        return False
    if script_type == "stream":
        cmd = [sys.executable, STREAM_SCRIPT, "--data", ttl_path, "--shapes", shapes_path, "--summary-report", f"artifacts/shacl-report-{standard}-summary.json"] + extra_args
    else:
        cmd = [sys.executable, PARALLEL_SCRIPT, "--data", ttl_path, "--shapes", shapes_path, "--summary-report", f"artifacts/shacl-report-{standard}-summary.json"] + extra_args
    print(f"\n[VALIDATING] {standard.upper()} using {script_type} script...")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"[SUCCESS] {standard.upper()} validated successfully.")
        return True
    else:
        print(f"[FAIL] {standard.upper()} validation failed.")
        return False

def main():
    # Validate CPE, CPEMATCH, CVE using stream script
    stream_standards = [
        ("cpe", "tmp/pipeline-stage1-cpe.ttl", "docs/ontology/shacl/cpe-shapes.ttl", ["--chunk-size", "500000", "--workers", "8"]),
        ("cpematch", "tmp/pipeline-stage2-cpematch.ttl", "docs/ontology/shacl/cpematch-shapes.ttl", ["--chunk-size", "500000", "--workers", "8"]),
        ("cve", "tmp/pipeline-stage3-cve.ttl", "docs/ontology/shacl/cve-shapes.ttl", ["--chunk-size", "50000", "--workers", "8"]),
    ]
    failed = []
    for standard, ttl_path, shapes_path, extra_args in stream_standards:
        if not Path(ttl_path).exists():
            print(f"[ERROR] TTL file missing for {standard}: {ttl_path}")
            failed.append(standard)
            continue
        if not Path(shapes_path).exists():
            print(f"[ERROR] SHACL shapes file missing for {standard}: {shapes_path}")
            failed.append(standard)
            continue
        cmd = [sys.executable, STREAM_SCRIPT, "--data", ttl_path, "--shapes", shapes_path, "--summary-report", f"artifacts/shacl-report-{standard}-summary.json"] + extra_args
        print(f"\n[VALIDATING] {standard.upper()} using stream script...")
        result = subprocess.run(cmd)
        if result.returncode == 0:
            print(f"[SUCCESS] {standard.upper()} validated successfully.")
        else:
            print(f"[FAIL] {standard.upper()} validation failed.")
            failed.append(standard)

    # Validate remaining standards using parallel script (single call)
    print("\n[VALIDATING] ATTACK, D3FEND, CAPEC, CWE, CAR, SHIELD, ENGAGE using parallel script...")
    result = subprocess.run([sys.executable, PARALLEL_SCRIPT])
    if result.returncode == 0:
        print(f"[SUCCESS] Parallel validation completed.")
    else:
        print(f"[FAIL] Parallel validation failed.")
        failed.append("PARALLEL_VALIDATION")

    if not failed:
        print("\nAll standards validated successfully.")
        sys.exit(0)
    else:
        print("\nSome standards failed validation. See above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
