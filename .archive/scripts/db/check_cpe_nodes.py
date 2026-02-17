#!/usr/bin/env python3
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'kgcs4Neo4j'))
session = driver.session()

result = session.run('MATCH (p:Platform) RETURN p.uri LIMIT 10')
print("Sample CPE nodes in database:")
for i, record in enumerate(result, 1):
    print(f"{i}. {record['p.uri']}")

session.close()
driver.close()
