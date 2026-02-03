#!/usr/bin/env python
"""Check CAPEC→Technique mappings across all ATT&CK datasets."""

import json
from pathlib import Path

total_capec_refs = 0
results = {}

for attack_file in ['enterprise-attack.json', 'ics-attack.json', 'mobile-attack.json', 'pre-attack.json']:
    try:
        with open(f'data/attack/raw/{attack_file}', 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        count_with_capec = 0
        total_patterns = 0
        
        for obj in data.get('objects', []):
            if obj.get('type') == 'attack-pattern':
                total_patterns += 1
                for ref in obj.get('external_references', []):
                    if ref.get('source_name') == 'capec':
                        count_with_capec += 1
                        break
        
        results[attack_file] = {'total': total_patterns, 'with_capec': count_with_capec}
        total_capec_refs += count_with_capec
    except Exception as e:
        results[attack_file] = {'error': str(e)}

for file, stats in results.items():
    if 'error' not in stats:
        pct = (stats['with_capec'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f'{file:30} {stats["total"]:4} techniques, {stats["with_capec"]:4} with CAPEC ({pct:5.1f}%)')
    else:
        print(f'{file:30} Error: {stats["error"]}')

print(f'\nTotal CAPEC->Technique mappings across all datasets: {total_capec_refs}')
