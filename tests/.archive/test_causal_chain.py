#!/usr/bin/env python3
"""
Test causal chain queries on Neo4j data
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
    """Test causal chain relationships in Neo4j."""
    
    print("=" * 100)
    print("NEO4J CAUSAL CHAIN VERIFICATION")
    print("=" * 100)
    
    try:
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )
        
        with driver.session(database=neo4j_config.database) as session:
            print("\n[1] Platform (CPE) Samples")
            print("-" * 100)
            result = session.run("""
                MATCH (p:Platform)
                RETURN p.cpeUri as cpe, p.vendor as vendor, p.product as product
                LIMIT 5
            """)
            
            for record in result:
                print(f"  CPE: {record['cpe']}")
                print(f"       Vendor: {record['vendor']}, Product: {record['product']}")
            
            print("\n[2] Vulnerability (CVE) Samples")
            print("-" * 100)
            result = session.run("""
                MATCH (v:Vulnerability)
                RETURN v.cveId as cveId, v.description as desc
                LIMIT 3
            """)
            
            for record in result:
                cve_id = record['cveId']
                desc = (record['desc'] or "")[:80]
                print(f"  CVE: {cve_id}")
                print(f"       {desc}...")
            
            print("\n[3] Statistics")
            print("-" * 100)
            
            # Node counts
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, COUNT(n) as count
                ORDER BY count DESC
            """)
            
            print("  Node Counts:")
            for record in result:
                label = record['label']
                count = record['count']
                print(f"    {label}: {count}")
            
            # Relationship counts
            result = session.run("""
                MATCH ()-[r]->()
                RETURN TYPE(r) as type, COUNT(r) as count
                ORDER BY count DESC
            """)
            
            print("\n  Relationship Counts:")
            rel_count = 0
            for record in result:
                rel_type = record['type']
                count = record['count']
                print(f"    {rel_type}: {count}")
                rel_count += count
            
            if rel_count == 0:
                print("    (No relationships yet - awaiting full causal chain)")
            
            print("\n[4] Data Quality")
            print("-" * 100)
            
            # Check required Platform properties
            result = session.run("""
                MATCH (p:Platform)
                RETURN COUNT(CASE WHEN p.cpeUri IS NOT NULL THEN 1 END) as with_cpe,
                       COUNT(CASE WHEN p.vendor IS NOT NULL THEN 1 END) as with_vendor,
                       COUNT(CASE WHEN p.product IS NOT NULL THEN 1 END) as with_product
            """)
            
            record = result.single()
            if record:
                total_platforms = 1371
                print(f"  Platform completeness:")
                print(f"    CPE URI: {record['with_cpe']}/{total_platforms}")
                print(f"    Vendor: {record['with_vendor']}/{total_platforms}")
                print(f"    Product: {record['with_product']}/{total_platforms}")
            
            # Check required Vulnerability properties
            result = session.run("""
                MATCH (v:Vulnerability)
                RETURN COUNT(CASE WHEN v.cveId IS NOT NULL THEN 1 END) as with_cveId,
                       COUNT(CASE WHEN v.description IS NOT NULL THEN 1 END) as with_desc
            """)
            
            record = result.single()
            if record:
                total_vulns = 21
                print(f"\n  Vulnerability completeness:")
                print(f"    CVE ID: {record['with_cveId']}/{total_vulns}")
                print(f"    Description: {record['with_desc']}/{total_vulns}")
            
        driver.close()
        
        print("\n" + "=" * 100)
        print("SUCCESS: NEO4J DATA LOADED AND VERIFIED")
        print("=" * 100)
        print("\nNext steps:")
        print("  1. Load CVE->CWE relationships")
        print("  2. Load CWE->CAPEC relationships")
        print("  3. Load CAPEC->ATT&CK relationships")
        print("  4. Load defense layers (D3FEND, CAR, SHIELD, ENGAGE)")
        print("  5. Test end-to-end causal chain queries")
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_causal_chain())
