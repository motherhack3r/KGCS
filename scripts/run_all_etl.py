#!/usr/bin/env python3
"""
Run all KGCS ETL transformers in correct order on downloaded raw data.
Outputs TTL files to tmp/ for each standard.
"""
import subprocess
import sys
import os
from pathlib import Path

ETL_STEPS = [
    # (transformer, input, output)
    ("etl_cpe",      "data/cpe/raw/nvdcpe-2.0.json",                "tmp/pipeline-stage1-cpe.ttl"),
    ("etl_cpematch", "data/cpe/raw/nvdcpematch-2.0.json",           "tmp/pipeline-stage2-cpematch.ttl"),
    ("etl_cve",      "data/cve/raw/nvdcve-2.0-2026.json",           "tmp/pipeline-stage3-cve.ttl"),
    ("etl_cwe",      "data/cwe/raw/cwec_latest.xml",                "tmp/pipeline-stage7-cwe.ttl"),
    ("etl_capec",    "data/capec/raw/capec.json",             "tmp/pipeline-stage6-capec.ttl"),
    ("etl_attack",   "data/attack/raw/enterprise-attack.json",      "tmp/pipeline-stage4-attack.ttl"),
    ("etl_d3fend",   "data/d3fend/raw/d3fend.json",                 "tmp/pipeline-stage5-d3fend.ttl"),
    ("etl_car",      "data/car/raw/analytics_CAR-2021-01-001.yaml", "tmp/pipeline-stage8-car.ttl"),
    ("etl_shield",   "data/shield/raw",             "tmp/pipeline-stage9-shield.ttl"),
    ("etl_engage",   "data/engage/raw",             "tmp/pipeline-stage10-engage.ttl"),
]

def run_etl(transformer, input_path, output_path):
    if not os.path.exists(input_path):
        print(f"[SKIP] {input_path} not found.")
        return False
    cmd = [sys.executable, '-m', f'src.etl.{transformer}', '--input', input_path, '--output', output_path]
    print(f"\n=== Running {transformer} ===\nInput:  {input_path}\nOutput: {output_path}\n")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"[OK] {transformer} complete.")
        return True
    else:
        print(f"[FAIL] {transformer} failed.")
        return False

def main():
    Path("tmp").mkdir(exist_ok=True)
    for transformer, input_path, output_path in ETL_STEPS:
        run_etl(transformer, input_path, output_path)

if __name__ == "__main__":
    main()
