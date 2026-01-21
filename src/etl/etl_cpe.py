"""ETL Pipeline: NVD CPE JSON → RDF Turtle with SHACL validation.

Transforms official NVD CPE API JSON into RDF triples conforming to the
Core Ontology Platform/PlatformConfiguration classes.

Usage:
    python -m src.etl.etl_cpe --input data/cpe/raw/cpe-api-response.json \
                              --output data/cpe/samples/cpe-output.ttl \
                              --validate
"""

import argparse
import json
import os
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import subprocess
import sys

SEC = Namespace('https://example.org/sec/core#')
EX = Namespace('https://example.org/')

class CPEtoRDFTransformer:
    """Transform NVD CPE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        self.graph.bind('sec', SEC)
        self.graph.bind('ex', EX)
        self.graph.bind('xsd', XSD)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)

    def transform(self, cpe_json: dict) -> Graph:
        """Transform CPE API JSON response to RDF."""
        if 'products' not in cpe_json:
            raise ValueError("Expected 'products' key in CPE API response")

        for product in cpe_json['products']:
            cpe = product.get('cpe', {})
            self._add_platform(cpe)

        return self.graph

    def _add_platform(self, cpe: dict):
        """Add a CPE entry as a sec:Platform node."""
        cpe_name = cpe.get('cpeName', '')
        if not cpe_name:
            return

        cpe_id = cpe.get('cpeNameId', 'unknown')
        platform_node = URIRef(f"{EX}platform/{cpe_id}")
        self.graph.add((platform_node, RDF.type, SEC.Platform))

        # CPE URI
        if cpe_name:
            self.graph.add((platform_node, SEC.cpeUri, Literal(cpe_name, datatype=XSD.string)))

        # Parse CPE string components (format: cpe:2.3:part:vendor:product:version:update:edition:...)
        # After split by ':', indices are: [0]="cpe" [1]="2.3" [2]=part [3]=vendor [4]=product [5]=version [6]=update...
        parts = cpe_name.split(':')
        if len(parts) >= 3:
            self.graph.add((platform_node, SEC.platformPart, Literal(parts[2], datatype=XSD.string)))
        if len(parts) >= 4:
            self.graph.add((platform_node, SEC.vendor, Literal(parts[3], datatype=XSD.string)))
        if len(parts) >= 5:
            self.graph.add((platform_node, SEC.product, Literal(parts[4], datatype=XSD.string)))
        if len(parts) >= 6 and parts[5] != '*':
            self.graph.add((platform_node, SEC.version, Literal(parts[5], datatype=XSD.string)))

        # Deprecation status
        if cpe.get('deprecated') is not None:
            deprecated = 'true' if cpe['deprecated'] else 'false'
            self.graph.add((platform_node, SEC.platformDeprecated, Literal(deprecated, datatype=XSD.boolean)))

        # CPE Name ID
        if cpe.get('cpeNameId'):
            self.graph.add((platform_node, SEC.cpeNameId, Literal(cpe['cpeNameId'], datatype=XSD.string)))

        # Created and modified dates
        if cpe.get('created'):
            try:
                created = datetime.fromisoformat(cpe['created'].replace('Z', '+00:00'))
                self.graph.add((platform_node, SEC.cpeCreatedDate, Literal(created, datatype=XSD.dateTime)))
            except:
                pass

        if cpe.get('lastModified'):
            try:
                modified = datetime.fromisoformat(cpe['lastModified'].replace('Z', '+00:00'))
                self.graph.add((platform_node, SEC.cpeLastModifiedDate, Literal(modified, datatype=XSD.dateTime)))
            except:
                pass


def main():
    parser = argparse.ArgumentParser(description='ETL: NVD CPE JSON → RDF Turtle')
    parser.add_argument('--input', '-i', required=True, help='Input CPE API JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file')
    parser.add_argument('--validate', action='store_true', help='Run SHACL validation on output')
    parser.add_argument('--shapes', default='docs/ontology/shacl/cpe-shapes.ttl', help='SHACL shapes file')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CPE JSON from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        cpe_json = json.load(f)

    print("Transforming to RDF...")
    transformer = CPEtoRDFTransformer()
    graph = transformer.transform(cpe_json)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    graph.serialize(destination=args.output, format='turtle')

    if args.validate:
        print("\nRunning SHACL validation...")
        # Call validation module
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


if __name__ == '__main__':
    sys.exit(main())
