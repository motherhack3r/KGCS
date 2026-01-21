"""ETL Pipeline: MITRE CAPEC JSON → RDF Turtle with SHACL validation.

Transforms official MITRE CAPEC (Common Attack Pattern Enumeration and Classification)
JSON into RDF triples conforming to the Core Ontology AttackPattern class.

CAPEC defines abstract exploitation patterns that exploit weaknesses (CWE).
The causal chain: Weakness → exploited_by → AttackPattern → implemented_as → Technique

Usage:
    python scripts/etl/etl_capec.py --input data/capec/raw/capec.json \
                              --output data/capec/samples/capec-output.ttl \
                              --validate

Reference:
    - MITRE CAPEC: https://capec.mitre.org/
    - CAPEC JSON Format: https://capec.mitre.org/downloads/community/
    - Core Ontology: docs/ontology/core-ontology-v1.0.md
    - SHACL Shapes: docs/ontology/shacl/capec-shapes.ttl
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


class CAPECtoRDFTransformer:
    """Transform MITRE CAPEC JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        # Bind namespaces
        self.graph.bind("sec", SEC)
        self.graph.bind("ex", EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)

    def transform(self, capec_json: dict) -> Graph:
        """
        Transform CAPEC API JSON response to RDF.

        Expected JSON structure (MITRE CAPEC JSON):
        {
          "AttackPatterns": [
            {
              "ID": "1",
              "Name": "Spear Phishing",
              "Description": {...},
              "Prerequisites": [...],
              "Consequences": [...],
              "RelatedWeaknesses": [
                {
                  "ID": "123",
                  "Relationship": "Exploits"
                }
              ],
              "RelatedAttackPatterns": [...]
            }
          ]
        }
        """
        patterns = capec_json.get("AttackPatterns", [])
        if not patterns:
            raise ValueError("Expected 'AttackPatterns' key in CAPEC JSON response")

        for pattern in patterns:
            self._add_attack_pattern(pattern)

        # Add relationships between attack patterns
        self._add_pattern_relationships(patterns)

        return self.graph

    def _add_attack_pattern(self, pattern: dict):
        """Add a CAPEC attack pattern entry as a sec:AttackPattern node."""
        capec_id = pattern.get("ID", "")
        if not capec_id:
            return

        # Create AttackPattern node
        capec_id_full = f"CAPEC-{capec_id}" if not capec_id.startswith("CAPEC-") else capec_id
        pattern_node = URIRef(f"{EX}attackPattern/{capec_id_full}")
        self.graph.add((pattern_node, RDF.type, SEC.AttackPattern))
        self.graph.add((pattern_node, SEC.capecId, Literal(capec_id_full, datatype=XSD.string)))

        # Add name
        if pattern.get("Name"):
            self.graph.add((pattern_node, RDFS.label, Literal(pattern["Name"], datatype=XSD.string)))

        # Add description (handle nested structure)
        if pattern.get("Description"):
            desc_text = self._extract_description(pattern["Description"])
            if desc_text:
                self.graph.add((pattern_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Add prerequisites
        if pattern.get("Prerequisites"):
            for prereq in pattern["Prerequisites"]:
                if prereq.get("Description"):
                    prereq_text = self._extract_description(prereq["Description"])
                    if prereq_text:
                        self.graph.add((pattern_node, SEC.prerequisite, Literal(prereq_text, datatype=XSD.string)))

        # Add consequences
        if pattern.get("Consequences"):
            for consequence in pattern["Consequences"]:
                if consequence.get("Description"):
                    cons_text = self._extract_description(consequence["Description"])
                    if cons_text:
                        self.graph.add((pattern_node, SEC.consequence, Literal(cons_text, datatype=XSD.string)))

        # Add related weaknesses (exploits relationship)
        if pattern.get("RelatedWeaknesses"):
            self._add_weakness_relationships(pattern_node, pattern["RelatedWeaknesses"])

        # Add related techniques (implements relationship)
        if pattern.get("RelatedTechniques"):
            self._add_technique_relationships(pattern_node, pattern["RelatedTechniques"])

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

            # Create the exploits edge (this pattern exploits the weakness)
            self.graph.add((pattern_node, SEC.exploits, weakness_node))

    def _add_technique_relationships(self, pattern_node, related_techniques: list):
        """Add implements relationships to ATT&CK techniques."""
        for rel in related_techniques:
            technique_id = rel.get("ID", "")
            if not technique_id:
                continue

            technique_id_full = f"{technique_id}" if technique_id.startswith("T") else f"T{technique_id}"
            technique_node = URIRef(f"{EX}technique/{technique_id_full}")

            # Create the implements edge (this pattern is implemented by the technique)
            self.graph.add((pattern_node, SEC.implements, technique_node))

    def _add_pattern_relationships(self, patterns: list):
        """Add relationships between attack patterns (parent/child/related)."""
        capec_lookup = {p.get("ID", ""): p for p in patterns if p.get("ID")}

        for pattern in patterns:
            capec_id = pattern.get("ID", "")
            if not capec_id:
                continue

            capec_id_full = f"CAPEC-{capec_id}" if not capec_id.startswith("CAPEC-") else capec_id
            pattern_node = URIRef(f"{EX}attackPattern/{capec_id_full}")

            # Add related attack patterns
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
                elif relationship == "PeerOf":
                    self.graph.add((pattern_node, SEC.peerOf, related_node))


def validate_output(ttl_file: str, shapes_file: str = "docs/ontology/shacl/capec-shapes.ttl") -> bool:
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
    parser = argparse.ArgumentParser(description="ETL: MITRE CAPEC JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CAPEC JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/capec-shapes.ttl", help="SHACL shapes file")
    args = parser.parse_args()

    # Load input JSON
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CAPEC JSON from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        capec_json = json.load(f)

    # Transform
    print("Transforming to RDF...")
    transformer = CAPECtoRDFTransformer()
    graph = transformer.transform(capec_json)

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
