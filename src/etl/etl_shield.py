"""ETL Pipeline: MITRE SHIELD JSON → RDF Turtle.

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
from rdflib.namespace import RDF, RDFS, XSD


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

        if technique.get("OperationalImpact"):
            self.graph.add((technique_node, self.SEC.operationalImpact, Literal(technique["OperationalImpact"], datatype=XSD.string)))

        if technique.get("EaseOfEmployment"):
            self.graph.add((technique_node, self.SEC.easeOfEmployment, Literal(technique["EaseOfEmployment"], datatype=XSD.string)))

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


def _load_shield_data(input_path: str) -> dict:
    if os.path.isdir(input_path):
        techniques_path = os.path.join(input_path, "techniques.json")
        if not os.path.exists(techniques_path):
            raise FileNotFoundError(f"Missing techniques.json in {input_path}")

        with open(techniques_path, "r", encoding="utf-8") as f:
            techniques = json.load(f)

        normalized = []
        for item in techniques:
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
    parser = argparse.ArgumentParser(description="ETL: MITRE SHIELD JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input SHIELD JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    
    args = parser.parse_args()
    
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
        ttl_content = transformer.graph.serialize(format="turtle")
        
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing RDF to {args.output}...")
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(ttl_content)
        
        print(f"Transformation complete: {args.output}")
        return 0
    
    except Exception as e:
        print(f"Transformation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
