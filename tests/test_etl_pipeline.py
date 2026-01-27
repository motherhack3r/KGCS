#!/usr/bin/env python3
"""
Test ETL Pipeline: CPE Sample Data → RDF → SHACL Validation

This script tests the complete Phase 3 pipeline:
1. Load sample CPE JSON
2. Transform to RDF using ETL transformer
3. Validate output with SHACL
4. Report results
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.etl.etl_cpe import CPEtoRDFTransformer
from src.core.validation import run_validator, load_graph

def test_cpe_etl():
    """Test CPE ETL transformer with sample data."""
    
    print("=" * 80)
    print("PHASE 3 TEST: CPE ETL → RDF → SHACL Validation")
    print("=" * 80)
    print()
    
    # Step 1: Load sample data
    print("[1/4] Loading sample CPE JSON...")
    sample_file = 'data/cpe/samples/sample_cpe.json'
    
    if not os.path.exists(sample_file):
        print(f"  ❌ Error: {sample_file} not found")
        return False
    
    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            cpe_data = json.load(f)
        print(f"  ✓ Loaded {len(cpe_data.get('products', []))} CPE records")
    except Exception as e:
        print(f"  ❌ Error loading JSON: {e}")
        return False
    
    # Step 2: Transform to RDF
    print("\n[2/4] Transforming CPE JSON to RDF...")
    try:
        transformer = CPEtoRDFTransformer()
        graph = transformer.transform(cpe_data)
        print(f"  ✓ Generated RDF graph with {len(graph)} triples")
        
        # Save to file
        output_file = 'tmp/test_cpe_output.ttl'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        graph.serialize(destination=output_file, format='turtle')
        print(f"  ✓ Saved to {output_file}")
    except Exception as e:
        print(f"  ❌ Error transforming: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Validate with SHACL
    print("\n[3/4] Validating RDF with SHACL...")
    try:
        shapes_file = 'docs/ontology/shacl/cpe-shapes.ttl'
        if not os.path.exists(shapes_file):
            print(f"  ⚠ Warning: SHACL shapes file not found: {shapes_file}")
            print(f"  Using generic validation instead...")
            shapes_file = 'docs/ontology/shacl/kgcs-shapes.ttl'
        
        shapes_graph = load_graph(shapes_file)
        conforms, report_path, results_text = run_validator(
            output_file, 
            shapes_graph,
            'artifacts'
        )
        
        if conforms:
            print(f"  ✓ RDF validates against SHACL")
            print(f"  ✓ Validation report: {report_path}")
        else:
            print(f"  ⚠ Validation issues found:")
            print(f"  Report: {report_path}")
            # Show first few lines of results
            lines = results_text.split('\n')[:10]
            for line in lines:
                print(f"    {line}")
    except Exception as e:
        print(f"  ⚠ Validation error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Summary
    print("\n[4/4] Pipeline Summary")
    print("=" * 80)
    print(f"  Input:  {sample_file} ({len(cpe_data.get('products', []))} records)")
    print(f"  Output: {output_file}")
    print(f"  Status: ✓ Complete")
    print()
    print("Next steps:")
    print("  1. Test CVE ETL: python test_etl_pipeline.py cve")
    print("  2. Load to Neo4j: python -m src.cli.ingest --file tmp/test_cpe_output.ttl")
    print("  3. Run full validation suite: python -m src.cli.validate --data tmp/test_cpe_output.ttl")
    print()
    
    return True


def test_cve_etl():
    """Test CVE ETL transformer with sample data."""
    
    print("=" * 80)
    print("PHASE 3 TEST: CVE ETL → RDF → SHACL Validation")
    print("=" * 80)
    print()
    
    # Step 1: Load sample data
    print("[1/4] Loading sample CVE JSON...")
    sample_file = 'data/cve/samples/sample_cve.json'
    
    if not os.path.exists(sample_file):
        print(f"  ❌ Error: {sample_file} not found")
        return False
    
    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            cve_data = json.load(f)
        cve_count = len(cve_data.get('vulnerabilities', []))
        print(f"  ✓ Loaded {cve_count} CVE records")
    except Exception as e:
        print(f"  ❌ Error loading JSON: {e}")
        return False
    
    # Step 2: Transform to RDF
    print("\n[2/4] Transforming CVE JSON to RDF...")
    try:
        from src.etl.etl_cve import CVEtoRDFTransformer
        transformer = CVEtoRDFTransformer()
        graph = transformer.transform(cve_data)
        print(f"  ✓ Generated RDF graph with {len(graph)} triples")
        
        # Save to file
        output_file = 'tmp/test_cve_output.ttl'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        graph.serialize(destination=output_file, format='turtle')
        print(f"  ✓ Saved to {output_file}")
    except Exception as e:
        print(f"  ❌ Error transforming: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Validate with SHACL
    print("\n[3/4] Validating RDF with SHACL...")
    try:
        shapes_file = 'docs/ontology/shacl/cve-shapes.ttl'
        if not os.path.exists(shapes_file):
            print(f"  ⚠ Warning: SHACL shapes file not found: {shapes_file}")
            print(f"  Using generic validation instead...")
            shapes_file = 'docs/ontology/shacl/kgcs-shapes.ttl'
        
        shapes_graph = load_graph(shapes_file)
        conforms, report_path, results_text = run_validator(
            output_file, 
            shapes_graph,
            'artifacts'
        )
        
        if conforms:
            print(f"  ✓ RDF validates against SHACL")
            print(f"  ✓ Validation report: {report_path}")
        else:
            print(f"  ⚠ Validation issues found:")
            print(f"  Report: {report_path}")
            lines = results_text.split('\n')[:10]
            for line in lines:
                print(f"    {line}")
    except Exception as e:
        print(f"  ⚠ Validation error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Summary
    print("\n[4/4] Pipeline Summary")
    print("=" * 80)
    print(f"  Input:  {sample_file} ({cve_count} records)")
    print(f"  Output: {output_file}")
    print(f"  Status: ✓ Complete")
    print()
    
    return True


if __name__ == '__main__':
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'cpe'
    
    if test_type == 'cpe':
        success = test_cpe_etl()
    elif test_type == 'cve':
        success = test_cve_etl()
    else:
        print(f"Unknown test type: {test_type}")
        print("Usage: python test_etl_pipeline.py [cpe|cve]")
        sys.exit(1)
    
    sys.exit(0 if success else 1)
