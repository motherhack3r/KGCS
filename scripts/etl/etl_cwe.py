"""ETL Pipeline: MITRE CWE JSON → RDF Turtle with SHACL validation.

Transforms official MITRE CWE (Common Weakness Enumeration) JSON into RDF triples
conforming to the Core Ontology Weakness class.

Usage:
    python scripts/etl/etl_cwe.py --input data/cwe/raw/cwe.json \
                              --output data/cwe/samples/cwe-output.ttl \
                              --validate

Reference:
    - MITRE CWE: https://cwe.mitre.org/
    - CWE JSON Format: https://cwe.mitre.org/data/downloads.html
    - Core Ontology: docs/ontology/core-ontology-v1.0.md
    - SHACL Shapes: docs/ontology/shacl/cwe-shapes.ttl
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# Define namespaces
SEC = Namespace("https://example.org/sec/core#")
EX = Namespace("https://example.org/")


class CWEtoRDFTransformer:
    """Transform MITRE CWE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        # Bind namespaces
        self.graph.bind("sec", SEC)
        self.graph.bind("ex", EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)

    def transform(self, cwe_json: dict) -> Graph:
        """
        Transform CWE API JSON response to RDF.

        Expected JSON structure (MITRE CWE JSON):
        {
          "Weakness": [
            {
              "ID": "78",
              "Name": "Improper Neutralization of Special Elements used in an OS Command",
              "Description": {...},
              "WeaknessAbstraction": "Base",
              "Status": "Incomplete",
              "Taxonomy": "OWASP Top Ten 2021",
              "RelatedWeaknesses": [
                {
                  "Relationship": "ChildOf",
                  "ID": "77",
                  "ViewID": "1000"
                }
              ],
              "ApplicablePlatforms": [
                {
                  "Language": "PHP",
                  "Prevalence": "Undetermined"
                }
              ],
              "CommonConsequences": [
                {
                  "Consequence": "Confidentiality",
                  "Note": "..."
                }
              ]
            }
          ]
        }
        """
        if "Weakness" not in cwe_json:
            raise ValueError("Expected 'Weakness' key in CWE JSON response")

        for weakness in cwe_json["Weakness"]:
            self._add_weakness(weakness)

        # Add relationships between weaknesses
        self._add_weakness_relationships(cwe_json.get("Weakness", []))

        return self.graph

    def _add_weakness(self, weakness: dict):
        """Add a CWE weakness entry as a sec:Weakness node."""
        cwe_id = weakness.get("ID", "")
        if not cwe_id:
            return

        # Create Weakness node (use CWE-<ID> format)
        cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
        weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")
        self.graph.add((weakness_node, RDF.type, SEC.Weakness))
        self.graph.add((weakness_node, SEC.cweId, Literal(cwe_id_full, datatype=XSD.string)))

        # Add name
        if weakness.get("Name"):
            self.graph.add((weakness_node, RDFS.label, Literal(weakness["Name"], datatype=XSD.string)))

        # Add description (handle nested structure)
        if weakness.get("Description"):
            desc_text = self._extract_description(weakness["Description"])
            if desc_text:
                self.graph.add((weakness_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Add abstraction level
        if weakness.get("WeaknessAbstraction"):
            self.graph.add(
                (weakness_node, SEC.weaknessAbstraction, Literal(weakness["WeaknessAbstraction"], datatype=XSD.string))
            )

        # Add status
        if weakness.get("Status"):
            self.graph.add((weakness_node, SEC.status, Literal(weakness["Status"], datatype=XSD.string)))

        # Add applicable platforms
        if weakness.get("ApplicablePlatforms"):
            for platform in weakness["ApplicablePlatforms"]:
                platform_str = self._format_platform(platform)
                if platform_str:
                    self.graph.add(
                        (weakness_node, SEC.applicablePlatform, Literal(platform_str, datatype=XSD.string))
                    )

        # Add common consequences
        if weakness.get("CommonConsequences"):
            for consequence in weakness["CommonConsequences"]:
                if consequence.get("Consequence"):
                    self.graph.add(
                        (weakness_node, SEC.commonConsequence, Literal(consequence["Consequence"], datatype=XSD.string))
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
        if platform_obj.get("Arch"):
            parts.append(platform_obj["Arch"])
        if platform_obj.get("Prevalence"):
            parts.append(f"(Prevalence: {platform_obj['Prevalence']})")
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

            # Add related weaknesses (parent/child)
            for related in weakness.get("RelatedWeaknesses", []):
                related_id = related.get("ID", "")
                if not related_id or related_id not in cwe_lookup:
                    continue

                related_id_full = f"CWE-{related_id}" if not related_id.startswith("CWE-") else related_id
                related_node = URIRef(f"{EX}weakness/{related_id_full}")
                relationship = related.get("Relationship", "")

                if relationship == "ChildOf":
                    # This weakness is a child of related weakness
                    self.graph.add((weakness_node, SEC.childOf, related_node))
                elif relationship == "ParentOf":
                    # This weakness is a parent of related weakness
                    self.graph.add((weakness_node, SEC.parentOf, related_node))
                elif relationship == "PeerOf":
                    # Related weakness is a peer
                    self.graph.add((weakness_node, SEC.peerOf, related_node))


def validate_output(ttl_file: str, shapes_file: str = "docs/ontology/shacl/cwe-shapes.ttl") -> bool:
    """Run SHACL validation on the generated TTL."""
    if not os.path.exists(shapes_file):
        print(f"Warning: Shapes file not found: {shapes_file}. Skipping validation.")
        return True

    result = subprocess.run(
        [sys.executable, "scripts/validate_shacl.py", "--data", ttl_file, "--shapes", shapes_file],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Validation failed for {ttl_file}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE CWE JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CWE JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/cwe-shapes.ttl", help="SHACL shapes file")
    args = parser.parse_args()

    # Load input JSON
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CWE JSON from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        cwe_json = json.load(f)

    # Transform
    print("Transforming to RDF...")
    transformer = CWEtoRDFTransformer()
    graph = transformer.transform(cwe_json)

    # Write output
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    graph.serialize(destination=args.output, format="turtle")

    # Validate (optional)
    if args.validate:
        print("\nRunning SHACL validation...")
        if validate_output(args.output, args.shapes):
            print("✓ Validation passed!")
            return 0
        else:
            print("✗ Validation failed!")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
