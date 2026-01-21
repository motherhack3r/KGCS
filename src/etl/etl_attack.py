"""ETL Pipeline: MITRE ATT&CK STIX JSON → RDF Turtle with SHACL validation.

Transforms official MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge)
STIX 2.1 JSON into RDF triples conforming to the Core Ontology Technique/Tactic classes.

Usage:
    python -m kgcs.etl.etl_attack --input data/attack/raw/attack-stix.json \
                              --output data/attack/samples/attack-output.ttl \
                              --validate
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

SEC = Namespace("https://example.org/sec/core#")
EX = Namespace("https://example.org/")


class ATTACKtoRDFTransformer:
    """Transform MITRE ATT&CK STIX JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        self.graph.bind("sec", SEC)
        self.graph.bind("ex", EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)

    def transform(self, attack_json: dict) -> Graph:
        """Transform ATT&CK STIX JSON response to RDF."""
        objects = attack_json.get("objects", [])
        if not objects:
            raise ValueError("Expected 'objects' key in ATT&CK STIX response")

        tactics_map = {}
        techniques = []

        for obj in objects:
            if obj.get("type") == "x-mitre-tactic":
                tactic_node = self._add_tactic(obj)
                shortname = obj.get("x_mitre_shortname", "")
                if shortname:
                    tactics_map[shortname] = tactic_node
            elif obj.get("type") == "attack-pattern":
                techniques.append(obj)

        for technique in techniques:
            self._add_technique(technique, tactics_map)

        return self.graph

    def _add_tactic(self, tactic_obj: dict):
        """Add a Tactic node."""
        tactic_id = tactic_obj.get("id", "")
        if not tactic_id:
            return None

        tactic_node = URIRef(f"{EX}tactic/{tactic_id}")
        self.graph.add((tactic_node, RDF.type, SEC.Tactic))

        shortname = tactic_obj.get("x_mitre_shortname", "")
        if shortname:
            self.graph.add((tactic_node, SEC.tacticId, Literal(shortname, datatype=XSD.string)))

        if tactic_obj.get("name"):
            self.graph.add((tactic_node, RDFS.label, Literal(tactic_obj["name"], datatype=XSD.string)))

        return tactic_node

    def _add_technique(self, technique_obj: dict, tactics_map: dict):
        """Add a Technique or SubTechnique node."""
        stix_id = technique_obj.get("id", "")
        if not stix_id:
            return

        attack_id = self._extract_attack_id(technique_obj)
        if not attack_id:
            return

        is_subtechnique = "." in attack_id

        if is_subtechnique:
            technique_node = URIRef(f"{EX}subtechnique/{attack_id}")
            self.graph.add((technique_node, RDF.type, SEC.SubTechnique))
        else:
            technique_node = URIRef(f"{EX}technique/{attack_id}")
            self.graph.add((technique_node, RDF.type, SEC.Technique))

        self.graph.add((technique_node, SEC.attackTechniqueId, Literal(attack_id, datatype=XSD.string)))

        name = technique_obj.get("name", "")
        if name:
            name = re.sub(r"^[A-Z]\d+(?:\.\d+)?\s*:\s*", "", name)
            self.graph.add((technique_node, RDFS.label, Literal(name, datatype=XSD.string)))

        if technique_obj.get("description"):
            self.graph.add((technique_node, SEC.description, Literal(technique_obj["description"], datatype=XSD.string)))

        if technique_obj.get("kill_chain_phases"):
            for phase in technique_obj["kill_chain_phases"]:
                phase_name = phase.get("phase_name", "")
                if phase_name in tactics_map:
                    tactic_node = tactics_map[phase_name]
                    self.graph.add((technique_node, SEC.belongs_to, tactic_node))

        if is_subtechnique:
            parent_id = attack_id.split(".")[0]
            parent_node = URIRef(f"{EX}technique/{parent_id}")
            self.graph.add((technique_node, SEC.subtechnique_of, parent_node))

    def _extract_attack_id(self, technique_obj: dict) -> str:
        """Extract ATT&CK ID (e.g., T1234) from external references."""
        external_refs = technique_obj.get("external_references", [])
        for ref in external_refs:
            if ref.get("source_name") == "mitre-attack":
                return ref.get("external_id", "")
        return ""


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE ATT&CK STIX JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input ATT&CK STIX JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/attack-shapes.ttl", help="SHACL shapes file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading ATT&CK STIX JSON from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        attack_json = json.load(f)

    print("Transforming to RDF...")
    transformer = ATTACKtoRDFTransformer()
    graph = transformer.transform(attack_json)

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
