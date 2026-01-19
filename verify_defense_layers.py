#!/usr/bin/env python3
"""Verify complete causal chain with all defense layers"""

from rdflib import Graph, Namespace, RDF

g = Graph()
# Load all layers
g.parse('tmp/sample_capec_impl.ttl', format='turtle')
g.parse('tmp/sample_cwe.ttl', format='turtle')
g.parse('tmp/sample_attack.ttl', format='turtle')
g.parse('tmp/sample_d3fend.ttl', format='turtle')
g.parse('tmp/sample_car.ttl', format='turtle')
g.parse('tmp/sample_shield.ttl', format='turtle')
g.parse('tmp/sample_engage.ttl', format='turtle')

SEC = Namespace('https://example.org/sec/core#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')

print('=' * 80)
print('COMPLETE CAUSAL CHAIN WITH DEFENSE LAYERS')
print('=' * 80)
print()

# Query techniques and their relationships
techniques = list(g.subjects(RDF.type, SEC.Technique))

for tech in sorted(techniques):
    tech_id = g.value(tech, SEC.attackTechniqueId)
    tech_label = g.value(tech, RDFS.label)
    
    if not tech_id:
        continue
    
    print(f'Technique: {tech_id} ({tech_label})')
    print()
    
    # Upstream: Find CAPEC patterns that implement this technique
    capec_patterns = list(g.subjects(SEC.implements, tech))
    if capec_patterns:
        print(f'  ← Implemented by CAPEC:')
        for pattern in capec_patterns:
            capec_id = g.value(pattern, SEC.capecId)
            capec_label = g.value(pattern, RDFS.label)
            weaknesses = list(g.objects(pattern, SEC.exploits))
            if weaknesses:
                cwe_uri = str(weaknesses[0]).split('/')[-1]
                cwe_label = g.value(weaknesses[0], RDFS.label)
                print(f'      CAPEC-{capec_id} ({capec_label})')
                print(f'        ← exploits CWE-{cwe_uri.split("-")[-1]} ({cwe_label})')
    print()
    
    # Downstream: Find defensive techniques, detections, and deceptions
    defenses = list(g.subjects(SEC.mitigates, tech))
    if defenses:
        print(f'  → Mitigated by D3FEND:')
        for defense in defenses:
            def_id = g.value(defense, SEC.d3fendId)
            def_label = g.value(defense, RDFS.label)
            print(f'      {def_id} ({def_label})')
    
    detections = list(g.subjects(SEC.detects, tech))
    if detections:
        print(f'  → Detected by CAR:')
        for detection in detections:
            car_id = g.value(detection, SEC.carId)
            car_label = g.value(detection, RDFS.label)
            print(f'      {car_id} ({car_label})')
    
    deceptions = list(g.subjects(SEC.counters, tech))
    if deceptions:
        print(f'  → Countered by SHIELD:')
        for deception in deceptions:
            shield_id = g.value(deception, SEC.shieldId)
            shield_label = g.value(deception, RDFS.label)
            print(f'      {shield_id} ({shield_label})')
    
    engagements = list(g.subjects(SEC.disrupts, tech))
    if engagements:
        print(f'  → Disrupted by ENGAGE:')
        for engagement in engagements:
            engage_id = g.value(engagement, SEC.engageId)
            engage_label = g.value(engagement, RDFS.label)
            print(f'      {engage_id} ({engage_label})')
    
    print()

print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'CWE Weaknesses:       {len(list(g.subjects(RDF.type, SEC.Weakness)))}')
print(f'CAPEC Patterns:       {len(list(g.subjects(RDF.type, SEC.AttackPattern)))}')
print(f'ATT&CK Techniques:    {len(techniques)}')
print(f'ATT&CK Tactics:       {len(list(g.subjects(RDF.type, SEC.Tactic)))}')
print(f'D3FEND Defenses:      {len(list(g.subjects(RDF.type, SEC.DefensiveTechnique)))}')
print(f'CAR Analytics:        {len(list(g.subjects(RDF.type, SEC.DetectionAnalytic)))}')
print(f'SHIELD Deceptions:    {len(list(g.subjects(RDF.type, SEC.DeceptionTechnique)))}')
print(f'ENGAGE Concepts:      {len(list(g.subjects(RDF.type, SEC.EngagementConcept)))}')
print()
print(f'Causal Chain Links:   {len(list(g.triples((None, SEC.caused_by, None))))} (CVE→CWE)')
print(f'Pattern Links:        {len(list(g.triples((None, SEC.exploits, None))))} (CWE→CAPEC)')
print(f'Technique Links:      {len(list(g.triples((None, SEC.implements, None))))} (CAPEC→Technique)')
print(f'Defense Links:        {len(list(g.triples((None, SEC.mitigates, None))))} (D3FEND→Technique)')
print(f'Detection Links:      {len(list(g.triples((None, SEC.detects, None))))} (CAR→Technique)')
print(f'Counter Links:        {len(list(g.triples((None, SEC.counters, None))))} (SHIELD→Technique)')
print(f'Disruption Links:     {len(list(g.triples((None, SEC.disrupts, None))))} (ENGAGE→Technique)')
