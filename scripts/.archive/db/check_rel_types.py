#!/usr/bin/env python3
"""Check existing relationship types in database."""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(uri, auth=(user, password))
session = driver.session()

# Get all relationship types in database
result = session.run('CALL db.relationshipTypes()')
rel_types = [record['relationshipType'] for record in result]
print('Relationship types in database:')
for rel_type in sorted(rel_types):
    print(f'  - {rel_type}')

# Check existing Platform-Vulnerability relationships
result = session.run('MATCH (p:Platform)-[r]->(v:Vulnerability) RETURN DISTINCT type(r) as rel_type, count(r) as count')
print('\nExisting Platform→Vulnerability relationships:')
for record in result:
    print(f'  - {record["rel_type"]}: {record["count"]}')

# Check what edges exist from Platform
result = session.run('MATCH (p:Platform)-[r]->() RETURN DISTINCT type(r) as rel_type, count(r) as count')
print('\nAll Platform outgoing edges:')
for record in result:
    print(f'  - {record["rel_type"]}: {record["count"]}')

session.close()
driver.close()
