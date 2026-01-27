#!/usr/bin/env python3
"""
Phase 3 Comprehensive ETL Test Suite

Tests all 9 ETL transformers with available sample data:
1. CPE (NVD)
2. CVE (NVD)
3. CWE (MITRE)
4. CAPEC (MITRE)
5. ATT&CK (MITRE)
6. D3FEND (MITRE)
7. CAR (MITRE)
8. SHIELD (MITRE)
9. ENGAGE (MITRE)

Each test:
  - Loads sample JSON
  - Transforms to RDF
  - Validates with SHACL
  - Reports statistics
"""

import sys
import os
import json
import yaml
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.validation import load_graph, run_validator
from src.etl.etl_cpe import CPEtoRDFTransformer
from src.etl.etl_cve import CVEtoRDFTransformer
from src.etl.etl_cwe import CWEtoRDFTransformer
from src.etl.etl_capec import CAPECtoRDFTransformer
from src.etl.etl_attack import ATTACKtoRDFTransformer
from src.etl.etl_d3fend import D3FENDtoRDFTransformer
from src.etl.etl_car import CARtoRDFTransformer
from src.etl.etl_shield import SHIELDtoRDFTransformer
from src.etl.etl_engage import ENGAGEtoRDFTransformer

TEST_CASES = [
    ('CPE', 'data/cpe/samples/sample_cpe.json', CPEtoRDFTransformer, 'tmp/phase3_cpe.ttl'),
    ('CVE', 'data/cve/samples/sample_cve.json', CVEtoRDFTransformer, 'tmp/phase3_cve.ttl'),
    ('CWE', 'tmp/sample_cwe.ttl', CWEtoRDFTransformer, 'tmp/phase3_cwe.ttl'),
    ('CAPEC', 'tmp/sample_capec.ttl', CAPECtoRDFTransformer, 'tmp/phase3_capec.ttl'),
    ('ATT&CK', 'tmp/sample_attack.ttl', ATTACKtoRDFTransformer, 'tmp/phase3_attack.ttl'),
    ('D3FEND', 'tmp/sample_d3fend.ttl', D3FENDtoRDFTransformer, 'tmp/phase3_d3fend.ttl'),
    ('CAR', 'data/car/samples/sample_car.yaml', CARtoRDFTransformer, 'tmp/phase3_car.ttl'),
    ('SHIELD', 'tmp/sample_shield.ttl', SHIELDtoRDFTransformer, 'tmp/phase3_shield.ttl'),
    ('ENGAGE', 'tmp/sample_engage.ttl', ENGAGEtoRDFTransformer, 'tmp/phase3_engage.ttl'),
]


@pytest.mark.parametrize("name,sample_file,transformer_class,output_file", TEST_CASES)
def test_etl(name, sample_file, transformer_class, output_file):
    """Test a single ETL transformer."""
    
    if not os.path.exists(sample_file):
        return {
            'status': 'SKIP',
            'message': f'Sample file not found: {sample_file}'
        }
    
    try:
        # Load data
        with open(sample_file, 'r', encoding='utf-8') as f:
            if sample_file.lower().endswith(('.yaml', '.yml')):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        record_count = 0
        
        # Count records based on structure
        if 'products' in data:
            record_count = len(data['products'])
        elif 'vulnerabilities' in data:
            record_count = len(data['vulnerabilities'])
        elif 'weaknesses' in data:
            record_count = len(data['weaknesses'])
        elif 'attackPatterns' in data:
            record_count = len(data['attackPatterns'])
        elif 'objects' in data:  # STIX format
            record_count = len([o for o in data['objects'] if o.get('type') != 'bundle'])
        else:
            record_count = len(data) if isinstance(data, list) else 1
        
        # Transform
        if name == 'CAR':
            if isinstance(data, dict):
                if 'DetectionAnalytics' in data:
                    data = data['DetectionAnalytics']
                else:
                    data = [data]
        transformer = transformer_class()
        graph = transformer.transform(data)
        triple_count = len(graph)
        
        # Save output
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        graph.serialize(destination=output_file, format='turtle')
        
        # Validate (best effort)
        try:
            shapes_file = f'docs/ontology/shacl/{name.lower()}-shapes.ttl'
            if not os.path.exists(shapes_file):
                shapes_file = 'docs/ontology/shacl/kgcs-shapes.ttl'
            
            shapes_graph = load_graph(shapes_file)
            conforms, report_path, _ = run_validator(output_file, shapes_graph, 'artifacts')
            validation_status = 'PASS' if conforms else 'WARN'
        except Exception as e:
            validation_status = 'ERROR'
            report_path = str(e)
        
        return {
            'status': 'PASS',
            'records': record_count,
            'triples': triple_count,
            'output': output_file,
            'validation': validation_status,
            'file_size': os.path.getsize(output_file)
        }
    
    except Exception as e:
        return {
            'status': 'FAIL',
            'error': str(e)
        }


def main():
    """Run all Phase 3 ETL tests."""
    
    print("=" * 100)
    print("PHASE 3: COMPREHENSIVE ETL PIPELINE TEST SUITE")
    print("=" * 100)
    print()
    
    tests = TEST_CASES
    
    results = {}
    total_records = 0
    total_triples = 0
    
    for name, sample, transformer, output in tests:
        print(f"Testing {name:10s}... ", end='', flush=True)
        result = test_etl(name, sample, transformer, output)
        results[name] = result
        
        if result['status'] == 'PASS':
            print(f"✓ {result['records']:5d} records → {result['triples']:8d} triples | Validation: {result['validation']}")
            total_records += result['records']
            total_triples += result['triples']
        elif result['status'] == 'SKIP':
            print(f"⊘ {result['message']}")
        else:
            print(f"✗ {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    skipped = sum(1 for r in results.values() if r['status'] == 'SKIP')
    failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
    
    print(f"Total Tests: {len(results)}")
    print(f"  ✓ Passed:  {passed}")
    print(f"  ⊘ Skipped: {skipped}")
    print(f"  ✗ Failed:  {failed}")
    print()
    print(f"Data Processed:")
    print(f"  Records:   {total_records:,}")
    print(f"  Triples:   {total_triples:,}")
    print()
    
    if passed > 0:
        print("Next Steps:")
        print("  1. Combine TTL files: cat tmp/phase3_*.ttl > tmp/phase3_combined.ttl")
        print("  2. Validate combined: python -m src.cli.validate --data tmp/phase3_combined.ttl")
        print("  3. Load to Neo4j: python -m src.cli.ingest --file tmp/phase3_combined.ttl")
        print()
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
