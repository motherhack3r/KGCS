#!/usr/bin/env python3
"""
D3FEND ETL: Transform MITRE D3FEND JSON to RDF (Turtle)
Defensive techniques that mitigate ATT&CK techniques.
"""

import json
import argparse
from pathlib import Path
from typing import Optional

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


class D3FENDtoRDFTransformer:
    """Transform D3FEND JSON to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        
        # Bind namespaces
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, json_data: dict) -> Graph:
        """Transform D3FEND JSON to RDF graph."""
        if "DefensiveTechniques" not in json_data:
            raise ValueError("JSON must contain 'DefensiveTechniques' array")
        
        techniques = json_data["DefensiveTechniques"]
        
        # Add all D3FEND defensive techniques
        for technique in techniques:
            self._add_defensive_technique(technique)
        
        # Add relationships between techniques
        self._add_technique_relationships(techniques)
        
        # Add mitigation relationships to ATT&CK techniques
        self._add_mitigation_relationships(techniques)
        
        return self.graph

    def _add_defensive_technique(self, technique: dict):
        """Add a D3FEND defensive technique node."""
        d3fend_id = technique.get("ID", "")
        if not d3fend_id:
            return
        
        d3fend_id_full = f"D3FEND-{d3fend_id}" if not d3fend_id.startswith("D3FEND-") else d3fend_id
        technique_node = URIRef(f"{self.EX}deftech/{d3fend_id_full}")
        
        # Add RDF type
        self.graph.add((technique_node, RDF.type, self.SEC.DefensiveTechnique))
        
        # Add identifier
        self.graph.add((technique_node, self.SEC.d3fendId, Literal(d3fend_id_full, datatype=XSD.string)))
        
        # Add label
        if technique.get("Name"):
            self.graph.add((technique_node, RDFS.label, Literal(technique["Name"], datatype=XSD.string)))
        
        # Add description
        if technique.get("Description"):
            desc_text = self._extract_description(technique["Description"])
            if desc_text:
                self.graph.add((technique_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))
        
        # Add references
        if technique.get("References"):
            for ref in technique["References"]:
                self._add_reference(technique_node, ref)

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

    def _add_reference(self, technique_node, ref: dict):
        """Add reference URL to technique."""
        if isinstance(ref, dict) and ref.get("URL"):
            try:
                ref_uri = URIRef(ref["URL"])
                self.graph.add((technique_node, self.SEC.references, ref_uri))
            except:
                pass

    def _add_technique_relationships(self, techniques: list):
        """Add parent/child relationships between defensive techniques."""
        d3fend_lookup = {t.get("ID", ""): t for t in techniques if t.get("ID")}
        
        for technique in techniques:
            d3fend_id = technique.get("ID", "")
            if not d3fend_id:
                continue
            
            d3fend_id_full = f"D3FEND-{d3fend_id}" if not d3fend_id.startswith("D3FEND-") else d3fend_id
            technique_node = URIRef(f"{self.EX}deftech/{d3fend_id_full}")
            
            # Parent relationships
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
            
            # Mitigates relationships
            if technique.get("MitigatesTechniques"):
                for att_technique in technique["MitigatesTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((technique_node, self.SEC.mitigates, att_node))

    def get_rdf(self) -> str:
        """Get RDF as Turtle string."""
        return self.graph.serialize(format="turtle")


def validate_output(ttl_content: str, shapes_path: Optional[str] = None) -> bool:
    """Validate RDF output against SHACL shapes."""
    try:
        from pyshacl import validate
        
        shapes_file = shapes_path or "docs/ontology/shacl/d3fend-shapes.ttl"
        if not Path(shapes_file).exists():
            print(f"⚠️  SHACL shapes file not found: {shapes_file}")
            return True
        
        data_graph = Graph()
        data_graph.parse(data=ttl_content, format="turtle")
        
        shapes_graph = Graph()
        shapes_graph.parse(shapes_file, format="turtle")
        
        conforms, report_graph, report_text = validate(data_graph, shapesgraph=shapes_graph)
        
        print(f"\n{report_text}")
        
        # Save report
        report_json = report_graph.serialize(format="json-ld")
        report_file = f"artifacts/shacl-report-d3fend-sample.ttl.json"
        Path(report_file).parent.mkdir(exist_ok=True)
        with open(report_file, "w") as f:
            f.write(report_json)
        
        return conforms
    except ImportError:
        print("⚠️  pyshacl not installed; skipping validation")
        return True
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Transform D3FEND JSON to RDF Turtle")
    parser.add_argument("--input", required=True, help="Input D3FEND JSON file")
    parser.add_argument("--output", required=True, help="Output RDF Turtle file")
    parser.add_argument("--shapes", help="SHACL shapes file for validation")
    parser.add_argument("--validate", action="store_true", help="Validate output against SHACL shapes")
    
    args = parser.parse_args()
    
    # Load JSON
    try:
        with open(args.input, "r") as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return 1
    
    # Transform to RDF
    try:
        print(f"Loading D3FEND JSON from {args.input}...")
        transformer = D3FENDtoRDFTransformer()
        print("Transforming to RDF...")
        transformer.transform(json_data)
        ttl_content = transformer.get_rdf()
        
        # Write output
        print(f"Writing RDF to {args.output}...")
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(ttl_content)
        
        # Validate if requested
        if args.validate:
            print("\nRunning SHACL validation...")
            conforms = validate_output(ttl_content, args.shapes)
            if conforms:
                print("Validation: CONFORMS\n✓ Validation passed!")
                return 0
            else:
                print("Validation: DOES NOT CONFORM\n❌ Validation failed!")
                return 1
        else:
            print(f"✓ Transformation complete: {args.output}")
            return 0
    
    except Exception as e:
        print(f"❌ Transformation error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
