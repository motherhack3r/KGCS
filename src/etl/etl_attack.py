"""ETL Pipeline: MITRE ATT&CK STIX JSON → RDF Turtle with SHACL validation.

Transforms official MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge)
STIX 2.1 JSON into RDF triples conforming to the Core Ontology Technique/Tactic classes.

Usage:
    python -m src.etl.etl_attack --input data/attack/raw/attack-stix.json \
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
from rdflib import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import (
        write_graph_turtle_lines,
        write_graph_ntriples_lines,
        write_graph_turtle_split_lines,
        write_graph_ntriples_split_lines,
    )
except Exception:
    from .ttl_writer import (
        write_graph_turtle_lines,
        write_graph_ntriples_lines,
        write_graph_turtle_split_lines,
        write_graph_ntriples_split_lines,
    )

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

        if tactic_obj.get("description"):
            self.graph.add((tactic_node, SEC.description, Literal(tactic_obj["description"], datatype=XSD.string)))

        if tactic_obj.get("x_mitre_deprecated") is not None:
            self.graph.add((tactic_node, SEC.deprecated, Literal(bool(tactic_obj["x_mitre_deprecated"]), datatype=XSD.boolean)))

        if tactic_obj.get("created"):
            self.graph.add((tactic_node, SEC.created, Literal(tactic_obj["created"], datatype=XSD.string)))
        if tactic_obj.get("modified"):
            self.graph.add((tactic_node, SEC.modified, Literal(tactic_obj["modified"], datatype=XSD.string)))

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

        # Platforms
        if technique_obj.get("x_mitre_platforms"):
            for p in technique_obj["x_mitre_platforms"]:
                self.graph.add((technique_node, SEC.platform, Literal(p, datatype=XSD.string)))

        # Data Sources
        if technique_obj.get("x_mitre_data_sources"):
            for ds in technique_obj["x_mitre_data_sources"]:
                self.graph.add((technique_node, SEC.dataSource, Literal(ds, datatype=XSD.string)))

        # Data Components
        if technique_obj.get("x_mitre_data_components"):
            for dc in technique_obj["x_mitre_data_components"]:
                self.graph.add((technique_node, SEC.dataComponent, Literal(dc, datatype=XSD.string)))

        # Detection guidance
        if technique_obj.get("x_mitre_detection"):
            self.graph.add((technique_node, SEC.detection, Literal(technique_obj["x_mitre_detection"], datatype=XSD.string)))

        # Permissions required
        if technique_obj.get("x_mitre_permissions_required"):
            for perm in technique_obj["x_mitre_permissions_required"]:
                self.graph.add((technique_node, SEC.permissionsRequired, Literal(perm, datatype=XSD.string)))

        # Effective permissions
        if technique_obj.get("x_mitre_effective_permissions"):
            for perm in technique_obj["x_mitre_effective_permissions"]:
                self.graph.add((technique_node, SEC.effectivePermissions, Literal(perm, datatype=XSD.string)))

        # Network requirements
        if technique_obj.get("x_mitre_network_requirements"):
            for req in technique_obj["x_mitre_network_requirements"]:
                self.graph.add((technique_node, SEC.networkRequirements, Literal(req, datatype=XSD.string)))

        # Contributors
        if technique_obj.get("x_mitre_contributors"):
            for c in technique_obj["x_mitre_contributors"]:
                self.graph.add((technique_node, SEC.contributor, Literal(c, datatype=XSD.string)))

        # Deprecated
        if technique_obj.get("x_mitre_deprecated") is not None:
            self.graph.add((technique_node, SEC.deprecated, Literal(bool(technique_obj["x_mitre_deprecated"]), datatype=XSD.boolean)))

        # Created/Modified
        if technique_obj.get("created"):
            self.graph.add((technique_node, SEC.created, Literal(technique_obj["created"], datatype=XSD.string)))
        if technique_obj.get("modified"):
            self.graph.add((technique_node, SEC.modified, Literal(technique_obj["modified"], datatype=XSD.string)))

        # Relationships: Tactic (belongs_to)
        if technique_obj.get("kill_chain_phases"):
            for phase in technique_obj["kill_chain_phases"]:
                phase_name = phase.get("phase_name", "")
                if phase_name in tactics_map:
                    tactic_node = tactics_map[phase_name]
                    self.graph.add((technique_node, SEC.belongs_to, tactic_node))

        # Subtechnique-of
        if is_subtechnique:
            parent_id = attack_id.split(".")[0]
            parent_node = URIRef(f"{EX}technique/{parent_id}")
            self.graph.add((technique_node, SEC.subtechnique_of, parent_node))

        # CAPEC References (extract from external_references with source_name='capec')
        capec_ids = self._extract_capec_ids(technique_obj)
        for capec_id in capec_ids:
            # Normalize CAPEC ID (remove 'CAPEC-' prefix if double-prefixed)
            capec_id_clean = capec_id.replace('CAPEC-CAPEC-', 'CAPEC-').replace('CAPEC-', '')
            if capec_id_clean:
                capec_node = URIRef(f"{EX}capec/{capec_id_clean}")
                self.graph.add((capec_node, RDF.type, SEC.AttackPattern))
                self.graph.add((capec_node, SEC.capecId, Literal(capec_id_clean, datatype=XSD.string)))
                # Link technique→capec (technique implements/is_derived_from CAPEC pattern)
                self.graph.add((technique_node, SEC.derived_from, capec_node))

    def _extract_attack_id(self, technique_obj: dict) -> str:
        """Extract ATT&CK ID (e.g., T1234) from external references."""
        external_refs = technique_obj.get("external_references", [])
        for ref in external_refs:
            if ref.get("source_name") == "mitre-attack":
                return ref.get("external_id", "")
        return ""

    def _extract_capec_ids(self, technique_obj: dict) -> list:
        """Extract CAPEC IDs from external references.
        
        CAPEC IDs may be stored with double prefix (CAPEC-CAPEC-13) due to STIX structure.
        This method returns all unique CAPEC IDs found.
        """
        capec_ids = []
        external_refs = technique_obj.get("external_references", [])
        for ref in external_refs:
            source = ref.get("source_name", "").lower()
            if source == "capec":
                capec_id = ref.get("external_id", "")
                if capec_id:
                    capec_ids.append(capec_id)
        return capec_ids


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE ATT&CK STIX JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input ATT&CK STIX JSON file or directory")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--nodes-out", help="Optional nodes-only output file")
    parser.add_argument("--rels-out", help="Optional relationships-only output file")
    parser.add_argument("--rels-include-types", action="store_true", help="Also write rdf:type triples to rels output")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/attack-shapes.ttl", help="SHACL shapes file")
    parser.add_argument("--append", action="store_true", help="Append to existing output file instead of overwriting")
    parser.add_argument("--format", choices=["ttl","nt"], default="ttl", help="Output format (ttl or nt)")
    args = parser.parse_args()

    if (args.nodes_out and not args.rels_out) or (args.rels_out and not args.nodes_out):
        print("Error: --nodes-out and --rels-out must be provided together", file=sys.stderr)
        sys.exit(1)

    # Support a single file or a directory of STIX JSON files (enterprise, mobile, ics, pre-attack)
    files = []
    if os.path.isdir(args.input):
        for fn in sorted(os.listdir(args.input)):
            # Skip per-directory metadata files (created by downloader)
            if fn.lower() == 'metadata.json':
                continue
            if fn.lower().endswith('.json'):
                files.append(os.path.join(args.input, fn))
    else:
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        files = [args.input]

    print(f"Loading ATT&CK STIX JSON files: {files}")
    combined_graph = Graph()
    transformer = ATTACKtoRDFTransformer()
    for fpath in files:
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                attack_json = json.load(fh)
        except Exception as e:
            print(f"Warning: failed to load {fpath}: {e}", file=sys.stderr)
            continue
        print(f"Transforming {os.path.basename(fpath)} to RDF...")
        try:
            g = transformer.transform(attack_json)
            for t in g:
                combined_graph.add(t)
        except Exception as e:
            print(f"Warning: transformation failed for {fpath}: {e}", file=sys.stderr)

    graph = combined_graph

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    if args.format == "nt":
        write_graph_ntriples_lines(graph, args.output, append=args.append)
    else:
        write_graph_turtle_lines(graph, args.output, include_prefixes=not args.append, append=args.append)

    if args.nodes_out and args.rels_out:
        os.makedirs(os.path.dirname(args.nodes_out) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(args.rels_out) or ".", exist_ok=True)
        if args.format == "nt":
            write_graph_ntriples_split_lines(
                graph,
                args.nodes_out,
                args.rels_out,
                append=args.append,
                rels_include_types=args.rels_include_types,
            )
        else:
            write_graph_turtle_split_lines(
                graph,
                args.nodes_out,
                args.rels_out,
                include_prefixes=not args.append,
                append=args.append,
                rels_include_types=args.rels_include_types,
            )

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
