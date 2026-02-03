#!/usr/bin/env python3
"""Parallel SHACL validation runner with per-standard progress lines."""
import argparse
import os
import sys
import threading
import subprocess
from pathlib import Path

STANDARD_JOBS = [
    # ("CPE", "tmp/pipeline-stage1-cpe.ttl", "docs/ontology/shacl/cpe-shapes.ttl", "artifacts/shacl-report-cpe-summary.json"),
    # ("CPEMATCH", "tmp/pipeline-stage2-cpematch.ttl", "docs/ontology/shacl/cpe-shapes.ttl", "artifacts/shacl-report-cpematch-summary.json"),
    # ("CVE", "tmp/pipeline-stage3-cve.ttl", "docs/ontology/shacl/cve-shapes.ttl", "artifacts/shacl-report-cve-summary.json"),
    ("ATTACK", "tmp/pipeline-stage4-attack.ttl", "docs/ontology/shacl/attack-shapes.ttl", "artifacts/shacl-report-attack-summary.json"),
    ("D3FEND", "tmp/pipeline-stage5-d3fend.ttl", "docs/ontology/shacl/d3fend-shapes.ttl", "artifacts/shacl-report-d3fend-summary.json"),
    ("CAPEC", "tmp/pipeline-stage6-capec.ttl", "docs/ontology/shacl/capec-shapes.ttl", "artifacts/shacl-report-capec-summary.json"),
    ("CWE", "tmp/pipeline-stage7-cwe.ttl", "docs/ontology/shacl/cwe-shapes.ttl", "artifacts/shacl-report-cwe-summary.json"),
    ("CAR", "tmp/pipeline-stage8-car.ttl", "docs/ontology/shacl/car-shapes.ttl", "artifacts/shacl-report-car-summary.json"),
    ("SHIELD", "tmp/pipeline-stage9-shield.ttl", "docs/ontology/shacl/shield-shapes.ttl", "artifacts/shacl-report-shield-summary.json"),
    ("ENGAGE", "tmp/pipeline-stage10-engage.ttl", "docs/ontology/shacl/engage-shapes.ttl", "artifacts/shacl-report-engage-summary.json"),
]


def stream_output(prefix: str, stream):
    for line in iter(stream.readline, ''):
        if not line:
            break
        print(f"[{prefix}] {line.rstrip()}")
    stream.close()


def run_job(job, workers, chunk_size, timeout):
    name, data_path, shapes_path, summary_path = job
    if not os.path.exists(data_path):
        print(f"[{name}] SKIP: data file not found: {data_path}")
        return 0
    if not os.path.exists(shapes_path):
        print(f"[{name}] SKIP: shapes file not found: {shapes_path}")
        return 0

    cmd = [
        sys.executable,
        "-u",
        "scripts/validate_shacl_stream.py",
        "--data", data_path,
        "--shapes", shapes_path,
        "--workers", str(workers),
        "--chunk-size", str(chunk_size),
        "--per-call-timeout", str(timeout),
        "--summary-report", summary_path,
        "--progress-newline"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    threads = [
        threading.Thread(target=stream_output, args=(name, process.stdout), daemon=True),
        threading.Thread(target=stream_output, args=(f"{name}:ERR", process.stderr), daemon=True)
    ]
    for t in threads:
        t.start()

    return_code = process.wait()
    for t in threads:
        t.join()

    if return_code != 0:
        print(f"[{name}] FAILED with exit code {return_code}")
    else:
        print(f"[{name}] DONE")

    return return_code


def parse_args():
    parser = argparse.ArgumentParser(description="Parallel SHACL validation runner")
    parser.add_argument("--workers-per-standard", type=int, default=2, help="Base workers per standard")
    parser.add_argument("--boost-workers-per-standard", type=int, default=4, help="Boost workers per standard when no standards are pending")
    parser.add_argument("--max-parallel-standards", type=int, default=3, help="Max standards to run concurrently")
    parser.add_argument("--chunk-size", type=int, default=20000, help="Subjects per chunk")
    parser.add_argument("--per-call-timeout", type=int, default=600, help="Timeout per validation call")
    return parser.parse_args()


def main():
    args = parse_args()
    Path("artifacts").mkdir(parents=True, exist_ok=True)

    runnable_jobs = [job for job in STANDARD_JOBS if os.path.exists(job[1]) and os.path.exists(job[2])]
    skipped_jobs = [job for job in STANDARD_JOBS if job not in runnable_jobs]

    for job in skipped_jobs:
        name, data_path, shapes_path, _ = job
        if not os.path.exists(data_path):
            print(f"[{name}] SKIP: data file not found: {data_path}")
        elif not os.path.exists(shapes_path):
            print(f"[{name}] SKIP: shapes file not found: {shapes_path}")

    if not runnable_jobs:
        print("No standards to validate.")
        return 1

    if len(runnable_jobs) <= args.max_parallel_standards:
        effective_workers = args.boost_workers_per_standard
    else:
        effective_workers = args.workers_per_standard

    results = []
    active_threads = []

    def start_job(job):
        name = job[0]
        code = run_job(job, effective_workers, args.chunk_size, args.per_call_timeout)
        results.append((name, code))

    job_iter = iter(runnable_jobs)

    while True:
        while len(active_threads) < args.max_parallel_standards:
            try:
                job = next(job_iter)
            except StopIteration:
                break
            thread = threading.Thread(target=start_job, args=(job,), daemon=True)
            active_threads.append(thread)
            thread.start()

        if not active_threads:
            break

        finished = []
        for thread in active_threads:
            thread.join(timeout=0.1)
            if not thread.is_alive():
                finished.append(thread)

        for thread in finished:
            active_threads.remove(thread)

        if not finished and len(active_threads) >= args.max_parallel_standards:
            for thread in active_threads:
                thread.join()
            active_threads = []

    failures = [name for name, code in results if code != 0]
    if failures:
        print(f"Failed standards: {', '.join(failures)}")
        return 1

    print("All standards completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
