"""ETL Pipeline: MITRE ENGAGE JSON → RDF Turtle.

Engagement concepts for adversary interaction and strategic disruption.

Usage:
    python -m kgcs.etl.etl_engage --input data/engage/raw/engage.json \
                              --output data/engage/samples/engage-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


class ENGAGEtoRDFTransformer:
    """Transform ENGAGE JSON to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, json_data: dict) -> Graph:
        """Transform ENGAGE JSON to RDF graph."""
        if "EngagementConcepts" not in json_data:
            raise ValueError("JSON must contain 'EngagementConcepts' array")
        
        concepts = json_data["EngagementConcepts"]
        
        for concept in concepts:
            self._add_engagement_concept(concept)
        
        self._add_disruption_relationships(concepts)
        
        return self.graph

    def _add_engagement_concept(self, concept: dict):
        """Add an ENGAGE engagement concept node."""
        engage_id = concept.get("ID", "")
        if not engage_id:
            return
        
        engage_id_full = f"ENGAGE-{engage_id}" if not engage_id.startswith("ENGAGE-") else engage_id
        concept_node = URIRef(f"{self.EX}engagement/{engage_id_full}")
        
        self.graph.add((concept_node, RDF.type, self.SEC.EngagementConcept))
        self.graph.add((concept_node, self.SEC.engageId, Literal(engage_id_full, datatype=XSD.string)))
        
        if concept.get("Name"):
            self.graph.add((concept_node, RDFS.label, Literal(concept["Name"], datatype=XSD.string)))
        
        if concept.get("Description"):
            desc_text = self._extract_description(concept["Description"])
            if desc_text:
                self.graph.add((concept_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))
        
        if concept.get("StrategicValue"):
            self.graph.add((concept_node, self.SEC.strategicValue, Literal(concept["StrategicValue"], datatype=XSD.string)))
        
        if concept.get("Category"):
            self.graph.add((concept_node, self.SEC.category, Literal(concept["Category"], datatype=XSD.string)))

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

    def _add_disruption_relationships(self, concepts: list):
        """Add disrupts relationships to ATT&CK techniques."""
        for concept in concepts:
            engage_id = concept.get("ID", "")
            if not engage_id:
                continue
            
            engage_id_full = f"ENGAGE-{engage_id}" if not engage_id.startswith("ENGAGE-") else engage_id
            concept_node = URIRef(f"{self.EX}engagement/{engage_id_full}")
            
            if concept.get("DisruptsTechniques"):
                for att_technique in concept["DisruptsTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((concept_node, self.SEC.disrupts, att_node))


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE ENGAGE JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input ENGAGE JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    
    args = parser.parse_args()
    
    try:
        with open(args.input, "r") as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return 1
    
    try:
        print(f"Loading ENGAGE JSON from {args.input}...")
        transformer = ENGAGEtoRDFTransformer()
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
