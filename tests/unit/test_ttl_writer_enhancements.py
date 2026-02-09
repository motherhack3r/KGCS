from rdflib import Graph, Literal, URIRef
from src.etl.ttl_writer import PREFIXES, _escape_literal, write_graph_turtle_lines, write_graph_ntriples_lines
from pathlib import Path


def test_prefixes_include_dcterms():
    assert 'dcterms' in PREFIXES


def test_escape_literal_strips_byte_repr():
    s = "This contains a byte repr b'abc' and newlines\nand tabs\t"
    out = _escape_literal(s)
    assert "b'" not in out
    assert "\\n" in out and "\\t" in out


def test_write_nodes_first_turtle(tmp_path):
    g = Graph()
    s = URIRef('https://example.org/s1')
    g.add((s, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), URIRef('https://example.org/Type')))
    g.add((s, URIRef('https://example.org/prop'), Literal('val')))
    g.add((s, URIRef('https://example.org/rel'), URIRef('https://example.org/other')))

    out = tmp_path / 'out.ttl'
    write_graph_turtle_lines(g, str(out), include_prefixes=True, append=False, nodes_first=True)
    text = out.read_text(encoding='utf-8')
    # ensure literal and type occur before relation for subject s
    idx_type = text.find('https://example.org/Type')
    idx_rel = text.find('<https://example.org/other>')
    assert idx_type != -1 and idx_type < idx_rel


def test_write_nodes_first_nt(tmp_path):
    g = Graph()
    s = URIRef('https://example.org/s2')
    g.add((s, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), URIRef('https://example.org/Type')))
    g.add((s, URIRef('https://example.org/prop'), Literal('val')))
    g.add((s, URIRef('https://example.org/rel'), URIRef('https://example.org/other')))

    out = tmp_path / 'out.nt'
    write_graph_ntriples_lines(g, str(out), append=False, nodes_first=True)
    text = out.read_text(encoding='utf-8')
    idx_type = text.find('https://example.org/Type')
    idx_rel = text.find('<https://example.org/other>')
    assert idx_type != -1 and idx_type < idx_rel
