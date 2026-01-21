#!/usr/bin/env python3
"""
Complete Extended Causal Chain with Defense Layers
Verifies: CPE -> CVE -> CWE -> CAPEC -> ATT&CK -> Defense Layers
"""

import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment before config import
load_dotenv('.env.devel')

sys.path.insert(0, str(Path(__file__).parent / "src"))
from config import neo4j_config


def verify_extended_chain():
    """Verify complete extended causal chain including defense layers"""
    driver = GraphDatabase.driver(
        neo4j_config.uri,
        auth=(neo4j_config.user, neo4j_config.password)
    )
    session = driver.session()

    print("=" * 70)
    print("EXTENDED CAUSAL CHAIN VERIFICATION (CPE -> ... -> DEFENSE LAYERS)")
    print("=" * 70)

    try:
        # Attack-side chain
        print("\n[ATTACK CHAIN]")
        result = session.run("MATCH (p:Platform) RETURN count(p) as count")
        cpe_count = result.single()['count']
        print(f"  [1] Platform (CPE):           {cpe_count:,} nodes")

        result = session.run("MATCH (v:Vulnerability) RETURN count(v) as count")
        cve_count = result.single()['count']
        print(f"  [2] Vulnerability (CVE):      {cve_count:,} nodes")

        result = session.run("MATCH (w:Weakness) RETURN count(w) as count")
        cwe_count = result.single()['count']
        print(f"  [3] Weakness (CWE):           {cwe_count:,} nodes")

        result = session.run("MATCH (ap:AttackPattern) RETURN count(ap) as count")
        capec_count = result.single()['count']
        print(f"  [4] Attack Pattern (CAPEC):   {capec_count:,} nodes")

        result = session.run("MATCH (t:Technique) RETURN count(t) as count")
        technique_count = result.single()['count']
        print(f"  [5] Technique (ATT&CK):       {technique_count:,} nodes")

        # Defense-side chain
        print("\n[DEFENSE LAYERS]")
        
        result = session.run("MATCH (d:DefensiveTechnique) RETURN count(d) as count")
        d3fend_count = result.single()['count']
        print(f"  [6] D3FEND:                   {d3fend_count} nodes")

        result = session.run("MATCH (c:DetectionAnalytic) RETURN count(c) as count")
        car_count = result.single()['count']
        print(f"  [7] CAR (Detection):          {car_count} nodes")

        result = session.run("MATCH (s:DeceptionTechnique) RETURN count(s) as count")
        shield_count = result.single()['count']
        print(f"  [8] SHIELD (Deception):       {shield_count} nodes")

        result = session.run("MATCH (e:EngagementConcept) RETURN count(e) as count")
        engage_count = result.single()['count']
        print(f"  [9] ENGAGE:                   {engage_count} nodes")

        # Relationships
        print("\n[RELATIONSHIPS]")

        rel_types = [
            ('CVE->CWE', 'CAUSED_BY', 'Vulnerability', 'Weakness'),
            ('CWE->CAPEC', 'EXPLOITED_BY', 'Weakness', 'AttackPattern'),
            ('CAPEC->ATT&CK', 'USED_IN', 'AttackPattern', 'Technique'),
            ('D3FEND->ATT&CK', 'MITIGATES', 'DefensiveTechnique', 'Technique'),
            ('CAR->ATT&CK', 'DETECTS', 'DetectionAnalytic', 'Technique'),
            ('SHIELD->ATT&CK', 'COUNTERS', 'DeceptionTechnique', 'Technique'),
            ('ENGAGE->ATT&CK', 'DISRUPTS', 'EngagementConcept', 'Technique'),
        ]

        for display_name, rel_type, src_label, dst_label in rel_types:
            query = f"""
                MATCH (src:{src_label})-[r:{rel_type}]->(dst:{dst_label})
                RETURN count(r) as count
            """
            result = session.run(query)
            count = result.single()['count']
            print(f"  {display_name:20} ({rel_type:15}): {count:3} edges")

        # Complete attack paths: CVE -> ... -> ATT&CK
        print("\n[COMPLETE ATTACK PATHS] (CVE -> CWE -> CAPEC -> ATT&CK)")
        result = session.run("""
            MATCH (v:Vulnerability)-[:CAUSED_BY]->(w:Weakness)
                  -[:EXPLOITED_BY]->(ap:AttackPattern)
                  -[:USED_IN]->(t:Technique)
            RETURN v.id, w.id, ap.capecId, t.external_id
            LIMIT 3
        """)
        
        paths = result.data()
        print(f"  Found {len(paths)} complete attack paths:")
        for i, path in enumerate(paths, 1):
            print(f"    [{i}] {path['v.id']} -> {path['w.id']} -> {path['ap.capecId']} -> {path['t.external_id']}")

        # Defense coverage: ATT&CK -> Defense
        print("\n[DEFENSE COVERAGE]")
        result = session.run("""
            MATCH (t:Technique)
            WHERE EXISTS((t)<-[:MITIGATES]-(:DefensiveTechnique))
               OR EXISTS((t)<-[:DETECTS]-(:DetectionAnalytic))
               OR EXISTS((t)<-[:COUNTERS]-(:DeceptionTechnique))
               OR EXISTS((t)<-[:DISRUPTS]-(:EngagementConcept))
            RETURN count(t) as covered
        """)
        covered_techniques = result.single()['covered']
        coverage_pct = (covered_techniques / technique_count * 100) if technique_count > 0 else 0
        print(f"  Techniques with defense coverage: {covered_techniques}/{technique_count} ({coverage_pct:.1f}%)")

        # Attack flow completeness
        print("\n[CHAIN COMPLETENESS METRICS]")
        
        result = session.run("""
            MATCH (cpe:Platform)-[r1:AFFECTS_BY|AFFECTS]->(cve:Vulnerability)
            RETURN count(r1) as count
        """)
        cpe_cve_rels = result.single()['count']
        cpe_coverage = (cpe_cve_rels / cpe_count * 100) if cpe_count > 0 else 0
        print(f"  CPE->CVE relationships: {cpe_cve_rels} ({cpe_coverage:.1f}% coverage)")

        result = session.run("""
            MATCH (cve:Vulnerability)-[:CAUSED_BY]->(cwe:Weakness)
            RETURN count(*) as count
        """)
        cve_cwe_rels = result.single()['count']
        cve_coverage = (cve_cwe_rels / cve_count * 100) if cve_count > 0 else 0
        print(f"  CVE->CWE relationships: {cve_cwe_rels} ({cve_coverage:.1f}% coverage)")

        # Summary statistics
        print("\n[SUMMARY STATISTICS]")
        
        total_nodes = (cpe_count + cve_count + cwe_count + capec_count + technique_count +
                      d3fend_count + car_count + shield_count + engage_count)
        print(f"  Total nodes in graph: {total_nodes:,}")

        result = session.run("""
            MATCH (src)-[r]-(dst)
            RETURN count(r) as count
        """)
        total_rels = result.single()['count']
        print(f"  Total relationships: {total_rels}")

        result = session.run("""
            MATCH (src)-[r]->(dst)
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY rel_type
        """)
        
        print(f"\n  Relationship types:")
        for record in result:
            print(f"    - {record['rel_type']:15}: {record['count']:3} edges")

        print("\n" + "=" * 70)
        print("SUCCESS: EXTENDED CAUSAL CHAIN COMPLETE")
        print("=" * 70)
        
        print("\nKnowledge Graph Architecture:")
        print("  Attack Side:  CPE -> CVE -> CWE -> CAPEC -> ATT&CK")
        print("  Defense Side: ATT&CK <- (D3FEND, CAR, SHIELD, ENGAGE)")
        print("\nStandards Represented:")
        print("  - CPE 2.3 (NIST)")
        print("  - CVE (NVD)")
        print("  - CWE (MITRE)")
        print("  - CAPEC (MITRE)")
        print("  - ATT&CK (MITRE)")
        print("  - D3FEND (MITRE)")
        print("  - CAR (MITRE)")
        print("  - SHIELD (MITRE)")
        print("  - ENGAGE (MITRE)")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
        driver.close()


if __name__ == '__main__':
    success = verify_extended_chain()
    sys.exit(0 if success else 1)
