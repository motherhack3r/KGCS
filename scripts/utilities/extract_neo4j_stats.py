#!/usr/bin/env python3
"""
Extract comprehensive statistics from Neo4j KGCS graph.

Usage:
    python scripts/utilities/extract_neo4j_stats.py [--output artifacts/neo4j-stats.json]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Handle Windows encoding issue with emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
# sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Add project root to Python path to enable src imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import neo4j_config


def get_most_recently_updated_database(driver) -> Optional[str]:
    """Get the most recently updated database from Neo4j."""
    try:
        with driver.session() as session:
            # Try to get database metadata
            result = session.run("""
                SHOW DATABASES
                YIELD name, currentStatus
                WHERE currentStatus = 'online'
                RETURN name
                ORDER BY name DESC
            """)
            
            databases = [record['name'] for record in result]
            
            if not databases:
                return None
            
            # If neo4j is in the list, use that as default, otherwise use first
            if 'neo4j' in databases:
                return 'neo4j'
            
            return databases[0]
    except Exception:
        # Fallback to default if metadata query fails
        return None


def get_neo4j_stats(driver, database: Optional[str] = None) -> Dict[str, Any]:
    """Extract comprehensive statistics from Neo4j."""
    target_db = database or neo4j_config.database
    stats = {
        "nodes": {},
        "relationships": {},
        "totals": {},
        "causal_chain_analysis": {},
        "cross_standard_links": {},
        "quality_metrics": {},
    }
    try:
        with driver.session(database=target_db) as session:
            # Node counts by label
            print("Extracting node statistics...")
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, COUNT(n) as count
                ORDER BY count DESC
            """)
            total_nodes = 0
            for record in result:
                label = record['label'] or '(untyped)'
                count = record['count']
                stats["nodes"][label] = count
                total_nodes += count

            stats["totals"]["nodes"] = total_nodes

            # Relationship counts by type
            print("Extracting relationship statistics...")
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, COUNT(r) as count
                ORDER BY count DESC
            """)
            total_rels = 0
            for record in result:
                rel_type = record['rel_type'] or '(untyped)'
                count = record['count']
                stats["relationships"][rel_type] = count
                total_rels += count

            stats["totals"]["relationships"] = total_rels

            # Causal chain analysis
            print("Analyzing causal chain...")

            # CVE → CWE links
            result = session.run("""
                MATCH (cve:Vulnerability)-[r:CAUSED_BY]->(cwe:Weakness)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["causal_chain_analysis"]["cve_to_cwe"] = record['count'] if record else 0

            # CWE → CAPEC links
            result = session.run("""
                MATCH (cwe:Weakness)-[r:EXPLOITED_BY]->(capec:AttackPattern)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["causal_chain_analysis"]["cwe_to_capec"] = record['count'] if record else 0

            # CAPEC → Technique links (breakdown by Technique vs SubTechnique)
            predicates = ['IMPLEMENTED_AS','IMPLEMENTS','IMPLEMENTS_AS','implemented_as','implements']
            pred_list = ",".join([f"'{p}'" for p in predicates])

            # Total (any Technique or SubTechnique)
            result = session.run(f"""
                MATCH (capec:AttackPattern)-[r]->(t)
                WHERE type(r) IN [{pred_list}] AND (t:Technique OR t:SubTechnique)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            total_capec_to_tech = record['count'] if record else 0

            # Technique only
            result = session.run(f"""
                MATCH (capec:AttackPattern)-[r]->(tech:Technique)
                WHERE type(r) IN [{pred_list}]
                RETURN COUNT(r) as count
            """)
            record = result.single()
            tech_count = record['count'] if record else 0

            # SubTechnique only
            result = session.run(f"""
                MATCH (capec:AttackPattern)-[r]->(sub:SubTechnique)
                WHERE type(r) IN [{pred_list}]
                RETURN COUNT(r) as count
            """)
            record = result.single()
            subtech_count = record['count'] if record else 0

            stats["causal_chain_analysis"]["capec_to_technique"] = total_capec_to_tech
            stats["causal_chain_analysis"]["capec_to_technique_breakdown"] = {
                "technique": tech_count,
                "subtechnique": subtech_count,
            }

            # Include a small sample of CAPEC -> Technique/SubTechnique mappings for inspection
            result = session.run(f"""
                MATCH (capec:AttackPattern)-[r]->(t)
                WHERE type(r) IN [{pred_list}] AND (t:Technique OR t:SubTechnique)
                RETURN capec.capecId AS capecId, type(r) AS relType, labels(t)[0] AS targetLabel, t.attackTechniqueId AS attackId
                LIMIT 20
            """)
            samples = []
            for record in result:
                samples.append({
                    "capecId": record.get('capecId'),
                    "relType": record.get('relType'),
                    "targetLabel": record.get('targetLabel'),
                    "attackId": record.get('attackId'),
                })
            stats["causal_chain_analysis"]["capec_to_technique_samples"] = samples

            # CVE → Platform links
            result = session.run("""
                MATCH (cve:Vulnerability)-[r:AFFECTS]->(config:PlatformConfiguration)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["causal_chain_analysis"]["cve_to_platform_config"] = record['count'] if record else 0

            # Technique → Defense links
            result = session.run("""
                MATCH (tech:Technique)-[r:MITIGATED_BY]->(defense:DefensiveTechnique)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["cross_standard_links"]["technique_to_defense"] = record['count'] if record else 0

            # Technique → Detection links
            result = session.run("""
                MATCH (tech:Technique)-[r:DETECTED_BY]->(car:DetectionAnalytic)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["cross_standard_links"]["technique_to_detection"] = record['count'] if record else 0

            # Technique → Deception links
            result = session.run("""
                MATCH (tech:Technique)-[r:COUNTERED_BY]->(shield:DeceptionTechnique)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["cross_standard_links"]["technique_to_deception"] = record['count'] if record else 0

            # Technique → Engagement links
            result = session.run("""
                MATCH (tech:Technique)-[r:DISRUPTED_BY]->(engage:EngagementConcept)
                RETURN COUNT(r) as count
            """)
            record = result.single()
            stats["cross_standard_links"]["technique_to_engagement"] = record['count'] if record else 0

            # Quality metrics: orphaned nodes (no relationships)
            print("Analyzing data quality...")
            result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN DISTINCT labels(n) as labels, COUNT(n) as count
            """)
            orphaned = {}
            for record in result:
                labels = record['labels'] or ['(untyped)']
                count = record['count']
                label_str = ':'.join(labels) if labels else '(untyped)'
                orphaned[label_str] = count

            stats["quality_metrics"]["orphaned_nodes"] = orphaned

            # CVSS version coverage
            print("Analyzing CVSS coverage...")
            cvss_versions = {}
            for version in ['v2.0', 'v3.1', 'v4.0']:
                result = session.run("""
                    MATCH (score:Score)
                    WHERE score.cvssVersion = $version
                    RETURN COUNT(score) as count
                """, version=version)
                record = result.single()
                cvss_versions[version] = record['count'] if record else 0

            stats["quality_metrics"]["cvss_versions"] = cvss_versions

            # Platform/PlatformConfiguration breakdown
            print("Analyzing platform coverage...")
            result = session.run("""
                MATCH (platform:Platform)
                OPTIONAL MATCH (platform)<-[r:INCLUDES]-(config:PlatformConfiguration)
                RETURN 
                    COUNT(DISTINCT platform) as total_platforms,
                    COUNT(DISTINCT config) as total_configs
            """)
            record = result.single()
            if record:
                stats["quality_metrics"]["total_platforms"] = record['total_platforms'] or 0
                stats["quality_metrics"]["total_configs"] = record['total_configs'] or 0

            # Technique coverage by tactic
            print("Analyzing technique coverage...")
            result = session.run("""
                MATCH (tactic:Tactic)
                OPTIONAL MATCH (tactic)<-[r:PART_OF]-(tech:Technique)
                RETURN 
                    tactic.tacticId as tactic_id,
                    COUNT(DISTINCT tech) as technique_count
                ORDER BY technique_count DESC
            """)
            tactics = {}
            for record in result:
                tactic_id = record['tactic_id'] or 'unknown'
                tactics[tactic_id] = record['technique_count'] or 0

            stats["quality_metrics"]["techniques_by_tactic"] = tactics

            # Relationship breakdown by source/target labels (UNWIND labels)
            print("Analyzing relationship patterns...")
            result = session.run("""
                MATCH (a)-[r]->(b)
                UNWIND labels(a) AS Label_Start
                UNWIND labels(b) AS Label_End
                RETURN
                  type(r) AS RelationshipType,
                  Label_Start,
                  Label_End,
                  count([Label_Start, Label_End]) AS Count
                ORDER BY Count DESC
                LIMIT 30
            """)
            rel_patterns = []
            for record in result:
                rel_patterns.append({
                    "relationship": record['RelationshipType'] or 'unknown',
                    "source": record['Label_Start'] or 'untyped',
                    "target": record['Label_End'] or 'untyped',
                    "count": record['Count'] or 0,
                })

            stats["quality_metrics"]["relationship_patterns"] = rel_patterns

            # Coverage analysis: what percentage of entities are linked?
            print("Analyzing cross-standard linkage...")

            # Vulnerabilities with CWE mappings
            result = session.run("""
                MATCH (cve:Vulnerability)
                OPTIONAL MATCH (cve)-[r:CAUSED_BY]->(cwe:Weakness)
                WITH COUNT(DISTINCT cve) as total_cves, COUNT(DISTINCT r) as cves_with_cwe
                RETURN total_cves, cves_with_cwe
            """)
            record = result.single()
            if record:
                total_cves = record['total_cves'] or 0
                cves_with_cwe = record['cves_with_cwe'] or 0
                coverage_pct = (cves_with_cwe / total_cves * 100) if total_cves > 0 else 0
                stats["quality_metrics"]["cve_cwe_coverage"] = {
                    "total_cves": total_cves,
                    "cves_with_cwe": cves_with_cwe,
                    "coverage_percent": round(coverage_pct, 2),
                }

            # Techniques with defenses
            result = session.run("""
                MATCH (tech:Technique)
                OPTIONAL MATCH (tech)-[r1:MITIGATED_BY|DETECTED_BY|COUNTERED_BY]-(defense)
                WITH COUNT(DISTINCT tech) as total_techs, COUNT(DISTINCT defense) as techs_with_defense
                RETURN total_techs, techs_with_defense
            """)
            record = result.single()
            if record:
                total_techs = record['total_techs'] or 0
                techs_with_defense = record['techs_with_defense'] or 0
                coverage_pct = (techs_with_defense / total_techs * 100) if total_techs > 0 else 0
                stats["quality_metrics"]["technique_defense_coverage"] = {
                    "total_techniques": total_techs,
                    "techniques_with_defense": techs_with_defense,
                    "coverage_percent": round(coverage_pct, 2),
                }

            print("\n✅ Statistics extracted successfully")
            return stats

    except Exception as e:
        print(f"❌ Error extracting statistics: {e}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description="Extract Neo4j KGCS graph statistics")
    parser.add_argument(
        "--output",
        default="artifacts/neo4j-stats.json",
        help="Output JSON file for statistics"
    )
    parser.add_argument(
        "--db",
        help="Override Neo4j database name (default: most recently updated)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )
    parser.add_argument(
        "--list-databases",
        action="store_true",
        help="List available databases and exit"
    )
    args = parser.parse_args()

    from neo4j import GraphDatabase

    uri = neo4j_config.uri
    user = neo4j_config.user
    password = neo4j_config.password

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        # List databases if requested
        if args.list_databases:
            print("Available databases:")
            with driver.session() as session:
                try:
                    result = session.run("SHOW DATABASES YIELD name, currentStatus")
                    for record in result:
                        print(f"  - {record['name']} ({record['currentStatus']})")
                except Exception as e:
                    print(f"  Could not list databases: {e}")
            driver.close()
            return 0

        # Determine which database to use
        target_db = args.db
        if not target_db:
            print("Detecting most recently updated database...")
            detected_db = get_most_recently_updated_database(driver)
            if detected_db:
                target_db = detected_db
                print(f"✅ Using database: {target_db}\n")
            else:
                target_db = neo4j_config.database
                print(f"⚠️  Could not auto-detect, using configured database: {target_db}\n")

        # Extract stats
        stats = get_neo4j_stats(driver, target_db)

        # Write to output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2 if args.pretty else None)
        print(f"\n📊 Statistics written to: {output_path}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
