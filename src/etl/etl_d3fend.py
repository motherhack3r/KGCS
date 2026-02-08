"""ETL Pipeline: MITRE D3FEND JSON -> RDF Turtle.

Defensive techniques that mitigate ATT&CK techniques.

Usage:
    python -m src.etl.etl_d3fend --input data/d3fend/raw/d3fend.json \
                              --output data/d3fend/samples/d3fend-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import write_graph_turtle_lines
except Exception:
    from .ttl_writer import write_graph_turtle_lines


class D3FENDtoRDFTransformer:
    """Transform D3FEND JSON to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, json_data: dict) -> Graph:
        """Transform D3FEND JSON to RDF graph."""
        if "DefensiveTechniques" in json_data:
            techniques = json_data["DefensiveTechniques"]

            for technique in techniques:
                self._add_defensive_technique(technique)

            self._add_technique_relationships(techniques)
            self._add_mitigation_relationships(techniques)
            return self.graph

        if "@graph" in json_data:
            self._transform_jsonld(json_data.get("@graph", []))
            return self.graph

        # SPARQL full mappings format (results -> bindings)
        if "results" in json_data and isinstance(json_data.get("results"), dict):
            bindings = json_data.get("results", {}).get("bindings", [])
            self._transform_sparql_bindings(bindings)
            return self.graph

        raise ValueError("Unsupported D3FEND JSON format")

    def _transform_jsonld(self, graph_items: list) -> None:
        """Transform D3FEND JSON-LD (@graph) into DefensiveTechnique nodes."""
        for item in graph_items:
            if not isinstance(item, dict):
                continue
            if not self._is_defensive_technique(item):
                continue

            d3fend_id = self._get_value(item.get("d3f:d3fend-id")) or self._get_value(item.get("d3f:d3fendId"))
            label = self._get_value(item.get("rdfs:label"))
            definition = self._get_value(item.get("d3f:definition"))

            if not d3fend_id:
                fallback_id = self._get_value(item.get("@id"))
                if not fallback_id:
                    continue
                d3fend_id = fallback_id

            d3fend_id_full = f"{d3fend_id}" if str(d3fend_id).startswith("D3") else f"D3FEND-{d3fend_id}"
            technique_node = URIRef(f"{self.EX}deftech/{d3fend_id_full}")

            self.graph.add((technique_node, RDF.type, self.SEC.DefensiveTechnique))
            self.graph.add((technique_node, self.SEC.d3fendId, Literal(d3fend_id_full, datatype=XSD.string)))

            if label:
                self.graph.add((technique_node, RDFS.label, Literal(label, datatype=XSD.string)))

            if definition:
                self.graph.add((technique_node, self.SEC.description, Literal(definition, datatype=XSD.string)))

    def _transform_sparql_bindings(self, bindings: list) -> None:
        """Transform SPARQL full mappings (D3FEND to ATT&CK) into mitigates relationships."""
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            
            # Extract D3FEND technique label and ATT&CK technique ID from SPARQL results
            def_tech_label = None
            if "def_tech_label" in binding and isinstance(binding["def_tech_label"], dict):
                def_tech_label = binding["def_tech_label"].get("value")
            
            att_tech_id = None
            if "off_tech_id" in binding and isinstance(binding["off_tech_id"], dict):
                att_tech_id = binding["off_tech_id"].get("value")
            
            # If we have both, create a mitigates relationship
            if def_tech_label and att_tech_id:
                # Normalize IDs
                att_id_full = f"{att_tech_id}" if str(att_tech_id).startswith("T") else f"T{att_tech_id}"
                
                # Use def_tech_label to create URI (convert to proper D3FEND ID-like format)
                # D3FEND uses CamelCase for technique names in URIs
                def_tech_uri = "".join(word.capitalize() for word in def_tech_label.split())
                
                def_tech_node = URIRef(f"{self.EX}deftech/{def_tech_uri}")
                att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                
                # Add the mitigates relationship
                self.graph.add((def_tech_node, self.SEC.mitigates, att_node))

    def _is_defensive_technique(self, item: dict) -> bool:
        types = item.get("@type")
        if isinstance(types, str):
            types = [types]

        if isinstance(types, list) and "d3f:DefensiveTechnique" in types:
            return True

        sub_classes = item.get("rdfs:subClassOf")
        if isinstance(sub_classes, dict):
            sub_classes = [sub_classes]

        if isinstance(sub_classes, list):
            for sub in sub_classes:
                if isinstance(sub, dict) and sub.get("@id") == "d3f:DefensiveTechnique":
                    return True

        # Some D3FEND JSON-LD represents techniques as owl:Class entries with
        # properties like d3f:d3fend-id or d3f:definition rather than explicit
        # type annotations. Treat presence of d3fend-id or definition as an
        # indicator of a defensive technique.
        if item.get("d3f:d3fend-id") or item.get("d3f:d3fendId"):
            return True
        if item.get("d3f:definition") or item.get("d3f:attack-id"):
            return True

        return False

    def _get_value(self, value):
        if isinstance(value, dict):
            return value.get("@value") or value.get("@id") or value.get("value")
        return value

    def _add_defensive_technique(self, technique: dict):
        """Add a D3FEND defensive technique node, with status, references, and tags."""
        d3fend_id = technique.get("ID", "")
        if not d3fend_id:
            return
        d3fend_id_full = f"D3FEND-{d3fend_id}" if not d3fend_id.startswith("D3FEND-") else d3fend_id
        technique_node = URIRef(f"{self.EX}deftech/{d3fend_id_full}")
        self.graph.add((technique_node, RDF.type, self.SEC.DefensiveTechnique))
        self.graph.add((technique_node, self.SEC.d3fendId, Literal(d3fend_id_full, datatype=XSD.string)))

        if technique.get("Name"):
            self.graph.add((technique_node, RDFS.label, Literal(technique["Name"], datatype=XSD.string)))

        if technique.get("Description"):
            desc_text = self._extract_description(technique["Description"])
            if desc_text:
                self.graph.add((technique_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Emit status if present
        if technique.get("Status"):
            self.graph.add((technique_node, self.SEC.status, Literal(technique["Status"], datatype=XSD.string)))

        # Emit tags if present (as repeated sec:tag literals)
        tags = technique.get("Tags")
        if tags:
            if isinstance(tags, str):
                self.graph.add((technique_node, self.SEC.tag, Literal(tags, datatype=XSD.string)))
            elif isinstance(tags, list):
                for tag in tags:
                    if tag:
                        self.graph.add((technique_node, self.SEC.tag, Literal(str(tag), datatype=XSD.string)))

        # Emit references if present (as nodes)
        for ref in technique.get("References", []):
            url = ref.get("URL") or ref.get("url")
            ref_type = ref.get("ReferenceType") or ref.get("referenceType")
            if not (url or ref_type):
                continue
            ref_id = f"{d3fend_id_full}-ref-{url or ref_type}".replace(" ", "_")
            ref_node = URIRef(f"{self.EX}reference/{ref_id}")
            self.graph.add((ref_node, RDF.type, self.SEC.Reference))
            if url:
                self.graph.add((ref_node, self.SEC.url, Literal(url, datatype=XSD.anyURI)))
            if ref_type:
                self.graph.add((ref_node, self.SEC.referenceType, Literal(ref_type, datatype=XSD.string)))
            self.graph.add((technique_node, self.SEC.references, ref_node))

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

    def _add_technique_relationships(self, techniques: list):
        """Add parent/child relationships between defensive techniques."""
        for technique in techniques:
            d3fend_id = technique.get("ID", "")
            if not d3fend_id:
                continue
            
            d3fend_id_full = f"D3FEND-{d3fend_id}" if not d3fend_id.startswith("D3FEND-") else d3fend_id
            technique_node = URIRef(f"{self.EX}deftech/{d3fend_id_full}")
            
            if technique.get("ParentID"):
                parent_id = technique["ParentID"]
                parent_id_full = f"D3FEND-{parent_id}" if not parent_id.startswith("D3FEND-") else parent_id
                parent_node = URIRef(f"{self.EX}deftech/{parent_id_full}")
                self.graph.add((technique_node, self.SEC.childOf, parent_node))
                self.graph.add((parent_node, self.SEC.parentOf, technique_node))

    def _add_mitigation_relationships(self, techniques: list):
        """Add mitigates relationships to ATT&CK techniques."""
        for technique in techniques:
            d3fend_id = technique.get("ID", "")
            if not d3fend_id:
                continue
            
            d3fend_id_full = f"D3FEND-{d3fend_id}" if not d3fend_id.startswith("D3FEND-") else d3fend_id
            technique_node = URIRef(f"{self.EX}deftech/{d3fend_id_full}")
            
            if technique.get("MitigatesTechniques"):
                for att_technique in technique["MitigatesTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((technique_node, self.SEC.mitigates, att_node))


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE D3FEND JSON -> RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input D3FEND JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--append", action='store_true', help='Append to existing output file (suppress headers)')
    parser.add_argument('--validate', action='store_true', help='Validate output with SHACL')
    parser.add_argument('--shapes', help='SHACL shapes file (defaults to docs/ontology/shacl/d3fend-shapes.ttl)')
    
    args = parser.parse_args()
    
    # Accept either a single JSON file or a directory containing multiple D3FEND JSON files
    json_files = []
    if os.path.isdir(args.input):
        for p in sorted(Path(args.input).rglob('*.json')):
            json_files.append(str(p))
    else:
        json_files = [args.input]

    transformer = D3FENDtoRDFTransformer()
    any_loaded = False
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8', errors='replace') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Warning: Error loading JSON {jf}: {e}")
            continue
        any_loaded = True
        print(f"Transforming {os.path.basename(jf)} to RDF...")
        try:
            transformer.transform(json_data)
        except Exception as e:
            print(f"Warning: transformation failed for {jf}: {e}")

    if not any_loaded:
        print(f"Error: no D3FEND JSON files loaded from {args.input}")
        return 1

    # Write the combined graph to output
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    write_graph_turtle_lines(transformer.graph, args.output, include_prefixes=not args.append, append=args.append)

    # SHACL validation
    if args.validate:
        print(f"\nValidating {args.output}...")
        try:
            from src.core.validation import run_validator, load_graph
        except ImportError:
            from core.validation import run_validator, load_graph

        shapes_file = args.shapes or 'docs/ontology/shacl/d3fend-shapes.ttl'
        if os.path.exists(shapes_file):
            shapes = load_graph(shapes_file)
            conforms, _, _ = run_validator(args.output, shapes)
            if conforms:
                print(f"[OK] Validation passed!")
            else:
                print(f"[FAIL] Validation failed!")
                return 1
        else:
            print(f"Warning: Could not find shapes file: {shapes_file}")

    print(f"Transformation complete: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
