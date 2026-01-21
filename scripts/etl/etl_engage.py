#!/usr/bin/env python3
"""
ENGAGE ETL: Transform MITRE ENGAGE JSON to RDF (Turtle)
Engagement concepts for adversary interaction and strategic disruption.
"""

import json
import argparse
from pathlib import Path
from typing import Optional

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


class ENGAGEtoRDFTransformer:
    """Transform ENGAGE JSON to RDF."""

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
        """Transform ENGAGE JSON to RDF graph."""
        if "EngagementConcepts" not in json_data:
            raise ValueError("JSON must contain 'EngagementConcepts' array")
        
        concepts = json_data["EngagementConcepts"]
        
        # Add all ENGAGE engagement concepts
        for concept in concepts:
            self._add_engagement_concept(concept)
        
        # Add disruption relationships
        self._add_disruption_relationships(concepts)
        
        return self.graph

    def _add_engagement_concept(self, concept: dict):
        """Add an ENGAGE engagement concept node."""
        engage_id = concept.get("ID", "")
        if not engage_id:
            return
        
        engage_id_full = f"ENGAGE-{engage_id}" if not engage_id.startswith("ENGAGE-") else engage_id
        concept_node = URIRef(f"{self.EX}engagement/{engage_id_full}")
        
        # Add RDF type
        self.graph.add((concept_node, RDF.type, self.SEC.EngagementConcept))
        
        # Add identifier
        self.graph.add((concept_node, self.SEC.engageId, Literal(engage_id_full, datatype=XSD.string)))
        
        # Add label
        if concept.get("Name"):
            self.graph.add((concept_node, RDFS.label, Literal(concept["Name"], datatype=XSD.string)))
        
        # Add description
        if concept.get("Description"):
            desc_text = self._extract_description(concept["Description"])
            if desc_text:
                self.graph.add((concept_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))
        
        # Add strategic value
        if concept.get("StrategicValue"):
            self.graph.add((concept_node, self.SEC.strategicValue, Literal(concept["StrategicValue"], datatype=XSD.string)))
        
        # Add category
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
            
            # Disrupts relationships
            if concept.get("DisruptsTechniques"):
                for att_technique in concept["DisruptsTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((concept_node, self.SEC.disrupts, att_node))

    def get_rdf(self) -> str:
        """Get RDF as Turtle string."""
        return self.graph.serialize(format="turtle")


def validate_output(ttl_content: str, shapes_path: Optional[str] = None) -> bool:
    """Validate RDF output against SHACL shapes."""
    try:
        from pyshacl import validate
        
        shapes_file = shapes_path or "docs/ontology/shacl/engage-shapes.ttl"
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
        report_file = f"artifacts/shacl-report-engage-sample.ttl.json"
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
    parser = argparse.ArgumentParser(description="Transform ENGAGE JSON to RDF Turtle")
    parser.add_argument("--input", required=True, help="Input ENGAGE JSON file")
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
        print(f"Loading ENGAGE JSON from {args.input}...")
        transformer = ENGAGEtoRDFTransformer()
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
