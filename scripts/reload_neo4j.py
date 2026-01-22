#!/usr/bin/env python3
"""Clear Neo4j database and reload with corrected transformer."""

import sys
sys.path.insert(0, '.')

from src.etl.rdf_to_neo4j import RDFtoNeo4jTransformer
from src.config import neo4j_config
from neo4j import GraphDatabase
from pathlib import Path

print("=" * 80)
print("NEO4J RELOAD - WITH PLATFORMCONFIGURATION SUPPORT")
print("=" * 80)

# Connect to Neo4j
print(f"\n🔌 Connecting to Neo4j at {neo4j_config.uri}...")
try:
    driver = GraphDatabase.driver(
        neo4j_config.uri,
        auth=(neo4j_config.user, neo4j_config.password),
        encrypted=neo4j_config.encrypted
    )
    
    # Clear database
    print(f"\n🗑️  Clearing database...")
    with driver.session(database=neo4j_config.database) as session:
        session.run("MATCH (n) DETACH DELETE n")
        print(f"   ✓ Database cleared")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Load pipeline stages
pipeline_files = [
    'tmp/pipeline-stage1-cpe.ttl',
    'tmp/pipeline-stage2-cpematch.ttl',
    'tmp/pipeline-stage3-cve.ttl',
]

for file_path in pipeline_files:
    filepath = Path(file_path)
    
    if not filepath.exists():
        print(f"\n⏭️  SKIPPED: {file_path} (not found)")
        continue
    
    print(f"\n📤 Loading: {file_path}")
    print(f"   Size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # Transform
        transformer = RDFtoNeo4jTransformer(file_path, batch_size=5000)
        g = transformer.load_rdf()
        transformer.extract_nodes_and_relationships(g)
        
        # Load to Neo4j
        success = transformer.load_to_neo4j(driver)
        
        if not success:
            print(f"   ❌ Load failed")
            continue
        
        print(f"   ✅ Loaded successfully")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

# Final stats
print(f"\n📊 Final database statistics:")
try:
    with driver.session(database=neo4j_config.database) as session:
        result = session.run("""
            MATCH (n) RETURN DISTINCT labels(n)[0] as label, COUNT(n) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            label = record['label'] or '(untyped)'
            count = record['count']
            print(f"   {label}: {count}")
        
        result = session.run("MATCH (n) RETURN COUNT(n) as count")
        record = result.single()
        total_nodes = record['count'] if record else 0
        
        result = session.run("MATCH ()-[r]->() RETURN COUNT(r) as count")
        record = result.single()
        total_rels = record['count'] if record else 0
        
        print(f"\n   TOTAL: {total_nodes} nodes, {total_rels} relationships")
        
        # Check for PlatformConfiguration
        result = session.run("MATCH (n:PlatformConfiguration) RETURN COUNT(n) as count")
        record = result.single()
        config_count = record['count'] if record else 0
        
        result = session.run("MATCH ()-[r:MATCHES_PLATFORM]->() RETURN COUNT(r) as count")
        record = result.single()
        rel_count = record['count'] if record else 0
        
        print(f"\n   ✅ PlatformConfiguration: {config_count} nodes")
        print(f"   ✅ MATCHES_PLATFORM: {rel_count} relationships")
        
finally:
    driver.close()

print("\n" + "=" * 80)
print("✅ RELOAD COMPLETE")
print("=" * 80)
