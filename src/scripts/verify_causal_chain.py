#!/usr/bin/env python3
"""Verify complete causal chain: CWE → CAPEC → Technique → Tactic"""

from rdflib import Graph, Namespace, RDF

g = Graph()
g.parse('tmp/sample_capec_impl.ttl', format='turtle')
g.parse('tmp/sample_cwe.ttl', format='turtle')
g.parse('tmp/sample_attack.ttl', format='turtle')

SEC = Namespace('https://example.org/sec/core#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')

patterns = list(g.subjects(RDF.type, SEC.AttackPattern))

print('=== CAUSAL CHAIN: CWE → CAPEC → Technique → Tactic ===')
print()

for pattern in sorted(patterns):
    capec_id = g.value(pattern, SEC.capecId)
    label = g.value(pattern, RDFS.label)
    weaknesses = list(g.objects(pattern, SEC.exploits))
    techniques = list(g.objects(pattern, SEC.implements))
    
    print(f'CAPEC-{capec_id}: {label}')
    if weaknesses:
        cwe_uri = str(weaknesses[0]).split('/')[-1]
        cwe_label = g.value(weaknesses[0], RDFS.label)
        print(f'  ├─ exploits: {cwe_uri} ({cwe_label})')
    if techniques:
        tech_uri = str(techniques[0]).split('/')[-1]
        tech_label = g.value(techniques[0], RDFS.label)
        tactic = g.value(techniques[0], SEC.belongs_to)
        if tactic:
            tactic_label = g.value(tactic, RDFS.label)
            print(f'  └─ implements: {tech_uri} ({tech_label}) → {tactic_label}')
        else:
            print(f'  └─ implements: {tech_uri} ({tech_label})')
    print()

print('\n=== SUMMARY ===')
print(f'CWE patterns: {len(list(g.subjects(RDF.type, SEC.Weakness)))}')
print(f'CAPEC patterns: {len(patterns)}')
print(f'ATT&CK techniques: {len(list(g.subjects(RDF.type, SEC.Technique)))}')
print(f'ATT&CK tactics: {len(list(g.subjects(RDF.type, SEC.Tactic)))}')
print(f'\nCAPEC→Technique implements edges: {len([p for p in patterns if list(g.objects(p, SEC.implements))])}')


if __name__ == '__main__':
    pass
