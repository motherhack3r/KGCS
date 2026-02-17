import json, glob, sys
out={'vulnerabilities':[]}
files=sorted(glob.glob('data/cve/raw/nvdcve-2.0-*.json'))
if not files:
    print('No nvdcve files found', file=sys.stderr)
    sys.exit(1)
count=0
for p in files:
    print('Loading',p)
    with open(p,'r',encoding='utf-8') as f:
        j=json.load(f)
        vs=j.get('vulnerabilities',[])
        out['vulnerabilities'].extend(vs)
        count+=len(vs)
with open('data/cve/raw/nvdcve-all.json','w',encoding='utf-8') as f:
    json.dump(out,f)
print('Wrote nvdcve-all.json with',count,'vulnerabilities')
