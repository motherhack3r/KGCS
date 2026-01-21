#!/usr/bin/env python3
"""
Quick verification that Phase 4 is fully operational.
Run this anytime to confirm CPE→CVE integration is working.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def quick_check():
    """Quick Phase 4 verification."""
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("\n" + "="*60)
            print("PHASE 4 OPERATIONAL STATUS CHECK")
            print("="*60)
            
            # Check CPE→CVE relationships
            result = session.run("""
                MATCH (p:Platform)-[r:AFFECTS]->(v:Vulnerability)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            cpe_cve = record['count'] if record else 0
            status1 = "✓ PASS" if cpe_cve >= 63 else "✗ FAIL"
            print(f"\n[1] CPE→CVE relationships: {cpe_cve}/63 {status1}")
            
            # Check complete 6-layer chains
            result = session.run("""
                MATCH (p:Platform)-[r1:AFFECTS]->(v:Vulnerability)
                      -[r2:CAUSED_BY]->(w:Weakness)
                      -[r3:EXPLOITED_BY]->(ap:AttackPattern)
                      -[r4:USED_IN]->(t:Technique)
                RETURN COUNT(*) as count
            """)
            record = result.single()
            chains = record['count'] if record else 0
            status2 = "✓ PASS" if chains >= 9 else "✗ FAIL"
            print(f"[2] 6-layer chains: {chains}/9 {status2}")
            
            # Check node counts
            result = session.run("""
                MATCH (n) RETURN COUNT(n) as count
            """)
            record = result.single()
            nodes = record['count'] if record else 0
            status3 = "✓ PASS" if nodes == 1475 else "✗ FAIL"
            print(f"[3] Total nodes: {nodes}/1475 {status3}")
            
            # Check relationship count
            result = session.run("""
                MATCH ()-[r]->() RETURN COUNT(r) as count
            """)
            record = result.single()
            rels = record['count'] if record else 0
            status4 = "✓ PASS" if rels >= 78 else "✗ FAIL"
            print(f"[4] Total relationships: {rels}/78 {status4}")
            
            print("\n" + "="*60)
            all_pass = all([
                cpe_cve >= 63,
                chains >= 9,
                nodes == 1475,
                rels >= 78
            ])
            
            if all_pass:
                print("STATUS: ✅ PHASE 4 FULLY OPERATIONAL")
            else:
                print("STATUS: ⚠️  PHASE 4 INCOMPLETE")
            print("="*60 + "\n")
            
            return all_pass
    
    finally:
        driver.close()


if __name__ == '__main__':
    success = quick_check()
    exit(0 if success else 1)
