#!/usr/bin/env python3
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'kgcs4Neo4j'))
session = driver.session()

result = session.run('MATCH (p:Platform) RETURN properties(p) LIMIT 5')
print("Sample CPE node properties:")
for i, record in enumerate(result, 1):
    props = record[0]
    print(f"{i}. {props}")

session.close()
driver.close()
