#!/usr/bin/env python3
"""Export KGCS Turtle outputs to CSV for fast neo4j-admin import.

This script performs a two-pass export:
  1) Collect all node property keys
  2) Write nodes.csv and relationships.csv with a stable header

Usage:
  python scripts/export_ttl_to_csv.py --input tmp --output tmp/neo4j-import --chunk-size 2000
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from rdflib import Graph

from src.etl.rdf_to_neo4j import RDFtoNeo4jTransformer, chunk_ttl_file


def collect_ttl_paths(path: str) -> List[str]:
    if os.path.isdir(path):
        return sorted(str(p) for p in Path(path).rglob("*.ttl"))
    return [path]


def iter_chunks(ttl_path: str, chunk_size: int) -> Iterable[Tuple[int, str]]:
    if chunk_size and chunk_size > 0:
        chunk_files, _ = chunk_ttl_file(ttl_path, chunk_size)
        return chunk_files
    return [(1, ttl_path)]


def _extract_nodes_and_rels(ttl_path: str, verbose: bool = False) -> RDFtoNeo4jTransformer:
    g = Graph()
    g.parse(ttl_path, format="turtle")
    transformer = RDFtoNeo4jTransformer(ttl_path)
    transformer.extract_nodes_and_relationships(g, verbose=verbose)
    return transformer


def _label_string(node_label: str, props: Dict) -> str:
    labels = [node_label]
    rdf_types = props.get("rdfTypes")
    if isinstance(rdf_types, list):
        for t in rdf_types:
            if t not in labels:
                labels.append(t)
    return ";".join(labels)


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    return str(value)


def collect_property_keys(ttl_paths: List[str], chunk_size: int) -> List[str]:
    keys: Set[str] = set()
    for ttl_path in ttl_paths:
        for _, chunk_path in iter_chunks(ttl_path, chunk_size):
            transformer = _extract_nodes_and_rels(chunk_path, verbose=False)
            for node in transformer.nodes.values():
                keys.update(node.properties.keys())
            if chunk_path != ttl_path:
                try:
                    os.remove(chunk_path)
                except Exception:
                    pass
    return sorted(keys)


def export_csv(ttl_paths: List[str], output_dir: str, chunk_size: int) -> Tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    nodes_csv = os.path.join(output_dir, "nodes.csv")
    rels_csv = os.path.join(output_dir, "relationships.csv")

    prop_keys = collect_property_keys(ttl_paths, chunk_size)
    node_header = [":ID", ":LABEL", "uri"] + prop_keys
    rel_header = [":START_ID", ":END_ID", ":TYPE"]

    with open(nodes_csv, "w", newline="", encoding="utf-8") as nf, \
            open(rels_csv, "w", newline="", encoding="utf-8") as rf:
        node_writer = csv.writer(nf)
        rel_writer = csv.writer(rf)
        node_writer.writerow(node_header)
        rel_writer.writerow(rel_header)

        for ttl_path in ttl_paths:
            for _, chunk_path in iter_chunks(ttl_path, chunk_size):
                transformer = _extract_nodes_and_rels(chunk_path, verbose=False)
                for node in transformer.nodes.values():
                    props = dict(node.properties)
                    label = _label_string(node.label, props)
                    row = [node.uri, label, node.uri]
                    for key in prop_keys:
                        row.append(_stringify(props.get(key)))
                    node_writer.writerow(row)

                for rel in transformer.relationships:
                    rel_writer.writerow([rel.source_uri, rel.target_uri, rel.relationship_type])

                if chunk_path != ttl_path:
                    try:
                        os.remove(chunk_path)
                    except Exception:
                        pass

    return nodes_csv, rels_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Export TTL to CSV for neo4j-admin import")
    parser.add_argument("--input", required=True, help="TTL file or directory containing TTL files")
    parser.add_argument("--output", required=True, help="Output directory for CSVs")
    parser.add_argument("--chunk-size", type=int, default=2000, help="Unique subjects per chunk (0 = no chunking)")
    args = parser.parse_args()

    ttl_paths = collect_ttl_paths(args.input)
    if not ttl_paths:
        print(f"No TTL files found under {args.input}", file=sys.stderr)
        return 1

    print(f"Exporting {len(ttl_paths)} TTL file(s) to CSV...")
    nodes_csv, rels_csv = export_csv(ttl_paths, args.output, args.chunk_size)
    print(f"Wrote nodes CSV: {nodes_csv}")
    print(f"Wrote relationships CSV: {rels_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
