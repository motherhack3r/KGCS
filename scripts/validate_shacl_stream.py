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
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed


def _validate_chunk(tmp_path: str, shapes: str, out_dir: str, per_call_timeout: int, idx: int):
    cmd = [sys.executable, '-m', 'src.core.validation', '--data', tmp_path, '--shapes', shapes, '--output', out_dir]
    try:
        start = time.time()
        result = subprocess.run(
            cmd,
            check=False,
            timeout=per_call_timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        elapsed = time.time() - start
        report_name = f"shacl-report-{os.path.basename(tmp_path)}.json"
        report_path = os.path.join(out_dir, report_name)
        report = None
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as fh:
                report = json.load(fh)
            try:
                os.remove(report_path)
            except Exception:
                pass
        error_text = None
        if result.returncode not in (0, 1) and (result.stderr or result.stdout):
            error_text = (result.stderr or result.stdout).strip()
        return idx, elapsed, result.returncode, report, error_text
    except subprocess.TimeoutExpired:
        return idx, None, None, None, f"Chunk {idx}: validation timed out after {per_call_timeout}s"
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def chunk_and_validate(data_path, shapes, out_dir, chunk_size=1000, per_call_timeout=300, workers=1, summary_report=None, progress_newline=False):
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
        return tmp_path

    idx = 0
    chunk_files = []
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
                    tmp_path = flush_chunk(chunk_lines, idx)
                    if tmp_path:
                        chunk_files.append((idx, tmp_path))
                    chunk_lines = []
                    current_chunk_subjects = set()
                    current_subject = subj
            chunk_lines.append(line)
            total_triples += 1

    # flush remaining
    if chunk_lines:
        idx += 1
        tmp_path = flush_chunk(chunk_lines, idx)
        if tmp_path:
            chunk_files.append((idx, tmp_path))

    total = len(chunk_files)
    completed = 0
    chunk_reports = []
    errors = []

    def update_progress():
        percent = (completed / total) * 100 if total else 100
        bar_width = 20
        filled = int(bar_width * (percent / 100)) if total else bar_width
        bar = "█" * filled + "░" * (bar_width - filled)
        message = f"Validated {completed}/{total} chunks ({percent:0.1f}%) {bar}"
        if progress_newline:
            print(message, flush=True)
        else:
            print(f"\r{message}", end='', flush=True)

    if workers and workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_validate_chunk, tmp_path, shapes, out_dir, per_call_timeout, chunk_idx)
                       for chunk_idx, tmp_path in chunk_files]
            for future in as_completed(futures):
                chunk_idx, elapsed, returncode, report, error = future.result()
                completed += 1
                update_progress()
                if error:
                    errors.append(error)
                if report:
                    report['chunk'] = chunk_idx
                    report['elapsed'] = elapsed
                    report['return_code'] = returncode
                    chunk_reports.append(report)
    else:
        for chunk_idx, tmp_path in chunk_files:
            chunk_idx, elapsed, returncode, report, error = _validate_chunk(tmp_path, shapes, out_dir, per_call_timeout, chunk_idx)
            completed += 1
            update_progress()
            if error:
                errors.append(error)
            if report:
                report['chunk'] = chunk_idx
                report['elapsed'] = elapsed
                report['return_code'] = returncode
                chunk_reports.append(report)

    if total:
        print()

    conforms = all(r.get('conforms') for r in chunk_reports) if chunk_reports else False

    if summary_report is None:
        base = os.path.basename(data_path)
        summary_report = os.path.join(out_dir, f"shacl-report-{base}-summary.json")

    summary = {
        'data_file': data_path,
        'conforms': bool(conforms),
        'chunks': idx,
        'triples_scanned': total_triples,
        'errors': errors,
        'chunk_reports': chunk_reports
    }

    with open(summary_report, 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2)

    print(f"Finished: chunks={idx}, triples_scanned={total_triples}")
    print(f"Summary report: {summary_report}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', '-d', required=True)
    p.add_argument('--shapes', '-s', required=True)
    p.add_argument('--output', '-o', default='artifacts')
    p.add_argument('--chunk-size', type=int, default=1000, help='Number of unique subjects per chunk')
    p.add_argument('--per-call-timeout', type=int, default=300, help='Seconds timeout per validation call')
    p.add_argument('--workers', type=int, default=1, help='Parallel validation workers (default: 1)')
    p.add_argument('--summary-report', help='Write a single summary report JSON to this path')
    p.add_argument('--progress-newline', action='store_true', help='Print progress updates as new lines (useful when piping)')
    args = p.parse_args()

    if not os.path.exists(args.data):
        print('Data file not found:', args.data, file=sys.stderr)
        raise SystemExit(2)
    if not os.path.exists(args.shapes):
        print('Shapes file not found:', args.shapes, file=sys.stderr)
        raise SystemExit(2)

    chunk_and_validate(
        args.data,
        args.shapes,
        args.output,
        chunk_size=args.chunk_size,
        per_call_timeout=args.per_call_timeout,
        workers=args.workers,
        summary_report=args.summary_report,
        progress_newline=args.progress_newline
    )


if __name__ == '__main__':
    main()
