#!/usr/bin/env python3
"""
Causal Chain Verification
Tests end-to-end relationships: CPE -> CVE -> CWE -> CAPEC
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load configuration
env_devel_path = Path(__file__).parent / ".env.devel"
load_dotenv(env_devel_path)

from src.config import neo4j_config
from neo4j import GraphDatabase


def test_causal_chain():
    """Test complete causal chain paths."""
    
    print("=" * 100)
    print("CAUSAL CHAIN VERIFICATION (CPE -> CVE -> CWE -> CAPEC)")
    print("=" * 100)
    
    try:
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )
        
        with driver.session(database=neo4j_config.database) as session:
            
            # Test 1: CPE samples
            print("\n[1] PLATFORM (CPE) LAYER")
            print("-" * 100)
            result = session.run("""
                MATCH (p:Platform)
                RETURN COUNT(p) as count
            """)
            
            record = result.single()
            cpe_count = record['count'] if record else 0
            print(f"   Total CPE nodes: {cpe_count}")
            
            # Test 2: CVE samples
            print("\n[2] VULNERABILITY (CVE) LAYER")
            print("-" * 100)
            result = session.run("""
                MATCH (v:Vulnerability)
                RETURN COUNT(v) as count
            """)
            
            record = result.single()
            cve_count = record['count'] if record else 0
            print(f"   Total CVE nodes: {cve_count}")
            
            # Test 3: CWE samples
            print("\n[3] WEAKNESS (CWE) LAYER")
            print("-" * 100)
            result = session.run("""
                MATCH (w:Weakness)
                RETURN COUNT(w) as count
            """)
            
            record = result.single()
            cwe_count = record['count'] if record else 0
            print(f"   Total CWE nodes: {cwe_count}")
            
            # Test 4: CAPEC samples
            print("\n[4] ATTACK PATTERN (CAPEC) LAYER")
            print("-" * 100)
            result = session.run("""
                MATCH (ap:AttackPattern)
                RETURN COUNT(ap) as count
            """)
            
            record = result.single()
            capec_count = record['count'] if record else 0
            print(f"   Total CAPEC nodes: {capec_count}")
            
            # Test 5: CVE -> CWE relationships
            print("\n[5] CVE->CWE RELATIONSHIPS")
            print("-" * 100)
            result = session.run("""
                MATCH (cve:Vulnerability)-[r:CAUSED_BY]->(cwe:Weakness)
                RETURN COUNT(r) as count
            """)
            
            record = result.single()
            cve_cwe_count = record['count'] if record else 0
            print(f"   Total CVE->CWE relationships: {cve_cwe_count}")
            
            # Sample paths
            result = session.run("""
                MATCH (cve:Vulnerability)-[r:CAUSED_BY]->(cwe:Weakness)
                RETURN cve.cveId as cveId, cwe.cweId as cweId
                LIMIT 3
            """)
            
            print(f"\n   Sample Paths (CVE -> CWE):")
            for record in result:
                print(f"     {record['cveId']} -> {record['cweId']}")
            
            # Test 6: CWE -> CAPEC relationships
            print("\n[6] CWE->CAPEC RELATIONSHIPS")
            print("-" * 100)
            result = session.run("""
                MATCH (cwe:Weakness)-[r:EXPLOITED_BY]->(ap:AttackPattern)
                RETURN COUNT(r) as count
            """)
            
            record = result.single()
            cwe_capec_count = record['count'] if record else 0
            print(f"   Total CWE->CAPEC relationships: {cwe_capec_count}")
            
            # Sample paths
            result = session.run("""
                MATCH (cwe:Weakness)-[r:EXPLOITED_BY]->(ap:AttackPattern)
                RETURN cwe.cweId as cweId, ap.capecId as capecId
                LIMIT 3
            """)
            
            print(f"\n   Sample Paths (CWE -> CAPEC):")
            for record in result:
                print(f"     {record['cweId']} -> {record['capecId']}")
            
            # Test 7: Complete chain paths
            print("\n[7] COMPLETE CAUSAL CHAIN PATHS")
            print("-" * 100)
            result = session.run("""
                MATCH (cve:Vulnerability)-[r1:CAUSED_BY]->(cwe:Weakness)-[r2:EXPLOITED_BY]->(ap:AttackPattern)
                RETURN cve.cveId as cveId, cwe.cweId as cweId, ap.capecId as capecId
                LIMIT 5
            """)
            
            chain_count = 0
            for record in result:
                print(f"   {record['cveId']} -> {record['cweId']} -> {record['capecId']}")
                chain_count += 1
            
            if chain_count == 0:
                print("   (No complete chains yet - awaiting more relationship data)")
            
            # Test 8: Statistics
            print("\n[8] GRAPH STATISTICS")
            print("-" * 100)
            
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as nodeType, COUNT(n) as count
                ORDER BY count DESC
            """)
            
            total_nodes = 0
            print("   Node Types:")
            for record in result:
                node_type = record['nodeType']
                count = record['count']
                print(f"     {node_type}: {count}")
                total_nodes += count
            
            print(f"\n   Total Nodes: {total_nodes}")
            
            # Relationship statistics
            result = session.run("""
                MATCH ()-[r]->()
                RETURN TYPE(r) as relType, COUNT(r) as count
                ORDER BY count DESC
            """)
            
            total_rels = 0
            print("\n   Relationship Types:")
            for record in result:
                rel_type = record['relType']
                count = record['count']
                print(f"     {rel_type}: {count}")
                total_rels += count
            
            print(f"\n   Total Relationships: {total_rels}")
            
            # Summary
            print("\n" + "=" * 100)
            print("CAUSAL CHAIN SUMMARY")
            print("=" * 100)
            print(f"\n   Layers Implemented:")
            print(f"     CPE:      {cpe_count:>6} nodes")
            print(f"     CVE:      {cve_count:>6} nodes")
            print(f"     CWE:      {cwe_count:>6} nodes")
            print(f"     CAPEC:    {capec_count:>6} nodes")
            print(f"\n   Relationships:")
            print(f"     CVE->CWE:      {cve_cwe_count:>6} edges")
            print(f"     CWE->CAPEC:    {cwe_capec_count:>6} edges")
            print(f"     Complete chain: {chain_count:>5} paths")
            
        driver.close()
        
        print("\n" + "=" * 100)
        print("SUCCESS: CAUSAL CHAIN VERIFICATION COMPLETE")
        print("=" * 100)
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_causal_chain())
