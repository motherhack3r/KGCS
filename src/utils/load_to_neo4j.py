"""Load KGCS Turtle exports into Neo4j with Core-aligned constraints.

Usage examples:
  python -m kgcs.utils.load_to_neo4j --input tmp/sample_cve.ttl \
      --uri bolt://localhost:7687 --user neo4j --password password

  python -m kgcs.utils.load_to_neo4j --input data/cve/samples \
      --uri bolt://localhost:7687 --user neo4j --password password --database neo4j
"""
import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, XSD
from rdflib.term import Literal

SEC = Namespace("https://example.org/sec/core#")


def literal_value(val: Any) -> Optional[Any]:
    if val is None:
        return None
    try:
        py_val = val.toPython()
    except Exception:
        return str(val)
    if hasattr(py_val, "isoformat"):
        return py_val.isoformat()
    return py_val


def clean_props(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in raw.items() if v is not None}


def collect_input_paths(path: str) -> List[str]:
    if os.path.isdir(path):
        ttl_files = []
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(".ttl"):
                    ttl_files.append(os.path.join(root, f))
        return sorted(ttl_files)
    return [path]


class TTLExtractor:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.platform_uri_to_cpe: Dict[str, str] = {}
        self.config_uri_to_id: Dict[str, str] = {}
        self.vuln_uri_to_cve: Dict[str, str] = {}
        self.reference_uri_to_url: Dict[str, str] = {}

    def extract(self) -> Dict[str, Any]:
        platforms = self._extract_platforms()
        configs = self._extract_configurations()
        vulns = self._extract_vulnerabilities()
        scores = self._extract_scores()
        references = self._extract_references()
        edges = self._extract_edges()
        return {
            "platforms": platforms,
            "configurations": configs,
            "vulnerabilities": vulns,
            "scores": scores,
            "references": references,
            "edges": edges,
        }

    def _extract_platforms(self) -> List[Dict[str, Any]]:
        rows = []
        for subject in self.graph.subjects(RDF.type, SEC.Platform):
            # Accept canonical `CPEUri` and legacy `cpeUri`
            cpe_val = self.graph.value(subject, SEC.CPEUri) or self.graph.value(subject, SEC.cpeUri)
            cpe_uri = literal_value(cpe_val)
            if not cpe_uri:
                continue
            self.platform_uri_to_cpe[str(subject)] = cpe_uri
            props = clean_props(
                {
                    "platformPart": literal_value(self.graph.value(subject, SEC.platformPart)),
                    "vendor": literal_value(self.graph.value(subject, SEC.vendor)),
                    "product": literal_value(self.graph.value(subject, SEC.product)),
                    "version": literal_value(self.graph.value(subject, SEC.version)),
                }
            )
            rows.append({"uri": str(subject), "cpeUri": cpe_uri, "props": props})
        return rows

    def _extract_configurations(self) -> List[Dict[str, Any]]:
        rows = []
        for subject in self.graph.subjects(RDF.type, SEC.PlatformConfiguration):
            match_id = literal_value(self.graph.value(subject, SEC.matchCriteriaId))
            if not match_id:
                continue
            self.config_uri_to_id[str(subject)] = match_id
            props = clean_props(
                {
                    "configurationCriteria": literal_value(self.graph.value(subject, SEC.configurationCriteria)),
                    "versionStartIncluding": literal_value(self.graph.value(subject, SEC.versionStartIncluding)),
                    "versionEndIncluding": literal_value(self.graph.value(subject, SEC.versionEndIncluding)),
                }
            )
            rows.append({"uri": str(subject), "matchCriteriaId": match_id, "props": props})
        return rows

    def _extract_vulnerabilities(self) -> List[Dict[str, Any]]:
        rows = []
        for subject in self.graph.subjects(RDF.type, SEC.Vulnerability):
            cve_id = literal_value(self.graph.value(subject, SEC.cveId))
            if not cve_id:
                continue
            self.vuln_uri_to_cve[str(subject)] = cve_id
            props = clean_props(
                {
                    "published": literal_value(self.graph.value(subject, SEC.published)),
                    "lastModified": literal_value(self.graph.value(subject, SEC.lastModified)),
                    "vulnStatus": literal_value(self.graph.value(subject, SEC.vulnStatus)),
                    "sourceIdentifier": literal_value(self.graph.value(subject, SEC.sourceIdentifier)),
                    "description": literal_value(self.graph.value(subject, SEC.description)),
                }
            )
            rows.append({"uri": str(subject), "cveId": cve_id, "props": props})
        return rows

    def _extract_scores(self) -> List[Dict[str, Any]]:
        rows = []
        for subject in self.graph.subjects(RDF.type, SEC.VulnerabilityScore):
            props = clean_props(
                {
                    "cvssVersion": literal_value(self.graph.value(subject, SEC.cvssVersion)),
                    "vectorString": literal_value(self.graph.value(subject, SEC.vectorString)),
                    "baseScore": literal_value(self.graph.value(subject, SEC.baseScore)),
                    "baseSeverity": literal_value(self.graph.value(subject, SEC.baseSeverity)),
                }
            )
            rows.append({"uri": str(subject), "props": props})
        return rows

    def _extract_references(self) -> List[Dict[str, Any]]:
        rows = []
        for subject in self.graph.subjects(RDF.type, SEC.Reference):
            url = literal_value(self.graph.value(subject, SEC.referenceUrl))
            if not url:
                continue
            props = clean_props({"referenceSource": literal_value(self.graph.value(subject, SEC.referenceSource))})
            self.reference_uri_to_url[str(subject)] = url
            rows.append({"uri": str(subject), "url": url, "props": props})
        return rows

    def _extract_edges(self) -> Dict[str, List[Dict[str, Any]]]:
        edges = {
            "config_platform": [],
            "config_vulnerability": [],
            "vulnerability_score": [],
            "vulnerability_reference": [],
        }
        for config_uri, match_id in self.config_uri_to_id.items():
            cfg_ref = URIRef(config_uri)
            # Accept canonical `matchesPlatform` and legacy `includes` predicates
            platform_obj = self.graph.value(cfg_ref, SEC.matchesPlatform) or self.graph.value(cfg_ref, SEC.includes)
            if platform_obj and str(platform_obj) in self.platform_uri_to_cpe:
                edges["config_platform"].append(
                    {
                        "matchCriteriaId": match_id,
                        "cpeUri": self.platform_uri_to_cpe[str(platform_obj)],
                    }
                )
            for vuln in self.graph.objects(cfg_ref, SEC.affected_by):
                cve_id = self.vuln_uri_to_cve.get(str(vuln))
                if cve_id:
                    edges["config_vulnerability"].append({"matchCriteriaId": match_id, "cveId": cve_id})

        for vuln_uri, cve_id in self.vuln_uri_to_cve.items():
            vuln_ref = URIRef(vuln_uri)
            for score in self.graph.objects(vuln_ref, SEC.scored_by):
                edges["vulnerability_score"].append({"cveId": cve_id, "score_uri": str(score)})
            for ref in self.graph.objects(vuln_ref, SEC.references):
                url = self.reference_uri_to_url.get(str(ref))
                if url:
                    edges["vulnerability_reference"].append({"cveId": cve_id, "url": url})
        return edges


class Neo4jLoader:
    def __init__(self, uri: str, user: str, password: str, database: Optional[str] = None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def ensure_constraints(self):
        with self.driver.session(database=self.database) as session:
            try:
                session.run("CREATE CONSTRAINT platform_cpe IF NOT EXISTS FOR (p:Platform) REQUIRE p.cpeUri IS UNIQUE")
            except Exception as e:
                print(f"Warning: Constraint query failed (may already exist): {e}", file=sys.stderr)

    def load(self, data: Dict[str, Any]):
        with self.driver.session(database=self.database) as session:
            self._merge_platforms(session, data["platforms"])
            self._merge_configurations(session, data["configurations"])
            self._merge_vulnerabilities(session, data["vulnerabilities"])
            self._merge_scores(session, data["scores"])
            self._merge_references(session, data["references"])
            self._merge_edges(session, data["edges"])

    @staticmethod
    def _merge_platforms(session, rows: List[Dict[str, Any]]):
        if not rows:
            return
        session.run(
            """
            UNWIND $rows AS row
            MERGE (p:Platform {cpeUri: row.cpeUri})
            SET p.uri = row.uri
            SET p += row.props
            """,
            rows=rows,
        )

    @staticmethod
    def _merge_configurations(session, rows: List[Dict[str, Any]]):
        if not rows:
            return
        session.run(
            """
            UNWIND $rows AS row
            MERGE (c:PlatformConfiguration {matchCriteriaId: row.matchCriteriaId})
            SET c.uri = row.uri
            SET c += row.props
            """,
            rows=rows,
        )

    @staticmethod
    def _merge_vulnerabilities(session, rows: List[Dict[str, Any]]):
        if not rows:
            return
        session.run(
            """
            UNWIND $rows AS row
            MERGE (v:Vulnerability {cveId: row.cveId})
            SET v.uri = row.uri
            SET v += row.props
            """,
            rows=rows,
        )

    @staticmethod
    def _merge_scores(session, rows: List[Dict[str, Any]]):
        if not rows:
            return
        session.run(
            """
            UNWIND $rows AS row
            MERGE (s:VulnerabilityScore {uri: row.uri})
            SET s += row.props
            """,
            rows=rows,
        )

    @staticmethod
    def _merge_references(session, rows: List[Dict[str, Any]]):
        if not rows:
            return
        session.run(
            """
            UNWIND $rows AS row
            MERGE (r:Reference {url: row.url})
            SET r.uri = row.uri
            SET r += row.props
            """,
            rows=rows,
        )

    @staticmethod
    def _merge_edges(session, edges: Dict[str, List[Dict[str, Any]]]):
        if edges.get("config_platform"):
            session.run(
                """
                UNWIND $rows AS row
                MATCH (c:PlatformConfiguration {matchCriteriaId: row.matchCriteriaId})
                MATCH (p:Platform {cpeUri: row.cpeUri})
                MERGE (c)-[:MATCHES_PLATFORM]->(p)
                """,
                rows=edges["config_platform"],
            )
        if edges.get("config_vulnerability"):
            session.run(
                """
                UNWIND $rows AS row
                MATCH (c:PlatformConfiguration {matchCriteriaId: row.matchCriteriaId})
                MATCH (v:Vulnerability {cveId: row.cveId})
                MERGE (c)-[:AFFECTED_BY]->(v)
                """,
                rows=edges["config_vulnerability"],
            )


def parse_args():
    parser = argparse.ArgumentParser(description="Load KGCS Turtle exports into Neo4j")
    parser.add_argument("--input", required=True, help="TTL file or directory of TTL files")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"), help="Neo4j bolt URI")
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"), help="Neo4j user")
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"), help="Neo4j password")
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE"), help="Neo4j database name")
    parser.add_argument("--dry-run", action="store_true", help="Parse TTL without writing to Neo4j")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.password and not args.dry_run:
        print("Neo4j password is required (use --password or NEO4J_PASSWORD)", file=sys.stderr)
        return 1

    input_paths = collect_input_paths(args.input)
    if not input_paths:
        print(f"No TTL files found under {args.input}", file=sys.stderr)
        return 1

    extractor_data: List[Tuple[str, Dict[str, Any]]] = []
    for path in input_paths:
        try:
            g = Graph()
            g.parse(path, format="turtle")
            data = TTLExtractor(g).extract()
            extractor_data.append((path, data))
            print(f"Parsed {path}: platforms={len(data['platforms'])}, configs={len(data['configurations'])}, vulns={len(data['vulnerabilities'])}")
        except Exception as e:
            print(f"Error parsing {path}: {e}", file=sys.stderr)
            continue

    if args.dry_run:
        print("Dry-run complete; no data written to Neo4j.")
        return 0

    loader = Neo4jLoader(args.uri, args.user, args.password, args.database)
    try:
        loader.ensure_constraints()
        for path, data in extractor_data:
            try:
                loader.load(data)
                print(f"Loaded {path} into Neo4j")
            except Exception as e:
                print(f"Error loading {path}: {e}", file=sys.stderr)
                continue
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}", file=sys.stderr)
        return 1
    finally:
        loader.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
