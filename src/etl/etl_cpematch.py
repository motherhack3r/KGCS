"""ETL Pipeline: NVD CPEMatch JSON → RDF Turtle with SHACL validation.

Transforms official NVD CPEMatch API JSON (2.0) into RDF triples conforming to the
Core Ontology PlatformConfiguration class.

This transformer creates PlatformConfiguration entities from matchString entries,
which are then referenced by CVE records via matchCriteriaId.

Usage:
    python -m src.etl.etl_cpematch --input data/cpe/raw/nvdcpematch-2.0/chunk-*.json \
                                   --output data/cpe/matches/cpe-matches-output.ttl \
                                   --validate
"""

import argparse
import json
import os
import urllib.parse
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import subprocess
import sys

SEC = Namespace('https://example.org/sec/core#')
EX = Namespace('https://example.org/')

class CPEMatchtoRDFTransformer:
    """Transform NVD CPEMatch JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        self.graph.bind('sec', SEC)
        self.graph.bind('ex', EX)
        self.graph.bind('xsd', XSD)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)
        self.platform_cache = {}  # Cache to avoid duplicate Platform nodes

    def transform(self, cpematch_json: dict) -> Graph:
        """Transform CPEMatch API JSON response to RDF."""
        if 'matchStrings' not in cpematch_json:
            raise ValueError("Expected 'matchStrings' key in CPEMatch API response")

        for match_string_container in cpematch_json['matchStrings']:
            if 'matchString' in match_string_container:
                self._add_platform_configuration(match_string_container['matchString'])

        return self.graph

    def _add_platform_configuration(self, match_string: dict):
        """Add a matchString entry as a sec:PlatformConfiguration node.
        
        This represents the match criteria with concrete CPE expansions (matches array).
        """
        match_id = match_string.get('matchCriteriaId', '')
        if not match_id:
            return

        # PlatformConfiguration identified by matchCriteriaId (1:1 mapping)
        config_node = URIRef(f"{EX}platformConfiguration/{match_id}")
        self.graph.add((config_node, RDF.type, SEC.PlatformConfiguration))
        self.graph.add((config_node, SEC.matchCriteriaId, Literal(match_id, datatype=XSD.string)))

        # criteria: the CPE string that defines the match criteria
        criteria = match_string.get('criteria')
        if criteria:
            self.graph.add((config_node, SEC.configurationCriteria, Literal(criteria, datatype=XSD.string)))

        # Version bounds (from criteria CPE 2.3 parsing)
        # Note: NVD cpematch doesn't store explicit bounds; they're implicit in criteria CPE
        # This is kept for compatibility with CVE ETL which may provide explicit bounds

        # Status: Active or Deprecated
        status = match_string.get('status')
        if status:
            self.graph.add((config_node, SEC.configurationStatus, Literal(status, datatype=XSD.string)))

        # Timestamps
        if match_string.get('created'):
            try:
                created = datetime.fromisoformat(match_string['created'].replace('Z', '+00:00'))
                self.graph.add((config_node, SEC.configCreatedDate, Literal(created, datatype=XSD.dateTime)))
            except Exception:
                pass

        if match_string.get('lastModified'):
            try:
                modified = datetime.fromisoformat(match_string['lastModified'].replace('Z', '+00:00'))
                self.graph.add((config_node, SEC.configLastModifiedDate, Literal(modified, datatype=XSD.dateTime)))
            except Exception:
                pass

        # matches array: concrete CPE instances that satisfy this criteria
        for match in match_string.get('matches', []):
            match_cpe = match.get('cpeName')
            if not match_cpe:
                continue

            # Create or reference Platform node for this CPE
            match_platform_id = match.get('cpeNameId') or urllib.parse.quote(match_cpe, safe='')
            match_platform_node = URIRef(f"{EX}platform/{match_platform_id}")

            # Check cache to avoid duplicate Platform creation
            if match_platform_id not in self.platform_cache:
                self.graph.add((match_platform_node, RDF.type, SEC.Platform))
                self.graph.add((match_platform_node, SEC.CPEUri, Literal(match_cpe, datatype=XSD.string)))
                self.platform_cache[match_platform_id] = match_platform_node
            else:
                match_platform_node = self.platform_cache[match_platform_id]

            # Link configuration to concrete platform instance
            self.graph.add((config_node, SEC.matchesPlatform, match_platform_node))

    def serialize(self, output_file: str):
        """Write RDF graph to Turtle file."""
        self.graph.serialize(destination=output_file, format='turtle')


def main():
    parser = argparse.ArgumentParser(
        description='Transform NVD CPEMatch JSON to RDF Turtle'
    )
    parser.add_argument('--input', required=True, help='Input CPEMatch JSON file(s)')
    parser.add_argument('--output', required=True, help='Output RDF Turtle file')
    parser.add_argument('--validate', action='store_true', help='Run SHACL validation after transformation')

    args = parser.parse_args()

    transformer = CPEMatchtoRDFTransformer()

    # Handle single file or glob pattern
    import glob
    input_files = glob.glob(args.input)
    if not input_files:
        # Try as direct path
        input_files = [args.input]

    print(f"Loading CPEMatch JSON from {args.input}...")
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Warning: {input_file} not found, skipping")
            continue

        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                cpematch_json = json.load(f)
                print(f"Transforming {os.path.basename(input_file)}...")
                transformer.transform(cpematch_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing {input_file}: {e}", file=sys.stderr)
                sys.exit(1)

    print(f"Writing RDF to {args.output}...")
    transformer.serialize(args.output)
    print(f"✓ RDF Turtle written: {args.output}")

    # Optional SHACL validation
    if args.validate:
        print("Running SHACL validation...")
        result = subprocess.run([
            sys.executable, '-m', 'src.core.validation',
            '--data', args.output,
            '--shapes', 'docs/ontology/shacl/cve-shapes.ttl'
        ], cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        sys.exit(result.returncode)


if __name__ == '__main__':
    main()
