#!/usr/bin/env python3
"""Wrapper to run `src/etl/rdf_to_neo4j.py` in nodes-first then relationships-second flow.

Creates timestamped logs under `logs/` and streams output to console.

Designed as a cross-platform alternative to the PowerShell wrapper.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_and_log(cmd: list[str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w', encoding='utf-8') as lf:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end='')
            lf.write(line)
        proc.wait()
        return proc.returncode


def build_py_cmd(args_list: list[str]) -> list[str]:
    # Use the same Python interpreter
    return [sys.executable] + args_list


def main():
    parser = argparse.ArgumentParser(description="Load TO Neo4j wrapper (nodes-first, rels-second)")
    parser.add_argument('--nodes-ttl', default='tmp/combined-nodes.ttl')
    parser.add_argument('--rels-ttl', default='tmp/combined-rels.ttl')
    parser.add_argument('--db-version', default=datetime.utcnow().strftime('%Y-%m-%d'))
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--chunk-size', type=int, default=50000)
    parser.add_argument('--batch-size', type=int, default=5000)
    parser.add_argument('--rel-batch-size', type=int, default=1000)
    parser.add_argument('--fast-parse', action='store_true')
    parser.add_argument('--progress-newline', action='store_true')
    parser.add_argument('--heartbeat', type=int, default=30)
    parser.add_argument('--logs-dir', default='logs')
    parsed = parser.parse_args()

    logs_dir = Path(parsed.logs_dir)
    logs_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    nodes_log = logs_dir / f'load-nodes-{ts}.log'
    rels_log = logs_dir / f'load-rels-{ts}.log'

    base_script = 'src/etl/rdf_to_neo4j.py'

    # Build dry-run command (estimation)
    if parsed.dry_run:
        dry_cmd = [base_script,
                   '--ttl', parsed.nodes_ttl,
                   '--chunk-size', str(parsed.chunk_size),
                   '--dry-run',
                   '--workers', '4']
        if parsed.fast_parse:
            dry_cmd.append('--fast-parse')
        if parsed.progress_newline:
            dry_cmd.append('--progress-newline')
        print('Running dry-run estimation...')
        rc = run_and_log(build_py_cmd(dry_cmd), logs_dir / f'dryrun-{ts}.log')
        sys.exit(rc)

    # Nodes load
    nodes_cmd = [base_script,
                 '--ttl', parsed.nodes_ttl,
                 '--chunk-size', str(parsed.chunk_size),
                 '--batch-size', str(parsed.batch_size),
                 '--db-version', parsed.db_version,
                 '--reset-db',
                 '--nodes-only']
    if parsed.fast_parse:
        nodes_cmd.append('--fast-parse')
    if parsed.progress_newline:
        nodes_cmd.append('--progress-newline')
    if parsed.heartbeat and parsed.heartbeat > 0:
        nodes_cmd += ['--parse-heartbeat-seconds', str(parsed.heartbeat)]

    print('Starting nodes load...')
    rc = run_and_log(build_py_cmd(nodes_cmd), nodes_log)
    if rc != 0:
        print(f'Nodes load failed (exit {rc}). See {nodes_log}')
        sys.exit(rc)

    print('Nodes load succeeded.')

    # Relationships load
    rels_cmd = [base_script,
                '--ttl', parsed.rels_ttl,
                '--chunk-size', str(parsed.chunk_size),
                '--batch-size', str(parsed.batch_size),
                '--rel-batch-size', str(parsed.rel_batch_size),
                '--db-version', parsed.db_version,
                '--rels-only']
    if parsed.fast_parse:
        rels_cmd.append('--fast-parse')
    if parsed.progress_newline:
        rels_cmd.append('--progress-newline')
    if parsed.heartbeat and parsed.heartbeat > 0:
        rels_cmd += ['--parse-heartbeat-seconds', str(parsed.heartbeat)]

    print('Starting relationships load...')
    rc = run_and_log(build_py_cmd(rels_cmd), rels_log)
    if rc != 0:
        print(f'Relationships load failed (exit {rc}). See {rels_log}')
        sys.exit(rc)

    print('Relationships load succeeded.')
    print('Load complete.')
    sys.exit(0)


if __name__ == '__main__':
    main()
