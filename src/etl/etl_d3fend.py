"""ETL Pipeline: MITRE D3FEND JSON → RDF Turtle.

Defensive techniques that mitigate ATT&CK techniques.

Usage:
    python -m kgcs.etl.etl_d3fend --input data/d3fend/raw/d3fend.json \
                              --output data/d3fend/samples/d3fend-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


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
        if "DefensiveTechniques" not in json_data:
            raise ValueError("JSON must contain 'DefensiveTechniques' array")
        
        techniques = json_data["DefensiveTechniques"]
        
        for technique in techniques:
            self._add_defensive_technique(technique)
        
        self._add_technique_relationships(techniques)
        self._add_mitigation_relationships(techniques)
        
        return self.graph

    def _add_defensive_technique(self, technique: dict):
        """Add a D3FEND defensive technique node."""
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
    parser = argparse.ArgumentParser(description="ETL: MITRE D3FEND JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input D3FEND JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    
    args = parser.parse_args()
    
    try:
        with open(args.input, "r") as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return 1
    
    try:
        print(f"Loading D3FEND JSON from {args.input}...")
        transformer = D3FENDtoRDFTransformer()
        print("Transforming to RDF...")
        transformer.transform(json_data)
        ttl_content = transformer.graph.serialize(format="turtle")
        
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing RDF to {args.output}...")
        with open(args.output, "w") as f:
            f.write(ttl_content)
        
        print(f"✓ Transformation complete: {args.output}")
        return 0
    
    except Exception as e:
        print(f"❌ Transformation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
