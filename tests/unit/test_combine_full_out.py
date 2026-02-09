from pathlib import Path
from scripts.combine_ttl_pipeline import combine_ttl_files


def test_combine_writes_full_out(tmp_path):
    inp = tmp_path / 'inp'
    inp.mkdir()
    # create simple node and rel files
    f1 = inp / 'pipeline-stage1-a.ttl'
    f1.write_text('@prefix ex: <https://example.org/> .\n<https://example.org/s1> a <https://example.org/Type> .\n<https://example.org/s1> <https://example.org/prop> "v1" .\n', encoding='utf-8')
    f2 = inp / 'pipeline-stage2-b.nt'
    f2.write_text('<https://example.org/s2> <https://example.org/rel> <https://example.org/s1> .\n', encoding='utf-8')

    nodes_out = tmp_path / 'nodes_out.nt'
    rels_out = tmp_path / 'rels_out.nt'
    full_out = tmp_path / 'full_out.nt'

    res = combine_ttl_files(nodes_out=str(nodes_out), rels_out=str(rels_out), heuristic_threshold=1, inputs=[str(inp)], full_out=str(full_out))
    assert res is True
    assert nodes_out.exists() and rels_out.exists()
    assert full_out.exists()

    # Check ordering: first occurrence of s1 should be in nodes part and rels later
    text = full_out.read_text(encoding='utf-8')
    idx_node = text.find('https://example.org/s1')
    idx_rel = text.find('<https://example.org/s2> <https://example.org/rel>')
    assert idx_node != -1 and idx_rel != -1 and idx_node < idx_rel
