#!/usr/bin/env python
"""Extract CAPEC→ATT&CK mappings from CAPEC XML Taxonomy_Mappings sections."""

import xml.etree.ElementTree as ET
from collections import defaultdict

capec_file = 'data/capec/raw/capec_latest.xml'

print("Parsing CAPEC XML...")
tree = ET.parse(capec_file)
root = tree.getroot()

# Extract namespace
ns = {'capec': 'http://capec.mitre.org/capec-3'}

# Collect mappings
capec_to_attack = defaultdict(set)
attack_mappings_found = 0

# Iterate over all Attack_Pattern elements
for pattern in root.findall('capec:Attack_Patterns/capec:Attack_Pattern', ns):
    capec_id = pattern.get('ID')
    if not capec_id:
        continue
    
    # Find Taxonomy_Mappings section
    tax_mappings = pattern.find('capec:Taxonomy_Mappings', ns)
    if tax_mappings is None:
        continue
    
    # Look for ATTACK taxonomy mappings
    for mapping in tax_mappings.findall('capec:Taxonomy_Mapping', ns):
        tax_name = mapping.get('Taxonomy_Name')
        
        if tax_name and tax_name.upper() == 'ATTACK':
            # Get the Entry_ID (ATT&CK technique ID)
            entry_id_elem = mapping.find('capec:Entry_ID', ns)
            if entry_id_elem is not None and entry_id_elem.text:
                attack_id = entry_id_elem.text.strip()
                capec_to_attack[capec_id].add(attack_id)
                attack_mappings_found += 1

print(f"\n{'='*80}")
print("CAPEC→ATT&CK MAPPINGS FROM XML TAXONOMY_MAPPINGS")
print(f"{'='*80}")
print(f"\nTotal mappings found: {attack_mappings_found}")
print(f"Unique CAPEC patterns with ATT&CK mappings: {len(capec_to_attack)}")

# Show all mappings
capec_ids_sorted = sorted([int(k) for k in capec_to_attack.keys()])
print(f"\nCAP EC IDs with ATTACK mappings ({len(capec_ids_sorted)}):")
print(capec_ids_sorted)

print(f"\n{'='*80}")
print("DETAILED MAPPINGS")
print(f"{'='*80}\n")

for capec_id in sorted(capec_to_attack.keys(), key=lambda x: int(x)):
    attack_ids = sorted(capec_to_attack[capec_id])
    print(f"CAPEC-{capec_id}:")
    for attack_id in attack_ids:
        print(f"  → {attack_id}")

# Compare with ATT&CK extraction
print(f"\n{'='*80}")
print("COMPARISON WITH ATT&CK STIX EXTRACTION")
print(f"{'='*80}")

# From previous analysis
attck_stix_capec_ids = {13, 17, 132, 159, 163, 187, 270, 471, 478, 479, 532, 550, 551, 552, 555, 556, 558, 561, 563, 564, 569, 570, 571, 572, 578, 579, 639, 641, 644, 645, 649, 650}

capec_xml_ids = set(int(k) for k in capec_to_attack.keys())

only_in_xml = capec_xml_ids - attck_stix_capec_ids
only_in_stix = attck_stix_capec_ids - capec_xml_ids

print(f"\nCAPEC patterns in CAPEC XML mappings: {len(capec_xml_ids)}")
print(f"CAPEC patterns in ATT&CK STIX data: {len(attck_stix_capec_ids)}")
print(f"CAPEC patterns in both: {len(capec_xml_ids & attck_stix_capec_ids)}")
print(f"\nOnly in CAPEC XML: {len(only_in_xml)}")
if only_in_xml:
    print(f"  {sorted(only_in_xml)}")

print(f"\nOnly in ATT&CK STIX: {len(only_in_stix)}")
if only_in_stix:
    print(f"  {sorted(only_in_stix)}")
