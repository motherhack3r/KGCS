#!/usr/bin/env python3
"""
Repair CPE Platform nodes in Neo4j database.

The original ETL had a bug where CPE URI properties were shifted by one index:
- platformPart was set to vendor value
- vendor was set to product value
- product was set to version value
- version was set to update value (wildcard)

This script fixes all existing Platform nodes by re-extracting properties
from the cpeUri field.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class CPEPropertyFixer:
    """Fix CPE properties in Neo4j nodes."""
    
    def __init__(self):
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password')
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def fix_all_platforms(self):
        """Fix all Platform nodes by re-parsing cpeUri."""
        
        print("\n" + "="*80)
        print("CPE PLATFORM PROPERTY REPAIR")
        print("="*80)
        
        with self.driver.session() as session:
            # Get all platforms with cpeUri
            print("\n[1] Loading all Platform nodes...")
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL
                RETURN p.uri as uri, p.cpeUri as cpeUri
                LIMIT 1000
            """)
            
            platforms = []
            for record in result:
                platforms.append({
                    'uri': record['uri'],
                    'cpeUri': record['cpeUri']
                })
            
            print(f"    Found {len(platforms)} platforms to repair")
            
            if len(platforms) == 0:
                print("    ✗ No platforms found")
                return 0
            
            # Fix each platform
            print(f"\n[2] Repairing {len(platforms)} platform properties...")
            fixed_count = 0
            
            for platform in platforms:
                cpe_uri = platform['cpeUri']
                
                # Parse CPE URI
                parts = cpe_uri.split(':')
                
                # Extract properties (correct indices)
                properties = {}
                if len(parts) >= 3:
                    properties['platformPart'] = parts[2]
                if len(parts) >= 4:
                    properties['vendor'] = parts[3]
                if len(parts) >= 5:
                    properties['product'] = parts[4]
                if len(parts) >= 6 and parts[5] != '*':
                    properties['version'] = parts[5]
                else:
                    properties['version'] = None
                
                # Update in Neo4j
                try:
                    query = """
                        MATCH (p:Platform {uri: $uri})
                        SET p.platformPart = $platformPart,
                            p.vendor = $vendor,
                            p.product = $product,
                            p.version = $version
                        RETURN p.uri as uri
                    """
                    
                    result = session.run(
                        query,
                        uri=platform['uri'],
                        platformPart=properties.get('platformPart'),
                        vendor=properties.get('vendor'),
                        product=properties.get('product'),
                        version=properties.get('version')
                    )
                    
                    if result.single():
                        fixed_count += 1
                
                except Exception as e:
                    print(f"    ✗ Error fixing {platform['uri']}: {e}")
            
            print(f"    ✓ Repaired {fixed_count}/{len(platforms)} nodes")
            
            # Verify repair
            print(f"\n[3] Verifying repairs...")
            
            # Check a sample node
            result = session.run("""
                MATCH (p:Platform)
                WHERE p.cpeUri IS NOT NULL AND p.vendor IS NOT NULL
                RETURN p.cpeUri as cpeUri, p.platformPart as part, 
                       p.vendor as vendor, p.product as product, p.version as version
                LIMIT 1
            """)
            
            record = result.single()
            if record:
                cpe_uri = record['cpeUri']
                parts = cpe_uri.split(':')
                
                print(f"\n    Sample CPE URI: {cpe_uri}")
                print(f"    Parsed parts: {parts}")
                print(f"\n    ✓ platformPart: {record['part']} (expected: {parts[2]})")
                print(f"    ✓ vendor: {record['vendor']} (expected: {parts[3]})")
                print(f"    ✓ product: {record['product']} (expected: {parts[4]})")
                if len(parts) > 5:
                    print(f"    ✓ version: {record['version']} (expected: {parts[5] if parts[5] != '*' else None})")
            
            print("\n" + "="*80)
            print(f"✅ REPAIR COMPLETE: {fixed_count} platforms fixed")
            print("="*80 + "\n")
            
            return fixed_count
    
    def close(self):
        self.driver.close()


if __name__ == '__main__':
    fixer = CPEPropertyFixer()
    fixer.fix_all_platforms()
    fixer.close()
