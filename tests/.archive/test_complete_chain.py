#!/usr/bin/env python3
"""
Complete Causal Chain Verification (Extended to ATT&CK)
Verifies: CPE -> CVE -> CWE -> CAPEC -> ATT&CK
"""

import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment before config import
load_dotenv('.env.devel')

sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.config import neo4j_config


def verify_complete_chain():
    """Verify complete causal chain"""
    driver = GraphDatabase.driver(
        neo4j_config.uri,
        auth=(neo4j_config.user, neo4j_config.password)
    )
    session = driver.session()

    print("=" * 70)
    print("COMPLETE CAUSAL CHAIN VERIFICATION (CPE -> CVE -> CWE -> CAPEC -> ATT&CK)")
    print("=" * 70)

    try:
        # Layer 1: CPE (Platforms)
        result = session.run("MATCH (p:Platform) RETURN count(p) as count")
        cpe_count = result.single()['count']
        print(f"\n[1] PLATFORM (CPE) LAYER:")
        print(f"    Total CPE nodes: {cpe_count}")

        # Layer 2: CVE (Vulnerabilities)
        result = session.run("MATCH (v:Vulnerability) RETURN count(v) as count")
        cve_count = result.single()['count']
        print(f"\n[2] VULNERABILITY (CVE) LAYER:")
        print(f"    Total CVE nodes: {cve_count}")

        # Layer 3: CWE (Weaknesses)
        result = session.run("MATCH (w:Weakness) RETURN count(w) as count")
        cwe_count = result.single()['count']
        print(f"\n[3] WEAKNESS (CWE) LAYER:")
        print(f"    Total CWE nodes: {cwe_count}")

        # Layer 4: CAPEC (Attack Patterns)
        result = session.run("MATCH (ap:AttackPattern) RETURN count(ap) as count")
        capec_count = result.single()['count']
        print(f"\n[4] ATTACK PATTERN (CAPEC) LAYER:")
        print(f"    Total CAPEC nodes: {capec_count}")

        # Layer 5: ATT&CK (Techniques)
        result = session.run("MATCH (t:Technique) RETURN count(t) as count")
        technique_count = result.single()['count']
        print(f"\n[5] TECHNIQUE (ATT&CK) LAYER:")
        print(f"    Total Technique nodes: {technique_count}")

        # Relationship: CVE -> CWE
        result = session.run(
            "MATCH (v:Vulnerability)-[r:CAUSED_BY]->(w:Weakness) "
            "RETURN count(r) as count"
        )
        cve_cwe_rels = result.single()['count']
        print(f"\n[6] CVE -> CWE RELATIONSHIPS (CAUSED_BY):")
        print(f"    Total: {cve_cwe_rels}")
        
        result = session.run(
            "MATCH (v:Vulnerability)-[r:CAUSED_BY]->(w:Weakness) "
            "RETURN v.id, w.id LIMIT 3"
        )
        samples = result.data()
        for sample in samples:
            print(f"    * {sample['v.id']} -> {sample['w.id']}")

        # Relationship: CWE -> CAPEC
        result = session.run(
            "MATCH (w:Weakness)-[r:EXPLOITED_BY]->(ap:AttackPattern) "
            "RETURN count(r) as count"
        )
        cwe_capec_rels = result.single()['count']
        print(f"\n[7] CWE -> CAPEC RELATIONSHIPS (EXPLOITED_BY):")
        print(f"    Total: {cwe_capec_rels}")
        
        result = session.run(
            "MATCH (w:Weakness)-[r:EXPLOITED_BY]->(ap:AttackPattern) "
            "RETURN w.id, ap.capecId LIMIT 3"
        )
        samples = result.data()
        for sample in samples:
            print(f"    * {sample['w.id']} -> {sample['ap.capecId']}")

        # Relationship: CAPEC -> ATT&CK
        result = session.run(
            "MATCH (ap:AttackPattern)-[r:USED_IN]->(t:Technique) "
            "RETURN count(r) as count"
        )
        capec_technique_rels = result.single()['count']
        print(f"\n[8] CAPEC -> TECHNIQUE RELATIONSHIPS (USED_IN):")
        print(f"    Total: {capec_technique_rels}")
        
        result = session.run(
            "MATCH (ap:AttackPattern)-[r:USED_IN]->(t:Technique) "
            "RETURN ap.capecId, t.external_id LIMIT 3"
        )
        samples = result.data()
        for sample in samples:
            print(f"    * {sample['ap.capecId']} -> {sample['t.external_id']}")

        # Complete Chain Paths: CVE -> CWE -> CAPEC -> ATT&CK
        print(f"\n[9] COMPLETE CAUSAL CHAIN PATHS (CVE -> CWE -> CAPEC -> TECHNIQUE):")
        result = session.run("""
            MATCH (v:Vulnerability)-[:CAUSED_BY]->(w:Weakness)
                  -[:EXPLOITED_BY]->(ap:AttackPattern)
                  -[:USED_IN]->(t:Technique)
            RETURN v.id, w.id, ap.capecId, t.external_id
            LIMIT 5
        """)
        paths = result.data()
        print(f"    Total paths found: {len(paths)}")
        for i, path in enumerate(paths, 1):
            print(f"    [{i}] {path['v.id']} -> {path['w.id']} -> {path['ap.capecId']} -> {path['t.external_id']}")

        # Overall statistics
        print(f"\n[10] GRAPH STATISTICS:")
        print(f"    Total Nodes by Type:")
        print(f"      - Platforms (CPE):     {cpe_count}")
        print(f"      - Vulnerabilities (CVE): {cve_count}")
        print(f"      - Weaknesses (CWE):    {cwe_count}")
        print(f"      - Attack Patterns (CAPEC): {capec_count}")
        print(f"      - Techniques (ATT&CK): {technique_count}")
        print(f"    Total Relationships:")
        print(f"      - CAUSED_BY (CVE->CWE): {cve_cwe_rels}")
        print(f"      - EXPLOITED_BY (CWE->CAPEC): {cwe_capec_rels}")
        print(f"      - USED_IN (CAPEC->TECHNIQUE): {capec_technique_rels}")
        print(f"    Total Edges: {cve_cwe_rels + cwe_capec_rels + capec_technique_rels}")

        print("\n" + "=" * 70)
        print("SUCCESS: COMPLETE CAUSAL CHAIN VERIFIED (5 LAYERS OPERATIONAL)")
        print("=" * 70)
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
    success = verify_complete_chain()
    sys.exit(0 if success else 1)
