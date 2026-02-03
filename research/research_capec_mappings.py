#!/usr/bin/env python
"""Research alternative CAPEC→Technique mapping paths using XML source."""

import json
import xml.etree.ElementTree as ET
from collections import defaultdict

# Load CAPEC data from XML
def load_capec_xml(path: str):
    """Load CAPEC from XML file."""
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'capec': 'http://capec.mitre.org/capec-3'}
    
    capec_to_cwe = defaultdict(set)
    capec_names = {}
    
    for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
        capec_id = ap.get('ID')
        name = ap.get('Name')
        capec_full = f'CAPEC-{capec_id}' if capec_id else 'UNKNOWN'
        
        if capec_id:
            capec_names[capec_full] = name
        
        # Get related weaknesses
        for rel in ap.findall('.//capec:Related_Weaknesses/capec:Related_Weakness', ns):
            cwe_id = rel.get('CWE_ID')
            if cwe_id:
                capec_to_cwe[capec_full].add(f'CWE-{cwe_id}')
    
    return capec_to_cwe, capec_names

capec_to_cwe, capec_names = load_capec_xml('data/capec/raw/capec_latest.xml')

print(f"Total CAPEC patterns: {len(capec_to_cwe)}")
print(f"CAPEC patterns with CWE links: {sum(1 for v in capec_to_cwe.values() if v)}")
print(f"Total CAPEC→CWE links: {sum(len(v) for v in capec_to_cwe.values())}")

# Load ATT&CK data for CWE→Technique mappings
print("\n--- Checking ATT&CK for CWE→Technique mappings ---")
cwe_to_technique = defaultdict(set)

for attack_file in ['data/attack/raw/enterprise-attack.json', 'data/attack/raw/ics-attack.json', 
                     'data/attack/raw/mobile-attack.json', 'data/attack/raw/pre-attack.json']:
    try:
        with open(attack_file, 'r', encoding='utf-8', errors='ignore') as f:
            attack_data = json.load(f)
        
        for obj in attack_data.get('objects', []):
            if obj.get('type') != 'attack-pattern':
                continue
            
            attack_id = None
            for ref in obj.get('external_references', []):
                if ref.get('source_name') == 'mitre-attack':
                    attack_id = ref.get('external_id')
                    break
            
            # Look for CWE references
            if attack_id:
                for ref in obj.get('external_references', []):
                    if ref.get('source_name') == 'cwe':
                        cwe_id = ref.get('external_id')
                        if cwe_id:
                            cwe_to_technique[cwe_id].add(attack_id)
    except Exception as e:
        print(f"Warning: Could not load {attack_file}: {e}")

print(f"CWE values linked to Techniques: {len(cwe_to_technique)}")
print(f"Total CWE→Technique mappings: {sum(len(v) for v in cwe_to_technique.values())}")

# Compute transitive CAPEC→CWE→Technique paths
inferred_capec_to_technique = defaultdict(set)

for capec_id, cwe_set in capec_to_cwe.items():
    for cwe_id in cwe_set:
        if cwe_id in cwe_to_technique:
            for technique in cwe_to_technique[cwe_id]:
                inferred_capec_to_technique[capec_id].add(technique)

print(f"\n--- Transitive CAPEC→CWE→Technique paths ---")
print(f"CAPEC patterns with inferred Technique links: {len(inferred_capec_to_technique)}")
print(f"Total inferred CAPEC→Technique links: {sum(len(v) for v in inferred_capec_to_technique.values())}")

# Show examples
print("\nSample inferred mappings (first 10):")
count = 0
for capec_id, techniques in sorted(inferred_capec_to_technique.items()):
    if techniques and count < 10:
        for tech in sorted(techniques)[:1]:
            capec_name = capec_names.get(capec_id, 'Unknown')
            print(f"  {capec_id:15} ({capec_name[:45]:45}) → {tech}")
            count += 1

# Coverage analysis
print(f"\n--- Coverage Summary ---")
print(f"Direct CAPEC→Technique (from STIX):  36 links")
print(f"Inferred CAPEC→Technique (via CWE): {sum(len(v) for v in inferred_capec_to_technique.values())} links")
total_inferred = sum(len(v) for v in inferred_capec_to_technique.values())
print(f"Combined potential:                   {36 + total_inferred} links")
print(f"\nRecommendation: {'USE INFERRED PATHS' if total_inferred > 200 else 'DIRECT PATHS ONLY (limited mapping in MITRE)'}")
