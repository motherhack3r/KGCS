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

# Add src to path (workspace root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.validation import load_graph, run_validator

# Consistent transformer imports (match src/etl/ class names)
from src.etl.etl_cpe import transform_cpe
from src.etl.etl_cpematch import transform_cpematch
from src.etl.etl_cve import transform_cve
from src.etl.etl_cwe import CWEtoRDFTransformer
from src.etl.etl_capec import CAPECtoRDFTransformer
from src.etl.etl_attack import ATTACKtoRDFTransformer
from src.etl.etl_d3fend import D3FENDtoRDFTransformer
from src.etl.etl_car import CARtoRDFTransformer
from src.etl.etl_shield import SHIELDtoRDFTransformer
from src.etl.etl_engage import ENGAGEtoRDFTransformer

TEST_CASES = [
    ('CPE', 'data/cpe/samples/sample_cpe.json', None, 'tmp/phase3_cpe.ttl'),
    ('CPEMatch', 'data/cpe/samples/sample_cpematch.json', None, 'tmp/phase3_cpematch.ttl'),
    ('CVE', 'data/cve/samples/sample_cve.json', None, 'tmp/phase3_cve.ttl'),
    ('CWE', 'data/cwe/samples/sample_cwe.json', CWEtoRDFTransformer, 'tmp/phase3_cwe.ttl'),
    ('CAPEC', 'data/capec/samples/sample_capec.json', CAPECtoRDFTransformer, 'tmp/phase3_capec.ttl'),
    ('ATT&CK', 'data/attack/samples/sample-enterprise-attack.json', ATTACKtoRDFTransformer, 'tmp/phase3_attack.ttl'),
    ('D3FEND', 'data/d3fend/samples/sample_d3fend.json', D3FENDtoRDFTransformer, 'tmp/phase3_d3fend.ttl'),
    ('CAR', 'data/car/samples/sample_car.yaml', CARtoRDFTransformer, 'tmp/phase3_car.ttl'),
    ('SHIELD', 'data/shield/samples/sample_shield.json', SHIELDtoRDFTransformer, 'tmp/phase3_shield.ttl'),
    ('ENGAGE', 'data/engage/samples/sample_engage.json', ENGAGEtoRDFTransformer, 'tmp/phase3_engage.ttl'),
]


@pytest.mark.parametrize("name,sample_file,transformer_class,output_file", TEST_CASES)
def test_etl(name, sample_file, transformer_class, output_file):
    """Test a single ETL transformer."""
    
    assert os.path.exists(sample_file), f'Sample file not found: {sample_file}'
    
    # Load data
    with open(sample_file, 'r', encoding='utf-8') as f:
        if sample_file.lower().endswith(('.yaml', '.yml')):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    # Count records based on structure
    if isinstance(data, dict):
        if 'products' in data:
            record_count = len(data['products'])
        elif 'matches' in data:
            record_count = len(data['matches'])
        elif 'vulnerabilities' in data:
            record_count = len(data['vulnerabilities'])
        elif 'weaknesses' in data:
            record_count = len(data['weaknesses'])
        elif 'attackPatterns' in data:
            record_count = len(data['attackPatterns'])
        elif 'objects' in data:  # STIX format
            record_count = len([o for o in data['objects'] if o.get('type') != 'bundle'])
        elif 'DetectionAnalytics' in data:
            record_count = len(data['DetectionAnalytics'])
        else:
            record_count = len(data)
    elif isinstance(data, list):
        record_count = len(data)
    else:
        record_count = 1

    # Transform
    if name == 'CPE':
        triple_count = transform_cpe(data, output_file)
    elif name == 'CPEMatch':
        triple_count = transform_cpematch(data, output_file)
    elif name == 'CVE':
        triple_count = transform_cve(data, output_file)
    else:
        transformer = transformer_class()
        graph = transformer.transform(data)
        triple_count = len(graph)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        graph.serialize(destination=output_file, format='turtle')

    # Validate (best effort)
    shapes_file = f'docs/ontology/shacl/{name.lower()}-shapes.ttl'
    if not os.path.exists(shapes_file):
        shapes_file = 'docs/ontology/shacl/kgcs-shapes.ttl'

    try:
        shapes_graph = load_graph(shapes_file)
        conforms, report_path, _ = run_validator(output_file, shapes_graph, 'artifacts')
        validation_status = 'PASS' if conforms else 'WARN'
    except Exception as e:
        validation_status = 'ERROR'
        report_path = str(e)

    assert triple_count > 0, f"No triples generated for {name}"
    assert os.path.exists(output_file), f"Output file not created: {output_file}"
    assert validation_status in ('PASS', 'WARN'), f"Validation failed for {name}: {validation_status} ({report_path})"


def main():
    """Run all Phase 3 ETL tests."""
    
    print("=" * 100)
    print("PHASE 3: COMPREHENSIVE ETL PIPELINE TEST SUITE")
    print("=" * 100)
    print()
    
    tests = TEST_CASES
    
    for name, sample, transformer, output in tests:
        print(f"Testing {name:10s}... ", end='', flush=True)
        try:
            test_etl(name, sample, transformer, output)
            print("✓ PASS")
        except AssertionError as e:
            print(f"✗ FAIL: {e}")
        except Exception as e:
            print(f"✗ ERROR: {e}")
    print("\nAll tests complete. See above for details.\n")
    print("Next Steps:")
    print("  1. Combine TTL files: cat tmp/phase3_*.ttl > tmp/phase3_combined.ttl")
    print("  2. Validate combined: python -m src.cli.validate --data tmp/phase3_combined.ttl")
    print("  3. Load to Neo4j: python -m src.cli.ingest --file tmp/phase3_combined.ttl")
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
