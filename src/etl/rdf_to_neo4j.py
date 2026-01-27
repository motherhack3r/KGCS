#!/usr/bin/env python3
"""
RDF-to-Neo4j Transformer for KGCS

Transforms RDF triples to Neo4j nodes and relationships, implementing
the causal chain: CPE -> CVE -> CWE -> CAPEC -> ATT&CK -> {D3FEND, CAR, SHIELD, ENGAGE}
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

# Load configuration
env_devel_path = Path(__file__).parent.parent.parent / ".env.devel"
load_dotenv(env_devel_path)

from src.config import neo4j_config
from rdflib import Graph, Namespace, RDF, Literal, URIRef
from rdflib.term import Node
from datetime import datetime


@dataclass
class NodeData:
    """Represents a node to be created in Neo4j."""
    label: str
    uri: str
    properties: Dict[str, Any]


@dataclass
class RelationshipData:
    """Represents a relationship to be created in Neo4j."""
    source_uri: str
    target_uri: str
    relationship_type: str
    properties: Dict[str, Any]


class RDFtoNeo4jTransformer:
    """
    Transforms RDF data to Neo4j nodes and relationships.
    
    Handles core KGCS classes and relationships in the sec/core namespace.
    """
    
    def __init__(self, ttl_file: str, batch_size: int = 1000):
        """Initialize transformer with RDF file."""
        self.ttl_file = Path(ttl_file)
        self.batch_size = batch_size
        
        # RDF namespaces
        self.sec_ns = Namespace("https://example.org/sec/core#")
        self.sec_ns_str = str(self.sec_ns)
        
        # Tracking
        self.nodes: Dict[str, NodeData] = {}
        self.relationships: List[RelationshipData] = []
        self.stats = {
            'labels': defaultdict(int),
            'relationships': 0,
        }
        
    def load_rdf(self) -> Graph:
        """Load RDF graph from Turtle file."""
        print(f"\nLoading RDF from {self.ttl_file.name}...")
        g = Graph()
        g.parse(self.ttl_file, format='turtle')
        print(f"   * Loaded {len(g)} triples")
        return g
    
    def extract_nodes_and_relationships(self, g: Graph, verbose: bool = True) -> None:
        """Extract nodes and relationships from RDF graph."""
        if verbose:
            print(f"\nExtracting nodes and relationships...")
        core_types_by_subject: Dict[Node, List[str]] = {}
        for subject in g.subjects(RDF.type, None):
            type_labels = []
            for obj in g.objects(subject, RDF.type):
                if isinstance(obj, URIRef) and str(obj).startswith(self.sec_ns_str):
                    type_labels.append(self._local_name(obj))

            if type_labels:
                core_types_by_subject[subject] = sorted(set(type_labels))

        for subject, labels in core_types_by_subject.items():
            self._extract_node(subject, g, labels)

        for subject, predicate, obj in g:
            if isinstance(obj, Literal):
                continue
            if predicate == RDF.type:
                continue
            if not self._is_core_uri(predicate):
                continue

            subject_uri = str(subject)
            target_uri = str(obj)
            if subject_uri not in self.nodes or target_uri not in self.nodes:
                continue

            predicate_name = self._local_name(predicate)
            rel_type = self._predicate_to_relationship(predicate_name)

            if rel_type in ['TYPE', 'VALUE', 'LABEL']:
                continue

            self.relationships.append(RelationshipData(
                source_uri=subject_uri,
                target_uri=target_uri,
                relationship_type=rel_type,
                properties={}
            ))
            self.stats['relationships'] += 1

        if verbose:
            for label, count in sorted(self.stats['labels'].items()):
                print(f"   * {label}: {count}")
            print(f"   * Relationships: {self.stats['relationships']}")
    
    def _extract_node(self, subject, g: Graph, labels: List[str]) -> None:
        """Extract node properties for any core class."""
        uri = str(subject)
        properties = {}

        for predicate, obj in g.predicate_objects(subject):
            if predicate == RDF.type:
                continue
            if isinstance(obj, Literal):
                prop_name = self._local_name(predicate)
                value = self._parse_literal(obj)
                if value is not None:
                    properties[prop_name] = value

        primary_label = labels[0]
        if len(labels) > 1:
            properties['rdfTypes'] = labels

        self.nodes[uri] = NodeData(label=primary_label, uri=uri, properties=properties)
        self.stats['labels'][primary_label] += 1
    
    def _parse_literal(self, obj):
        """Parse RDF literal to Python value with proper type conversion."""
        if isinstance(obj, Literal):
            # Get the datatype
            datatype = obj.datatype
            value = obj.toPython()
            
            # Handle XSD datatypes
            if datatype:
                datatype_str = str(datatype)
                
                # Boolean
                if 'boolean' in datatype_str:
                    return isinstance(value, bool) and value or str(value).lower() in ('true', '1', 'yes')
                
                # Numeric types
                if 'integer' in datatype_str or 'int' in datatype_str:
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return value
                
                if 'float' in datatype_str or 'double' in datatype_str:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return value
                
                # DateTime types
                if any(x in datatype_str for x in ['dateTime', 'datetime', 'date', 'time']):
                    if isinstance(value, datetime):
                        return value.isoformat()
                    return str(value)
            
            # Default: return toPython() result
            return value
        
        elif isinstance(obj, str):
            return obj
        else:
            return str(obj)
    
    def _predicate_to_relationship(self, predicate_name: str) -> str:
        """Convert RDF predicate name to Neo4j relationship type (UPPER_SNAKE_CASE)."""
        # Convert camelCase or snake_case to UPPER_SNAKE_CASE
        import re
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', predicate_name)
        # Insert underscore before uppercase in sequences
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()

    def _local_name(self, uri: Node) -> str:
        """Return the local name for a URIRef."""
        return str(uri).split('#')[-1]

    def _is_core_uri(self, uri: Node) -> bool:
        """Check if a URIRef is in the core namespace."""
        return str(uri).startswith(self.sec_ns_str)
    
    def load_to_neo4j(self, driver, include_indexes: bool = True, include_stats: bool = True) -> bool:
        """Load nodes and relationships into Neo4j."""
        print(f"\nLoading to Neo4j...")
        
        try:
            with driver.session(database=neo4j_config.database) as session:
                if include_indexes:
                    self._create_indexes(session)
                self._load_nodes_batch(session)
                self._load_relationships(session)
                if include_stats:
                    self._get_database_stats(session)
            return True
            
        except Exception as e:
            print(f"\nError loading to Neo4j: {e}")
            return False
    
    def _create_indexes(self, session) -> None:
        """Create indexes in Neo4j."""
        print(f"   Creating indexes...")
        
        constraints = [
            ("Platform", "cpeNameId", "platform_cpe_name_id_unique"),
            ("Platform", "cpeUri", "platform_cpe_uri_unique"),
            ("PlatformConfiguration", "matchCriteriaId", "platform_config_match_id_unique"),
            ("Vulnerability", "cveId", "vulnerability_cve_id_unique"),
            ("Weakness", "cweId", "weakness_cwe_id_unique"),
            ("AttackPattern", "capecId", "attackpattern_capec_id_unique"),
            ("Technique", "attackTechniqueId", "technique_attack_id_unique"),
            ("SubTechnique", "attackTechniqueId", "subtechnique_attack_id_unique"),
            ("Tactic", "tacticId", "tactic_id_unique"),
            ("DefensiveTechnique", "d3fendId", "deftech_d3fend_id_unique"),
            ("DetectionAnalytic", "carId", "car_id_unique"),
            ("DeceptionTechnique", "shieldId", "deception_shield_id_unique"),
            ("EngagementConcept", "engageId", "engage_id_unique"),
            ("Reference", "referenceUrl", "reference_url_unique"),
            ("Score", "uri", "score_uri_unique"),
        ]
        
        for label, property_name, constraint_name in constraints:
            try:
                session.run(f"""
                    CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                    FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE
                """)
            except Exception as e:
                if "already exists" not in str(e):
                    pass
        
        print(f"   * Indexes created")
    
    def _load_nodes_batch(self, session) -> None:
        """Load nodes to Neo4j in batches."""
        print(f"   Loading {len(self.nodes)} nodes...")
        
        batch = []
        for i, (uri, node) in enumerate(self.nodes.items(), 1):
            batch.append(node)
            
            if len(batch) >= self.batch_size or i == len(self.nodes):
                self._insert_node_batch(session, batch)
                batch = []
                if i % (self.batch_size * 10) == 0:
                    print(f"      Progress: {i}/{len(self.nodes)} nodes")
        
        print(f"   * All {len(self.nodes)} nodes loaded")
    
    def _insert_node_batch(self, session, nodes: List[NodeData]) -> None:
        """Insert batch of nodes."""
        by_label = defaultdict(list)
        for node in nodes:
            by_label[node.label].append({
                'uri': node.uri,
                'properties': node.properties
            })
        
        for label, node_list in by_label.items():
            cypher = f"UNWIND $nodes as node MERGE (n:`{label}` {{uri: node.uri}}) SET n += node.properties"
            session.run(cypher, nodes=node_list)
    
    def _load_relationships(self, session) -> None:
        """Load relationships to Neo4j."""
        if not self.relationships:
            return
        
        print(f"   Loading {len(self.relationships)} relationships...")
        
        batch = []
        for i, rel in enumerate(self.relationships, 1):
            batch.append(rel)
            
            if len(batch) >= self.batch_size or i == len(self.relationships):
                self._insert_relationship_batch(session, batch)
                batch = []
                if i % (self.batch_size * 10) == 0:
                    print(f"      Progress: {i}/{len(self.relationships)} relationships")
        
        print(f"   * All relationships loaded")
    
    def _insert_relationship_batch(self, session, rels: List[RelationshipData]) -> None:
        """Insert batch of relationships."""
        by_type = defaultdict(list)
        for rel in rels:
            by_type[rel.relationship_type].append({
                'sourceUri': rel.source_uri,
                'targetUri': rel.target_uri,
                'properties': rel.properties
            })
        
        for rel_type, rel_list in by_type.items():
            cypher = f"UNWIND $rels as rel MATCH (source {{uri: rel.sourceUri}}) MATCH (target {{uri: rel.targetUri}}) MERGE (source)-[r:`{rel_type}`]->(target) SET r += rel.properties"
            try:
                session.run(cypher, rels=rel_list)
            except Exception:
                pass
    
    def _get_database_stats(self, session) -> None:
        """Get and print database statistics."""
        print(f"\nDatabase Statistics:")
        
        result = session.run("""
            MATCH (n) RETURN DISTINCT labels(n) as labels, COUNT(n) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            labels = record['labels'] or ['(untyped)']
            count = record['count']
            label_str = ':'.join(labels) if labels else '(untyped)'
            print(f"   {label_str}: {count}")
        
        result = session.run("MATCH (n) RETURN COUNT(n) as count")
        record = result.single()
        total_nodes = record['count'] if record else 0
        
        result = session.run("MATCH ()-[r]->() RETURN COUNT(r) as count")
        record = result.single()
        total_rels = record['count'] if record else 0
        
        print(f"\n   TOTAL: {total_nodes} nodes, {total_rels} relationships")


def _write_chunk_file(lines: List[str], idx: int) -> str:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=f'.chunk{idx}.ttl')
    os.close(tmp_fd)
    with open(tmp_path, 'w', encoding='utf-8') as tf:
        tf.write('@prefix dcterms: <http://purl.org/dc/terms/> .\n')
        tf.write('@prefix sec: <https://example.org/sec/core#> .\n')
        tf.write('@prefix ex: <https://example.org/> .\n\n')
        tf.write('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n')
        tf.write('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n')
        for line in lines:
            tf.write(line)
    return tmp_path


def chunk_ttl_file(data_path: str, chunk_size: int) -> Tuple[List[Tuple[int, str]], int]:
    total_triples = 0
    idx = 0
    chunk_files: List[Tuple[int, str]] = []
    current_subject = None
    current_chunk_subjects = set()
    chunk_lines: List[str] = []

    with open(data_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            if not line.strip():
                continue
            if line.startswith('@prefix') or line.startswith('PREFIX') or line.startswith('#'):
                continue
            parts = line.split(None, 1)
            if not parts:
                continue
            subj = parts[0]
            if current_subject is None:
                current_subject = subj
            if subj != current_subject:
                if subj not in current_chunk_subjects:
                    current_chunk_subjects.add(subj)
                if len(current_chunk_subjects) >= chunk_size:
                    idx += 1
                    tmp_path = _write_chunk_file(chunk_lines, idx)
                    chunk_files.append((idx, tmp_path))
                    chunk_lines = []
                    current_chunk_subjects = set()
                    current_subject = subj
            chunk_lines.append(line)
            total_triples += 1

    if chunk_lines:
        idx += 1
        tmp_path = _write_chunk_file(chunk_lines, idx)
        chunk_files.append((idx, tmp_path))

    return chunk_files, total_triples


def _dry_run_chunk(tmp_path: str) -> Dict[str, Any]:
    g = Graph()
    g.parse(tmp_path, format='turtle')
    transformer = RDFtoNeo4jTransformer(tmp_path)
    transformer.extract_nodes_and_relationships(g, verbose=False)
    return {
        'labels': dict(transformer.stats['labels']),
        'relationships': transformer.stats['relationships'],
    }


def _merge_label_counts(target: Dict[str, int], delta: Dict[str, int]) -> None:
    for key, value in delta.items():
        target[key] = target.get(key, 0) + value


def _update_progress(completed: int, total: int, worker_id: int | None = None, progress_newline: bool = False) -> None:
    percent = (completed / total) * 100 if total else 100
    bar_width = 20
    filled = int(bar_width * (percent / 100)) if total else bar_width
    bar = "=" * filled + "." * (bar_width - filled)
    message = f"Processed {completed}/{total} chunks ({percent:0.1f}%) [{bar}]"
    if worker_id is not None:
        message = f"{message} (worker {worker_id})"
    if progress_newline:
        print(message, flush=True)
    else:
        print(f"\r{message}", end='', flush=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RDF-to-Neo4j loader")
    parser.add_argument("--ttl", required=False, default="tmp/phase3_combined.ttl", help="Input Turtle file")
    parser.add_argument("--batch-size", type=int, default=1000, help="Neo4j batch size")
    parser.add_argument("--dry-run", action="store_true", help="Parse and extract without loading to Neo4j")
    parser.add_argument("--chunk-size", type=int, default=0, help="Unique subjects per chunk (0 = load whole file)")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers for dry-run only")
    parser.add_argument("--progress-newline", action="store_true", help="Print progress updates as new lines")
    args = parser.parse_args()

    print("=" * 100)
    print("RDF-TO-NEO4J TRANSFORMATION")
    print("=" * 100)
    
    try:
        if args.chunk_size and args.chunk_size > 0:
            chunk_files, total_triples = chunk_ttl_file(args.ttl, args.chunk_size)
            total_chunks = len(chunk_files)
            completed = 0
            aggregate_labels: Dict[str, int] = {}
            aggregate_rels = 0

            if args.dry_run:
                workers = max(args.workers or 1, 1)
                if workers > 1:
                    with ProcessPoolExecutor(max_workers=workers) as executor:
                        futures = [executor.submit(_dry_run_chunk, tmp_path) for _, tmp_path in chunk_files]
                        for future in as_completed(futures):
                            result = future.result()
                            completed += 1
                            worker_id = ((completed - 1) % workers) + 1
                            _update_progress(completed, total_chunks, worker_id, args.progress_newline)
                            _merge_label_counts(aggregate_labels, result.get('labels', {}))
                            aggregate_rels += result.get('relationships', 0)
                else:
                    for chunk_idx, tmp_path in chunk_files:
                        result = _dry_run_chunk(tmp_path)
                        completed += 1
                        _update_progress(completed, total_chunks, ((chunk_idx - 1) % workers) + 1, args.progress_newline)
                        _merge_label_counts(aggregate_labels, result.get('labels', {}))
                        aggregate_rels += result.get('relationships', 0)

                if total_chunks:
                    print()
                print("\nDry run enabled — skipping Neo4j load.")
            else:
                if args.workers and args.workers > 1:
                    print("\nNote: workers > 1 is ignored for Neo4j load to avoid write contention.")

                from neo4j import GraphDatabase

                print(f"\nConnecting to Neo4j at {neo4j_config.uri}...")
                driver = GraphDatabase.driver(
                    neo4j_config.uri,
                    auth=(neo4j_config.user, neo4j_config.password),
                    encrypted=neo4j_config.encrypted
                )

                with driver.session(database=neo4j_config.database) as session:
                    transformer = RDFtoNeo4jTransformer(args.ttl, batch_size=args.batch_size)
                    transformer._create_indexes(session)

                for chunk_idx, tmp_path in chunk_files:
                    transformer = RDFtoNeo4jTransformer(tmp_path, batch_size=args.batch_size)
                    g = transformer.load_rdf()
                    transformer.extract_nodes_and_relationships(g, verbose=False)
                    success = transformer.load_to_neo4j(driver, include_indexes=False, include_stats=False)
                    if not success:
                        driver.close()
                        return 1
                    completed += 1
                    _update_progress(completed, total_chunks, None, args.progress_newline)
                    _merge_label_counts(aggregate_labels, dict(transformer.stats['labels']))
                    aggregate_rels += transformer.stats['relationships']

                driver.close()
                if total_chunks:
                    print()

            for _, tmp_path in chunk_files:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            print("\nSummary:")
            for label, count in sorted(aggregate_labels.items()):
                print(f"   * {label}: {count}")
            print(f"   * Relationships: {aggregate_rels}")
            print(f"   * Triples scanned: {total_triples}")

            if args.dry_run:
                return 0

            print("\n" + "=" * 100)
            print("SUCCESS: RDF-TO-NEO4J TRANSFORMATION COMPLETE")
            print("=" * 100)
            return 0

        transformer = RDFtoNeo4jTransformer(args.ttl, batch_size=args.batch_size)
        g = transformer.load_rdf()
        transformer.extract_nodes_and_relationships(g)

        if args.dry_run:
            print("\nDry run enabled — skipping Neo4j load.")
            return 0

        from neo4j import GraphDatabase

        print(f"\nConnecting to Neo4j at {neo4j_config.uri}...")
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )

        success = transformer.load_to_neo4j(driver)
        driver.close()

        if success:
            print("\n" + "=" * 100)
            print("SUCCESS: RDF-TO-NEO4J TRANSFORMATION COMPLETE")
            print("=" * 100)
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
