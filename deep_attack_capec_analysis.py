#!/usr/bin/env python
"""Deep analysis of ATT&CK STIX data for CAPEC references."""

import json
import os
from pathlib import Path
from collections import defaultdict

attack_files = [
    'data/attack/raw/enterprise-attack.json',
    'data/attack/raw/ics-attack.json',
    'data/attack/raw/mobile-attack.json',
    'data/attack/raw/pre-attack.json',
]

# Collect all CAPEC references
capec_to_technique = defaultdict(set)
technique_info = {}
all_capec_ids = set()
capec_by_dataset = defaultdict(list)

print("=" * 80)
print("COMPREHENSIVE ATT&CK → CAPEC MAPPING ANALYSIS")
print("=" * 80)

for attack_file in attack_files:
    if not os.path.exists(attack_file):
        print(f"\n⚠️  File not found: {attack_file}")
        continue
    
    dataset_name = Path(attack_file).stem.replace('-attack', '').upper()
    print(f"\nProcessing {dataset_name}...")
    
    with open(attack_file, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    
    objects = data.get('objects', [])
    attack_patterns = [o for o in objects if o.get('type') == 'attack-pattern']
    print(f"  Total attack patterns: {len(attack_patterns)}")
    
    capec_count = 0
    
    for obj in attack_patterns:
        attack_id = None
        capec_ids = []
        
        # Get the ATT&CK technique ID
        for ref in obj.get('external_references', []):
            if ref.get('source_name') == 'mitre-attack':
                attack_id = ref.get('external_id')
                break
        
        if not attack_id:
            continue
        
        # Find all CAPEC references
        for ref in obj.get('external_references', []):
            source = ref.get('source_name', '')
            if source.lower() == 'capec':
                capec_id = ref.get('external_id')
                if capec_id:
                    capec_ids.append(capec_id)
                    all_capec_ids.add(capec_id)
        
        # Store mapping
        if capec_ids:
            capec_count += len(capec_ids)
            for capec_id in capec_ids:
                capec_to_technique[capec_id].add(attack_id)
            capec_by_dataset[dataset_name].extend(capec_ids)
            
            # Store technique info for display
            technique_name = obj.get('name', 'UNKNOWN')
            technique_info[attack_id] = {
                'name': technique_name,
                'capec_ids': capec_ids,
                'dataset': dataset_name
            }
    
    print(f"  CAPEC references found: {capec_count}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nTotal unique CAPEC patterns: {len(all_capec_ids)}")
print(f"Total unique Techniques: {len(technique_info)}")
print(f"Total CAPEC→Technique links: {sum(len(v) for v in capec_to_technique.values())}")

# Breakdown by dataset
print("\nBreakdown by dataset:")
for dataset, capec_ids in sorted(capec_by_dataset.items()):
    unique_capecs = len(set(capec_ids))
    print(f"  {dataset:20} {unique_capecs:4} unique CAPEC, {len(capec_ids):4} total links")

# Show all mappings (not just first 10)
print("\n" + "=" * 80)
print("ALL CAPEC→TECHNIQUE MAPPINGS")
print("=" * 80)

for capec_id in sorted(all_capec_ids):
    techniques = sorted(capec_to_technique[capec_id])
    print(f"\nCAPEC-{capec_id}:")
    for tech in techniques:
        info = technique_info.get(tech, {})
        name = info.get('name', 'UNKNOWN')
        dataset = info.get('dataset', 'UNKNOWN')
        print(f"  → {tech:15} ({dataset:15}) {name[:60]}")

# Check for sub-techniques (T1234.001 format)
print("\n" + "=" * 80)
print("SUB-TECHNIQUE ANALYSIS")
print("=" * 80)

parent_techniques = set()
sub_techniques = set()

for tech in technique_info.keys():
    if '.' in tech:
        sub_techniques.add(tech)
        parent = tech.split('.')[0]
        parent_techniques.add(parent)

print(f"Total parent techniques: {len(parent_techniques)}")
print(f"Total sub-techniques with CAPEC: {len(sub_techniques)}")

if sub_techniques:
    print(f"\nSub-techniques with CAPEC mappings:")
    for tech in sorted(sub_techniques):
        info = technique_info[tech]
        print(f"  {tech}: {info['capec_ids']}")

# Find CAPEC IDs that don't map to any technique
print("\n" + "=" * 80)
print("CAPEC COVERAGE ANALYSIS")
print("=" * 80)

print(f"\nCAPEC patterns with Technique mappings: {len(all_capec_ids)}")
print(f"Total unique Techniques linked: {len(set(tech for techs in capec_to_technique.values() for tech in techs))}")

# Check multiple techniques per CAPEC
multi_tech_capec = {k: v for k, v in capec_to_technique.items() if len(v) > 1}
if multi_tech_capec:
    print(f"\nCAPEC patterns mapping to MULTIPLE techniques: {len(multi_tech_capec)}")
    for capec_id in sorted(multi_tech_capec.keys())[:5]:
        techniques = sorted(multi_tech_capec[capec_id])
        print(f"  CAPEC-{capec_id}: {len(techniques)} techniques → {', '.join(techniques[:3])}...")
