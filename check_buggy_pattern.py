#!/usr/bin/env python3
"""Check which Platform nodes still have the OLD buggy values."""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo4jpass')

def diagnose():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        print("=" * 80)
        print("CHECKING FOR OLD BUGGY VALUES (OFF-BY-ONE SHIFT)")
        print("=" * 80)
        
        # Query: Show a sample of nodes with their actual properties
        print("\n[1] Checking sample of Platform nodes...")
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NOT NULL
            RETURN p.cpeUri, p.platformPart, p.vendor, p.product, p.version
            LIMIT 10
        """)
        
        records = result.data()
        for i, record in enumerate(records, 1):
            cpe = record.get('cpeUri', 'N/A')
            parts = cpe.split(':')
            
            print(f"\n  [{i}] {cpe}")
            print(f"      parts[2]={parts[2] if len(parts) > 2 else 'N/A'} (platformPart expected)")
            print(f"      parts[3]={parts[3] if len(parts) > 3 else 'N/A'} (vendor expected)")
            print(f"      parts[4]={parts[4] if len(parts) > 4 else 'N/A'} (product expected)")
            print(f"      parts[5]={parts[5] if len(parts) > 5 else 'N/A'} (version expected)")
            
            print(f"      platformPart={record.get('platformPart', 'NULL')}")
            print(f"      vendor={record.get('vendor', 'NULL')}")
            print(f"      product={record.get('product', 'NULL')}")
            print(f"      version={record.get('version', 'NULL')}")
            
            # Check if OLD buggy pattern (off-by-one)
            if (record.get('platformPart') == (parts[3] if len(parts) > 3 else None)):
                print(f"      ❌ DETECTED: OLD BUGGY PATTERN (off-by-one shift)")
            elif (record.get('platformPart') == (parts[2] if len(parts) > 2 else None)):
                print(f"      ✅ CORRECT: Matches fixed pattern")
        
        # Count how many nodes have the OLD buggy pattern vs CORRECT pattern
        print("\n" + "=" * 80)
        print("[2] Counting patterns across all nodes...")
        
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NOT NULL AND p.platformPart IS NOT NULL
            WITH p, split(p.cpeUri, ':') as parts
            WITH p, parts,
                 CASE WHEN parts[3] = p.platformPart THEN 'OLD_BUGGY' ELSE 'FIXED' END as pattern
            RETURN pattern, COUNT(*) as count
        """)
        
        counts = result.data()
        for row in counts:
            pattern = row.get('pattern', 'UNKNOWN')
            count = row.get('count', 0)
            if pattern == 'OLD_BUGGY':
                print(f"  ❌ OLD BUGGY (off-by-one): {count} nodes")
            elif pattern == 'FIXED':
                print(f"  ✅ CORRECT: {count} nodes")
            else:
                print(f"  ? {pattern}: {count} nodes")
        
    driver.close()

if __name__ == '__main__':
    diagnose()
