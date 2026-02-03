#!/usr/bin/env python3
"""
Test Neo4j data loading using sample RDF data
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load from .env.devel
env_devel_path = Path(__file__).parent / ".env.devel"
load_dotenv(env_devel_path)

from src.config import neo4j_config
from neo4j import GraphDatabase

def load_rdf_to_neo4j(ttl_file: str):
    """
    Load RDF data from Turtle file to Neo4j.
    
    This is a simplified example that creates nodes and relationships
    from parsed RDF triples.
    """
    
    print("\n" + "=" * 100)
    print("NEO4J DATA LOADING TEST")
    print("=" * 100)
    
    ttl_path = Path(__file__).parent / ttl_file
    if not ttl_path.exists():
        print(f"\n❌ File not found: {ttl_file}")
        return False
    
    try:
        # Parse RDF
        print(f"\n📂 Loading RDF data from: {ttl_file}")
        from rdflib import Graph
        
        g = Graph()
        g.parse(ttl_path, format='turtle')
        
        print(f"   ✓ Loaded {len(g)} triples")
        
        # Connect to Neo4j
        print(f"\n🔌 Connecting to Neo4j...")
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )
        
        # Create sample nodes from RDF
        print(f"\n📊 Transforming RDF to Neo4j nodes...")
        
        with driver.session(database=neo4j_config.database) as session:
            
            # Clear existing test data (optional)
            # session.run("MATCH (n) DETACH DELETE n")
            
            # Create constraint on CPE IDs
            try:
                session.run("""
                    CREATE CONSTRAINT platform_cpe_unique IF NOT EXISTS
                    FOR (p:Platform) REQUIRE p.cpe IS UNIQUE
                """)
                print("   ✓ CPE uniqueness constraint created")
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"   ⚠ Constraint warning: {e}")
            
            # Parse RDF subjects and create nodes
            subjects = set()
            for s, p, o in g:
                subjects.add(str(s))
            
            print(f"   ✓ Found {len(subjects)} unique subjects")
            
            # Create a few sample Platform nodes from RDF
            cpe_count = 0
            for subject in list(subjects)[:10]:  # Sample first 10
                subject_str = str(subject)
                if 'cpe' in subject_str.lower():
                    # Extract CPE string
                    cpe = subject_str.split('/')[-1]
                    session.run("""
                        CREATE (p:Platform {cpe: $cpe, uri: $uri})
                    """, cpe=cpe, uri=subject_str)
                    cpe_count += 1
            
            if cpe_count > 0:
                print(f"   ✓ Created {cpe_count} Platform nodes")
            
            # Get database stats
            result = session.run("""
                MATCH (n) RETURN DISTINCT labels(n) as labels, COUNT(n) as count
            """)
            
            print(f"\n📈 Database Statistics:")
            for record in result:
                labels = record['labels'] or ['(untyped)']
                count = record['count']
                label_str = ':'.join(labels) if labels else '(untyped)'
                print(f"   {label_str}: {count} nodes")
            
            # Get total count
            result = session.run("MATCH (n) RETURN COUNT(n) as count")
            record = result.single()
            total = record['count'] if record else 0
            print(f"\n   Total nodes: {total}")
        
        driver.close()
        print("\n" + "=" * 100)
        print("✅ NEO4J DATA LOADING TEST PASSED")
        print("=" * 100)
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing package: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load sample CPE/CVE data
    success = load_rdf_to_neo4j("tmp/phase3_combined.ttl")
    sys.exit(0 if success else 1)
