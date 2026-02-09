#!/usr/bin/env python3
"""Split a combined TTL into two TTLs: node triples and relationship triples.

Heuristic used:
- Node triples: predicate == rdf:type OR object is a Literal OR predicate listed in
  --node-predicate (can be repeated).
- Relationship triples: object is a URI or BNode and predicate != rdf:type and
  predicate not in --node-predicate.

Requires: rdflib
"""
import argparse
import sys
from rdflib import Graph, RDF, URIRef, BNode, Literal


def split_ttl(input_path, nodes_out, rels_out, node_predicates):
    g = Graph()
    g.parse(input_path, format="turtle")

    nodes_g = Graph()
    rels_g = Graph()

    # copy namespaces
    for prefix, ns in g.namespaces():
        nodes_g.bind(prefix, ns)
        rels_g.bind(prefix, ns)

    node_predicates_set = set(node_predicates or [])

    for s, p, o in g:
        # predicate may be a string from args; compare by URI if provided
        p_str = str(p)
        is_node_pred = (p == RDF.type) or (p_str in node_predicates_set)

        if is_node_pred or isinstance(o, Literal):
            nodes_g.add((s, p, o))
        else:
            # object is URIRef or BNode -> relationship-like
            if isinstance(o, (URIRef, BNode)):
                # but still allow predicate override
                if p_str in node_predicates_set:
                    nodes_g.add((s, p, o))
                else:
                    rels_g.add((s, p, o))
            else:
                # fallback: treat as node triple
                nodes_g.add((s, p, o))

    nodes_g.serialize(destination=nodes_out, format="turtle")
    rels_g.serialize(destination=rels_out, format="turtle")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Split TTL into nodes and relationships TTLs.")
    parser.add_argument("input", help="Input combined TTL file")
    parser.add_argument("--nodes-out", default="combined-nodes.ttl", help="Output TTL for node triples")
    parser.add_argument("--rels-out", default="combined-rels.ttl", help="Output TTL for relationship triples")
    parser.add_argument("--node-predicate", action="append", help="Predicate URI to force into nodes file (can repeat)")

    args = parser.parse_args(argv)

    try:
        split_ttl(args.input, args.nodes_out, args.rels_out, args.node_predicate)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
