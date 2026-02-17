#!/usr/bin/env python3
"""
Final verification that CPE ETL bug is fixed and database is repaired.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import sys

load_dotenv()

class CPEFixVerifier:
    """Verify CPE properties are correctly set in database."""
    
    def __init__(self):
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password')
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def verify(self):
        """Run all verifications."""
        print("\n" + "="*80)
        print("CPE ETL BUG FIX - FINAL VERIFICATION")
        print("="*80)
        
        with self.driver.session() as session:
            # Check 1: Verify vendor property is correct
            print("\n[1] Checking vendor property alignment...")
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL AND p.vendor IS NOT NULL
                WITH p, p.cpeUri as cpeUri, p.vendor as vendor
                WITH *, split(cpeUri, ':') as parts
                WHERE parts[3] = vendor
                RETURN COUNT(p) as correct_count
            """)
            
            record = result.single()
            correct = record['correct_count'] if record else 0
            
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL AND p.vendor IS NOT NULL
                RETURN COUNT(p) as total_count
            """)
            
            record = result.single()
            total = record['total_count'] if record else 0
            
            if correct == total:
                print(f"  ✅ Vendor property: {correct}/{total} nodes correct (100%)")
                vendor_pass = True
            else:
                print(f"  ❌ Vendor property: {correct}/{total} nodes correct ({100*correct//total}%)")
                vendor_pass = False
            
            # Check 2: Verify product property is correct
            print("\n[2] Checking product property alignment...")
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL AND p.product IS NOT NULL
                WITH p, p.cpeUri as cpeUri, p.product as product
                WITH *, split(cpeUri, ':') as parts
                WHERE parts[4] = product
                RETURN COUNT(p) as correct_count
            """)
            
            record = result.single()
            correct = record['correct_count'] if record else 0
            
            if correct == total:
                print(f"  ✅ Product property: {correct}/{total} nodes correct (100%)")
                product_pass = True
            else:
                print(f"  ❌ Product property: {correct}/{total} nodes correct ({100*correct//total}%)")
                product_pass = False
            
            # Check 3: Verify platformPart property is correct
            print("\n[3] Checking platformPart property alignment...")
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL AND p.platformPart IS NOT NULL
                WITH p, p.cpeUri as cpeUri, p.platformPart as part
                WITH *, split(cpeUri, ':') as parts
                WHERE parts[2] = part
                RETURN COUNT(p) as correct_count
            """)
            
            record = result.single()
            correct = record['correct_count'] if record else 0
            
            if correct == total:
                print(f"  ✅ Platform part: {correct}/{total} nodes correct (100%)")
                part_pass = True
            else:
                print(f"  ❌ Platform part: {correct}/{total} nodes correct ({100*correct//total}%)")
                part_pass = False
            
            # Check 4: Sample inspection
            print("\n[4] Sample node inspection...")
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL AND p.vendor IS NOT NULL
                WITH p, split(p.cpeUri, ':') as parts
                RETURN p.cpeUri as cpe, 
                       parts[2] as cpe_part, p.platformPart as db_part,
                       parts[3] as cpe_vendor, p.vendor as db_vendor,
                       parts[4] as cpe_product, p.product as db_product,
                       parts[5] as cpe_version, p.version as db_version
                LIMIT 3
            """)
            
            all_match = True
            for i, record in enumerate(result, 1):
                cpe = record['cpe']
                matches = (
                    record['cpe_part'] == record['db_part'] and
                    record['cpe_vendor'] == record['db_vendor'] and
                    record['cpe_product'] == record['db_product'] and
                    (record['cpe_version'] == record['db_version'] or 
                     (record['cpe_version'] == '*' and record['db_version'] is None))
                )
                
                status = "✅" if matches else "❌"
                print(f"\n  {status} Sample {i}: {cpe[:50]}...")
                if not matches:
                    print(f"      CPE:  {record['cpe_part']} | {record['cpe_vendor']} | {record['cpe_product']} | {record['cpe_version']}")
                    print(f"      DB:   {record['db_part']} | {record['db_vendor']} | {record['db_product']} | {record['db_version']}")
                    all_match = False
            
            # Summary
            print("\n" + "="*80)
            if vendor_pass and product_pass and part_pass and all_match:
                print("✅ CPE ETL BUG FIX VERIFIED - ALL SYSTEMS OPERATIONAL")
                print("="*80 + "\n")
                return True
            else:
                print("❌ CPE ETL BUG FIX VERIFICATION FAILED")
                print("="*80 + "\n")
                return False
    
    def close(self):
        self.driver.close()


if __name__ == '__main__':
    verifier = CPEFixVerifier()
    success = verifier.verify()
    verifier.close()
    sys.exit(0 if success else 1)
