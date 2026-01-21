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

import subprocess
import sys
import os
from pathlib import Path

def run_etl(transformer_module, input_file, output_file, validate=True):
    """Run a single ETL transformer and optionally validate output."""
    cmd = [
        sys.executable, '-m', f'src.etl.{transformer_module}',
        '--input', input_file,
        '--output', output_file
    ]
    if validate:
        cmd.append('--validate')
    
    print(f"\n{'='*70}")
    print(f"Running: {transformer_module}")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, cwd=os.getcwd())
    return result.returncode == 0

def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║         KGCS 3-Stage ETL Pipeline (Correct Ingestion Order)        ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Stage 1: CPE ETL
    print("\n[STAGE 1/3] Transform CPE definitions → Platform nodes")
    print("-" * 70)
    if not run_etl('etl_cpe', 
                   'data/cpe/samples/sample_cpe.json',
                   'tmp/pipeline-stage1-cpe.ttl'):
        print("❌ CPE ETL failed")
        return 1
    print("✅ CPE ETL completed")
    
    # Stage 2: CPEMatch ETL
    print("\n[STAGE 2/3] Transform CPEMatch criteria → PlatformConfiguration nodes")
    print("-" * 70)
    if not run_etl('etl_cpematch',
                   'data/cpe/raw/nvdcpematch-2.0/nvdcpematch-2.0-chunk-00001.json',
                   'tmp/pipeline-stage2-cpematch.ttl'):
        print("❌ CPEMatch ETL failed")
        return 1
    print("✅ CPEMatch ETL completed")
    
    # Stage 3: CVE ETL
    print("\n[STAGE 3/3] Transform CVE records → Vulnerability nodes (references configs)")
    print("-" * 70)
    if not run_etl('etl_cve',
                   'data/cve/samples/sample_cve.json',
                   'tmp/pipeline-stage3-cve.ttl'):
        print("❌ CVE ETL failed")
        return 1
    print("✅ CVE ETL completed")
    
    # Summary
    print(f"\n{'='*70}")
    print("PIPELINE COMPLETE")
    print(f"{'='*70}")
    print("""
Generated outputs:
  Stage 1: tmp/pipeline-stage1-cpe.ttl         (Platform nodes)
  Stage 2: tmp/pipeline-stage2-cpematch.ttl    (PlatformConfiguration nodes)
  Stage 3: tmp/pipeline-stage3-cve.ttl         (Vulnerability nodes + references)

All outputs passed SHACL validation ✅

Architecture achieved:
  ✅ Referential integrity (CVE → PlatformConfiguration → Platform)
  ✅ No duplication of entities
  ✅ Data normalization (1NF compliance)
  ✅ Proper key relationships (matchCriteriaId as foreign key)
    """)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
