"""ETL Pipeline: MITRE SHIELD JSON -> RDF Turtle.

Deception techniques that counter ATT&CK techniques.

Usage:
    python -m src.etl.etl_shield --input data/shield/raw/shield.json \
                              --output data/shield/samples/shield-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
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


class SHIELDtoRDFTransformer:
    """Transform SHIELD JSON to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, json_data: dict) -> Graph:
        """Transform SHIELD JSON to RDF graph."""
        if "DeceptionTechniques" not in json_data:
            raise ValueError("JSON must contain 'DeceptionTechniques' array")
        
        techniques = json_data["DeceptionTechniques"]
        
        for technique in techniques:
            self._add_deception_technique(technique)
        
        self._add_counter_relationships(techniques)
        
        return self.graph

    def _add_deception_technique(self, technique: dict):
        """Add a SHIELD deception technique node."""
        shield_id = technique.get("ID", "")
        if not shield_id:
            return

        shield_id_full = f"SHIELD-{shield_id}" if not shield_id.startswith("SHIELD-") else shield_id
        technique_node = URIRef(f"{self.EX}deception/{shield_id_full}")

        self.graph.add((technique_node, RDF.type, self.SEC.DeceptionTechnique))
        self.graph.add((technique_node, self.SEC.shieldId, Literal(shield_id_full, datatype=XSD.string)))

        if technique.get("Name"):
            self.graph.add((technique_node, RDFS.label, Literal(technique["Name"], datatype=XSD.string)))

        if technique.get("Description"):
            desc_text = self._extract_description(technique["Description"])
            if desc_text:
                self.graph.add((technique_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))

        operational_impact = technique.get("OperationalImpact")
        ease_of_employment = technique.get("EaseOfEmployment")
        if operational_impact:
            self.graph.add((technique_node, self.SEC.operationalImpact, Literal(operational_impact, datatype=XSD.string)))
        if ease_of_employment:
            self.graph.add((technique_node, self.SEC.easeOfEmployment, Literal(ease_of_employment, datatype=XSD.string)))

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

    def _add_counter_relationships(self, techniques: list):
        """Add counters relationships to ATT&CK techniques."""
        for technique in techniques:
            shield_id = technique.get("ID", "")
            if not shield_id:
                continue

            shield_id_full = f"SHIELD-{shield_id}" if not shield_id.startswith("SHIELD-") else shield_id
            technique_node = URIRef(f"{self.EX}deception/{shield_id_full}")

            if technique.get("CountersTechniques"):
                for att_technique in technique["CountersTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((technique_node, self.SEC.counters, att_node))
            # Ensure to handle missing/optional fields gracefully
            if technique.get("Counters"):
                counters = technique["Counters"]
                if isinstance(counters, list):
                    for tech_id in counters:
                        if tech_id:
                            self.graph.add((technique_node, self.SEC.counters, URIRef(f"{self.EX}technique/{tech_id}")))
                elif isinstance(counters, str):
                    self.graph.add((technique_node, self.SEC.counters, URIRef(f"{self.EX}technique/{counters}")))


def _load_shield_data(input_path: str) -> dict:
    if os.path.isdir(input_path):
        # Merge all JSON files in the directory into a single DeceptionTechniques array
        import glob
        normalized = []
        for file in glob.glob(os.path.join(input_path, "*.json")):
            with open(file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    continue
                # Accept both arrays and dicts with arrays
                items = []
                if isinstance(data, list):
                    # If the file is a top-level array, treat each element as a technique dict if possible
                    for item in data:
                        if isinstance(item, dict):
                            items.append(item)
                elif isinstance(data, dict):
                    # Try common keys
                    items = data.get("DeceptionTechniques") or data.get("techniques") or data.get("Techniques") or data.get("items") or []
                    if isinstance(items, dict):
                        items = [items]
                # else: skip non-dict, non-list
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    tech_id = item.get("id") or item.get("ID")
                    name = item.get("name") or item.get("Name")
                    description = item.get("description") or item.get("Description") or item.get("long_description")
                    normalized.append({
                        "ID": tech_id,
                        "Name": name,
                        "Description": description
                    })
        return {"DeceptionTechniques": normalized}
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE SHIELD JSON -> RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input SHIELD JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--nodes-out", help="Optional nodes-only output file")
    parser.add_argument("--rels-out", help="Optional relationships-only output file")
    parser.add_argument("--rels-include-types", action="store_true", help="Also write rdf:type triples to rels output")
    parser.add_argument("--format", choices=["ttl","nt"], default="ttl", help="Output format (ttl or nt)")
    parser.add_argument("--append", action='store_true', help='Append to existing output file (suppress headers)')
    
    args = parser.parse_args()

    if (args.nodes_out and not args.rels_out) or (args.rels_out and not args.nodes_out):
        print("Error: --nodes-out and --rels-out must be provided together", file=sys.stderr)
        return 1
    
    try:
        json_data = _load_shield_data(args.input)
    except Exception as e:
        print(f"Error loading SHIELD data: {e}")
        return 1
    
    try:
        print(f"Loading SHIELD data from {args.input}...")
        transformer = SHIELDtoRDFTransformer()
        print("Transforming to RDF...")
        transformer.transform(json_data)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing RDF to {args.output}...")
        if args.format == "nt":
            write_graph_ntriples_lines(transformer.graph, args.output, append=args.append)
        else:
            write_graph_turtle_lines(transformer.graph, args.output, include_prefixes=not args.append, append=args.append)

        if args.nodes_out and args.rels_out:
            Path(args.nodes_out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.rels_out).parent.mkdir(parents=True, exist_ok=True)
            if args.format == "nt":
                write_graph_ntriples_split_lines(
                    transformer.graph,
                    args.nodes_out,
                    args.rels_out,
                    append=args.append,
                    rels_include_types=args.rels_include_types,
                )
            else:
                write_graph_turtle_split_lines(
                    transformer.graph,
                    args.nodes_out,
                    args.rels_out,
                    include_prefixes=not args.append,
                    append=args.append,
                    rels_include_types=args.rels_include_types,
                )
        
        print(f"Transformation complete: {args.output}")
        return 0
    
    except Exception as e:
        print(f"Transformation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
