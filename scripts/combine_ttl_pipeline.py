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
                      heuristic_threshold=200_000_000, node_predicates=None, inputs=None, full_out: str | None = None):
    """Stream-combine pipeline TTL files into two outputs: nodes and relationships.

    For each stage file we attempt to parse with rdflib (safe, accurate). If the file
    exceeds `heuristic_threshold` bytes we fall back to a line-based heuristic to avoid
    loading very large files into memory.
    """

    # Determine stage files to process (either explicit inputs or default stage discovery)
    stage_files = []
    import glob
    import os

    if inputs:
        # Explicit inputs provided: accept files, directories, or glob patterns
        expanded = []
        for inp in inputs:
            hits = sorted(glob.glob(inp))
            if hits:
                for h in hits:
                    if os.path.isdir(h):
                        # include .ttl and .nt files in directory
                        expanded.extend(sorted(glob.glob(os.path.join(h, "*.ttl")) + glob.glob(os.path.join(h, "*.nt"))))
                    else:
                        expanded.append(h)
            else:
                # not a glob match: treat as path
                if os.path.isdir(inp):
                    expanded.extend(sorted(glob.glob(os.path.join(inp, "*.ttl")) + glob.glob(os.path.join(inp, "*.nt"))))
                elif os.path.exists(inp):
                    expanded.append(inp)
                else:
                    # try to find matching files in data/*/samples/
                    fb_matches = sorted(glob.glob(inp) + glob.glob(os.path.join('data', '*', 'samples', os.path.basename(inp))))
                    if fb_matches:
                        expanded.extend(fb_matches)
        # deduplicate and sort
        stage_files = sorted(dict.fromkeys(expanded))
        print(f"Combining explicit inputs ({len(stage_files)} files): {stage_files}")
    else:
        for i in range(1, 11):
            # search for both .ttl and .nt pipeline stage outputs
            patterns = [f"tmp/pipeline-stage{i}-*.ttl", f"tmp/pipeline-stage{i}-*.nt"]
            matches = []
            for p in patterns:
                matches.extend(sorted(glob.glob(p)))
            # If no matches in tmp/, fall back to data/*/samples/ for both extensions
            if not matches:
                fb_patterns = [f"data/*/samples/pipeline-stage{i}-*.ttl", f"data/*/samples/pipeline-stage{i}-*.nt"]
                fb_matches = []
                for p in fb_patterns:
                    fb_matches.extend(sorted(glob.glob(p)))
                if fb_matches:
                    print(f"  Found {len(fb_matches)} data/samples file(s) for stage {i}: {fb_matches}")
                    matches = fb_matches
            if matches:
                print(f"  Found {len(matches)} file(s) for stage {i}: {matches}")
                stage_files.extend(matches)

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
                        # select parse format by file extension
                        ext = path_p.suffix.lower()
                        parse_format = 'nt' if ext == '.nt' else 'turtle'
                        g.parse(input_file, format=parse_format)

                        # bind namespaces to a tmp graph for n3() rendering
                        tmp = Graph()
                        for prefix, ns in g.namespaces():
                            tmp.bind(prefix, ns)

                        triples = 0
                        node_triples = 0
                        rel_triples = 0
                        # Use a safe literal formatter so large literals are written as single-line
                        try:
                            from src.etl.ttl_writer import _format_literal
                        except Exception:
                            from .ttl_writer import _format_literal

                        def _n3_full(node):
                            from rdflib import Literal as _Literal
                            if isinstance(node, _Literal):
                                return _format_literal(node)
                            return f"<{str(node)}>"

                        for s, p, o in g:
                            triples += 1
                            p_str = str(p)
                            subj_txt = _n3_full(s)
                            pred_txt = _n3_full(p)
                            if isinstance(o, Literal):
                                obj_txt = _format_literal(o)
                            else:
                                obj_txt = _n3_full(o)

                            if (p == RDF.type) or isinstance(o, Literal) or (p_str in node_predicates_set):
                                nodes_f.write(f"{subj_txt} {pred_txt} {obj_txt} .\n")
                                node_triples += 1
                            else:
                                rels_f.write(f"{subj_txt} {pred_txt} {obj_txt} .\n")
                                rel_triples += 1

                        malformed = 0
                        file_stats.append((path_p.name, size, triples, node_triples, rel_triples, malformed))
                        print(f"       Parsed triples: {triples:,} (nodes: {node_triples:,}, rels: {rel_triples:,})")
                    except Exception as e:
                        print(f"       rdflib parse failed ({e}), falling back to heuristic line parser")
                        # fall through to heuristic
                        res = parse_with_heuristic(input_file, nodes_f, rels_f, node_predicates_set)
                        if res:
                            triples, nodes_t, rels_t, malformed = res
                            file_stats.append((path_p.name, size, triples, nodes_t, rels_t, malformed))
                else:
                    # large file: heuristic parse
                    res = parse_with_heuristic(input_file, nodes_f, rels_f, node_predicates_set)
                    if res:
                        triples, nodes_t, rels_t, malformed = res
                        file_stats.append((path_p.name, size, triples, nodes_t, rels_t, malformed))

        # Report
        print("\nCOMBINE/SPLIT COMPLETE\n")
        print("File breakdown:")
        total_triples = 0
        total_nodes = 0
        total_rels = 0
        stages = []
        for name, size, triples, nodes_t, rels_t, malformed in file_stats:
            if malformed:
                print(f"  {name:40s} size={size/1024/1024:7.2f}MB triples={triples:,} nodes={nodes_t:,} rels={rels_t:,} malformed={malformed:,}")
            else:
                print(f"  {name:40s} size={size/1024/1024:7.2f}MB triples={triples:,} nodes={nodes_t:,} rels={rels_t:,}")
            total_triples += triples
            total_nodes += nodes_t
            total_rels += rels_t
            stages.append({"name": name, "size_bytes": size, "triples": triples, "node_triples": nodes_t, "rel_triples": rels_t, "malformed_triples": malformed})

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

        # Reorder node triples by subject (rdf:type first) to produce a grouped nodes file.
        # Uses disk-backed bucketing to avoid loading the full file into memory.
        try:
            _reorder_nodes_grouped(nodes_out)
            print(f"Reordered nodes file by subject: {nodes_out}")
        except Exception as e:
            print(f"Warning: node reordering failed: {e}")

        # Optionally write a full combined file with nodes followed by relationships
        if full_out:
            try:
                with open(full_out, 'w', encoding='utf-8') as fo, open(nodes_out, 'r', encoding='utf-8') as nf, open(rels_out, 'r', encoding='utf-8') as rf:
                    for line in nf:
                        fo.write(line)
                    for line in rf:
                        fo.write(line)
                print(f"Wrote combined full load file: {full_out}")
            except Exception as e:
                print(f"Warning: could not write full_out file {full_out}: {e}")

        # Post-combine diagnostics: scan nodes output for suspicious lines that do not start
        # with a valid subject token (i.e., '<', '_:', or 'a'). This detects stray fragments
        # caused by multi-line triples or tokenization problems and writes examples to a log.
        bad_examples = []
        try:
            with open(nodes_out, 'r', encoding='utf-8') as nf:
                for idx, line in enumerate(nf, start=1):
                    ln = line.strip()
                    if not ln or ln.startswith('@') or ln.startswith('#'):
                        continue
                    first_tok = ln.split(' ', 1)[0]
                    if not (first_tok.startswith('<') or first_tok.startswith('_:') or first_tok == 'a'):
                        bad_examples.append({'line': idx, 'token': first_tok, 'snippet': ln[:200]})
                        if len(bad_examples) >= 50:
                            break
        except Exception:
            bad_examples = []

        if bad_examples:
            Path('logs').mkdir(exist_ok=True)
            bad_nodes_log = Path('logs') / 'bad_nodes_lines.log'
            with open(bad_nodes_log, 'w', encoding='utf-8') as bf:
                for ex in bad_examples:
                    bf.write(f"{nodes_out}:{ex['line']}: {ex['token']}: {ex['snippet']}\n")
            print(f"[WARN] Suspicious lines found in {nodes_out}: {len(bad_examples)} (see {bad_nodes_log})")
            # Add to summary JSON
            summary.setdefault('diagnostics', {})['bad_node_lines_examples'] = bad_examples[:10]
            summary['diagnostics']['bad_node_lines_count'] = len(bad_examples)
            with open(summary_path, 'w', encoding='utf-8') as sf:
                json.dump(summary, sf, indent=2)

        # Post-combine diagnostics: detect subjects that have literal properties but no rdf:type
        # (these are the small set of problematic subjects you observed; report examples).
        try:
            types_set = set()
            literal_subjects = set()
            with open(nodes_out, 'r', encoding='utf-8') as nf:
                for line in nf:
                    ln = line.strip()
                    if not ln or ln.startswith('@') or ln.startswith('#'):
                        continue
                    parts = ln.split(' ', 2)
                    if len(parts) < 3:
                        continue
                    subj_tok, pred_tok, obj_tok = parts[0], parts[1], parts[2]
                    lower_pred = pred_tok.lower()
                    if 'rdf-syntax-ns#type' in lower_pred or 'rdf:type' in lower_pred or pred_tok == 'a':
                        types_set.add(subj_tok)
                    if obj_tok.startswith('"') or obj_tok.startswith("'"):
                        literal_subjects.add(subj_tok)
            candidates = sorted(list(literal_subjects - types_set))
            if candidates:
                Path('logs').mkdir(exist_ok=True)
                bad_subjects_log = Path('logs') / 'bad_node_subjects.log'
                with open(bad_subjects_log, 'w', encoding='utf-8') as bf:
                    for c in candidates[:50]:
                        bf.write(f"{nodes_out}: SUBJECT_WITH_LITERAL_NO_TYPE: {c}\n")
                print(f"[WARN] Subjects have literals but no rdf:type: {len(candidates)} examples written to {bad_subjects_log}")
                summary.setdefault('diagnostics', {})['bad_node_subjects_examples'] = candidates[:10]
                summary['diagnostics']['bad_node_subjects_count'] = len(candidates)
                with open(summary_path, 'w', encoding='utf-8') as sf:
                    json.dump(summary, sf, indent=2)
        except Exception:
            pass
        return True

    except Exception as e:
        print(f"[ERROR] combine failed: {e}")
        return False


def parse_with_heuristic(input_file, nodes_f, rels_f, node_predicates_set):
    """Very small heuristic line-based parser: assumes triples are single-line and headers handled.

    Adds a lightweight validation pass to detect malformed triples (tokenization errors) and
    writes them to logs/bad_triples.log for later inspection.
    """
    from pathlib import Path
    Path('logs').mkdir(exist_ok=True)
    bad_log = Path('logs') / 'bad_triples.log'

    triples = 0
    nodes_t = 0
    rels_t = 0
    malformed = 0

    with open(input_file, 'r', encoding='utf-8') as fh, open(bad_log, 'a', encoding='utf-8') as bad_f:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip() or line.startswith('@prefix') or line.startswith('@base') or line.startswith('#'):
                continue
            triples += 1

            # Basic tokenization check: ensure at least 3 whitespace-separated tokens
            parts = line.strip().split()
            if len(parts) < 3:
                malformed += 1
                bad_f.write(f"{input_file}:{lineno}: MALFORMED (too few tokens): {line}")
                continue

            subj_tok, pred_tok = parts[0], parts[1]
            obj_tok = ' '.join(parts[2:])

            # Validate subject/predicate minimal form
            subj_valid = subj_tok.startswith('<') or subj_tok.startswith('_:') or subj_tok == 'a'
            pred_valid = pred_tok.startswith('<') or (':' in pred_tok) or pred_tok == 'a'
            if not subj_valid or not pred_valid:
                malformed += 1
                bad_f.write(f"{input_file}:{lineno}: MALFORMED (bad subject/predicate): {line}")
                continue

            # crude: if line contains a quote it's likely a literal -> node triple
            if '"' in line or "'" in line:
                nodes_f.write(line)
                nodes_t += 1
                continue

            # check for ' a ' (rdf:type), explicit rdf:type tokens, or '#type' in full-URI predicates
            lower = line.lower()
            if ' a ' in lower or 'rdf:type' in lower or '#type' in lower or 'rdf-syntax-ns#type' in lower:
                nodes_f.write(line)
                nodes_t += 1
                continue

            # check configured node_predicates
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

    if malformed:
        print(f"       Heuristic triples: {triples:,} (nodes: {nodes_t:,}, rels: {rels_t:,}, malformed: {malformed:,})")
    else:
        print(f"       Heuristic triples: {triples:,} (nodes: {nodes_t:,}, rels: {rels_t:,})")
    return triples, nodes_t, rels_t, malformed


def _reorder_nodes_grouped(nodes_out: str, buckets: int = 256) -> None:
    """Reorder the node triples file so that triples are grouped by subject and any
    rdf:type triples for a subject are written before other triples for the same
    subject.

    Uses on-disk bucketing (by SHA1 prefix) to avoid holding the entire file in
    memory for large datasets.
    """
    import hashlib
    import shutil
    from pathlib import Path

    nodes_path = Path(nodes_out)
    if not nodes_path.exists():
        return

    bucket_dir = nodes_path.parent / 'combine_buckets'
    if bucket_dir.exists():
        shutil.rmtree(bucket_dir)
    bucket_dir.mkdir(parents=True, exist_ok=True)

    header_lines = []

    # Distribute lines into buckets (skip header/prefix lines)
    with open(nodes_out, 'r', encoding='utf-8') as nf:
        for line in nf:
            if not line.strip():
                continue
            if line.startswith('@prefix') or line.startswith('@base') or line.startswith('#'):
                header_lines.append(line)
                continue
            first_tok = line.split(' ', 1)[0]
            bucket_name = hashlib.sha1(first_tok.encode('utf-8')).hexdigest()[:2]
            with open(bucket_dir / f'bucket_{bucket_name}.tmp', 'a', encoding='utf-8') as bf:
                bf.write(line)

    # Assemble final nodes file
    tmp_nodes = nodes_path.with_suffix(nodes_path.suffix + '.sorted')
    with open(tmp_nodes, 'w', encoding='utf-8') as out_f:
        # write header lines first
        for hl in header_lines:
            out_f.write(hl)
        out_f.write('\n')

        # process buckets in sorted order for determinism
        for bucket in sorted(bucket_dir.iterdir()):
            lines = bucket.read_text(encoding='utf-8').splitlines()
            # sort by subject then predicate for deterministic grouping
            def _sort_key(l: str):
                parts = l.split(' ', 2)
                subj = parts[0] if len(parts) >= 1 else ''
                pred = parts[1] if len(parts) >= 2 else ''
                return (subj, pred)
            lines.sort(key=_sort_key)

            i = 0
            while i < len(lines):
                    parts0 = lines[i].split(' ', 2)
                    subj = parts0[0] if parts0 else ''
                    group = []
                    j = i
                    while j < len(lines) and lines[j].split(' ', 2)[0] == subj:
                        group.append(lines[j] + '\n')
                        j += 1
                    # Within group, write rdf:type lines first
                    type_lines = []
                    other_lines = []
                    for l in group:
                        parts = l.strip().split(' ', 2)
                        if len(parts) < 2:
                            other_lines.append(l)
                            continue
                        pred_tok = parts[1]
                        pred_lower = pred_tok.lower()
                        if pred_tok == 'a' or 'rdf:type' in pred_lower or '#type' in pred_lower:
                            type_lines.append(l)
                        else:
                            other_lines.append(l)
                    for l in type_lines + other_lines:
                        out_f.write(l)
                    i = j
    # Move sorted file into place
    shutil.move(str(tmp_nodes), str(nodes_path))
    # cleanup buckets
    shutil.rmtree(bucket_dir, ignore_errors=True)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Combine all pipeline TTL stages into nodes/rels outputs")
    parser.add_argument("--nodes-out", default="tmp/combined-nodes.ttl", help="Output file for node triples")
    parser.add_argument("--rels-out", default="tmp/combined-rels.ttl", help="Output file for relationship triples")
    parser.add_argument("--heuristic-threshold", type=int, default=200_000_000, help="File size in bytes above which to use heuristic parsing")
    parser.add_argument("--node-predicate", action="append", help="Predicate URI (or substring) to force into nodes file; repeatable")
    parser.add_argument("--inputs", nargs='*', help="Explicit list of input files or directories to combine (overrides automatic discovery)")
    parser.add_argument("--full-out", help="Write a single combined file with nodes followed by relationships (path)")

    args = parser.parse_args()
    
    print("")
    print("="*70)
    print("COMBINING PIPELINE TTL FILES")
    print("="*70)
    print(f"Start time: {datetime.now().isoformat()}")
    print("")
    
    success = combine_ttl_files(nodes_out=args.nodes_out, rels_out=args.rels_out,
                                heuristic_threshold=args.heuristic_threshold,
                                node_predicates=args.node_predicate,
                                inputs=args.inputs,
                                full_out=args.full_out)
    
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
