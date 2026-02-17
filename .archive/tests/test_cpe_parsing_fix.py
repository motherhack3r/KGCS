#!/usr/bin/env python3
"""
Test to verify CPE ETL parsing fix.
Ensures platformPart, vendor, product, version are correctly extracted from CPE URI.
"""

import sys
import json
sys.path.insert(0, 'src')

from src.etl.etl_cpe import CPEtoRDFTransformer
from rdflib import Namespace

SEC = Namespace('https://example.org/sec/core#')

def test_cpe_parsing():
    """Test that CPE URI is correctly parsed into components."""
    
    # Test data with known CPE URIs
    test_cases = [
        {
            'cpeName': 'cpe:2.3:a:adobe:acrobat:2021.001.20160:*:*:*:*:*:*:*',
            'expected': {
                'platformPart': 'a',
                'vendor': 'adobe',
                'product': 'acrobat',
                'version': '2021.001.20160'
            }
        },
        {
            'cpeName': 'cpe:2.3:o:microsoft:windows_10:21h2:*:*:*:*:*:*:*',
            'expected': {
                'platformPart': 'o',
                'vendor': 'microsoft',
                'product': 'windows_10',
                'version': '21h2'
            }
        },
        {
            'cpeName': 'cpe:2.3:h:intel:core_i7:*:*:*:*:*:*:*:*',
            'expected': {
                'platformPart': 'h',
                'vendor': 'intel',
                'product': 'core_i7',
                'version': None  # Should not be set
            }
        }
    ]
    
    print("\n" + "="*80)
    print("CPE ETL PARSING VERIFICATION TEST")
    print("="*80)
    
    transformer = CPEtoRDFTransformer()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['cpeName']}")
        print("-" * 80)
        
        # Create minimal CPE product object
        cpe_json = {
            'products': [{
                'cpeNameId': f'test-{i}',
                'cpeName': test['cpeName'],
                'deprecated': False
            }]
        }
        
        # Transform to RDF
        graph = transformer.transform(cpe_json)
        
        # Extract values from graph
        from rdflib import URIRef
        from rdflib.namespace import RDF
        
        EX = Namespace('https://example.org/')
        platform_node = URIRef(f"{EX}platform/test-{i}")
        
        # Get properties
        platform_part = None
        vendor = None
        product = None
        version = None
        
        # Query graph for values
        for obj in graph.objects(platform_node, SEC.platformPart):
            platform_part = str(obj)
        for obj in graph.objects(platform_node, SEC.vendor):
            vendor = str(obj)
        for obj in graph.objects(platform_node, SEC.product):
            product = str(obj)
        for obj in graph.objects(platform_node, SEC.version):
            version = str(obj)
        
        # Check results
        results = {
            'platformPart': platform_part,
            'vendor': vendor,
            'product': product,
            'version': version
        }
        
        all_pass = True
        for key, expected in test['expected'].items():
            actual = results[key]
            status = "✓" if actual == expected else "✗"
            match = "PASS" if actual == expected else "FAIL"
            print(f"  {status} {key:15s}: {actual!r:25s} (expected: {expected!r})")
            if actual != expected:
                all_pass = False
        
        print(f"  Result: {'✓ PASS' if all_pass else '✗ FAIL'}")
    
    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_cpe_parsing()
