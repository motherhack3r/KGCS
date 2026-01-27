#!/usr/bin/env python3
"""Phase 3 end-to-end integration tests (ETL → SHACL → Neo4j).

These tests are opt-in because they can take a long time and require
local data + a running Neo4j instance.

Enable by setting:
  RUN_PHASE3_E2E=1
Optional:
  RUN_PHASE3_E2E_SHACL=1
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = PROJECT_ROOT / "tmp"

RUN_E2E = os.getenv("RUN_PHASE3_E2E") == "1"
RUN_SHACL = os.getenv("RUN_PHASE3_E2E_SHACL") == "1"


@pytest.mark.skipif(not RUN_E2E, reason="Set RUN_PHASE3_E2E=1 to enable")
def test_phase3_etl_pipeline_order():
    """Run ETL pipeline in correct order and verify outputs exist."""
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "validate_etl_pipeline_order.py")]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0

    expected_outputs = [
        TMP_DIR / "pipeline-stage1-cpe.ttl",
        TMP_DIR / "pipeline-stage2-cpematch.ttl",
        TMP_DIR / "pipeline-stage3-cve.ttl",
        TMP_DIR / "pipeline-stage4-attack.ttl",
        TMP_DIR / "pipeline-stage5-d3fend.ttl",
        TMP_DIR / "pipeline-stage6-capec.ttl",
        TMP_DIR / "pipeline-stage7-cwe.ttl",
        TMP_DIR / "pipeline-stage9-shield.ttl",
        TMP_DIR / "pipeline-stage10-engage.ttl",
    ]

    missing = [str(path) for path in expected_outputs if not path.exists()]
    assert not missing, f"Missing ETL outputs: {', '.join(missing)}"


@pytest.mark.skipif(not RUN_E2E, reason="Set RUN_PHASE3_E2E=1 to enable")
def test_phase3_neo4j_load():
    """Load pipeline outputs into Neo4j using the loader utility."""
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    if not neo4j_password:
        pytest.skip("NEO4J_PASSWORD is required for Neo4j load test")

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "src" / "utils" / "load_to_neo4j.py"),
        "--input",
        str(TMP_DIR),
    ]

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0


@pytest.mark.skipif(not (RUN_E2E and RUN_SHACL), reason="Set RUN_PHASE3_E2E=1 and RUN_PHASE3_E2E_SHACL=1 to enable")
def test_phase3_shacl_validation():
    """Run SHACL validation on selected pipeline outputs."""
    data_shapes_pairs = [
        ("tmp/pipeline-stage1-cpe.ttl", "docs/ontology/shacl/cpe-shapes.ttl"),
        ("tmp/pipeline-stage2-cpematch.ttl", "docs/ontology/shacl/cpe-shapes.ttl"),
        ("tmp/pipeline-stage3-cve.ttl", "docs/ontology/shacl/cve-shapes.ttl"),
    ]

    for data_file, shapes_file in data_shapes_pairs:
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "validate_shacl_stream.py"),
            "--data",
            data_file,
            "--shapes",
            shapes_file,
        ]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        assert result.returncode == 0
