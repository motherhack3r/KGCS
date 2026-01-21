"""ETL Pipeline: MITRE CAPEC JSON → RDF Turtle with SHACL validation.

Transforms official MITRE CAPEC (Common Attack Pattern Enumeration and Classification)
JSON into RDF triples conforming to the Core Ontology AttackPattern class.

Usage:
    python -m src.etl.etl_capec --input data/capec/raw/capec.json \
                              --output data/capec/samples/capec-output.ttl \
                              --validate
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

SEC = Namespace("https://example.org/sec/core#")
EX = Namespace("https://example.org/")


class CAPECtoRDFTransformer:
    """Transform MITRE CAPEC JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        self.graph.bind("sec", SEC)
        self.graph.bind("ex", EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)

    def transform(self, capec_json: dict) -> Graph:
        """Transform CAPEC API JSON response to RDF."""
        patterns = capec_json.get("AttackPatterns", [])
        if not patterns:
            raise ValueError("Expected 'AttackPatterns' key in CAPEC JSON response")

        for pattern in patterns:
            self._add_attack_pattern(pattern)

        self._add_pattern_relationships(patterns)

        return self.graph

    def _add_attack_pattern(self, pattern: dict):
        """Add a CAPEC attack pattern entry as a sec:AttackPattern node."""
        capec_id = pattern.get("ID", "")
        if not capec_id:
            return

        capec_id_full = f"CAPEC-{capec_id}" if not capec_id.startswith("CAPEC-") else capec_id
        pattern_node = URIRef(f"{EX}attackPattern/{capec_id_full}")
        self.graph.add((pattern_node, RDF.type, SEC.AttackPattern))
        self.graph.add((pattern_node, SEC.capecId, Literal(capec_id_full, datatype=XSD.string)))

        if pattern.get("Name"):
            self.graph.add((pattern_node, RDFS.label, Literal(pattern["Name"], datatype=XSD.string)))

        if pattern.get("Description"):
            desc_text = self._extract_description(pattern["Description"])
            if desc_text:
                self.graph.add((pattern_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        if pattern.get("Prerequisites"):
            for prereq in pattern["Prerequisites"]:
                if prereq.get("Description"):
                    prereq_text = self._extract_description(prereq["Description"])
                    if prereq_text:
                        self.graph.add((pattern_node, SEC.prerequisite, Literal(prereq_text, datatype=XSD.string)))

        if pattern.get("Consequences"):
            for consequence in pattern["Consequences"]:
                if consequence.get("Description"):
                    cons_text = self._extract_description(consequence["Description"])
                    if cons_text:
                        self.graph.add((pattern_node, SEC.consequence, Literal(cons_text, datatype=XSD.string)))

        if pattern.get("RelatedWeaknesses"):
            self._add_weakness_relationships(pattern_node, pattern["RelatedWeaknesses"])

    def _extract_description(self, description_obj) -> str:
        """Extract description text from potentially nested structure."""
        if isinstance(description_obj, str):
            return description_obj
        if isinstance(description_obj, dict):
            if "Description" in description_obj:
                return self._extract_description(description_obj["Description"])
            if "Text" in description_obj:
                return description_obj["Text"]
        if isinstance(description_obj, list) and len(description_obj) > 0:
            return self._extract_description(description_obj[0])
        return ""

    def _add_weakness_relationships(self, pattern_node, related_weaknesses: list):
        """Add exploits relationships to weaknesses (CWE)."""
        for rel in related_weaknesses:
            cwe_id = rel.get("ID", "")
            if not cwe_id:
                continue

            cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
            weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")
            self.graph.add((pattern_node, SEC.exploits, weakness_node))

    def _add_pattern_relationships(self, patterns: list):
        """Add relationships between attack patterns (parent/child/related)."""
        capec_lookup = {p.get("ID", ""): p for p in patterns if p.get("ID")}

        for pattern in patterns:
            capec_id = pattern.get("ID", "")
            if not capec_id:
                continue

            capec_id_full = f"CAPEC-{capec_id}" if not capec_id.startswith("CAPEC-") else capec_id
            pattern_node = URIRef(f"{EX}attackPattern/{capec_id_full}")

            for related in pattern.get("RelatedAttackPatterns", []):
                related_id = related.get("ID", "")
                if not related_id or related_id not in capec_lookup:
                    continue

                related_id_full = f"CAPEC-{related_id}" if not related_id.startswith("CAPEC-") else related_id
                related_node = URIRef(f"{EX}attackPattern/{related_id_full}")
                relationship = related.get("Relationship", "")

                if relationship == "ParentOf":
                    self.graph.add((pattern_node, SEC.parentOf, related_node))
                elif relationship == "ChildOf":
                    self.graph.add((pattern_node, SEC.childOf, related_node))


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE CAPEC JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CAPEC JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/capec-shapes.ttl", help="SHACL shapes file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CAPEC JSON from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        capec_json = json.load(f)

    print("Transforming to RDF...")
    transformer = CAPECtoRDFTransformer()
    graph = transformer.transform(capec_json)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    graph.serialize(destination=args.output, format="turtle")

    if args.validate:
        print("\nRunning SHACL validation...")
        try:
            from core.validation import run_validator, load_graph
            shapes = load_graph(args.shapes)
            conforms, _, _ = run_validator(args.output, shapes)
            if conforms:
                print("✓ Validation passed!")
                return 0
            else:
                print("✗ Validation failed!")
                return 1
        except Exception as e:
            print(f"Warning: Could not run validation: {e}")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
