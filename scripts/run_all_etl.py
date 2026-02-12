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

def run_etl(transformer, input_path, output_path, nodes_out=None, rels_out=None, extra_args=None, rels_include_types=False):
    """Run a single ETL transformer."""
    if not os.path.exists(input_path):
        print(f"[SKIP] {input_path} not found.")
        return False
    cmd = [sys.executable, '-m', f'src.etl.{transformer}', '--input', input_path, '--output', output_path]
    if nodes_out and rels_out:
        cmd += ['--nodes-out', nodes_out, '--rels-out', rels_out]
        if rels_include_types:
            cmd.append('--rels-include-types')
    if extra_args:
        cmd += list(extra_args)
    print(f"\n=== Running {transformer} ===\nInput:  {input_path}\nOutput: {output_path}\n")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode == 0:
        print(f"[OK] {transformer} complete.")
        return True
    else:
        print(f"[FAIL] {transformer} failed (exit code: {result.returncode}).")
        return False


def run_etl_with_append(transformer, input_path, output_path, append=False, nodes_out=None, rels_out=None, extra_args=None, rels_include_types=False):
    """Run a single ETL transformer with optional append mode."""
    if not os.path.exists(input_path):
        print(f"[SKIP] {input_path} not found.")
        return False
    cmd = [sys.executable, '-m', f'src.etl.{transformer}', '--input', input_path, '--output', output_path]
    if append:
        cmd.append('--append')
    if nodes_out and rels_out:
        cmd += ['--nodes-out', nodes_out, '--rels-out', rels_out]
        if rels_include_types:
            cmd.append('--rels-include-types')
    if extra_args:
        cmd += list(extra_args)
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
    rels_include_types = True
    include_orphan_configs = os.getenv("KGCS_INCLUDE_ORPHAN_CONFIGS", "1").strip().lower() in ("1", "true", "yes")
    
    # Stage 1: Process CPE chunks
    print("\n" + "="*70)
    print("STAGE 1: CPE (National Vulnerability Database Platform Enumeration)")
    print("="*70)
    cpe_chunks = find_files("data/cpe/raw/nvdcpe-2.0-chunks/*.json")
    if cpe_chunks:
        # Clean up output file before processing
        output_cpe = "data/cpe/samples/pipeline-stage1-cpe.ttl"
        nodes_cpe = "data/cpe/samples/pipeline-stage1-cpe-nodes.ttl"
        rels_cpe = "data/cpe/samples/pipeline-stage1-cpe-rels.ttl"
        Path(output_cpe).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_cpe):
            os.remove(output_cpe)
        for p in (nodes_cpe, rels_cpe):
            if os.path.exists(p):
                os.remove(p)
        for i, chunk_file in enumerate(cpe_chunks):
            # Append to output after first file
            run_etl_with_append(
                "etl_cpe",
                chunk_file,
                output_cpe,
                append=(i > 0),
                nodes_out=nodes_cpe,
                rels_out=rels_cpe,
                rels_include_types=rels_include_types,
            )
    else:
        print("[SKIP] No CPE chunk files found in data/cpe/raw/nvdcpe-2.0-chunks/")
    
    # # Stage 2: Process CPEMatch chunks
    print("\n" + "="*70)
    print("STAGE 2: CPEMatch (CVE to CPE Mappings)")
    print("="*70)
    cpematch_chunks = find_files("data/cpe/raw/nvdcpematch-2.0-chunks/*.json")
    if cpematch_chunks:
        # Clean up output file before processing
        output_cpematch = "data/cpe/samples/pipeline-stage2-cpematch.ttl"
        nodes_cpematch = "data/cpe/samples/pipeline-stage2-cpematch-nodes.ttl"
        rels_cpematch = "data/cpe/samples/pipeline-stage2-cpematch-rels.ttl"
        Path(output_cpematch).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_cpematch):
            os.remove(output_cpematch)
        for p in (nodes_cpematch, rels_cpematch):
            if os.path.exists(p):
                os.remove(p)
        cpematch_extra_args = ['--include-orphan-configs'] if include_orphan_configs else ['--exclude-orphan-configs']
        for i, chunk_file in enumerate(cpematch_chunks):
            # Append to output after first file
            run_etl_with_append(
                "etl_cpematch",
                chunk_file,
                output_cpematch,
                append=(i > 0),
                nodes_out=nodes_cpematch,
                rels_out=rels_cpematch,
                rels_include_types=rels_include_types,
                extra_args=cpematch_extra_args,
            )
    else:
        print("[SKIP] No CPEMatch chunk files found in data/cpe/raw/nvdcpematch-2.0-chunks/")
    # Build a reusable CPEMatch criteria index once for CVE ETL to consume
    cpematch_index_path = "data/cpe/samples/cpematch-criteria-index.json"
    cpematch_index_meta = cpematch_index_path + ".meta.json"
    if cpematch_chunks:
        try:
            from src.utils.cpematch_index import build_cpematch_index, save_index

            # Compute fingerprint of raw chunk files: max mtime, total size, count
            files = find_files("data/cpe/raw/nvdcpematch-2.0-chunks/*.json")
            mtimes = []
            sizes = []
            for f in files:
                try:
                    stat = os.stat(f)
                    mtimes.append(int(stat.st_mtime))
                    sizes.append(stat.st_size)
                except Exception:
                    continue
            fingerprint = {
                "max_mtime": max(mtimes) if mtimes else 0,
                "total_size": sum(sizes) if sizes else 0,
                "count": len(files),
            }

            need_build = True
            if os.path.exists(cpematch_index_path) and os.path.exists(cpematch_index_meta):
                try:
                    import json
                    with open(cpematch_index_meta, 'r', encoding='utf-8') as mfh:
                        meta = json.load(mfh)
                    if meta.get('fingerprint') == fingerprint:
                        need_build = False
                        print(f"CPEMatch index up-to-date ({cpematch_index_path}), skipping rebuild")
                except Exception:
                    need_build = True

            if need_build:
                print(f"Building CPEMatch index at {cpematch_index_path}...")
                index = build_cpematch_index("data/cpe/raw/nvdcpematch-2.0-chunks")
                save_index(cpematch_index_path, index)
                try:
                    import json
                    meta = {"fingerprint": fingerprint, "entries": len(index)}
                    Path(os.path.dirname(cpematch_index_meta)).mkdir(parents=True, exist_ok=True)
                    tmp = cpematch_index_meta + '.tmp'
                    with open(tmp, 'w', encoding='utf-8') as mfh:
                        json.dump(meta, mfh)
                    os.replace(tmp, cpematch_index_meta)
                except Exception as e:
                    print(f"Warning: failed to write cpematch index meta: {e}")
                print(f"CPEMatch index saved ({len(index)} entries) to {cpematch_index_path}")
        except Exception as e:
            print(f"Warning: failed to build/save cpematch index: {e}")
    
    # Stage 3: Process CVE files (all years)
    print("\n" + "="*70)
    print("STAGE 3: CVE (Common Vulnerabilities and Exposures)")
    print("="*70)
    cve_files = find_files("data/cve/raw/nvdcve-2.0-*.json")
    if cve_files:
        # Clean up output file before processing
        output_cve = "data/cve/samples/pipeline-stage3-cve.ttl"
        nodes_cve = "data/cve/samples/pipeline-stage3-cve-nodes.ttl"
        rels_cve = "data/cve/samples/pipeline-stage3-cve-rels.ttl"
        Path(output_cve).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_cve):
            os.remove(output_cve)
        for p in (nodes_cve, rels_cve):
            if os.path.exists(p):
                os.remove(p)
        # Prefer passing the pre-built cpematch index to CVE ETL
        cpematch_input = "data/cpe/raw/nvdcpematch-2.0-chunks"
        extra_args = []
        if os.path.exists(cpematch_index_path):
            extra_args = ['--cpematch-index', cpematch_index_path]
        elif os.path.exists(cpematch_input):
            extra_args = ['--cpematch-input', cpematch_input]
        for i, cve_file in enumerate(cve_files):
            # Append to output after first file
            run_etl_with_append(
                "etl_cve",
                cve_file,
                output_cve,
                append=(i > 0),
                nodes_out=nodes_cve,
                rels_out=rels_cve,
                extra_args=extra_args,
                rels_include_types=rels_include_types,
            )
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
        nodes_attack = "data/attack/samples/pipeline-stage4-attack-nodes.ttl"
        rels_attack = "data/attack/samples/pipeline-stage4-attack-rels.ttl"
        Path(output_attack).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_attack):
            os.remove(output_attack)
        for p in (nodes_attack, rels_attack):
            if os.path.exists(p):
                os.remove(p)
        for i, attack_file in enumerate(attack_files):
            # Append to output after first file
            run_etl_with_append(
                "etl_attack",
                attack_file,
                output_attack,
                append=(i > 0),
                nodes_out=nodes_attack,
                rels_out=rels_attack,
                rels_include_types=rels_include_types,
            )
    else:
        print("[SKIP] No ATT&CK JSON files found in data/attack/raw/")
    
    # Stage 5: D3FEND
    print("\n" + "="*70)
    print("STAGE 5: D3FEND (Detection, Denial, and Disruption Framework)")
    print("="*70)
    output_file = "data/d3fend/samples/pipeline-stage5-d3fend.ttl"
    nodes_d3fend = "data/d3fend/samples/pipeline-stage5-d3fend-nodes.ttl"
    rels_d3fend = "data/d3fend/samples/pipeline-stage5-d3fend-rels.ttl"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(output_file):
        os.remove(output_file)
    for p in (nodes_d3fend, rels_d3fend):
        if os.path.exists(p):
            os.remove(p)
    
    # Process both D3FEND files: definitions + full mappings
    d3fend_files = ["data/d3fend/raw/d3fend.json", "data/d3fend/raw/d3fend-full-mappings.json"]
    d3fend_files = [f for f in d3fend_files if os.path.exists(f)]
    
    for idx, d3fend_file in enumerate(d3fend_files):
        print(f"Processing: {d3fend_file} ({idx+1}/{len(d3fend_files)})")
        run_etl_with_append(
            "etl_d3fend",
            d3fend_file,
            output_file,
            append=(idx > 0),
            nodes_out=nodes_d3fend,
            rels_out=rels_d3fend,
            rels_include_types=rels_include_types,
        )
    
    if not d3fend_files:
        print("[SKIP] No D3FEND JSON files found in data/d3fend/raw/")
    
    # Stage 6: CAPEC
    print("\n" + "="*70)
    print("STAGE 6: CAPEC (Common Attack Pattern Expression and Enumeration)")
    print("="*70)
    output_capec = "data/capec/samples/pipeline-stage6-capec.ttl"
    nodes_capec = "data/capec/samples/pipeline-stage6-capec-nodes.ttl"
    rels_capec = "data/capec/samples/pipeline-stage6-capec-rels.ttl"
    Path(output_capec).parent.mkdir(parents=True, exist_ok=True)
    for p in (nodes_capec, rels_capec):
        if os.path.exists(p):
            os.remove(p)
    run_etl(
        "etl_capec",
        "data/capec/raw/capec_latest.xml",
        output_capec,
        nodes_out=nodes_capec,
        rels_out=rels_capec,
        rels_include_types=rels_include_types,
    )
    
    # Stage 7: CWE
    print("\n" + "="*70)
    print("STAGE 7: CWE (Common Weakness Enumeration)")
    print("="*70)
    output_cwe = "data/cwe/samples/pipeline-stage7-cwe.ttl"
    nodes_cwe = "data/cwe/samples/pipeline-stage7-cwe-nodes.ttl"
    rels_cwe = "data/cwe/samples/pipeline-stage7-cwe-rels.ttl"
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
        for p in (nodes_cwe, rels_cwe):
            if os.path.exists(p):
                os.remove(p)
        run_etl(
            "etl_cwe",
            cwe_inputs[0],
            output_cwe,
            nodes_out=nodes_cwe,
            rels_out=rels_cwe,
            rels_include_types=rels_include_types,
        )
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
        nodes_car = "data/car/samples/pipeline-stage8-car-nodes.ttl"
        rels_car = "data/car/samples/pipeline-stage8-car-rels.ttl"
        Path(output_car).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(output_car):
            os.remove(output_car)
        for p in (nodes_car, rels_car):
            if os.path.exists(p):
                os.remove(p)
        # Process all CAR files, appending to same output file after first
        for i, car_file in enumerate(car_files):
            if i == 0:
                # First file: create new output
                run_etl_with_append(
                    "etl_car",
                    car_file,
                    output_car,
                    append=False,
                    nodes_out=nodes_car,
                    rels_out=rels_car,
                    rels_include_types=rels_include_types,
                )
            else:
                # Subsequent files: append to output
                run_etl_with_append(
                    "etl_car",
                    car_file,
                    output_car,
                    append=True,
                    nodes_out=nodes_car,
                    rels_out=rels_car,
                    rels_include_types=rels_include_types,
                )
    else:
        print("[SKIP] No CAR YAML files found in data/car/raw/")
    
    # Stage 9: SHIELD
    print("\n" + "="*70)
    print("STAGE 9: SHIELD (Deception Techniques)")
    print("="*70)
    output_shield = "data/shield/samples/pipeline-stage9-shield.ttl"
    nodes_shield = "data/shield/samples/pipeline-stage9-shield-nodes.ttl"
    rels_shield = "data/shield/samples/pipeline-stage9-shield-rels.ttl"
    Path(output_shield).parent.mkdir(parents=True, exist_ok=True)
    for p in (nodes_shield, rels_shield):
        if os.path.exists(p):
            os.remove(p)
    run_etl(
        "etl_shield",
        "data/shield/raw",
        output_shield,
        nodes_out=nodes_shield,
        rels_out=rels_shield,
        rels_include_types=rels_include_types,
    )
    
    # Stage 10: ENGAGE
    print("\n" + "="*70)
    print("STAGE 10: ENGAGE (Strategic Engagement Framework)")
    print("="*70)
    output_engage = "data/engage/samples/pipeline-stage10-engage.ttl"
    nodes_engage = "data/engage/samples/pipeline-stage10-engage-nodes.ttl"
    rels_engage = "data/engage/samples/pipeline-stage10-engage-rels.ttl"
    Path(output_engage).parent.mkdir(parents=True, exist_ok=True)
    for p in (nodes_engage, rels_engage):
        if os.path.exists(p):
            os.remove(p)
    run_etl(
        "etl_engage",
        "data/engage/raw",
        output_engage,
        nodes_out=nodes_engage,
        rels_out=rels_engage,
        rels_include_types=rels_include_types,
    )
    
    print("\n" + "="*70)
    print("ETL PIPELINE COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
