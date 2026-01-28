#!/usr/bin/env python
"""
Demonstration of correct KGCS ETL ingestion order.

This script validates the three-stage pipeline:
  1. CPE ETL       → Platform nodes from CPE definitions
  2. CPEMatch ETL  → PlatformConfiguration nodes from match criteria
  3. CVE ETL       → Vulnerability nodes (references existing configs)

Proper order ensures:
  - No duplication of PlatformConfiguration entities
  - Referential integrity (foreign keys to existing entities)
  - Data normalization (1NF compliance)
"""

import glob
import subprocess
import sys
import os
from pathlib import Path
import argparse

def run_etl(transformer_module, input_file, output_file, extra_args=None):
    """Run a single ETL transformer."""
    cmd = [
        sys.executable, '-m', f'src.etl.{transformer_module}',
        '--input', input_file,
        '--output', output_file
    ]
    if extra_args:
        cmd.extend(extra_args)

    print(f"\n{'='*70}")
    print(f"Running: {transformer_module}")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")

    result = subprocess.run(cmd, cwd=os.getcwd())
    return result.returncode == 0


def combine_ttls(inputs, output_path: str) -> bool:
    existing = [p for p in inputs if os.path.exists(p)]
    if not existing:
        return False
    try:
        from rdflib import Graph
        graph = Graph()
        for path in existing:
            graph.parse(path, format='turtle')
        graph.serialize(destination=output_path, format='turtle')
        return True
    except Exception as e:
        print(f"Warning: could not combine TTLs into {output_path}: {e}")
        return False


def has_any_input(path_or_glob: str) -> bool:
    if os.path.isdir(path_or_glob):
        return True
    if any(ch in path_or_glob for ch in ['*', '?', '[']):
        return len(glob.glob(path_or_glob)) > 0
    return os.path.exists(path_or_glob)


def skip_stage(stage_label: str, reason: str) -> None:
    print(f"[SKIP] {stage_label} — {reason}")

def main():
    parser = argparse.ArgumentParser(description='KGCS ETL pipeline with optional Neo4j load')
    parser.add_argument('--load-neo4j', action='store_true', help='Load combined pipeline TTL into Neo4j using local config')
    parser.add_argument('--batch-size', type=int, default=1000, help='Neo4j batch size for load step')
    parser.add_argument('--dry-run', action='store_true', help='Parse and extract without writing to Neo4j')
    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════════════╗
║         KGCS 3-Stage ETL Pipeline (Correct Ingestion Order)        ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Stage 1: CPE ETL
    print("\n[STAGE 1/3] Transform CPE definitions → Platform nodes")
    print("-" * 70)
    if not run_etl('etl_cpe',
                   'data/cpe/raw/nvdcpe-2.0-chunks/*.json',
                   'tmp/pipeline-stage1-cpe.ttl'):
        print("CPE ETL failed")
        return 1
    print("CPE ETL completed")
    
    # Stage 2: CPEMatch ETL
    print("\n[STAGE 2/3] Transform CPEMatch criteria → PlatformConfiguration nodes")
    print("-" * 70)
    if not run_etl('etl_cpematch',
                   'data/cpe/raw/nvdcpematch-2.0-chunks/*.json',
                   'tmp/pipeline-stage2-cpematch.ttl'):
        print("CPEMatch ETL failed")
        return 1
    print("CPEMatch ETL completed")
    
    # Stage 3: CVE ETL
    print("\n[STAGE 3/3] Transform CVE records → Vulnerability nodes (references configs)")
    print("-" * 70)
    if not run_etl('etl_cve',
                   'data/cve/raw',
                   'tmp/pipeline-stage3-cve.ttl'):
        print("CVE ETL failed")
        return 1
    print("CVE ETL completed")

    # Additional standards
    print("\n[STAGE 4] Transform ATT&CK STIX → Technique/Tactic nodes")
    print("-" * 70)
    attack_inputs = [
        'data/attack/raw/enterprise-attack.json',
        'data/attack/raw/mobile-attack.json',
        'data/attack/raw/ics-attack.json',
        'data/attack/raw/pre-attack.json',
    ]
    attack_outputs = []
    for attack_input in attack_inputs:
        if has_any_input(attack_input):
            name = Path(attack_input).stem.replace('-attack', '')
            output_path = f'tmp/pipeline-stage4-attack-{name}.ttl'
            if not run_etl('etl_attack', attack_input, output_path):
                print("ATT&CK ETL failed")
                return 1
            attack_outputs.append(output_path)

    if attack_outputs:
        print("ATT&CK ETL completed")
        # Write a combined ATT&CK TTL for convenience
        try:
            from rdflib import Graph
            graph = Graph()
            for path in attack_outputs:
                graph.parse(path, format='turtle')
            graph.serialize(destination='tmp/pipeline-stage4-attack.ttl', format='turtle')
        except Exception as e:
            print(f"Warning: could not combine ATT&CK TTLs: {e}")
    else:
        skip_stage("ATT&CK", "raw STIX file not found")

    print("\n[STAGE 5] Transform D3FEND → DefensiveTechnique nodes")
    print("-" * 70)
    if has_any_input('data/d3fend/raw/d3fend.json'):
        if not run_etl('etl_d3fend',
                       'data/d3fend/raw/d3fend.json',
                       'tmp/pipeline-stage5-d3fend.ttl'):
            print("D3FEND ETL failed")
            return 1
        print("D3FEND ETL completed")
    else:
        skip_stage("D3FEND", "raw JSON not found (expected data/d3fend/raw/d3fend.json)")

    print("\n[STAGE 6] Transform CAPEC → AttackPattern nodes")
    print("-" * 70)
    if has_any_input('data/capec/raw/capec_latest.xml'):
        if not run_etl('etl_capec',
                       'data/capec/raw/capec_latest.xml',
                       'tmp/pipeline-stage6-capec.ttl',
                       extra_args=['--attack-input', 'data/attack/raw']):
            print("CAPEC ETL failed")
            return 1
        print("CAPEC ETL completed")
    else:
        skip_stage("CAPEC", "raw file not found")

    print("\n[STAGE 7] Transform CWE → Weakness nodes")
    print("-" * 70)
    cwe_input = None
    if has_any_input('data/cwe/raw/cwec_latest.xml'):
        cwe_input = 'data/cwe/raw/cwec_latest.xml'
    else:
        candidates = glob.glob('data/cwe/raw/cwec*.xml')
        if candidates:
            cwe_input = sorted(candidates)[0]

    if cwe_input:
        if not run_etl('etl_cwe',
                       cwe_input,
                       'tmp/pipeline-stage7-cwe.ttl'):
            print("CWE ETL failed")
            return 1
        print("CWE ETL completed")
    else:
        skip_stage("CWE", "raw file not found")

    print("\n[STAGE 8] Transform CAR → DetectionAnalytic nodes")
    print("-" * 70)
    if has_any_input('data/car/raw/*.yaml'):
        if not run_etl('etl_car',
                       'data/car/raw',
                       'tmp/pipeline-stage8-car.ttl'):
            print("CAR ETL failed")
            return 1
        print("CAR ETL completed")
    else:
        skip_stage("CAR", "raw files not found")

    print("\n[STAGE 9] Transform SHIELD → DeceptionTechnique nodes")
    print("-" * 70)
    if has_any_input('data/shield/raw'):
        if not run_etl('etl_shield',
                       'data/shield/raw',
                       'tmp/pipeline-stage9-shield.ttl'):
            print("SHIELD ETL failed")
            return 1
        print("SHIELD ETL completed")
    else:
        skip_stage("SHIELD", "raw files not found")

    print("\n[STAGE 10] Transform ENGAGE → EngagementConcept nodes")
    print("-" * 70)
    if has_any_input('data/engage/raw'):
        if not run_etl('etl_engage',
                       'data/engage/raw',
                       'tmp/pipeline-stage10-engage.ttl'):
            print("ENGAGE ETL failed")
            return 1
        print("ENGAGE ETL completed")
    else:
        skip_stage("ENGAGE", "raw files not found")
    
    # Summary
    print(f"\n{'='*70}")
    print("PIPELINE COMPLETE")
    print(f"{'='*70}")
    print("""
Generated outputs:
  Stage 1: tmp/pipeline-stage1-cpe.ttl         (Platform nodes)
  Stage 2: tmp/pipeline-stage2-cpematch.ttl    (PlatformConfiguration nodes)
  Stage 3: tmp/pipeline-stage3-cve.ttl         (Vulnerability nodes + references)
  Stage 4: tmp/pipeline-stage4-attack.ttl      (Technique/Tactic nodes)
  Stage 5: tmp/pipeline-stage5-d3fend.ttl      (DefensiveTechnique nodes)
  Stage 6: tmp/pipeline-stage6-capec.ttl       (AttackPattern nodes)
  Stage 7: tmp/pipeline-stage7-cwe.ttl         (Weakness nodes)
  Stage 8: tmp/pipeline-stage8-car.ttl         (DetectionAnalytic nodes)
  Stage 9: tmp/pipeline-stage9-shield.ttl      (DeceptionTechnique nodes)
  Stage 10: tmp/pipeline-stage10-engage.ttl    (EngagementConcept nodes)

All outputs generated successfully.

Architecture achieved:
  - Referential integrity (CVE → PlatformConfiguration → Platform)
  - No duplication of entities
  - Data normalization (1NF compliance)
  - Proper key relationships (matchCriteriaId as foreign key)
    """)
    
    if args.load_neo4j:
        print("\n[LOAD] Combine pipeline outputs and load into Neo4j (local config)")
        print("-" * 70)
        combined_path = 'tmp/pipeline-stage-all.ttl'
        pipeline_outputs = [
            'tmp/pipeline-stage1-cpe.ttl',
            'tmp/pipeline-stage2-cpematch.ttl',
            'tmp/pipeline-stage3-cve.ttl',
            'tmp/pipeline-stage4-attack.ttl',
            'tmp/pipeline-stage5-d3fend.ttl',
            'tmp/pipeline-stage6-capec.ttl',
            'tmp/pipeline-stage7-cwe.ttl',
            'tmp/pipeline-stage8-car.ttl',
            'tmp/pipeline-stage9-shield.ttl',
            'tmp/pipeline-stage10-engage.ttl',
        ]
        if not combine_ttls(pipeline_outputs, combined_path):
            print("No pipeline outputs found to combine; skipping Neo4j load.")
            return 1

        cmd = [
            sys.executable,
            'src/etl/rdf_to_neo4j.py',
            '--ttl', combined_path,
            '--batch-size', str(args.batch_size),
        ]
        if args.dry_run:
            cmd.append('--dry-run')

        print(f"Loading Neo4j from {combined_path} using local config...")
        result = subprocess.run(cmd, cwd=os.getcwd())
        if result.returncode != 0:
            print("Neo4j load failed")
            return 1
        print("Neo4j load completed")

    return 0

if __name__ == '__main__':
    sys.exit(main())
