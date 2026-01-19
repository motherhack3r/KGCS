"""ETL Pipeline: NVD CPE JSON → RDF Turtle with SHACL validation.

Transforms official NVD CPE API JSON into RDF triples conforming to the
Core Ontology Platform/PlatformConfiguration classes.

Usage:
    python scripts/etl_cpe.py --input data/cpe/raw/cpe-api-response.json \
                              --output data/cpe/samples/cpe-output.ttl \
                              --validate

Reference:
    - NVD CPE API: https://nvd.nist.gov/products/cpe/api
    - Core Ontology: docs/ontology/core-ontology-v1.0.md
    - SHACL Shapes: docs/ontology/shacl/cpe-shapes.ttl
"""

import argparse
import json
import os
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import subprocess
import sys

# Define namespaces
SEC = Namespace('https://example.org/sec/core#')
EX = Namespace('https://example.org/')

class CPEtoRDFTransformer:
    """Transform NVD CPE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        # Bind namespaces
        self.graph.bind('sec', SEC)
        self.graph.bind('ex', EX)
        self.graph.bind('xsd', XSD)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)

    def transform(self, cpe_json: dict) -> Graph:
        """
        Transform CPE API JSON response to RDF.

        Expected JSON structure (NVD CPE API 2.0):
        {
          "resultsPerPage": int,
          "startIndex": int,
          "totalResults": int,
          "timestamp": "ISO datetime",
          "products": [
            {
              "cpeNameId": "uuid",
              "deprecated": false,
              "cpeName": "cpe:2.3:a:...",
              "createdDate": "ISO datetime",
              "lastModifiedDate": "ISO datetime",
              "deprecatedBy": [...]  (optional)
            }
          ]
        }
        """
        if 'products' not in cpe_json:
            raise ValueError("Expected 'products' key in CPE API response")

        for cpe in cpe_json['products']:
            self._add_platform(cpe)

        return self.graph

    def _add_platform(self, cpe: dict):
        """Add a CPE entry as a sec:Platform node."""
        cpe_uri = cpe.get('cpeName', '')
        if not cpe_uri:
            return

        # Create a URI for the platform (use CPE name as identifier)
        platform_node = URIRef(f"{EX}platform/{cpe.get('cpeNameId', 'unknown')}")

        # Add RDF type
        self.graph.add((platform_node, RDF.type, SEC.Platform))

        # Add properties directly from NVD CPE
        if cpe_uri:
            self.graph.add((platform_node, SEC.CPEUri, Literal(cpe_uri, datatype=XSD.string)))

        # Parse CPE URI to extract components (optional but useful)
        # CPE 2.3: cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other
        parts = cpe_uri.split(':')
        if len(parts) >= 5:
            self.graph.add((platform_node, SEC.platformPart, Literal(parts[3], datatype=XSD.string)))
        if len(parts) >= 6:
            self.graph.add((platform_node, SEC.vendor, Literal(parts[4], datatype=XSD.string)))
        if len(parts) >= 7:
            self.graph.add((platform_node, SEC.product, Literal(parts[5], datatype=XSD.string)))
        if len(parts) >= 8:
            self.graph.add((platform_node, SEC.version, Literal(parts[6], datatype=XSD.string)))

        # Add metadata
        if cpe.get('deprecated') is not None:
            deprecated = 'true' if cpe['deprecated'] else 'false'
            self.graph.add((platform_node, SEC.platformDeprecated, Literal(deprecated, datatype=XSD.boolean)))

        if cpe.get('cpeNameId'):
            self.graph.add((platform_node, SEC.cpeNameId, Literal(cpe['cpeNameId'], datatype=XSD.string)))

        if cpe.get('createdDate'):
            created = datetime.fromisoformat(cpe['createdDate'].replace('Z', '+00:00'))
            self.graph.add((platform_node, SEC.cpeCreatedDate, Literal(created, datatype=XSD.dateTime)))

        if cpe.get('lastModifiedDate'):
            modified = datetime.fromisoformat(cpe['lastModifiedDate'].replace('Z', '+00:00'))
            self.graph.add((platform_node, SEC.cpeLastModifiedDate, Literal(modified, datatype=XSD.dateTime)))


def validate_output(ttl_file: str, shapes_file: str = 'docs/ontology/shacl/cpe-shapes.ttl') -> bool:
    """Run SHACL validation on the generated TTL."""
    if not os.path.exists(shapes_file):
        print(f"Warning: Shapes file not found: {shapes_file}. Skipping validation.")
        return True

    result = subprocess.run(
        [sys.executable, 'scripts/validate_shacl.py', '--data', ttl_file, '--shapes', shapes_file],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Validation failed for {ttl_file}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='ETL: NVD CPE JSON → RDF Turtle')
    parser.add_argument('--input', '-i', required=True, help='Input CPE API JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file')
    parser.add_argument('--validate', action='store_true', help='Run SHACL validation on output')
    parser.add_argument('--shapes', default='docs/ontology/shacl/cpe-shapes.ttl', help='SHACL shapes file')
    args = parser.parse_args()

    # Load input JSON
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CPE JSON from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        cpe_json = json.load(f)

    # Transform
    print("Transforming to RDF...")
    transformer = CPEtoRDFTransformer()
    graph = transformer.transform(cpe_json)

    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    graph.serialize(destination=args.output, format='turtle')

    # Validate (optional)
    if args.validate:
        print("\nRunning SHACL validation...")
        if validate_output(args.output, args.shapes):
            print("✓ Validation passed!")
            return 0
        else:
            print("✗ Validation failed!")
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
