#!/usr/bin/env python
"""Extract exact text mentioning MITRE/ATT&CK from CAPEC XML."""

import xml.etree.ElementTree as ET
from collections import defaultdict

tree = ET.parse('data/capec/raw/capec_latest.xml')
root = tree.getroot()
ns = {'capec': 'http://capec.mitre.org/capec-3'}

print("Extracting MITRE/ATT&CK mentions from CAPEC...")
print("=" * 80)

mitre_contexts = defaultdict(list)
count = 0

for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
    capec_id = ap.get('ID')
    capec_full = f'CAPEC-{capec_id}'
    name = ap.get('Name')
    
    # Check all text in this CAPEC element
    full_text = ET.tostring(ap, encoding='unicode', method='text')
    text_lower = full_text.lower()
    
    if ('attack' in text_lower and 'mitre' in text_lower) or 'attck' in text_lower:
        # Extract context around the mention
        lines = full_text.split('\n')
        for line in lines:
            if ('mitre' in line.lower() or 'attck' in line.lower() or 
                ('attack' in line.lower() and 'mitre' in text_lower)):
                line_stripped = line.strip()
                if line_stripped and len(line_stripped) > 20:  # Skip very short lines
                    mitre_contexts[capec_full].append(line_stripped[:200])
                    count += 1

print(f"\nFound {count} context lines mentioning MITRE/ATT&CK")
print(f"Across {len(mitre_contexts)} CAPEC patterns\n")

# Show first 10 examples
print("Sample contexts (first 10):")
print("-" * 80)

shown = 0
for capec_id in sorted(mitre_contexts.keys())[:10]:
    print(f"\n{capec_id}:")
    for context in mitre_contexts[capec_id][:2]:  # Show up to 2 per CAPEC
        print(f"  {context[:100]}...")
        shown += 1

# Search for specific patterns that might indicate technique mapping
print("\n" + "=" * 80)
print("Searching for external reference patterns...")
print("-" * 80)

ext_ref_patterns = defaultdict(int)

for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
    for ext_ref in ap.findall('.//capec:External_References/capec:External_Reference', ns):
        ref_type = ext_ref.get('Type', 'UNKNOWN')
        url = ext_ref.get('URL', '')
        title = ext_ref.get('Title', '')
        
        if 'mitre' in url.lower() or 'mitre' in title.lower():
            # Extract domain/path from URL
            if url:
                domain_match = url.split('/')[2] if '//' in url else 'unknown'
                ext_ref_patterns[f"{ref_type} -> {domain_match}"] += 1

print("\nExternalReference patterns mentioning MITRE:")
for pattern, count in sorted(ext_ref_patterns.items(), key=lambda x: -x[1])[:20]:
    print(f"  {pattern:50} : {count:4} references")
