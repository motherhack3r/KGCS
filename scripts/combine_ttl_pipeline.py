#!/usr/bin/env python3
"""
Combine all 10 pipeline TTL stages into single file.

Usage:
    python scripts/combine_ttl_pipeline.py [--output tmp/combined-pipeline.ttl]
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def combine_ttl_files(nodes_out="tmp/combined-nodes.ttl", rels_out="tmp/combined-rels.ttl",
                      heuristic_threshold=200_000_000, node_predicates=None):
    """Stream-combine pipeline TTL files into two outputs: nodes and relationships.

    For each stage file we attempt to parse with rdflib (safe, accurate). If the file
    exceeds `heuristic_threshold` bytes we fall back to a line-based heuristic to avoid
    loading very large files into memory.
    """

    # Find all pipeline stage files in order
    stage_files = []
    for i in range(1, 11):
        stage_file = f"tmp/pipeline-stage{i}-*.ttl"
        # Use glob to find exact file
        import glob
        matches = glob.glob(stage_file)
        if matches:
            stage_files.append(matches[0])

    if not stage_files:
        print("[ERROR] No pipeline stage files found in tmp/")
        return False

    print(f"Processing {len(stage_files)} stage files into:\n  nodes: {nodes_out}\n  rels: {rels_out}\n")

    node_predicates_set = set(node_predicates or [])

    # Stats
    file_stats = []
    prefixes_written = False

    try:
        # Ensure logs dir exists
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)

        # Open outputs
        with open(nodes_out, 'w', encoding='utf-8') as nodes_f, open(rels_out, 'w', encoding='utf-8') as rels_f:
            for idx, input_file in enumerate(stage_files, 1):
                path_p = Path(input_file)
                size = path_p.stat().st_size
                print(f"[{idx:2d}/{len(stage_files)}] {path_p.name} (size: {size/1024/1024:.1f} MB)")

                # read header lines quickly to preserve prefixes if present
                header_lines = []
                with open(input_file, 'r', encoding='utf-8') as fh:
                    for _ in range(2000):
                        pos = fh.tell()
                        line = fh.readline()
                        if not line:
                            break
                        if line.startswith("@prefix ") or line.startswith("@base "):
                            header_lines.append(line)
                        else:
                            # rewind to start of first non-header line
                            fh.seek(pos)
                            break

                if not prefixes_written and header_lines:
                    # write shared prefixes to both outputs
                    nodes_f.writelines(header_lines)
                    nodes_f.write("\n")
                    rels_f.writelines(header_lines)
                    rels_f.write("\n")
                    prefixes_written = True

                # Choose parsing strategy
                if size <= heuristic_threshold:
                    # rdflib parse (accurate)
                    try:
                        from rdflib import Graph, RDF, Literal
                        g = Graph()
                        g.parse(input_file, format='turtle')

                        # bind namespaces to a tmp graph for n3() rendering
                        tmp = Graph()
                        for prefix, ns in g.namespaces():
                            tmp.bind(prefix, ns)

                        triples = 0
                        node_triples = 0
                        rel_triples = 0
                        def _n3_full(node):
                            from rdflib import Literal as _Literal
                            if isinstance(node, _Literal):
                                return node.n3()
                            return f"<{str(node)}>"

                        for s, p, o in g:
                            triples += 1
                            p_str = str(p)
                            subj_txt = _n3_full(s)
                            pred_txt = _n3_full(p)
                            if isinstance(o, Literal):
                                obj_txt = o.n3()
                            else:
                                obj_txt = _n3_full(o)

                            if (p == RDF.type) or isinstance(o, Literal) or (p_str in node_predicates_set):
                                nodes_f.write(f"{subj_txt} {pred_txt} {obj_txt} .\n")
                                node_triples += 1
                            else:
                                rels_f.write(f"{subj_txt} {pred_txt} {obj_txt} .\n")
                                rel_triples += 1

                        file_stats.append((path_p.name, size, triples, node_triples, rel_triples))
                        print(f"       Parsed triples: {triples:,} (nodes: {node_triples:,}, rels: {rel_triples:,})")
                    except Exception as e:
                        print(f"       rdflib parse failed ({e}), falling back to heuristic line parser")
                        # fall through to heuristic
                        res = parse_with_heuristic(input_file, nodes_f, rels_f, node_predicates_set)
                        if res:
                            triples, nodes_t, rels_t = res
                            file_stats.append((path_p.name, size, triples, nodes_t, rels_t))
                else:
                    # large file: heuristic parse
                    res = parse_with_heuristic(input_file, nodes_f, rels_f, node_predicates_set)
                    if res:
                        triples, nodes_t, rels_t = res
                        file_stats.append((path_p.name, size, triples, nodes_t, rels_t))

        # Report
        print("\nCOMBINE/SPLIT COMPLETE\n")
        print("File breakdown:")
        total_triples = 0
        total_nodes = 0
        total_rels = 0
        stages = []
        for name, size, triples, nodes_t, rels_t in file_stats:
            print(f"  {name:40s} size={size/1024/1024:7.2f}MB triples={triples:,} nodes={nodes_t:,} rels={rels_t:,}")
            total_triples += triples
            total_nodes += nodes_t
            total_rels += rels_t
            stages.append({"name": name, "size_bytes": size, "triples": triples, "node_triples": nodes_t, "rel_triples": rels_t})

        # write summary JSON to logs
        summary = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "nodes_out": str(nodes_out),
            "rels_out": str(rels_out),
            "stages": stages,
            "totals": {"triples": total_triples, "node_triples": total_nodes, "rel_triples": total_rels}
        }
        summary_path = logs_dir / f"combine-split-summary-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        with open(summary_path, 'w', encoding='utf-8') as sf:
            json.dump(summary, sf, indent=2)

        print(f"\nSummary written to: {summary_path}")
        return True

    except Exception as e:
        print(f"[ERROR] combine failed: {e}")
        return False


def parse_with_heuristic(input_file, nodes_f, rels_f, node_predicates_set):
    """Very small heuristic line-based parser: assumes triples are single-line and headers handled."""
    triples = 0
    nodes_t = 0
    rels_t = 0
    with open(input_file, 'r', encoding='utf-8') as fh:
        for line in fh:
            if not line.strip() or line.startswith('@prefix') or line.startswith('@base') or line.startswith('#'):
                continue
            triples += 1
            # crude: if line contains a quote it's likely a literal -> node triple
            if '"' in line or "'" in line:
                nodes_f.write(line)
                nodes_t += 1
            else:
                # check for ' a ' (rdf:type) or explicit node_predicates substring
                lower = line.lower()
                if ' a ' in lower or 'rdf:type' in lower:
                    nodes_f.write(line)
                    nodes_t += 1
                else:
                    matched = False
                    for pred in node_predicates_set:
                        if pred in line:
                            nodes_f.write(line)
                            nodes_t += 1
                            matched = True
                            break
                    if not matched:
                        rels_f.write(line)
                        rels_t += 1
    print(f"       Heuristic triples: {triples:,} (nodes: {nodes_t:,}, rels: {rels_t:,})")
    return triples, nodes_t, rels_t


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Combine all pipeline TTL stages into nodes/rels outputs")
    parser.add_argument("--nodes-out", default="tmp/combined-nodes.ttl", help="Output file for node triples")
    parser.add_argument("--rels-out", default="tmp/combined-rels.ttl", help="Output file for relationship triples")
    parser.add_argument("--heuristic-threshold", type=int, default=200_000_000, help="File size in bytes above which to use heuristic parsing")
    parser.add_argument("--node-predicate", action="append", help="Predicate URI (or substring) to force into nodes file; repeatable")

    args = parser.parse_args()
    
    print("")
    print("="*70)
    print("COMBINING PIPELINE TTL FILES")
    print("="*70)
    print(f"Start time: {datetime.now().isoformat()}")
    print("")
    
    success = combine_ttl_files(nodes_out=args.nodes_out, rels_out=args.rels_out,
                                heuristic_threshold=args.heuristic_threshold,
                                node_predicates=args.node_predicate)
    
    if success:
        print(f"End time: {datetime.now().isoformat()}")
        print("[OK] Combination successful!")
        return 0
    else:
        print(f"End time: {datetime.now().isoformat()}")
        print("[FAIL] Combination failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
