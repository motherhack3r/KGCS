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
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load configuration
env_devel_path = project_root / ".env.devel"
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
    source_label: str | None = None
    target_label: str | None = None


class RDFtoNeo4jTransformer:
    """
    Transforms RDF data to Neo4j nodes and relationships.
    
    Handles core KGCS classes and relationships in the sec/core namespace.
    """
    
    def __init__(
        self,
        ttl_file: str,
        batch_size: int = 1000,
        parse_heartbeat_seconds: float = 0,
        relationship_batch_size: int | None = None,
        skip_deprecates: bool = False,
    ):
        """Initialize transformer with RDF file."""
        self.ttl_file = Path(ttl_file)
        self.batch_size = batch_size
        self.relationship_batch_size = relationship_batch_size or batch_size
        self.parse_heartbeat_seconds = parse_heartbeat_seconds
        self.skip_deprecates = skip_deprecates
        
        # RDF namespaces
        self.sec_ns = Namespace("https://example.org/sec/core#")
        self.sec_ns_str = str(self.sec_ns)
        
        # Tracking
        self.nodes: Dict[str, NodeData] = {}
        self.relationships: List[RelationshipData] = []
        self.stats = {
            'labels': defaultdict(int),
            'relationships': 0,
            'rel_types': defaultdict(int),
        }
        self.merge_keys = {
            "Platform": "cpeUri",
            "PlatformConfiguration": "matchCriteriaId",
            "Vulnerability": "cveId",
            "Weakness": "cweId",
            "AttackPattern": "capecId",
            "Technique": "attackTechniqueId",
            "SubTechnique": "attackTechniqueId",
            "Tactic": "tacticId",
            "DefensiveTechnique": "d3fendId",
            "DetectionAnalytic": "carId",
            "DeceptionTechnique": "shieldId",
            "EngagementConcept": "engageId",
            "Reference": "referenceUrl",
            "Score": "uri",
        }
        
    def load_rdf(self) -> Graph:
        """Load RDF graph from Turtle file."""
        print(f"\nLoading RDF from {self.ttl_file.name}...")
        g = Graph()
        start = time.perf_counter()

        if self.parse_heartbeat_seconds and self.parse_heartbeat_seconds > 0:
            stop_event = threading.Event()

            def heartbeat():
                elapsed_ticks = 0
                while not stop_event.wait(self.parse_heartbeat_seconds):
                    elapsed_ticks += self.parse_heartbeat_seconds
                    print(f"   ... parsing ({elapsed_ticks:0.0f}s elapsed) ...", flush=True)

            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            try:
                g.parse(self.ttl_file, format='turtle')
            finally:
                stop_event.set()
                thread.join()
        else:
            g.parse(self.ttl_file, format='turtle')

        elapsed = time.perf_counter() - start
        print(f"   * Loaded {len(g)} triples in {elapsed:0.1f}s")
        return g
    
    def extract_nodes_and_relationships(
        self,
        g: Graph,
        verbose: bool = True,
        include_relationships: bool = True,
        allow_external_targets: bool = False,
        allow_missing_sources: bool = False,
    ) -> None:
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

        if not include_relationships:
            return

        for subject, predicate, obj in g:
            if isinstance(obj, Literal):
                continue
            if predicate == RDF.type:
                continue
            if not self._is_core_uri(predicate):
                continue

            subject_uri = str(subject)
            target_uri = str(obj)
            if subject_uri not in self.nodes and not allow_missing_sources:
                continue
            if not allow_external_targets and target_uri not in self.nodes:
                continue

            predicate_name = self._local_name(predicate)
            rel_type = self._predicate_to_relationship(predicate_name)

            if rel_type in ['TYPE', 'VALUE', 'LABEL']:
                continue
            if self.skip_deprecates and rel_type == 'DEPRECATES':
                continue

            self.relationships.append(RelationshipData(
                source_uri=subject_uri,
                target_uri=target_uri,
                relationship_type=rel_type,
                properties={"predicate_uri": str(predicate)},
                source_label=self.nodes[subject_uri].label if subject_uri in self.nodes else None,
                target_label=self.nodes[target_uri].label if target_uri in self.nodes else None,
            ))
            self.stats['relationships'] += 1
            try:
                self.stats['rel_types'][rel_type] += 1
            except Exception:
                pass

        if verbose:
            for label, count in sorted(self.stats['labels'].items()):
                print(f"   * {label}: {count}")
            print(f"   * Relationships: {self.stats['relationships']}")

    def extract_nodes_and_relationships_stream(
        self,
        ttl_path: Path,
        verbose: bool = True,
        include_relationships: bool = True,
        allow_external_targets: bool = False,
        include_literals: bool = True,
        allow_missing_sources: bool = False,
    ) -> None:
        """Stream-parse a TTL file without rdflib graph construction (fast path).

        Assumes one triple per line and full URIs for subjects/predicates/objects.
        """
        if verbose:
            print("\nExtracting nodes and relationships (streaming)...")

        # Read prefix mappings from the TTL header so we can expand prefixed names
        prefix_map: Dict[str, str] = {}
        try:
            with open(ttl_path, 'r', encoding='utf-8') as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if line.startswith('@prefix'):
                        # expected form: @prefix sec: <https://example.org/sec/core#> .
                        parts = line.split()
                        if len(parts) >= 3:
                            pfx = parts[1]
                            ns = parts[2]
                            if pfx.endswith(':'):
                                pfx_key = pfx[:-1]
                                if ns.startswith('<') and ns.endswith('>'):
                                    prefix_map[pfx_key] = ns[1:-1]
                        continue
                    # stop at first non-prefix/header line
                    break

        except Exception:
            prefix_map = {}

        def iter_triples(path: Path):
            with open(path, 'r', encoding='utf-8') as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if line.startswith('@prefix') or line.startswith('PREFIX') or line.startswith('#'):
                        continue
                    first_space = line.find(' ')
                    if first_space == -1:
                        continue
                    second_space = line.find(' ', first_space + 1)
                    if second_space == -1:
                        continue
                    subj_token = line[:first_space]
                    pred_token = line[first_space + 1:second_space]
                    obj_token = line[second_space + 1:]
                    if obj_token.endswith(' .'):
                        obj_token = obj_token[:-2]
                    elif obj_token.endswith('.'):
                        obj_token = obj_token[:-1]
                    yield subj_token, pred_token, obj_token

        def parse_uri(token: str) -> URIRef | None:
            # full URI: <http://...>
            if token.startswith('<') and token.endswith('>'):
                return URIRef(token[1:-1])
            # shorthand rdf:type
            if token == 'a':
                return RDF.type
            # prefixed name: prefix:local
            if ':' in token:
                pfx, local = token.split(':', 1)
                if pfx in prefix_map:
                    return URIRef(prefix_map[pfx] + local)
            return None

        def parse_object(token: str):
            if token.startswith('<') and token.endswith('>'):
                return URIRef(token[1:-1])
            if token.startswith('"'):
                # Handle typed literals with prefixed datatypes (e.g., ^^xsd:dateTime)
                if '^^' in token:
                    literal_part, dtype_part = token.rsplit('^^', 1)
                    try:
                        literal_val = Literal.from_n3(literal_part)  # type: ignore[attr-defined]
                    except Exception:
                        literal_val = Literal(literal_part.strip('"'))

                    dtype_uri = None
                    if dtype_part.startswith('xsd:'):
                        dtype_uri = URIRef(f"http://www.w3.org/2001/XMLSchema#{dtype_part.split(':', 1)[1]}")
                    elif dtype_part.startswith('<') and dtype_part.endswith('>'):
                        dtype_uri = URIRef(dtype_part[1:-1])

                    if dtype_uri is not None:
                        return Literal(literal_val.toPython(), datatype=dtype_uri)

                try:
                    return Literal.from_n3(token)  # type: ignore[attr-defined]
                except Exception:
                    return Literal(token.strip('"'))
            return None

        core_types_by_subject: Dict[str, List[str]] = {}
        rdfs_label = URIRef("http://www.w3.org/2000/01/rdf-schema#label")
        rdfs_comment = URIRef("http://www.w3.org/2000/01/rdf-schema#comment")

        for subj_token, pred_token, obj_token in iter_triples(ttl_path):
            subj_uri = parse_uri(subj_token)
            pred_uri = parse_uri(pred_token)
            obj_uri = parse_uri(obj_token)
            if not subj_uri or not pred_uri or not obj_uri:
                continue
            if str(pred_uri) != str(RDF.type):
                continue
            if str(obj_uri).startswith(self.sec_ns_str):
                core_types_by_subject.setdefault(str(subj_uri), []).append(self._local_name(obj_uri))

        for subject_uri, labels in core_types_by_subject.items():
            unique_labels = sorted(set(labels))
            if not unique_labels:
                continue
            properties = {}
            if len(unique_labels) > 1:
                properties['rdfTypes'] = unique_labels
            primary_label = unique_labels[0]
            self.nodes[subject_uri] = NodeData(label=primary_label, uri=subject_uri, properties=properties)
            self.stats['labels'][primary_label] += 1

        for subj_token, pred_token, obj_token in iter_triples(ttl_path):
            subj_uri_ref = parse_uri(subj_token)
            pred_uri_ref = parse_uri(pred_token)
            if not subj_uri_ref or not pred_uri_ref:
                continue

            subject_uri = str(subj_uri_ref)
            if subject_uri not in self.nodes and not allow_missing_sources:
                continue

            if str(pred_uri_ref) == str(RDF.type):
                continue

            obj_value = parse_object(obj_token)
            if include_literals and isinstance(obj_value, Literal):
                prop_name = self._local_name(pred_uri_ref)
                value = self._parse_literal(obj_value)
                if value is not None:
                    self.nodes[subject_uri].properties[prop_name] = value
                continue

            if not self._is_core_uri(pred_uri_ref):
                continue

            if not include_relationships:
                continue

            if isinstance(obj_value, URIRef):
                target_uri = str(obj_value)
                if not allow_external_targets and target_uri not in self.nodes:
                    continue
                predicate_name = self._local_name(pred_uri_ref)
                rel_type = self._predicate_to_relationship(predicate_name)
                if rel_type in ['TYPE', 'VALUE', 'LABEL']:
                    continue
                if self.skip_deprecates and rel_type == 'DEPRECATES':
                    continue
                self.relationships.append(RelationshipData(
                    source_uri=subject_uri,
                    target_uri=target_uri,
                    relationship_type=rel_type,
                    properties={"predicate_uri": str(pred_uri_ref)},
                    source_label=self.nodes[subject_uri].label if subject_uri in self.nodes else None,
                    target_label=self.nodes[target_uri].label if target_uri in self.nodes else None,
                ))
                self.stats['relationships'] += 1
                try:
                    self.stats['rel_types'][rel_type] += 1
                except Exception:
                    pass

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
        uri_str = str(uri)
        if '#' in uri_str:
            return uri_str.split('#')[-1]
        return uri_str.rsplit('/', 1)[-1]

    def _is_core_uri(self, uri: Node) -> bool:
        """Check if a URIRef is in the core namespace."""
        return str(uri).startswith(self.sec_ns_str)
    
    def load_to_neo4j(
        self,
        driver,
        include_indexes: bool = True,
        include_stats: bool = True,
        database: str | None = None,
        load_nodes: bool = True,
        load_relationships: bool = True,
    ) -> bool:
        """Load nodes and relationships into Neo4j."""
        print(f"\nLoading to Neo4j...")
        
        try:
            target_db = database or neo4j_config.database
            with driver.session(database=target_db) as session:
                if include_indexes:
                    self._create_indexes(session)
                if load_nodes:
                    self._load_nodes_batch(session)
                if load_relationships:
                    self._load_relationships(session)
                if include_stats:
                    self._get_database_stats(session)
            return True
            
        except Exception as e:
            print(f"\nError loading to Neo4j: {e}")
            return False

    def reset_database(self, driver, database: str) -> bool:
        """Drop and recreate the target database; fall back to delete-all if needed."""
        print(f"\nResetting Neo4j database: {database}")
        try:
            with driver.session(database="system") as session:
                session.run(f"DROP DATABASE `{database}` IF EXISTS")
                session.run(f"CREATE DATABASE `{database}` IF NOT EXISTS WAIT")
            print("   * Database reset complete")
            return True
        except Exception as e:
            print(f"   * Database drop/create failed ({e}); falling back to DETACH DELETE")
            try:
                with driver.session(database=database) as session:
                    session.run("MATCH (n) DETACH DELETE n")
                print("   * Database cleared via DETACH DELETE")
                return True
            except Exception as e2:
                print(f"   * Database clear failed: {e2}")
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

        # Create uri indexes for relationship lookups
        for label in self.merge_keys.keys():
            try:
                session.run(f"""
                    CREATE INDEX {label.lower()}_uri_index IF NOT EXISTS
                    FOR (n:{label}) ON (n.uri)
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
            key_prop = self.merge_keys.get(label)
            if key_prop:
                with_key = [n for n in node_list if n['properties'].get(key_prop) is not None]
                without_key = [n for n in node_list if n['properties'].get(key_prop) is None]
            else:
                with_key = []
                without_key = node_list

            if with_key:
                cypher = (
                    f"UNWIND $nodes as node "
                    f"MERGE (n:`{label}` {{{key_prop}: node.properties.{key_prop}}}) "
                    f"SET n += node.properties, n.uri = node.uri"
                )
                session.run(cypher, nodes=with_key)
            if without_key:
                cypher = f"UNWIND $nodes as node MERGE (n:`{label}` {{uri: node.uri}}) SET n += node.properties"
                session.run(cypher, nodes=without_key)
    
    def _load_relationships(self, session) -> None:
        """Load relationships to Neo4j."""
        if not self.relationships:
            return
        
        print(f"   Loading {len(self.relationships)} relationships...")
        
        batch = []
        for i, rel in enumerate(self.relationships, 1):
            batch.append(rel)
            
            if len(batch) >= self.relationship_batch_size or i == len(self.relationships):
                self._insert_relationship_batch(session, batch)
                batch = []
                if i % (self.relationship_batch_size * 10) == 0:
                    print(f"      Progress: {i}/{len(self.relationships)} relationships")
        
        print(f"   * All relationships loaded")
    
    def _insert_relationship_batch(self, session, rels: List[RelationshipData]) -> None:
        """Insert batch of relationships."""
        by_key = defaultdict(list)
        for rel in rels:
            key = (rel.relationship_type, rel.source_label, rel.target_label)
            by_key[key].append({
                'sourceUri': rel.source_uri,
                'targetUri': rel.target_uri,
                'properties': rel.properties,
            })

        for (rel_type, source_label, target_label), rel_list in by_key.items():
            unique_rels = {}
            for rel in rel_list:
                unique_rels[(rel['sourceUri'], rel['targetUri'])] = rel
            rel_list = list(unique_rels.values())
            source_clause = f"MATCH (source:`{source_label}` {{uri: rel.sourceUri}})" if source_label else "MATCH (source {uri: rel.sourceUri})"
            target_clause = f"MATCH (target:`{target_label}` {{uri: rel.targetUri}})" if target_label else "MATCH (target {uri: rel.targetUri})"
            cypher = (
                f"UNWIND $rels as rel "
                f"{source_clause} "
                f"{target_clause} "
                f"MERGE (source)-[r:`{rel_type}`]->(target) SET r += rel.properties"
            )
            # Execute in smaller sub-batches to avoid large MERGE transactions stalling
            SUB_BATCH = 100
            try:
                if len(rel_list) <= SUB_BATCH:
                    session.run(cypher, rels=rel_list)
                else:
                    total = len(rel_list)
                    print(f"      Splitting {total} relationships into sub-batches of {SUB_BATCH}")
                    for i in range(0, total, SUB_BATCH):
                        sub = rel_list[i:i+SUB_BATCH]
                        session.run(cypher, rels=sub)
            except Exception as e:
                # As a fallback, attempt progressively smaller chunks
                print(f"      Warning: relationship batch failed: {e}. Retrying in smaller chunks")
                chunk = max(1, min(SUB_BATCH, len(rel_list)//4))
                try:
                    for i in range(0, len(rel_list), chunk):
                        session.run(cypher, rels=rel_list[i:i+chunk])
                except Exception as e2:
                    print(f"      Error: relationship sub-batch retry failed: {e2}")
    
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

        rel_result = session.run("""
            MATCH ()-[r]->() RETURN type(r) as rel_type, COUNT(r) as count
            ORDER BY count DESC
        """)

        print("\nRelationship Types:")
        for record in rel_result:
            rel_type = record['rel_type'] or '(untyped)'
            count = record['count']
            print(f"   {rel_type}: {count}")
        
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
        tf.write('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n')
        tf.write('@prefix ex: <https://example.org/> .\n\n')
        tf.write('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n')
        tf.write('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n')
        for line in lines:
            tf.write(line)
    return tmp_path


def split_ttl_nodes_relationships(data_path: str, nodes_path: str, rels_path: str) -> Tuple[int, int]:
    """Split a TTL file into nodes-only (rdf:type + literals) and relationships-only (URI objects)."""
    rdf_type_token = f"<{RDF.type}>"
    rdf_prefixed_token = "rdf:type"
    rdf_shorthand_token = "a"
    nodes_written = 0
    rels_written = 0

    nodes_out_path = Path(nodes_path)
    rels_out_path = Path(rels_path)
    nodes_out_path.parent.mkdir(parents=True, exist_ok=True)
    rels_out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(data_path, 'r', encoding='utf-8') as fh, \
            open(nodes_out_path, 'w', encoding='utf-8') as nodes_out, \
            open(rels_out_path, 'w', encoding='utf-8') as rels_out:
        for raw_line in fh:
            line = raw_line.rstrip('\n')
            if not line.strip():
                nodes_out.write(raw_line)
                rels_out.write(raw_line)
                continue
            if line.startswith('@prefix') or line.startswith('PREFIX') or line.startswith('#'):
                nodes_out.write(raw_line)
                rels_out.write(raw_line)
                continue

            first_space = line.find(' ')
            if first_space == -1:
                continue
            second_space = line.find(' ', first_space + 1)
            if second_space == -1:
                continue
            pred_token = line[first_space + 1:second_space]
            obj_token = line[second_space + 1:]
            if obj_token.endswith(' .'):
                obj_token = obj_token[:-2]
            elif obj_token.endswith('.'):
                obj_token = obj_token[:-1]

            if pred_token == rdf_type_token or pred_token == rdf_prefixed_token or pred_token == rdf_shorthand_token:
                nodes_out.write(raw_line)
                nodes_written += 1
            elif obj_token.startswith('"'):
                nodes_out.write(raw_line)
                nodes_written += 1
            elif obj_token.startswith('<') or obj_token.startswith('_:'):
                rels_out.write(raw_line)
                rels_written += 1

    return nodes_written, rels_written


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


def _dry_run_chunk(tmp_path: str, skip_deprecates: bool) -> Dict[str, Any]:
    g = Graph()
    g.parse(tmp_path, format='turtle')
    transformer = RDFtoNeo4jTransformer(tmp_path, skip_deprecates=skip_deprecates)
    transformer.extract_nodes_and_relationships(g, verbose=False)
    return {
        'labels': dict(transformer.stats['labels']),
        'relationships': transformer.stats['relationships'],
        'rel_types': dict(transformer.stats.get('rel_types', {})),
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
    parser.add_argument("--parse-heartbeat-seconds", type=float, default=0, help="Emit a heartbeat while parsing RDF (0 = off)")
    parser.add_argument("--reset-db", action="store_true", help="Drop and recreate the target Neo4j database before loading")
    parser.add_argument("--db-name", help="Override target Neo4j database name")
    parser.add_argument("--db-version", help="Append a version suffix to the configured database name")
    parser.add_argument("--fast-parse", action="store_true", help="Use a streaming TTL parser instead of rdflib Graph.parse")
    parser.add_argument("--rel-batch-size", type=int, default=None, help="Batch size for relationship inserts (default: same as --batch-size)")
    parser.add_argument("--export-nodes-ttl", help="Write a nodes-only TTL (rdf:type + literal properties)")
    parser.add_argument("--export-rels-ttl", help="Write a relationships-only TTL (URI object triples)")
    parser.add_argument("--export-only", action="store_true", help="Exit after exporting split TTL files")
    parser.add_argument("--nodes-only", action="store_true", help="Load nodes only (skip relationships)")
    parser.add_argument("--rels-only", action="store_true", help="Load relationships only (requires nodes already loaded)")
    parser.add_argument("--skip-deprecates", action="store_true", help="Skip DEPRECATES relationships during load")
    args = parser.parse_args()

    if args.db_name and args.db_version:
        print("Error: --db-name and --db-version are mutually exclusive")
        return 2

    if args.nodes_only and args.rels_only:
        print("Error: --nodes-only and --rels-only are mutually exclusive")
        return 2

    if args.rels_only and args.reset_db:
        print("Error: --rels-only cannot be used with --reset-db (nodes would be deleted)")
        return 2

    if (args.export_nodes_ttl and not args.export_rels_ttl) or (args.export_rels_ttl and not args.export_nodes_ttl):
        print("Error: --export-nodes-ttl and --export-rels-ttl must be provided together")
        return 2

    def _normalize_db_name(name: str) -> str:
        # Neo4j allows ascii letters, numbers, dots, and dashes. Replace others with '-'.
        import re
        sanitized = re.sub(r"[^A-Za-z0-9.-]", "-", name)
        sanitized = sanitized.strip("-.")
        return sanitized or "neo4j"

    if args.db_name:
        target_db = _normalize_db_name(args.db_name)
    elif args.db_version:
        target_db = _normalize_db_name(f"{neo4j_config.database}-{args.db_version}")
    else:
        target_db = _normalize_db_name(neo4j_config.database)

    if args.export_nodes_ttl and args.export_rels_ttl:
        print(f"\nSplitting TTL into nodes/relationships files...")
        nodes_written, rels_written = split_ttl_nodes_relationships(
            args.ttl,
            args.export_nodes_ttl,
            args.export_rels_ttl,
        )
        print(f"   * Nodes triples: {nodes_written}")
        print(f"   * Relationship triples: {rels_written}")
        print(f"   * Nodes file: {args.export_nodes_ttl}")
        print(f"   * Relationships file: {args.export_rels_ttl}")
        if args.export_only:
            return 0

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
            aggregate_rel_types: Dict[str, int] = {}

            if args.dry_run:
                workers = max(args.workers or 1, 1)
                if workers > 1:
                    with ProcessPoolExecutor(max_workers=workers) as executor:
                        futures = [executor.submit(_dry_run_chunk, tmp_path, args.skip_deprecates) for _, tmp_path in chunk_files]
                        for future in as_completed(futures):
                            result = future.result()
                            completed += 1
                            worker_id = ((completed - 1) % workers) + 1
                            _update_progress(completed, total_chunks, worker_id, args.progress_newline)
                            _merge_label_counts(aggregate_labels, result.get('labels', {}))
                            aggregate_rels += result.get('relationships', 0)
                            _merge_label_counts(aggregate_rel_types, result.get('rel_types', {}))
                else:
                    for chunk_idx, tmp_path in chunk_files:
                        result = _dry_run_chunk(tmp_path, args.skip_deprecates)
                        completed += 1
                        _update_progress(completed, total_chunks, ((chunk_idx - 1) % workers) + 1, args.progress_newline)
                        _merge_label_counts(aggregate_labels, result.get('labels', {}))
                        aggregate_rels += result.get('relationships', 0)
                        _merge_label_counts(aggregate_rel_types, result.get('rel_types', {}))

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

                with driver.session(database=target_db) as session:
                    transformer = RDFtoNeo4jTransformer(
                        args.ttl,
                        batch_size=args.batch_size,
                        skip_deprecates=args.skip_deprecates,
                    )
                    if args.reset_db and not args.dry_run:
                        if not transformer.reset_database(driver, target_db):
                            driver.close()
                            return 1
                    transformer._create_indexes(session)

                # Pass 1: load nodes only (unless relationships-only)
                if not args.rels_only:
                    for chunk_idx, tmp_path in chunk_files:
                        transformer = RDFtoNeo4jTransformer(
                            tmp_path,
                            batch_size=args.batch_size,
                            parse_heartbeat_seconds=args.parse_heartbeat_seconds,
                            relationship_batch_size=args.rel_batch_size,
                            skip_deprecates=args.skip_deprecates,
                        )
                        if args.fast_parse:
                            transformer.extract_nodes_and_relationships_stream(
                                Path(tmp_path),
                                verbose=False,
                                include_relationships=False,
                            )
                        else:
                            g = transformer.load_rdf()
                            transformer.extract_nodes_and_relationships(g, verbose=False, include_relationships=False)
                        success = transformer.load_to_neo4j(
                            driver,
                            include_indexes=False,
                            include_stats=False,
                            database=target_db,
                            load_nodes=True,
                            load_relationships=False,
                        )
                        if not success:
                            driver.close()
                            return 1
                        completed += 1
                        _update_progress(completed, total_chunks, None, args.progress_newline)
                        _merge_label_counts(aggregate_labels, dict(transformer.stats['labels']))

                # Pass 2: load relationships after all nodes exist (unless nodes-only)
                if not args.nodes_only:
                    completed = 0
                    for chunk_idx, tmp_path in chunk_files:
                        transformer = RDFtoNeo4jTransformer(
                            tmp_path,
                            batch_size=args.batch_size,
                            parse_heartbeat_seconds=args.parse_heartbeat_seconds,
                            relationship_batch_size=args.rel_batch_size,
                            skip_deprecates=args.skip_deprecates,
                        )
                        if args.fast_parse:
                            transformer.extract_nodes_and_relationships_stream(
                                Path(tmp_path),
                                verbose=False,
                                include_relationships=True,
                                allow_external_targets=True,
                                allow_missing_sources=args.rels_only,
                            )
                        else:
                            g = transformer.load_rdf()
                            transformer.extract_nodes_and_relationships(
                                g,
                                verbose=False,
                                include_relationships=True,
                                allow_external_targets=True,
                                allow_missing_sources=args.rels_only,
                            )
                        success = transformer.load_to_neo4j(
                            driver,
                            include_indexes=False,
                            include_stats=False,
                            database=target_db,
                            load_nodes=False,
                            load_relationships=True,
                        )
                        if not success:
                            driver.close()
                            return 1
                        completed += 1
                        _update_progress(completed, total_chunks, None, args.progress_newline)
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
            if aggregate_rel_types:
                print("   * Relationships by type:")
                for rel_type, count in sorted(aggregate_rel_types.items(), key=lambda x: -x[1]):
                    print(f"      - {rel_type}: {count}")
            print(f"   * Relationships: {aggregate_rels}")
            print(f"   * Triples scanned: {total_triples}")

            if args.dry_run:
                return 0

            print("\n" + "=" * 100)
            print("SUCCESS: RDF-TO-NEO4J TRANSFORMATION COMPLETE")
            print("=" * 100)
            return 0

        transformer = RDFtoNeo4jTransformer(
            args.ttl,
            batch_size=args.batch_size,
            parse_heartbeat_seconds=args.parse_heartbeat_seconds,
            relationship_batch_size=args.rel_batch_size,
            skip_deprecates=args.skip_deprecates,
        )
        if args.fast_parse:
            transformer.extract_nodes_and_relationships_stream(
                Path(args.ttl),
                include_relationships=not args.nodes_only,
                include_literals=not args.rels_only,
                allow_external_targets=args.rels_only,
                allow_missing_sources=args.rels_only,
            )
        else:
            g = transformer.load_rdf()
            transformer.extract_nodes_and_relationships(
                g,
                include_relationships=not args.nodes_only,
                allow_external_targets=args.rels_only,
                allow_missing_sources=args.rels_only,
            )

        if args.dry_run:
            print()
            print("Dry run enabled — skipping Neo4j load.")
            print("\nSummary:")
            for label, count in sorted(transformer.stats['labels'].items()):
                print(f"   * {label}: {count}")
            rel_types = transformer.stats.get('rel_types', {})
            if rel_types:
                print("   * Relationships by type:")
                for rel_type, count in sorted(rel_types.items(), key=lambda x: -x[1]):
                    print(f"      - {rel_type}: {count}")
            print(f"   * Relationships: {transformer.stats['relationships']}")
            return 0

        from neo4j import GraphDatabase

        print(f"\nConnecting to Neo4j at {neo4j_config.uri}...")
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )

        if args.reset_db and not args.dry_run:
            if not transformer.reset_database(driver, target_db):
                driver.close()
                return 1

        success = transformer.load_to_neo4j(
            driver,
            database=target_db,
            load_nodes=not args.rels_only,
            load_relationships=not args.nodes_only,
        )
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
