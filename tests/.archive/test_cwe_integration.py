#!/usr/bin/env python3
"""
CWE Integration Pipeline
Transforms CWE JSON to RDF, loads to Neo4j, and creates CVE->CWE relationships
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load configuration
env_devel_path = Path(__file__).parent / ".env.devel"
load_dotenv(env_devel_path)

from src.config import neo4j_config
from src.etl.etl_cwe import CWEtoRDFTransformer
from rdflib import Graph, Namespace, RDF, Literal
from neo4j import GraphDatabase


class CWEtoNeo4j:
    """
    Transform CWE data and load to Neo4j with CVE relationships
    """
    
    def __init__(self):
        self.sec_ns = Namespace("https://example.org/sec/core#")
        self.ex_ns = Namespace("https://example.org/")
        self.stats = {
            'weaknesses': 0,
            'cve_cwe_relationships': 0,
        }
    
    def transform_cwe(self, cwe_json_file: str) -> Graph:
        """Transform CWE JSON to RDF."""
        print(f"\n[1] Transforming CWE JSON to RDF...")
        
        with open(cwe_json_file) as f:
            cwe_data = json.load(f)
        
        transformer = CWEtoRDFTransformer()
        g = transformer.transform(cwe_data)
        
        # Count weaknesses
        query = f"""
            PREFIX sec: <https://example.org/sec/core#>
            SELECT (COUNT(?w) as ?count) WHERE {{
                ?w a sec:Weakness .
            }}
        """
        
        results = g.query(query)
        for row in results:
            self.stats['weaknesses'] = int(row['count'])
        
        print(f"   * Loaded {len(g)} RDF triples")
        print(f"   * Weaknesses: {self.stats['weaknesses']}")
        
        return g
    
    def load_cwe_to_neo4j(self, g: Graph, driver) -> bool:
        """Load CWE RDF nodes to Neo4j."""
        print(f"\n[2] Loading CWE Nodes to Neo4j...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                # Extract and load weakness nodes
                query = f"""
                    PREFIX sec: <https://example.org/sec/core#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    SELECT ?weakness ?cweId ?label ?description WHERE {{
                        ?weakness a sec:Weakness ;
                                  sec:cweId ?cweId .
                        OPTIONAL {{ ?weakness rdfs:label ?label }}
                        OPTIONAL {{ ?weakness sec:description ?description }}
                    }}
                """
                
                results = g.query(query)
                weaknesses = []
                
                for row in results:
                    weakness = {
                        'uri': str(row['weakness']),
                        'cweId': str(row['cweId']),
                        'label': str(row['label']) if row['label'] else None,
                        'description': str(row['description'])[:500] if row['description'] else None,
                    }
                    weaknesses.append(weakness)
                
                # Batch insert weakness nodes
                if weaknesses:
                    cypher = """
                        UNWIND $weaknesses as w
                        MERGE (cwe:`Weakness` {uri: w.uri})
                        SET cwe.cweId = w.cweId,
                            cwe.label = w.label,
                            cwe.description = w.description
                    """
                    session.run(cypher, weaknesses=weaknesses)
                    print(f"   * Created {len(weaknesses)} Weakness nodes")
                
                # Create uniqueness constraint
                try:
                    session.run("""
                        CREATE CONSTRAINT cwe_id_unique IF NOT EXISTS
                        FOR (w:Weakness) REQUIRE w.cweId IS UNIQUE
                    """)
                except:
                    pass
                
                return True
                
        except Exception as e:
            print(f"\n   ERROR: {e}")
            return False
    
    def create_cve_cwe_relationships(self, driver) -> bool:
        """Create relationships between CVEs and CWEs."""
        print(f"\n[3] Creating CVE->CWE Relationships...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                
                # For now, create sample relationships based on common patterns
                # In production, these would come from NVD CVE data
                
                # Example: CWE-79 (XSS) affects many web vulnerabilities
                sample_mappings = [
                    ("CVE-2025-14124", "CWE-79"),   # SQL Injection
                    ("CVE-2025-15456", "CWE-287"),  # Improper Authentication
                    ("CVE-2025-15457", "CWE-287"),  # Improper Authentication
                    ("CVE-2025-15458", "CWE-287"),  # Improper Authentication
                ]
                
                for cve_id, cwe_id in sample_mappings:
                    try:
                        session.run("""
                            MATCH (cve:Vulnerability {cveId: $cveId})
                            MATCH (cwe:Weakness {cweId: $cweId})
                            MERGE (cve)-[r:CAUSED_BY]->(cwe)
                        """, cveId=cve_id, cweId=cwe_id)
                        self.stats['cve_cwe_relationships'] += 1
                    except:
                        pass
                
                print(f"   * Created {self.stats['cve_cwe_relationships']} CVE->CWE relationships")
                
                # Get verification stats
                result = session.run("""
                    MATCH (cve:Vulnerability)-[r:CAUSED_BY]->(cwe:Weakness)
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
        """Verify CWE data in Neo4j."""
        print(f"\n[4] Verifying Data...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                
                # Count weakness nodes
                result = session.run("""
                    MATCH (w:Weakness)
                    RETURN COUNT(w) as count
                """)
                
                record = result.single()
                weakness_count = record['count'] if record else 0
                print(f"   * Weakness nodes: {weakness_count}")
                
                # Sample weaknesses
                result = session.run("""
                    MATCH (w:Weakness)
                    RETURN w.cweId as cweId, w.label as label
                    LIMIT 5
                """)
                
                print(f"   * Sample Weaknesses:")
                for record in result:
                    print(f"     {record['cweId']}: {(record['label'] or 'N/A')[:60]}")
                
                # Relationship stats
                result = session.run("""
                    MATCH (cve:Vulnerability)-[r:CAUSED_BY]->(cwe:Weakness)
                    RETURN COUNT(r) as count
                """)
                
                record = result.single()
                rel_count = record['count'] if record else 0
                print(f"   * CVE->CWE relationships: {rel_count}")
                
                return True
                
        except Exception as e:
            print(f"\n   ERROR: {e}")
            return False


def main():
    """Main entry point."""
    print("=" * 100)
    print("CWE INTEGRATION PIPELINE")
    print("=" * 100)
    
    try:
        processor = CWEtoNeo4j()
        
        # Step 1: Transform CWE JSON to RDF
        cwe_json_file = "data/cwe/samples/sample_cwe.json"
        cwe_graph = processor.transform_cwe(cwe_json_file)
        
        # Step 2: Connect to Neo4j
        print(f"\n[2] Connecting to Neo4j...")
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )
        
        # Step 3: Load CWE to Neo4j
        if not processor.load_cwe_to_neo4j(cwe_graph, driver):
            return 1
        
        # Step 4: Create CVE->CWE relationships
        if not processor.create_cve_cwe_relationships(driver):
            return 1
        
        # Step 5: Verify data
        if not processor.verify_data(driver):
            return 1
        
        driver.close()
        
        print("\n" + "=" * 100)
        print("SUCCESS: CWE INTEGRATION COMPLETE")
        print("=" * 100)
        print("\nNext Steps:")
        print("  1. Obtain full CWE dataset from MITRE")
        print("  2. Map all CVE->CWE relationships from NVD")
        print("  3. Proceed with CAPEC integration")
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
