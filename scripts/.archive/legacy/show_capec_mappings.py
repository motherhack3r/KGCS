import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.etl.etl_capec import _load_capec_data
capec_json = _load_capec_data('data/capec/raw/capec_latest.xml')
patterns = capec_json.get('AttackPatterns', [])
count = 0
for p in patterns:
    maps = p.get('AttackMappings', [])
    if maps:
        print(p.get('ID'), maps)
        count += 1
        if count >= 10:
            break
print('shown', count)
