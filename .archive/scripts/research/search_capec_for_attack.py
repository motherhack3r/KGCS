#!/usr/bin/env python
"""Search CAPEC XML for ATT&CK technique references using regex."""

import re
import xml.etree.ElementTree as ET
from collections import defaultdict

# Load CAPEC XML
tree = ET.parse('data/capec/raw/capec_latest.xml')
root = tree.getroot()
ns = {'capec': 'http://capec.mitre.org/capec-3'}

print("=" * 80)
print("CAPEC→ATT&CK REFERENCES SEARCH")
print("=" * 80)

# Patterns to search for
attack_technique_pattern = re.compile(r'\bT\d{4}(?:\.\d{3})?\b')
mitre_attack_pattern = re.compile(r'(?:mitre\s+)?attack', re.IGNORECASE)
technique_pattern = re.compile(r'(?:technique|tactic|subtechnique)', re.IGNORECASE)

found_references = defaultdict(set)
capec_with_tech_refs = []

for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
    capec_id = ap.get('ID')
    name = ap.get('Name')
    capec_full = f'CAPEC-{capec_id}'
    
    # Search all text content
    all_text = ET.tostring(ap, encoding='unicode', method='text')
    
    # Find technique IDs
    tech_matches = attack_technique_pattern.findall(all_text)
    if tech_matches:
        capec_with_tech_refs.append((capec_full, name, tech_matches))
        for tech_id in tech_matches:
            found_references[capec_full].add(tech_id)
    
    # Also search in all element text
    for elem in ap.iter():
        if elem.text:
            tech_matches = attack_technique_pattern.findall(elem.text)
            if tech_matches:
                for tech_id in tech_matches:
                    found_references[capec_full].add(tech_id)

# Also search element tags and attributes for CAPEC-specific external reference patterns
print("\nSearching for ExternalReferences elements...")
ext_ref_count = 0
for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
    capec_id = ap.get('ID')
    capec_full = f'CAPEC-{capec_id}'
    name = ap.get('Name')
    
    # Look for External References section
    for ext_ref in ap.findall('.//capec:External_References/capec:External_Reference', ns):
        title = ext_ref.get('Title', '')
        reference_type = ext_ref.get('Type', '')
        url = ext_ref.get('URL', '')
        
        # Check if references attack/techniques
        full_text = f"{title} {reference_type} {url}".lower()
        if 'attack' in full_text or 'technique' in full_text or 't100' in full_text:
            ext_ref_count += 1
            # Try to extract technique IDs from the text
            tech_ids = attack_technique_pattern.findall(url + title)
            if tech_ids:
                if capec_full not in found_references:
                    capec_with_tech_refs.append((capec_full, name, tech_ids))
                for tech_id in tech_ids:
                    found_references[capec_full].add(tech_id)

print(f"\nFound {len(found_references)} CAPEC with potential ATT&CK technique references")
print(f"Found {ext_ref_count} external references mentioning 'attack' or 'technique'")

if found_references:
    print("\n" + "=" * 80)
    print("CAPEC→ATT&CK MAPPINGS FOUND VIA REGEX")
    print("=" * 80)
    
    for i, (capec_id, techniques) in enumerate(sorted(found_references.items())[:20]):
        print(f"\n{capec_id}:")
        for tech in sorted(techniques):
            print(f"  → {tech}")
        
        if i == 0:
            # Show first CAPEC details
            ap = root.find(f".//capec:Attack_Pattern[@ID='{capec_id.replace('CAPEC-', '')}']", ns)
            if ap is not None:
                name = ap.get('Name')
                desc = ap.find('.//capec:Description', ns)
                if desc is not None:
                    desc_text = ''.join(desc.itertext())[:200]
                    print(f"  Name: {name}")
                    print(f"  Description: {desc_text}...")
    
    print(f"\n... and {len(found_references) - 20} more" if len(found_references) > 20 else "")
    
    print(f"\nTotal inferred CAPEC→Technique links via regex: {sum(len(v) for v in found_references.values())}")
else:
    print("\n⚠️ No ATT&CK technique references found in CAPEC data using regex")
    print("\nSearching for any mention of 'ATT&CK' or 'mitre' in CAPEC...")
    
    mitre_mentions = 0
    for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
        all_text = ET.tostring(ap, encoding='unicode', method='text').lower()
        if 'attack' in all_text and ('mitre' in all_text or 'attck' in all_text):
            mitre_mentions += 1
    
    print(f"Found {mitre_mentions} CAPEC patterns mentioning MITRE/ATT&CK")
