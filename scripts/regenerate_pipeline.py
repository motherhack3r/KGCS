#!/usr/bin/env python
"""Regenerate all 10 pipeline stages in dependency order with SHACL validation.

Pipeline order (dependencies):
1. CPE (base)
2. CPEMatch (depends on CPE)
3. CVE (depends on CPE)
4. ATT&CK (independent, but now includes CAPEC extraction)
5. D3FEND (independent)
6. CAPEC (includes CWE relationships from XML)
7. CWE (independent)
8. CAR (depends on ATT&CK for detection mappings)
9. SHIELD (depends on ATT&CK for technique mappings)
10. ENGAGE (independent)
"""

import subprocess
import sys
import os
from pathlib import Path

# Define pipeline stages
STAGES = [
    {
        'name': 'CPE',
        'module': 'src.etl.etl_cpe',
        'input': 'data/cpe/raw/nvdcpe-2.0.json',
        'output': 'tmp/pipeline-stage1-cpe.ttl'
    },
    {
        'name': 'CPEMatch',
        'module': 'src.etl.etl_cpematch',
        'input': 'data/cpe/raw/nvdcpematch-1.0.json',
        'output': 'tmp/pipeline-stage2-cpematch.ttl'
    },
    {
        'name': 'CVE',
        'module': 'src.etl.etl_cve',
        'input': 'data/cve/raw',
        'output': 'tmp/pipeline-stage3-cve.ttl'
    },
    {
        'name': 'ATT&CK (Enterprise)',
        'module': 'src.etl.etl_attack',
        'input': 'data/attack/raw/enterprise-attack.json',
        'output': 'tmp/pipeline-stage4-attack.ttl'
    },
    {
        'name': 'ATT&CK (ICS)',
        'module': 'src.etl.etl_attack',
        'input': 'data/attack/raw/ics-attack.json',
        'output': 'tmp/pipeline-stage4-attack-ics.ttl'
    },
    {
        'name': 'ATT&CK (Mobile)',
        'module': 'src.etl.etl_attack',
        'input': 'data/attack/raw/mobile-attack.json',
        'output': 'tmp/pipeline-stage4-attack-mobile.ttl'
    },
    {
        'name': 'ATT&CK (Pre)',
        'module': 'src.etl.etl_attack',
        'input': 'data/attack/raw/pre-attack.json',
        'output': 'tmp/pipeline-stage4-attack-pre.ttl'
    },
    {
        'name': 'D3FEND',
        'module': 'src.etl.etl_d3fend',
        'input': 'data/d3fend/raw/d3fend.json',
        'output': 'tmp/pipeline-stage5-d3fend.ttl'
    },
    {
        'name': 'CAPEC',
        'module': 'src.etl.etl_capec',
        'input': 'data/capec/raw/capec_latest.xml',
        'output': 'tmp/pipeline-stage6-capec.ttl'
    },
    {
        'name': 'CWE',
        'module': 'src.etl.etl_cwe',
        'input': 'data/cwe/raw/cwec_latest.xml',
        'output': 'tmp/pipeline-stage7-cwe.ttl'
    },
    {
        'name': 'CAR',
        'module': 'src.etl.etl_car',
        'input': 'data/car/raw',
        'output': 'tmp/pipeline-stage8-car.ttl'
    },
    {
        'name': 'SHIELD',
        'module': 'src.etl.etl_shield',
        'input': 'data/shield/raw/shield.json',
        'output': 'tmp/pipeline-stage9-shield.ttl'
    },
    {
        'name': 'ENGAGE',
        'module': 'src.etl.etl_engage',
        'input': 'data/engage/raw/engage.json',
        'output': 'tmp/pipeline-stage10-engage.ttl'
    }
]

def run_stage(stage: dict) -> bool:
    """Run a single ETL stage with validation."""
    name = stage['name']
    module = stage['module']
    input_path = stage['input']
    output = stage['output']
    
    # Skip if input doesn't exist
    if not os.path.exists(input_path):
        print(f"\n⚠️  SKIP: {name}")
        print(f"   Input not found: {input_path}")
        return True  # Don't fail, just skip
    
    print(f"\n{'='*80}")
    print(f"[{STAGES.index(stage) + 1}/{len(STAGES)}] {name}")
    print(f"{'='*80}")
    print(f"Input:  {input_path}")
    print(f"Output: {output}")
    
    cmd = [
        sys.executable, '-m', module,
        '--input', input_path,
        '--output', output,
        '--validate'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {name}")
            # Show last few lines of output
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:
                if line.strip():
                    print(f"   {line}")
            return True
        else:
            print(f"❌ FAILED: {name}")
            print("STDOUT:")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            print("\nSTDERR:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {name} (exceeded 300 seconds)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {name}")
        print(f"   {e}")
        return False

def main():
    print("="*80)
    print("KGCS FULL PIPELINE REGENERATION")
    print("="*80)
    print(f"Total stages: {len(STAGES)}")
    print(f"Running with SHACL validation...")
    
    results = {}
    for stage in STAGES:
        success = run_stage(stage)
        results[stage['name']] = success
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n⚠️  Some stages failed. Review output above.")
        return 1
    else:
        print("\n✅ All stages completed successfully!")
        print("\nNext steps:")
        print("1. Verify SHACL validation reports in artifacts/")
        print("2. Combine pipeline stages: cat tmp/pipeline-stage*.ttl > tmp/combined-pipeline.ttl")
        print("3. Load into Neo4j: python src/etl/rdf_to_neo4j.py --ttl tmp/combined-pipeline.ttl")
        return 0

if __name__ == '__main__':
    sys.exit(main())
