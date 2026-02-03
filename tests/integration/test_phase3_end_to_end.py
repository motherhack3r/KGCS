#!/usr/bin/env python3
"""Phase 3 end-to-end integration tests (ETL → SHACL → Neo4j).

These tests are opt-in because they can take a long time and require
local data + a running Neo4j instance.

Enable by setting:
    RUN_PHASE3_E2E=1
Optional:
    RUN_PHASE3_E2E_SHACL=1
    RUN_PHASE3_E2E_CLEAR=1  (clear Neo4j before loading)
"""

import os
import subprocess
import sys
from pathlib import Path

from rdflib import Graph

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = PROJECT_ROOT / "tmp"
COMBINED_TTL = TMP_DIR / "pipeline-stage-all.ttl"

RUN_E2E = os.getenv("RUN_PHASE3_E2E") == "1"
RUN_SHACL = os.getenv("RUN_PHASE3_E2E_SHACL") == "1"
RUN_CLEAR = os.getenv("RUN_PHASE3_E2E_CLEAR") == "1"


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
        TMP_DIR / "pipeline-stage5-d3fend.ttl",
        TMP_DIR / "pipeline-stage6-capec.ttl",
        TMP_DIR / "pipeline-stage7-cwe.ttl",
        TMP_DIR / "pipeline-stage8-car.ttl",
        TMP_DIR / "pipeline-stage9-shield.ttl",
        TMP_DIR / "pipeline-stage10-engage.ttl",
    ]

    missing = [str(path) for path in expected_outputs if not path.exists()]
    assert not missing, f"Missing ETL outputs: {', '.join(missing)}"

    attack_outputs = sorted(TMP_DIR.glob("pipeline-stage4-attack*.ttl"))
    assert attack_outputs, "Missing ATT&CK ETL outputs (pipeline-stage4-attack*.ttl)"


@pytest.mark.skipif(not RUN_E2E, reason="Set RUN_PHASE3_E2E=1 to enable")
def test_phase3_neo4j_load():
    """Load combined pipeline outputs into Neo4j using the loader utility."""
    neo4j = pytest.importorskip("neo4j")

    # Combine TTLs into a single file for relationship integrity
    files = [
        TMP_DIR / "pipeline-stage1-cpe.ttl",
        TMP_DIR / "pipeline-stage2-cpematch.ttl",
        TMP_DIR / "pipeline-stage3-cve.ttl",
        TMP_DIR / "pipeline-stage5-d3fend.ttl",
        TMP_DIR / "pipeline-stage6-capec.ttl",
        TMP_DIR / "pipeline-stage7-cwe.ttl",
        TMP_DIR / "pipeline-stage8-car.ttl",
        TMP_DIR / "pipeline-stage9-shield.ttl",
        TMP_DIR / "pipeline-stage10-engage.ttl",
    ]
    files.extend(sorted(TMP_DIR.glob("pipeline-stage4-attack*.ttl")))
    graph = Graph()
    for path in files:
        if path.exists():
            graph.parse(path, format="turtle")
    COMBINED_TTL.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(COMBINED_TTL), format="turtle")

    from src.config import neo4j_config
    if RUN_CLEAR:
        driver = neo4j.GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted,
        )
        with driver.session(database=neo4j_config.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()

    batch_size = os.getenv("NEO4J_BATCH_SIZE", "5000")
    cmd = [
        sys.executable,
        "-m",
        "src.etl.rdf_to_neo4j",
        "--ttl",
        str(COMBINED_TTL),
        "--batch-size",
        str(batch_size),
    ]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0

    from src.config import neo4j_config
    driver = neo4j.GraphDatabase.driver(
        neo4j_config.uri,
        auth=(neo4j_config.user, neo4j_config.password),
        encrypted=neo4j_config.encrypted,
    )
    with driver.session(database=neo4j_config.database) as session:
        counts = session.run(
            """
            MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt
            """
        ).data()
        by_type = {row["rel_type"]: row["cnt"] for row in counts}

        assert by_type.get("MATCHES_PLATFORM", 0) > 0
        assert by_type.get("AFFECTED_BY", 0) > 0
        assert by_type.get("CAUSED_BY", 0) > 0
        assert by_type.get("IMPLEMENTS", 0) > 0
    driver.close()


@pytest.mark.skipif(not (RUN_E2E and RUN_SHACL), reason="Set RUN_PHASE3_E2E=1 and RUN_PHASE3_E2E_SHACL=1 to enable")
def test_phase3_shacl_validation():
    """Run SHACL validation on selected pipeline outputs."""
    data_shapes_pairs = [
        ("tmp/pipeline-stage1-cpe.ttl", "docs/ontology/shacl/cpe-shapes.ttl"),
        ("tmp/pipeline-stage2-cpematch.ttl", "docs/ontology/shacl/cpe-shapes.ttl"),
        ("tmp/pipeline-stage3-cve.ttl", "docs/ontology/shacl/cve-shapes.ttl"),
        ("tmp/pipeline-stage5-d3fend.ttl", "docs/ontology/shacl/d3fend-shapes.ttl"),
        ("tmp/pipeline-stage6-capec.ttl", "docs/ontology/shacl/capec-shapes.ttl"),
        ("tmp/pipeline-stage7-cwe.ttl", "docs/ontology/shacl/cwe-shapes.ttl"),
        ("tmp/pipeline-stage8-car.ttl", "docs/ontology/shacl/car-shapes.ttl"),
        ("tmp/pipeline-stage9-shield.ttl", "docs/ontology/shacl/shield-shapes.ttl"),
        ("tmp/pipeline-stage10-engage.ttl", "docs/ontology/shacl/engage-shapes.ttl"),
    ]

    attack_shapes = "docs/ontology/shacl/attck-shapes.ttl"
    for attack_ttl in sorted(TMP_DIR.glob("pipeline-stage4-attack*.ttl")):
        data_shapes_pairs.append((str(attack_ttl), attack_shapes))

    for data_file, shapes_file in data_shapes_pairs:
        if not (PROJECT_ROOT / data_file).exists():
            continue
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
