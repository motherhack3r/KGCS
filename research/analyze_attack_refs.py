#!/usr/bin/env python
"""Analyze external references in ATT&CK data."""

import json
from collections import defaultdict, Counter

ref_sources = Counter()
ref_source_examples = defaultdict(list)

# Check enterprise-attack.json
with open('data/attack/raw/enterprise-attack.json', 'r', encoding='utf-8', errors='ignore') as f:
    data = json.load(f)

for obj in data.get('objects', []):
    if obj.get('type') != 'attack-pattern':
        continue
    
    attack_id = None
    for ref in obj.get('external_references', []):
        if ref.get('source_name') == 'mitre-attack':
            attack_id = ref.get('external_id')
            break
    
    if attack_id:
        for ref in obj.get('external_references', []):
            source = ref.get('source_name', 'UNKNOWN')
            ref_sources[source] += 1
            
            if len(ref_source_examples[source]) < 2:
                ref_source_examples[source].append({
                    'technique': attack_id,
                    'id': ref.get('external_id'),
                    'url': ref.get('url', '')[:80]
                })

print("ATT&CK External Reference Sources (enterprise):")
for source, count in ref_sources.most_common():
    print(f"  {source:30} {count:4} references")
    for ex in ref_source_examples[source]:
        ext_id = ex['id'] or 'NONE'
        print(f"    - {ex['technique']:10} -> {ext_id:20} ({ex['url']})")

# Check if there's a CVE source
if 'cve' in [s.lower() for s in ref_sources.keys()]:
    print("\nFound CVE references in ATT&CK!")
else:
    print("\nNo CVE references found in ATT&CK techniques.")
