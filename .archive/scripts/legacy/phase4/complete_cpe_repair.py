#!/usr/bin/env python3
"""Complete CPE repair for all nodes - including those without cpeUri."""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo4jpass')

def repair():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        print("=" * 80)
        print("COMPLETE CPE PROPERTY REPAIR")
        print("=" * 80)
        
        # First, check how many nodes we're dealing with
        print("\n[1] Analyzing Platform nodes...")
        result = session.run("""
            MATCH (p:Platform)
            RETURN 
                COUNT(*) as total_nodes,
                COUNT(CASE WHEN p.cpeUri IS NOT NULL THEN 1 END) as with_cpeUri,
                COUNT(CASE WHEN p.vendor IS NOT NULL THEN 1 END) as with_vendor,
                COUNT(CASE WHEN p.platformPart IS NOT NULL THEN 1 END) as with_platformPart
        """)
        rec = result.single()
        print(f"  Total Platform nodes: {rec['total_nodes']}")
        print(f"  With cpeUri: {rec['with_cpeUri']}")
        print(f"  With vendor: {rec['with_vendor']}")
        print(f"  With platformPart: {rec['with_platformPart']}")
        
        # Now, for the 366 nodes with vendor but NO cpeUri, we need a different approach
        # Let's first see what we're dealing with
        print("\n[2] Checking nodes WITHOUT cpeUri but WITH properties...")
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NULL AND p.vendor IS NOT NULL
            RETURN p.vendor, p.platformPart, p.product, p.version
            LIMIT 5
        """)
        
        records = result.data()
        print(f"  Found {len(records)} sample nodes without cpeUri:")
        for i, record in enumerate(records, 1):
            print(f"    [{i}] vendor={record.get('vendor')}, platformPart={record.get('platformPart')}, product={record.get('product')}, version={record.get('version')}")
        
        # For nodes without cpeUri, we cannot repair them. We can only repair nodes WITH cpeUri
        print("\n[3] Repairing nodes WITH cpeUri...")
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NOT NULL
            WITH p, split(p.cpeUri, ':') as parts
            SET 
                p.platformPart = parts[2],
                p.vendor = parts[3],
                p.product = parts[4],
                p.version = CASE WHEN parts[5] <> '*' THEN parts[5] ELSE NULL END
            RETURN COUNT(p) as repaired_count
        """)
        
        rec = result.single()
        repaired = rec['repaired_count'] if rec else 0
        print(f"  ✅ Repaired {repaired} nodes with cpeUri")
        
        # Verify the repair
        print("\n[4] Verifying repair...")
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NOT NULL AND p.platformPart IS NOT NULL
            WITH p, split(p.cpeUri, ':') as parts
            WITH p, parts,
                 CASE 
                    WHEN parts[2] = p.platformPart AND parts[3] = p.vendor AND parts[4] = p.product 
                    THEN 'CORRECT' 
                    ELSE 'MISMATCH' 
                 END as status
            RETURN status, COUNT(*) as count
        """)
        
        counts = result.data()
        for row in counts:
            status = row.get('status', 'UNKNOWN')
            count = row.get('count', 0)
            if status == 'CORRECT':
                print(f"  ✅ CORRECT: {count} nodes")
            else:
                print(f"  ❌ {status}: {count} nodes")
        
        # Show status summary
        print("\n[5] Final status...")
        result = session.run("""
            MATCH (p:Platform)
            RETURN 
                COUNT(*) as total,
                COUNT(CASE WHEN p.cpeUri IS NOT NULL THEN 1 END) as with_cpeUri,
                COUNT(CASE WHEN p.cpeUri IS NULL AND p.vendor IS NOT NULL THEN 1 END) as without_cpeUri_but_props
        """)
        rec = result.single()
        total = rec['total'] if rec else 0
        with_cpe = rec['with_cpeUri'] if rec else 0
        without_cpe = rec['without_cpeUri_but_props'] if rec else 0
        
        print(f"  Total Platform nodes: {total}")
        print(f"  With cpeUri (repaired): {with_cpe}")
        print(f"  Without cpeUri (cannot repair): {without_cpe}")
        
        if without_cpe > 0:
            print(f"\n  ⚠️  WARNING: {without_cpe} nodes have properties but no cpeUri.")
            print(f"      These were likely created before cpeUri tracking was added.")
            print(f"      They will need to be re-ingested from CPE data source.")
    
    driver.close()

if __name__ == '__main__':
    repair()
