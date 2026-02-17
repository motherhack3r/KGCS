import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.etl.etl_capec import _capec_xml_to_json

path = 'data/capec/raw/capec_latest.xml'
if not os.path.exists(path):
    print('CAPEC XML not found at', path)
    raise SystemExit(1)

j = _capec_xml_to_json(path)
patterns = j.get('AttackPatterns', [])

total = 0
subtech = 0
tech = 0
capec_with_mapping = 0
ids = set()
for p in patterns:
    maps = p.get('AttackMappings', [])
    if maps:
        capec_with_mapping += 1
        for m in maps:
            tid = m.get('TechniqueID')
            if tid:
                total += 1
                ids.add(tid)
                if '.' in tid:
                    subtech += 1
                else:
                    tech += 1

print('patterns:', len(patterns))
print('capec patterns with AttackMappings:', capec_with_mapping)
print('total Taxonomy_Mapping entries (ATTACK):', total)
print('unique mapped technique ids:', len(ids))
print('tech:', tech, 'subtech:', subtech)
print('example ids (first 20):', list(ids)[:20])
