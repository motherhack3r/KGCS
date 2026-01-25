#!/usr/bin/env python3
"""Streamed SHACL validator: split large Turtle into subject-chunks and validate each.

This avoids loading a huge data graph into memory. It relies on the fact that
ETL outputs write one triple per line and group triples for the same subject
consecutively (as our streaming ETLs do).

Usage:
  python scripts/validate_shacl_stream.py --data data/cpe/samples/cpe-output-stream.ttl \
      --shapes docs/ontology/shacl/cpe-shapes.ttl --output artifacts --chunk-size 2000

The script will call the existing validation module (`src.core.validation`) as a subprocess
for each chunk, writing per-chunk JSON reports to the output directory.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time


def chunk_and_validate(data_path, shapes, out_dir, chunk_size=1000, per_call_timeout=300):
    os.makedirs(out_dir, exist_ok=True)
    header_lines = []

    total_chunks = 0
    total_triples = 0
    subjects_seen = 0

    # We assume one triple per line and subject is the first token on the line
    current_subject = None
    current_chunk_subjects = set()
    chunk_lines = []

    def flush_chunk(tmp_lines, idx):
        nonlocal total_chunks, total_triples
        if not tmp_lines:
            return None
        total_chunks += 1
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=f'.chunk{idx}.ttl')
        os.close(tmp_fd)
        with open(tmp_path, 'w', encoding='utf-8') as tf:
            # minimal prefix header for Turtle
            tf.write('@prefix dcterms: <http://purl.org/dc/terms/> .\n')
            tf.write('@prefix sec: <https://example.org/sec/core#> .\n')
            tf.write('@prefix ex: <https://example.org/> .\n\n')
            for L in tmp_lines:
                tf.write(L)
        # call validator as subprocess to avoid importing packaging issues
        cmd = [sys.executable, '-m', 'src.core.validation', '--data', tmp_path, '--shapes', shapes, '--output', out_dir]
        try:
            start = time.time()
            subprocess.run(cmd, check=False, timeout=per_call_timeout)
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            print(f"Chunk {idx}: validation timed out after {per_call_timeout}s", file=sys.stderr)
            elapsed = None
        # remove tmp file to save space
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return elapsed

    idx = 0
    with open(data_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            if not line.strip():
                continue
            # skip prefix/header lines
            if line.startswith('@prefix') or line.startswith('PREFIX') or line.startswith('#'):
                continue
            parts = line.split(None, 1)
            if not parts:
                continue
            subj = parts[0]
            if current_subject is None:
                current_subject = subj
            if subj != current_subject:
                # new subject encountered
                if subj not in current_chunk_subjects:
                    current_chunk_subjects.add(subj)
                    subjects_seen += 1
                # if chunk reached
                if len(current_chunk_subjects) >= chunk_size:
                    idx += 1
                    elapsed = flush_chunk(chunk_lines, idx)
                    print(f"Validated chunk {idx}; elapsed={elapsed}")
                    chunk_lines = []
                    current_chunk_subjects = set()
                    current_subject = subj
            chunk_lines.append(line)
            total_triples += 1

    # flush remaining
    if chunk_lines:
        idx += 1
        elapsed = flush_chunk(chunk_lines, idx)
        print(f"Validated chunk {idx}; elapsed={elapsed}")

    print(f"Finished: chunks={idx}, triples_scanned={total_triples}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', '-d', required=True)
    p.add_argument('--shapes', '-s', required=True)
    p.add_argument('--output', '-o', default='artifacts')
    p.add_argument('--chunk-size', type=int, default=1000, help='Number of unique subjects per chunk')
    p.add_argument('--per-call-timeout', type=int, default=300, help='Seconds timeout per validation call')
    args = p.parse_args()

    if not os.path.exists(args.data):
        print('Data file not found:', args.data, file=sys.stderr)
        raise SystemExit(2)
    if not os.path.exists(args.shapes):
        print('Shapes file not found:', args.shapes, file=sys.stderr)
        raise SystemExit(2)

    chunk_and_validate(args.data, args.shapes, args.output, chunk_size=args.chunk_size, per_call_timeout=args.per_call_timeout)


if __name__ == '__main__':
    main()
