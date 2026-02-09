"""Utility to write RDF graphs as line-based Turtle with full URIs.

This ensures one triple per line, which is required by KGCS streaming parsers.
"""

from __future__ import annotations

from typing import Iterable
from rdflib import Graph
from rdflib.term import URIRef, BNode, Literal

PREFIXES = (
    "@prefix sec: <https://example.org/sec/core#> .\n"
    "@prefix ex: <https://example.org/> .\n"
    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
)


def _escape_literal(value: str) -> str:
    return (
        value
        .replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _format_literal(literal: Literal) -> str:
    text = _escape_literal(str(literal))
    if literal.language:
        return f"\"{text}\"@{literal.language}"
    if literal.datatype:
        return f"\"{text}\"^^<{literal.datatype}>"
    return f"\"{text}\""


def _format_term(term) -> str | None:
    if isinstance(term, URIRef):
        return f"<{term}>"
    if isinstance(term, BNode):
        return f"_:{term}"
    if isinstance(term, Literal):
        return _format_literal(term)
    return None


def write_graph_turtle_lines(graph: Graph, output_path: str, include_prefixes: bool = True, append: bool = False) -> None:
    """Write a graph to a Turtle file with one triple per line and full URIs.
    
    Args:
        graph: RDF graph to write
        output_path: Output Turtle file path
        include_prefixes: Write RDF prefixes if True (only on new files)
        append: Append to file if True, overwrite if False
    """
    # Group triples by subject
    from collections import defaultdict
    triples_by_subject = defaultdict(list)
    for subj, pred, obj in graph:
        triples_by_subject[subj].append((subj, pred, obj))

    mode = "a" if append else "w"
    with open(output_path, mode, encoding="utf-8") as fh:
        # Only write prefixes on new files or when explicitly requested and not appending
        if include_prefixes and not append:
            fh.write(PREFIXES)
        # Write triples grouped by subject, sorted for determinism
        for subj in sorted(triples_by_subject, key=lambda s: str(s)):
            for s, p, o in triples_by_subject[subj]:
                s_fmt = _format_term(s)
                p_fmt = _format_term(p)
                o_fmt = _format_term(o)
                if not s_fmt or not p_fmt or not o_fmt:
                    continue
                fh.write(f"{s_fmt} {p_fmt} {o_fmt} .\n")


def write_graph_ntriples_lines(graph: Graph, output_path: str, append: bool = False) -> None:
    """Write a graph in N-Triples format (one triple per line).

    Args:
        graph: RDF graph to write
        output_path: Output file path
        append: Append to file if True, overwrite if False
    """
    mode = "a" if append else "w"
    # Sort triples for deterministic output
    triples = sorted(graph, key=lambda t: (str(t[0]), str(t[1]), str(t[2])))
    with open(output_path, mode, encoding="utf-8") as fh:
        for s, p, o in triples:
            s_fmt = _format_term(s)
            p_fmt = _format_term(p)
            o_fmt = _format_term(o)
            if not s_fmt or not p_fmt or not o_fmt:
                # Skip triples we cannot serialize safely
                continue
            fh.write(f"{s_fmt} {p_fmt} {o_fmt} .\n")
