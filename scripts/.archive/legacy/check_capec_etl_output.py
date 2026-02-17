import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.etl.etl_capec import _load_capec_data, CAPECtoRDFTransformer, SEC

path = 'data/capec/raw/capec_latest.xml'
if not os.path.exists(path):
    print('CAPEC XML not found at', path); raise SystemExit(1)

capec_json = _load_capec_data(path)
transformer = CAPECtoRDFTransformer()
g = transformer.transform(capec_json)

# count CAPEC -> technique triples using canonical predicate
count = 0
sub_count = 0
tech_count = 0
examples = []
for s,p,o in g.triples((None, SEC.implements, None)):
    count += 1
    o_str = str(o)
    if '/subtechnique/' in o_str:
        sub_count += 1
    elif '/technique/' in o_str:
        tech_count += 1
    if len(examples) < 20:
        examples.append((str(s), str(p), str(o)))

print('total CAPEC->ATT&CK triples emitted by ETL:', count)
print('tech:', tech_count, 'subtech:', sub_count)
print('examples:')
for e in examples:
    print(e)
