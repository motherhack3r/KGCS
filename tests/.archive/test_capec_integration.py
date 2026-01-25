#!/usr/bin/env python3
"""
CAPEC Integration Pipeline
Transforms CAPEC JSON to Neo4j and creates CWE->CAPEC relationships
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load configuration
env_devel_path = Path(__file__).parent / ".env.devel"
load_dotenv(env_devel_path)

from src.config import neo4j_config
from neo4j import GraphDatabase


class CAPECtoNeo4j:
    """
    Load CAPEC data to Neo4j with CWE relationships
    """
    
    def __init__(self):
        self.stats = {
            'attack_patterns': 0,
            'cwe_capec_relationships': 0,
        }
    
    def load_capec_json(self, capec_json_file: str) -> dict:
        """Load CAPEC JSON data."""
        print(f"\n[1] Loading CAPEC JSON...")
        
        with open(capec_json_file) as f:
            capec_data = json.load(f)
        
        attack_patterns = capec_data.get('AttackPatterns', [])
        print(f"   * Loaded {len(attack_patterns)} attack patterns")
        
        return capec_data
    
    def load_capec_to_neo4j(self, capec_data: dict, driver) -> bool:
        """Load CAPEC attack patterns to Neo4j."""
        print(f"\n[2] Loading CAPEC Nodes to Neo4j...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                
                # Extract attack patterns
                attack_patterns = []
                for ap in capec_data.get('AttackPatterns', []):
                    ap_id = ap.get('ID', '')
                    if not ap_id:
                        continue
                    
                    capec_id = f"CAPEC-{ap_id}" if not ap_id.startswith('CAPEC-') else ap_id
                    description = ap.get('Description', {})
                    desc_text = description.get('Text', '') if isinstance(description, dict) else str(description)
                    
                    pattern = {
                        'uri': f"https://example.org/attack-pattern/{capec_id}",
                        'capecId': capec_id,
                        'name': ap.get('Name', ''),
                        'description': desc_text[:500],
                    }
                    attack_patterns.append(pattern)
                    self.stats['attack_patterns'] += 1
                
                # Batch insert
                if attack_patterns:
                    cypher = """
                        UNWIND $patterns as p
                        MERGE (ap:`AttackPattern` {uri: p.uri})
                        SET ap.capecId = p.capecId,
                            ap.name = p.name,
                            ap.description = p.description
                    """
                    session.run(cypher, patterns=attack_patterns)
                    print(f"   * Created {len(attack_patterns)} AttackPattern nodes")
                
                # Create uniqueness constraint
                try:
                    session.run("""
                        CREATE CONSTRAINT capec_id_unique IF NOT EXISTS
                        FOR (ap:AttackPattern) REQUIRE ap.capecId IS UNIQUE
                    """)
                except:
                    pass
                
                return True
                
        except Exception as e:
            print(f"\n   ERROR: {e}")
            return False
    
    def create_cwe_capec_relationships(self, capec_data: dict, driver) -> bool:
        """Create relationships between CWEs and CAPECs."""
        print(f"\n[3] Creating CWE->CAPEC Relationships...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                
                # Extract CWE->CAPEC relationships from JSON
                relationship_count = 0
                
                for ap in capec_data.get('AttackPatterns', []):
                    ap_id = ap.get('ID', '')
                    if not ap_id:
                        continue
                    
                    capec_id = f"CAPEC-{ap_id}" if not ap_id.startswith('CAPEC-') else ap_id
                    
                    # Create relationships to related weaknesses
                    for weakness in ap.get('RelatedWeaknesses', []):
                        cwe_id = weakness.get('ID', '')
                        if cwe_id:
                            cwe_id = f"CWE-{cwe_id}" if not str(cwe_id).startswith('CWE-') else str(cwe_id)
                            
                            try:
                                session.run("""
                                    MATCH (cwe:Weakness {cweId: $cweId})
                                    MATCH (ap:AttackPattern {capecId: $capecId})
                                    MERGE (cwe)-[r:EXPLOITED_BY]->(ap)
                                """, cweId=cwe_id, capecId=capec_id)
                                relationship_count += 1
                            except:
                                pass
                
                self.stats['cwe_capec_relationships'] = relationship_count
                print(f"   * Created {relationship_count} CWE->CAPEC relationships")
                
                # Get verification stats
                result = session.run("""
                    MATCH (cwe:Weakness)-[r:EXPLOITED_BY]->(ap:AttackPattern)
                    RETURN COUNT(r) as relationship_count
                """)
                
                record = result.single()
                if record:
                    count = record['relationship_count']
                    print(f"   * Verified: {count} relationships in database")
                
                return True
                
        except Exception as e:
            print(f"\n   ERROR: {e}")
            return False
    
    def verify_data(self, driver) -> bool:
        """Verify CAPEC data in Neo4j."""
        print(f"\n[4] Verifying Data...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                
                # Count attack pattern nodes
                result = session.run("""
                    MATCH (ap:AttackPattern)
                    RETURN COUNT(ap) as count
                """)
                
                record = result.single()
                ap_count = record['count'] if record else 0
                print(f"   * AttackPattern nodes: {ap_count}")
                
                # Sample patterns
                result = session.run("""
                    MATCH (ap:AttackPattern)
                    RETURN ap.capecId as capecId, ap.name as name
                    LIMIT 5
                """)
                
                print(f"   * Sample AttackPatterns:")
                for record in result:
                    print(f"     {record['capecId']}: {(record['name'] or 'N/A')[:60]}")
                
                # Relationship stats
                result = session.run("""
                    MATCH (cwe:Weakness)-[r:EXPLOITED_BY]->(ap:AttackPattern)
                    RETURN COUNT(r) as count
                """)
                
                record = result.single()
                rel_count = record['count'] if record else 0
                print(f"   * CWE->CAPEC relationships: {rel_count}")
                
                return True
                
        except Exception as e:
            print(f"\n   ERROR: {e}")
            return False


def main():
    """Main entry point."""
    print("=" * 100)
    print("CAPEC INTEGRATION PIPELINE")
    print("=" * 100)
    
    try:
        processor = CAPECtoNeo4j()
        
        # Step 1: Load CAPEC JSON
        capec_json_file = "data/capec/samples/sample_capec.json"
        capec_data = processor.load_capec_json(capec_json_file)
        
        # Step 2: Connect to Neo4j
        print(f"\n[2] Connecting to Neo4j...")
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )
        
        # Step 3: Load CAPEC to Neo4j
        if not processor.load_capec_to_neo4j(capec_data, driver):
            return 1
        
        # Step 4: Create CWE->CAPEC relationships
        if not processor.create_cwe_capec_relationships(capec_data, driver):
            return 1
        
        # Step 5: Verify data
        if not processor.verify_data(driver):
            return 1
        
        driver.close()
        
        print("\n" + "=" * 100)
        print("SUCCESS: CAPEC INTEGRATION COMPLETE")
        print("=" * 100)
        print("\nNext Steps:")
        print("  1. Test end-to-end causal chain: CPE -> CVE -> CWE -> CAPEC")
        print("  2. Proceed with ATT&CK integration")
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
