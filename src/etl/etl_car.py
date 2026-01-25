"""ETL Pipeline: MITRE CAR JSON → RDF Turtle.

Detection analytics that detect ATT&CK techniques.

Usage:
    python -m src.etl.etl_car --input data/car/raw/car.json \
                              --output data/car/samples/car-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


class CARtoRDFTransformer:
    """Transform CAR JSON to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, json_data: dict) -> Graph:
        """Transform CAR JSON to RDF graph."""
        if "DetectionAnalytics" not in json_data:
            raise ValueError("JSON must contain 'DetectionAnalytics' array")
        
        analytics = json_data["DetectionAnalytics"]
        
        for analytic in analytics:
            self._add_detection_analytic(analytic)
        
        self._add_detection_relationships(analytics)
        
        return self.graph

    def _add_detection_analytic(self, analytic: dict):
        """Add a CAR detection analytic node."""
        car_id = analytic.get("ID", "")
        if not car_id:
            return
        
        car_id_full = f"CAR-{car_id}" if not car_id.startswith("CAR-") else car_id
        analytic_node = URIRef(f"{self.EX}analytic/{car_id_full}")
        
        self.graph.add((analytic_node, RDF.type, self.SEC.DetectionAnalytic))
        self.graph.add((analytic_node, self.SEC.carId, Literal(car_id_full, datatype=XSD.string)))
        
        if analytic.get("Name"):
            self.graph.add((analytic_node, RDFS.label, Literal(analytic["Name"], datatype=XSD.string)))
        
        if analytic.get("Description"):
            desc_text = self._extract_description(analytic["Description"])
            if desc_text:
                self.graph.add((analytic_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))
        
        if analytic.get("LogicExpression"):
            self.graph.add((analytic_node, self.SEC.logicExpression, Literal(analytic["LogicExpression"], datatype=XSD.string)))
        
        if analytic.get("DataSources"):
            for source in analytic["DataSources"]:
                self.graph.add((analytic_node, self.SEC.dataSource, Literal(source, datatype=XSD.string)))

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

    def _add_detection_relationships(self, analytics: list):
        """Add detects relationships to ATT&CK techniques."""
        for analytic in analytics:
            car_id = analytic.get("ID", "")
            if not car_id:
                continue
            
            car_id_full = f"CAR-{car_id}" if not car_id.startswith("CAR-") else car_id
            analytic_node = URIRef(f"{self.EX}analytic/{car_id_full}")
            
            if analytic.get("DetectsTechniques"):
                for att_technique in analytic["DetectsTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((analytic_node, self.SEC.detects, att_node))


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE CAR JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CAR JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    
    args = parser.parse_args()
    
    try:
        with open(args.input, "r") as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return 1
    
    try:
        print(f"Loading CAR JSON from {args.input}...")
        transformer = CARtoRDFTransformer()
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
