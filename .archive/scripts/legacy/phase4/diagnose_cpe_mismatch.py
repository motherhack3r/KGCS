#!/usr/bin/env python3
"""Diagnose CPE property mismatches in the database."""

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
        print("DIAGNOSING CPE PROPERTY MISMATCHES")
        print("=" * 80)
        
        # Get a few mismatched nodes
        print("\n[1] Finding vendor mismatches...")
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NOT NULL AND p.vendor IS NOT NULL
            WITH p, split(p.cpeUri, ':') as parts
            WHERE parts[3] <> p.vendor
            RETURN p.cpeUri, parts[3] as expected_vendor, p.vendor as actual_vendor
            LIMIT 5
        """)
        
        vendor_mismatches = result.data()
        if vendor_mismatches:
            print(f"  Found {len(vendor_mismatches)} vendor mismatches:")
            for record in vendor_mismatches:
                cpe = record.get('cpeUri') or record.get('p.cpeUri')
                exp = record.get('expected_vendor')
                act = record.get('actual_vendor')
                if not cpe:
                    print(f"    Record keys: {list(record.keys())}")
                    continue
                print(f"    CPE: {cpe}")
                print(f"      Expected vendor: {exp}")
                print(f"      Actual vendor:   {act}")
                
                # Debug: show full split
                parts = cpe.split(':')
                print(f"      Parts: {parts}")
                print()
        else:
            print("  ✅ No vendor mismatches found!")
        
        # Check product mismatches
        print("\n[2] Finding product mismatches...")
        result = session.run("""
            MATCH (p:Platform)
            WHERE p.cpeUri IS NOT NULL AND p.product IS NOT NULL
            WITH p, split(p.cpeUri, ':') as parts
            WHERE parts[4] <> p.product
            RETURN p.cpeUri, parts[4] as expected_product, p.product as actual_product
            LIMIT 5
        """)
        
        product_mismatches = result.data()
        if product_mismatches:
            print(f"  Found {len(product_mismatches)} product mismatches:")
            for record in product_mismatches:
                cpe = record['cpeUri']
                exp = record['expected_product']
                act = record['actual_product']
                print(f"    CPE: {cpe}")
                print(f"      Expected product: {exp}")
                print(f"      Actual product:   {act}")
                print()
        else:
            print("  ✅ No product mismatches found!")
        
        # Check total nodes
        print("\n[3] Database statistics...")
        result = session.run("MATCH (p:Platform) RETURN COUNT(p) as total")
        rec = result.single()
        total = rec['total'] if rec else 0
        print(f"  Total Platform nodes: {total}")
        
        # Check nodes with properties set
        result = session.run("""
            MATCH (p:Platform) 
            WHERE p.vendor IS NOT NULL RETURN COUNT(p) as count
        """)
        rec = result.single()
        vendor_set = rec['count'] if rec else 0
        print(f"  Nodes with vendor set: {vendor_set}")
        
        result = session.run("""
            MATCH (p:Platform) 
            WHERE p.cpeUri IS NOT NULL RETURN COUNT(p) as count
        """)
        rec = result.single()
        cpe_set = rec['count'] if rec else 0
        print(f"  Nodes with cpeUri set: {cpe_set}")
    
    driver.close()

if __name__ == '__main__':
    diagnose()
