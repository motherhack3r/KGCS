#!/usr/bin/env python
"""Count CAPEC references in generated TTL."""

import re

with open('tmp/pipeline-stage4-attack-capec-test.ttl', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

# Count using simpler patterns
capec_uris = set(re.findall(r'https://example.org/capec/(\d+)', content))
print(f'Unique CAPEC patterns found: {len(capec_uris)}')

# Count derived_from relationships
derived_count = len(re.findall(r'derived_from.*capec', content))
print(f'Technique→CAPEC derived_from relationships: {derived_count}')

# Count total CAPEC references
total_capec_refs = len(re.findall(r'capec/\d+', content))
print(f'Total CAPEC references in TTL: {total_capec_refs}')

# Show the CAPEC IDs
capec_ids = sorted([int(x) for x in capec_uris])
print(f'\nCAPEC IDs ({len(capec_ids)} total):\n{capec_ids}')

# Count techniques
technique_uris = set(re.findall(r'https://example.org/technique/(T\d+)', content))
print(f'\nTechniques with CAPEC mappings: {len(technique_uris)}')
technique_refs = len(re.findall(r'technique/T\d+', content))
print(f'Total technique references: {technique_refs}')
