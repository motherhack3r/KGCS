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


def write_graph_turtle_lines(graph: Graph, output_path: str, include_prefixes: bool = True) -> None:
    """Write a graph to a Turtle file with one triple per line and full URIs."""
    with open(output_path, "w", encoding="utf-8") as fh:
        if include_prefixes:
            fh.write(PREFIXES)
        for subj, pred, obj in graph:
            s = _format_term(subj)
            p = _format_term(pred)
            o = _format_term(obj)
            if not s or not p or not o:
                continue
            fh.write(f"{s} {p} {o} .\n")
