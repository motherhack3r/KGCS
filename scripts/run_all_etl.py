#!/usr/bin/env python3
"""
Run all KGCS ETL transformers in correct order on downloaded raw data.
Outputs TTL files to tmp/ for each standard.
Processes chunked files (CPE, CPEMatch, CVE) by iterating through all chunks.
"""
import subprocess
import sys
import os
import glob
from pathlib import Path

def find_files(pattern, recursive=False):
    """Find all files matching a glob pattern."""
    files = sorted(glob.glob(pattern, recursive=recursive))
    return files

def run_etl(transformer, input_path, output_path):
    """Run a single ETL transformer."""
    if not os.path.exists(input_path):
        print(f"[SKIP] {input_path} not found.")
        return False
    cmd = [sys.executable, '-m', f'src.etl.{transformer}', '--input', input_path, '--output', output_path]
    print(f"\n=== Running {transformer} ===\nInput:  {input_path}\nOutput: {output_path}\n")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode == 0:
        print(f"[OK] {transformer} complete.")
        return True
    else:
        print(f"[FAIL] {transformer} failed (exit code: {result.returncode}).")
        return False


def run_etl_with_append(transformer, input_path, output_path, append=False):
    """Run a single ETL transformer with optional append mode."""
    if not os.path.exists(input_path):
        print(f"[SKIP] {input_path} not found.")
        return False
    cmd = [sys.executable, '-m', f'src.etl.{transformer}', '--input', input_path, '--output', output_path]
    if append:
        cmd.append('--append')
    print(f"\n=== Running {transformer} ===\nInput:  {input_path}\nOutput: {output_path} (append={append})\n")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode == 0:
        print(f"[OK] {transformer} complete.")
        return True
    else:
        print(f"[FAIL] {transformer} failed (exit code: {result.returncode}).")
        return False

def main():
    Path("tmp").mkdir(exist_ok=True)
    
    # Stage 1: Process CPE chunks
    print("\n" + "="*70)
    print("STAGE 1: CPE (National Vulnerability Database Platform Enumeration)")
    print("="*70)
    cpe_chunks = find_files("data/cpe/raw/nvdcpe-2.0-chunks/*.json")
    if cpe_chunks:
        # Clean up output file before processing
        output_cpe = "tmp/pipeline-stage1-cpe.ttl"
        if os.path.exists(output_cpe):
            os.remove(output_cpe)
        for i, chunk_file in enumerate(cpe_chunks):
            # Append to output after first file
            run_etl_with_append("etl_cpe", chunk_file, output_cpe, append=(i > 0))
    else:
        print("[SKIP] No CPE chunk files found in data/cpe/raw/nvdcpe-2.0-chunks/")
    
    # Stage 2: Process CPEMatch chunks
    print("\n" + "="*70)
    print("STAGE 2: CPEMatch (CVE to CPE Mappings)")
    print("="*70)
    cpematch_chunks = find_files("data/cpe/raw/nvdcpematch-2.0-chunks/*.json")
    if cpematch_chunks:
        # Clean up output file before processing
        output_cpematch = "tmp/pipeline-stage2-cpematch.ttl"
        if os.path.exists(output_cpematch):
            os.remove(output_cpematch)
        for i, chunk_file in enumerate(cpematch_chunks):
            # Append to output after first file
            run_etl_with_append("etl_cpematch", chunk_file, output_cpematch, append=(i > 0))
    else:
        print("[SKIP] No CPEMatch chunk files found in data/cpe/raw/nvdcpematch-2.0-chunks/")
    
    # Stage 3: Process CVE files (all years)
    print("\n" + "="*70)
    print("STAGE 3: CVE (Common Vulnerabilities and Exposures)")
    print("="*70)
    cve_files = find_files("data/cve/raw/nvdcve-2.0-*.json")
    if cve_files:
        # Clean up output file before processing
        output_cve = "tmp/pipeline-stage3-cve.ttl"
        if os.path.exists(output_cve):
            os.remove(output_cve)
        for i, cve_file in enumerate(cve_files):
            # Append to output after first file
            run_etl_with_append("etl_cve", cve_file, output_cve, append=(i > 0))
    else:
        print("[SKIP] No CVE files found in data/cve/raw/")
    
    # Stage 4: ATT&CK (all variants: Enterprise, ICS, Mobile, Pre-Attack)
    print("\n" + "="*70)
    print("STAGE 4: ATT&CK (Adversarial Tactics, Techniques & Common Knowledge)")
    print("="*70)
    attack_files = find_files("data/attack/raw/*-attack.json")
    if attack_files:
        # Save attack output to standard samples directory
        output_attack = "data/attack/samples/pipeline-stage4-attack.ttl"
        Path(output_attack).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_attack):
            os.remove(output_attack)
        for i, attack_file in enumerate(attack_files):
            # Append to output after first file
            run_etl_with_append("etl_attack", attack_file, output_attack, append=(i > 0))
    else:
        print("[SKIP] No ATT&CK JSON files found in data/attack/raw/")
    
    # Stage 5: D3FEND
    print("\n" + "="*70)
    print("STAGE 5: D3FEND (Detection, Denial, and Disruption Framework)")
    print("="*70)
    output_file = "data/d3fend/samples/pipeline-stage5-d3fend.ttl"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Process both D3FEND files: definitions + full mappings
    d3fend_files = ["data/d3fend/raw/d3fend.json", "data/d3fend/raw/d3fend-full-mappings.json"]
    d3fend_files = [f for f in d3fend_files if os.path.exists(f)]
    
    for idx, d3fend_file in enumerate(d3fend_files):
        print(f"Processing: {d3fend_file} ({idx+1}/{len(d3fend_files)})")
        run_etl_with_append("etl_d3fend", d3fend_file, output_file, append=(idx > 0))
    
    if not d3fend_files:
        print("[SKIP] No D3FEND JSON files found in data/d3fend/raw/")
    
    # Stage 6: CAPEC
    print("\n" + "="*70)
    print("STAGE 6: CAPEC (Common Attack Pattern Expression and Enumeration)")
    print("="*70)
    output_capec = "data/capec/samples/pipeline-stage6-capec.ttl"
    Path(output_capec).parent.mkdir(parents=True, exist_ok=True)
    run_etl("etl_capec", "data/capec/raw/capec_latest.xml", output_capec)
    
    # Stage 7: CWE
    print("\n" + "="*70)
    print("STAGE 7: CWE (Common Weakness Enumeration)")
    print("="*70)
    output_cwe = "data/cwe/samples/pipeline-stage7-cwe.ttl"
    Path(output_cwe).parent.mkdir(parents=True, exist_ok=True)
    # Support variable CWE filenames (e.g. cwe_latest.xml)
    cwe_inputs = find_files("data/cwe/raw/*.xml")
    if cwe_inputs:
        # If multiple CWE XMLs are present, process the first one only
        if len(cwe_inputs) > 1:
            print(f"[WARN] Multiple CWE files found; using first: {cwe_inputs[0]}")
        # Ensure fresh write
        if os.path.exists(output_cwe):
            os.remove(output_cwe)
        run_etl("etl_cwe", cwe_inputs[0], output_cwe)
    else:
        print("[SKIP] No CWE XML file found in data/cwe/raw/")
    
    # Stage 8: CAR (Cyber Analytics Repository - all analytics, data_model, and sensors)
    print("\n" + "="*70)
    print("STAGE 8: CAR (Cyber Analytics Repository)")
    print("="*70)
    # Get both root-level files and files in subdirectories
    car_files = find_files("data/car/raw/*.yaml", recursive=False)
    car_files += find_files("data/car/raw/**/*.yaml", recursive=True)
    car_files = sorted(list(set(car_files)))  # Deduplicate
    if car_files:
        # Save CAR output to standard samples directory
        output_car = "data/car/samples/pipeline-stage8-car.ttl"
        Path(output_car).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_car):
            os.remove(output_car)
        # Process all CAR files, appending to same output file after first
        for i, car_file in enumerate(car_files):
            if i == 0:
                # First file: create new output
                run_etl_with_append("etl_car", car_file, output_car, append=False)
            else:
                # Subsequent files: append to output
                run_etl_with_append("etl_car", car_file, output_car, append=True)
    else:
        print("[SKIP] No CAR YAML files found in data/car/raw/")
    
    # Stage 9: SHIELD
    print("\n" + "="*70)
    print("STAGE 9: SHIELD (Deception Techniques)")
    print("="*70)
    output_shield = "data/shield/samples/pipeline-stage9-shield.ttl"
    Path(output_shield).parent.mkdir(parents=True, exist_ok=True)
    run_etl("etl_shield", "data/shield/raw", output_shield)
    
    # Stage 10: ENGAGE
    print("\n" + "="*70)
    print("STAGE 10: ENGAGE (Strategic Engagement Framework)")
    print("="*70)
    output_engage = "data/engage/samples/pipeline-stage10-engage.ttl"
    Path(output_engage).parent.mkdir(parents=True, exist_ok=True)
    run_etl("etl_engage", "data/engage/raw", output_engage)
    
    print("\n" + "="*70)
    print("ETL PIPELINE COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
