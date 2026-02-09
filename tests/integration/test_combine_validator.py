import os
import glob
from pathlib import Path
from scripts.combine_ttl_pipeline import combine_ttl_files


def read_latest_summary():
    logs = list(Path('logs').glob('combine-split-summary-*.json'))
    if not logs:
        return None
    latest = max(logs, key=lambda p: p.stat().st_mtime)
    import json
    with open(latest, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_combine_detects_missing_type(tmp_path):
    tmp_dir = Path('tmp')
    tmp_dir.mkdir(exist_ok=True)
    # Create a bad stage file (literal property, no rdf:type)
    stage = tmp_dir / 'pipeline-stage1-bad.ttl'
    stage.write_text('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n<http://example.org/s1> <http://example.org/prop> "value" .\n', encoding='utf-8')

    nodes_out = tmp_path / 'nodes_out.ttl'
    rels_out = tmp_path / 'rels_out.ttl'

    # Run combine
    res = combine_ttl_files(nodes_out=str(nodes_out), rels_out=str(rels_out), heuristic_threshold=1)
    assert res is True

    summary = read_latest_summary()
    assert summary is not None
    diag = summary.get('diagnostics', {})
    assert diag.get('bad_node_subjects_count', 0) > 0


def test_combine_passes_when_types_present(tmp_path):
    tmp_dir = Path('tmp')
    tmp_dir.mkdir(exist_ok=True)
    # Create a good stage file (literal property with rdf:type)
    stage = tmp_dir / 'pipeline-stage1-good.ttl'
    stage.write_text('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n<http://example.org/s1> a <http://example.org/Type> .\n<http://example.org/s1> <http://example.org/prop> "value" .\n', encoding='utf-8')

    nodes_out = tmp_path / 'nodes_out2.ttl'
    rels_out = tmp_path / 'rels_out2.ttl'

    res = combine_ttl_files(nodes_out=str(nodes_out), rels_out=str(rels_out), heuristic_threshold=1)
    assert res is True

    summary = read_latest_summary()
    assert summary is not None
    diag = summary.get('diagnostics', {})
    assert diag.get('bad_node_subjects_count', 0) == 0
