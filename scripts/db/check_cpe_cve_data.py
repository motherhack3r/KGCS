#!/usr/bin/env python3
"""Check CPE and CVE data structures and identify proper relationship type."""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(uri, auth=(user, password))
session = driver.session()

# Check all relationship types
print("All relationship types in database:")
result = session.run('CALL db.relationshipTypes()')
rel_types = [record['relationshipType'] for record in result]
for rel_type in sorted(rel_types):
    print(f'  - {rel_type}')

# Check if we can create new relationship types
print("\n\nTesting relationship creation:")

# Try to create a test relationship
try:
    result = session.run("""
        MATCH (p:Platform) LIMIT 1
        MATCH (v:Vulnerability) LIMIT 1
        CREATE (p)-[r:AFFECTS]->(v)
        RETURN type(r) as rel_type
    """)
    record = result.single()
    if record:
        print(f"✓ Can create relationship: {record['rel_type']}")
    
    # Clean up test
    session.run("MATCH (p:Platform)-[r:AFFECTS]->(v:Vulnerability) DELETE r")
except Exception as e:
    print(f"✗ Cannot create relationship: {e}")

session.close()
driver.close()
