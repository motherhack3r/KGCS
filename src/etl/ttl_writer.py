"""Utility to write RDF graphs as line-based Turtle with full URIs.

This ensures one triple per line, which is required by KGCS streaming parsers.
"""

from __future__ import annotations

from typing import Iterable
from rdflib import Graph, RDF
from rdflib.term import URIRef, BNode, Literal

PREFIXES = (
    "@prefix sec: <https://example.org/sec/core#> .\n"
    "@prefix ex: <https://example.org/> .\n"
    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
    "@prefix dcterms: <http://purl.org/dc/terms/> .\n\n"
)


import re


def _escape_literal(value: str) -> str:
    # Normalize to str in case non-str types are passed
    s = str(value)
    # Remove embedded Python byte-string reprs like b'...'
    s = re.sub(r"\bb'([^']*)'", r"\1", s)
    # Escape backslashes and double quotes, and common control chars
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    # Remove other non-printable control chars (except allowed whitespace above)
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", s)
    return s


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


def write_graph_turtle_lines(graph: Graph, output_path: str, include_prefixes: bool = True, append: bool = False, nodes_first: bool = True) -> None:
    """Write a graph to a Turtle file with one triple per line and full URIs.

    Args:
        graph: RDF graph to write
        output_path: Output Turtle file path
        include_prefixes: Write RDF prefixes if True (only on new files)
        append: Append to file if True, overwrite if False
        nodes_first: When True, write node triples (rdf:type or literal objects)
                     before relation triples for each subject.
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
            group = triples_by_subject[subj]
            if nodes_first:
                type_lines = []
                literal_lines = []
                other_lines = []
                for s, p, o in group:
                    s_fmt = _format_term(s)
                    p_fmt = _format_term(p)
                    o_fmt = _format_term(o)
                    if not s_fmt or not p_fmt or not o_fmt:
                        continue
                    # identify rdf:type (or 'a')
                    pred_lower = str(p).lower() if isinstance(p, URIRef) else ''
                    if str(p) == 'a' or 'rdf-syntax-ns#type' in pred_lower or 'rdf:type' in pred_lower:
                        type_lines.append(f"{s_fmt} {p_fmt} {o_fmt} .\n")
                    elif isinstance(o, Literal):
                        literal_lines.append(f"{s_fmt} {p_fmt} {o_fmt} .\n")
                    else:
                        other_lines.append(f"{s_fmt} {p_fmt} {o_fmt} .\n")
                for l in type_lines + literal_lines + other_lines:
                    fh.write(l)
            else:
                for s, p, o in group:
                    s_fmt = _format_term(s)
                    p_fmt = _format_term(p)
                    o_fmt = _format_term(o)
                    if not s_fmt or not p_fmt or not o_fmt:
                        continue
                    fh.write(f"{s_fmt} {p_fmt} {o_fmt} .\n")


def write_graph_ntriples_lines(graph: Graph, output_path: str, append: bool = False, nodes_first: bool = True) -> None:
    """Write a graph in N-Triples format (one triple per line).

    Args:
        graph: RDF graph to write
        output_path: Output file path
        append: Append to file if True, overwrite if False
        nodes_first: When True, order triples so that node triples (literal objects or rdf:type)
                     come before relationship triples for the same subject.
    """
    mode = "a" if append else "w"
    # Sort triples for deterministic output, optionally putting node triples first
    def _is_node_triple(t):
        o = t[2]
        if isinstance(o, Literal):
            return True
        # rdf:type detection (predicate == rdf:type)
        try:
            pred_str = str(t[1]).lower()
            if 'rdf-syntax-ns#type' in pred_str or 'rdf:type' in pred_str or str(t[1]) == 'a':
                return True
        except Exception:
            pass
        return False

    if nodes_first:
        triples = sorted(graph, key=lambda t: (str(t[0]), 0 if _is_node_triple(t) else 1, str(t[1]), str(t[2])))
    else:
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


def _is_node_triple(triple) -> bool:
    _, pred, obj = triple
    if isinstance(obj, Literal):
        return True
    try:
        return str(pred) == str(RDF.type)
    except Exception:
        return False


def write_graph_turtle_split_lines(
    graph: Graph,
    nodes_output_path: str,
    rels_output_path: str,
    include_prefixes: bool = True,
    append: bool = False,
    nodes_first: bool = True,
    rels_include_types: bool = False,
) -> None:
    """Write a graph into nodes-only and relationships-only Turtle files."""
    mode = "a" if append else "w"
    with open(nodes_output_path, mode, encoding="utf-8") as nodes_fh, \
            open(rels_output_path, mode, encoding="utf-8") as rels_fh:
        if include_prefixes and not append:
            nodes_fh.write(PREFIXES)
            rels_fh.write(PREFIXES)

        triples = list(graph)
        rel_endpoints = set()
        if rels_include_types:
            for s, p, o in triples:
                if _is_node_triple((s, p, o)):
                    continue
                if isinstance(o, Literal):
                    continue
                rel_endpoints.add(s)
                rel_endpoints.add(o)
        if nodes_first:
            triples = sorted(triples, key=lambda t: (str(t[0]), 0 if _is_node_triple(t) else 1, str(t[1]), str(t[2])))
        else:
            triples = sorted(triples, key=lambda t: (str(t[0]), str(t[1]), str(t[2])))

        for s, p, o in triples:
            s_fmt = _format_term(s)
            p_fmt = _format_term(p)
            o_fmt = _format_term(o)
            if not s_fmt or not p_fmt or not o_fmt:
                continue
            line = f"{s_fmt} {p_fmt} {o_fmt} .\n"
            is_node_triple = _is_node_triple((s, p, o))
            if is_node_triple:
                nodes_fh.write(line)
                if rels_include_types and str(p) == str(RDF.type) and s in rel_endpoints:
                    rels_fh.write(line)
            else:
                rels_fh.write(line)


def write_graph_ntriples_split_lines(
    graph: Graph,
    nodes_output_path: str,
    rels_output_path: str,
    append: bool = False,
    nodes_first: bool = True,
    rels_include_types: bool = False,
) -> None:
    """Write a graph into nodes-only and relationships-only N-Triples files."""
    mode = "a" if append else "w"
    triples = list(graph)
    rel_endpoints = set()
    if rels_include_types:
        for s, p, o in triples:
            if _is_node_triple((s, p, o)):
                continue
            if isinstance(o, Literal):
                continue
            rel_endpoints.add(s)
            rel_endpoints.add(o)
    if nodes_first:
        triples = sorted(triples, key=lambda t: (str(t[0]), 0 if _is_node_triple(t) else 1, str(t[1]), str(t[2])))
    else:
        triples = sorted(triples, key=lambda t: (str(t[0]), str(t[1]), str(t[2])))

    with open(nodes_output_path, mode, encoding="utf-8") as nodes_fh, \
            open(rels_output_path, mode, encoding="utf-8") as rels_fh:
        for s, p, o in triples:
            s_fmt = _format_term(s)
            p_fmt = _format_term(p)
            o_fmt = _format_term(o)
            if not s_fmt or not p_fmt or not o_fmt:
                continue
            line = f"{s_fmt} {p_fmt} {o_fmt} .\n"
            is_node_triple = _is_node_triple((s, p, o))
            if is_node_triple:
                nodes_fh.write(line)
                if rels_include_types and str(p) == str(RDF.type) and s in rel_endpoints:
                    rels_fh.write(line)
            else:
                rels_fh.write(line)
