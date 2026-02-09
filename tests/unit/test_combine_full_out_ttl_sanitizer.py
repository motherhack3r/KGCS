from pathlib import Path
from scripts.combine_ttl_pipeline import combine_ttl_files
from rdflib import Graph


def test_combine_ttl_sanitizer(tmp_path):
    inp = tmp_path / 'inp'
    inp.mkdir()

    # Create a sample TTL with a multi-line literal value that would normally break
    f1 = inp / 'pipeline-stage1-sample.ttl'
    f1.write_text('@prefix ex: <https://example.org/> .\n<https://example.org/s1> a <https://example.org/Type> .\n<https://example.org/s1> <https://example.org/prop> "Line one\nLine two" .\n', encoding='utf-8')

    # Create a rel file referencing s1
    f2 = inp / 'pipeline-stage2-rel.ttl'
    f2.write_text('@prefix ex: <https://example.org/> .\n<https://example.org/s2> <https://example.org/rel> <https://example.org/s1> .\n', encoding='utf-8')

    nodes_out = tmp_path / 'nodes_out.ttl'
    rels_out = tmp_path / 'rels_out.ttl'
    full_out = tmp_path / 'full_out.ttl'

    res = combine_ttl_files(nodes_out=str(nodes_out), rels_out=str(rels_out), heuristic_threshold=1, inputs=[str(inp)], full_out=str(full_out))
    assert res is True
    assert nodes_out.exists() and rels_out.exists()
    assert full_out.exists()

    # Now attempt to parse the combined TTL; this should succeed since sanitizer
    # merges/escapes multi-line literals and removes malformed fragments.
    g = Graph()
    g.parse(str(full_out), format='turtle')
    # Basic checks: s1 and s2 subjects present
    s1_count = len(list(g.subjects()))
    assert s1_count >= 2
