#!/usr/bin/env python3
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'kgcs4Neo4j'))
session = driver.session()

result = session.run('MATCH (t:Technique) RETURN count(t) as count')
techniques = result.single()['count']
print(f'Techniques: {techniques}')

result = session.run('MATCH (ap:AttackPattern) RETURN count(ap) as count')
attack_patterns = result.single()['count']
print(f'AttackPatterns: {attack_patterns}')

session.close()
driver.close()
