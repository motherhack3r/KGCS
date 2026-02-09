from pathlib import Path
from scripts.combine_ttl_pipeline import combine_ttl_files


def test_combine_with_explicit_inputs(tmp_path):
    tmp_dir = tmp_path / "inputs"
    tmp_dir.mkdir()

    # Create two pipeline files (one .ttl, one .nt)
    f1 = tmp_dir / "pipeline-stage1-cwe.ttl"
    f1.write_text('@prefix ex: <https://example.org/> .\n<https://example.org/s1> a <https://example.org/Type> .\n<https://example.org/s1> <https://example.org/prop> "value1" .\n', encoding='utf-8')

    f2 = tmp_dir / "pipeline-stage2-car.nt"
    f2.write_text('<https://example.org/s2> <https://example.org/rel> <https://example.org/s1> .\n', encoding='utf-8')

    nodes_out = tmp_path / 'nodes_out.ttl'
    rels_out = tmp_path / 'rels_out.ttl'

    # Run combine with explicit inputs (directory)
    res = combine_ttl_files(nodes_out=str(nodes_out), rels_out=str(rels_out), heuristic_threshold=1, inputs=[str(tmp_dir)])
    assert res is True

    nodes_text = nodes_out.read_text(encoding='utf-8')
    rels_text = rels_out.read_text(encoding='utf-8')

    assert 'https://example.org/s1' in nodes_text
    assert '"value1"' in nodes_text
    assert '<https://example.org/s2> <https://example.org/rel> <https://example.org/s1>' in rels_text
