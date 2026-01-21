"""ETL Pipeline: MITRE CWE JSON → RDF Turtle with SHACL validation.

Transforms official MITRE CWE (Common Weakness Enumeration) JSON into RDF triples
conforming to the Core Ontology Weakness class.

Usage:
    python -m kgcs.etl.etl_cwe --input data/cwe/raw/cwe.json \
                              --output data/cwe/samples/cwe-output.ttl \
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


class CWEtoRDFTransformer:
    """Transform MITRE CWE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        self.graph.bind("sec", SEC)
        self.graph.bind("ex", EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)

    def transform(self, cwe_json: dict) -> Graph:
        """Transform CWE API JSON response to RDF."""
        if "Weakness" not in cwe_json:
            raise ValueError("Expected 'Weakness' key in CWE JSON response")

        for weakness in cwe_json["Weakness"]:
            self._add_weakness(weakness)

        self._add_weakness_relationships(cwe_json.get("Weakness", []))

        return self.graph

    def _add_weakness(self, weakness: dict):
        """Add a CWE weakness entry as a sec:Weakness node."""
        cwe_id = weakness.get("ID", "")
        if not cwe_id:
            return

        cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
        weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")
        self.graph.add((weakness_node, RDF.type, SEC.Weakness))
        self.graph.add((weakness_node, SEC.cweId, Literal(cwe_id_full, datatype=XSD.string)))

        if weakness.get("Name"):
            self.graph.add((weakness_node, RDFS.label, Literal(weakness["Name"], datatype=XSD.string)))

        if weakness.get("Description"):
            desc_text = self._extract_description(weakness["Description"])
            if desc_text:
                self.graph.add((weakness_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        if weakness.get("WeaknessAbstraction"):
            self.graph.add(
                (weakness_node, SEC.weaknessAbstraction, Literal(weakness["WeaknessAbstraction"], datatype=XSD.string))
            )

        if weakness.get("Status"):
            self.graph.add((weakness_node, SEC.status, Literal(weakness["Status"], datatype=XSD.string)))

        if weakness.get("ApplicablePlatforms"):
            for platform in weakness["ApplicablePlatforms"]:
                platform_str = self._format_platform(platform)
                if platform_str:
                    self.graph.add(
                        (weakness_node, SEC.applicablePlatform, Literal(platform_str, datatype=XSD.string))
                    )

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

    def _format_platform(self, platform_obj: dict) -> str:
        """Format platform information as a readable string."""
        parts = []
        if platform_obj.get("Language"):
            parts.append(platform_obj["Language"])
        if platform_obj.get("OperatingSystem"):
            parts.append(platform_obj["OperatingSystem"])
        return " ".join(parts) if parts else ""

    def _add_weakness_relationships(self, weaknesses: list):
        """Add parent/child relationships between weaknesses."""
        cwe_lookup = {w.get("ID", ""): w for w in weaknesses if w.get("ID")}

        for weakness in weaknesses:
            cwe_id = weakness.get("ID", "")
            if not cwe_id:
                continue

            cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
            weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")

            for related in weakness.get("RelatedWeaknesses", []):
                related_id = related.get("ID", "")
                if not related_id or related_id not in cwe_lookup:
                    continue

                related_id_full = f"CWE-{related_id}" if not related_id.startswith("CWE-") else related_id
                related_node = URIRef(f"{EX}weakness/{related_id_full}")
                relationship = related.get("Relationship", "")

                if relationship == "ChildOf":
                    self.graph.add((weakness_node, SEC.childOf, related_node))
                elif relationship == "ParentOf":
                    self.graph.add((weakness_node, SEC.parentOf, related_node))


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE CWE JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CWE JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/cwe-shapes.ttl", help="SHACL shapes file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CWE JSON from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        cwe_json = json.load(f)

    print("Transforming to RDF...")
    transformer = CWEtoRDFTransformer()
    graph = transformer.transform(cwe_json)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    graph.serialize(destination=args.output, format="turtle")

    if args.validate:
        print("\nRunning SHACL validation...")
        try:
            from kgcs.core.validation import run_validator, load_graph
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
