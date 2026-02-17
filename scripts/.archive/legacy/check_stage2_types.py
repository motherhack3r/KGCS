#!/usr/bin/env python3
"""Check RDF types in stage2 CPEMatch data."""

import sys
sys.path.insert(0, '.')

from rdflib import Graph, RDF

print("Checking RDF types in stage 2 (CPEMatch)...")

g = Graph()
g.parse('tmp/pipeline-stage2-cpematch.ttl', format='turtle')

# Get all unique rdf:type values
types = {}
for subject, predicate, obj in g:
    if predicate == RDF.type:
        type_name = str(obj).split('#')[-1]
        types[type_name] = types.get(type_name, 0) + 1

print("\nRDF types found in stage2:")
for type_name, count in sorted(types.items()):
    print(f"  {type_name}: {count}")

# Check for PlatformConfiguration vs Platform
config_count = sum(c for t, c in types.items() if 'Configuration' in t)
platform_count = types.get('Platform', 0)

print(f"\n✓ PlatformConfiguration nodes: {config_count}")
print(f"✓ Platform nodes: {platform_count}")

if config_count == 0:
    print("\n⚠️  WARNING: No PlatformConfiguration nodes found!")
    print("   The CPEMatch stage2 data is creating Platform nodes instead")
    print("   This is likely an issue in src/etl/etl_cpematch.py")
