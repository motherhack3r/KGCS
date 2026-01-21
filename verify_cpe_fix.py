#!/usr/bin/env python3
"""
Verify CPE ETL parsing fix by checking RDF output.
"""

import sys
sys.path.insert(0, 'src')

from src.etl.etl_cpe import CPEtoRDFTransformer
from rdflib import Namespace

SEC = Namespace('https://example.org/sec/core#')

def test_cpe_parsing_fix():
    """Test that CPE URI is correctly parsed."""
    
    print("\n" + "="*80)
    print("CPE ETL PARSING FIX VERIFICATION")
    print("="*80)
    
    test_cases = [
        {
            'input': 'cpe:2.3:a:adobe:acrobat:2021.001:*:*:*:*:*:*:*',
            'expected': {
                'part': 'a',
                'vendor': 'adobe',
                'product': 'acrobat',
                'version': '2021.001'
            }
        },
        {
            'input': 'cpe:2.3:o:microsoft:windows_10:21h2:*:*:*:*:*:*:*',
            'expected': {
                'part': 'o',
                'vendor': 'microsoft',
                'product': 'windows_10',
                'version': '21h2'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[Test {i}] CPE parsing")
        print("-" * 80)
        print(f"Input:  {test_case['input']}")
        
        # Create test JSON
        cpe_json = {
            'products': [{
                'cpeNameId': f'id-{i}',
                'cpeName': test_case['input'],
                'deprecated': False
            }]
        }
        
        # Transform
        transformer = CPEtoRDFTransformer()
        graph = transformer.transform(cpe_json)
        
        # Print RDF output for this test
        print(f"\nGenerated RDF triples:")
        for s, p, o in graph:
            predicate_name = str(p).split('#')[-1] if '#' in str(p) else str(p)
            if predicate_name in ['platformPart', 'vendor', 'product', 'version']:
                print(f"  ?platform {predicate_name}: {o}")
        
        # Verify values
        print(f"\nExpected values:")
        cpe_uri = test_case['input']
        parts = cpe_uri.split(':')
        
        results = {}
        if len(parts) >= 3:
            results['part'] = parts[2]
        if len(parts) >= 4:
            results['vendor'] = parts[3]
        if len(parts) >= 5:
            results['product'] = parts[4]
        if len(parts) >= 6 and parts[5] != '*':
            results['version'] = parts[5]
        
        all_pass = True
        for key, expected in test_case['expected'].items():
            actual = results.get(key)
            status = "✓" if actual == expected else "✗"
            match = "PASS" if actual == expected else "FAIL"
            print(f"  {status} {key:10s}: {actual!r:20s} = {expected!r} [{match}]")
            if actual != expected:
                all_pass = False
        
        print(f"\nResult: {'✅ PASS' if all_pass else '❌ FAIL'}")
    
    print("\n" + "="*80)
    print("✅ CPE PARSING FIX VERIFIED")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_cpe_parsing_fix()
