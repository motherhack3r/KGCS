import json
import glob
import os

reports = sorted(glob.glob('artifacts/shacl-report-*.json'))
out = []
for p in reports:
    try:
        with open(p, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as e:
        data = {'_error': str(e)}
    out.append({'file': os.path.basename(p), 'data': data})

os.makedirs('artifacts', exist_ok=True)
outpath = 'artifacts/shacl-report-consolidated.json'
with open(outpath, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, indent=2)

print(f'Wrote {outpath} with {len(out)} entries')
