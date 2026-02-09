from rdflib import Graph, URIRef, Literal
from src.etl.ttl_writer import write_graph_ntriples_lines
import tempfile
import os


def test_write_ntriples_simple(tmp_path):
    g = Graph()
    s = URIRef("https://example.org/foo")
    p = URIRef("https://example.org/prop")
    o = Literal("a string")
    g.add((s, p, o))

    out = tmp_path / "out.nt"
    write_graph_ntriples_lines(g, str(out))

    assert out.exists()
    text = out.read_text(encoding='utf-8')
    assert "<https://example.org/foo> <https://example.org/prop> \"a string\" ." in text
