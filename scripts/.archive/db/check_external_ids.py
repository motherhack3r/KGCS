#!/usr/bin/env python3
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'kgcs4Neo4j'))
session = driver.session()

result = session.run('MATCH (ap:AttackPattern) RETURN ap.external_id ORDER BY ap.external_id')
patterns = [record['ap.external_id'] for record in result]
print(f'AttackPattern nodes: {patterns}')

result = session.run('MATCH (t:Technique) RETURN t.external_id ORDER BY t.external_id')
techniques = [record['t.external_id'] for record in result]
print(f'Technique nodes: {techniques}')

session.close()
driver.close()
