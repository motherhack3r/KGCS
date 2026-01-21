"""ETL Pipeline: NVD CVE JSON → RDF Turtle with SHACL validation.

Transforms official NVD CVE API JSON (2.0) into RDF triples conforming to the
Core Ontology Vulnerability/VulnerabilityScore classes.

**IMPORTANT: This transformer assumes PlatformConfiguration entities have been created
by etl_cpematch.py. CVE records reference existing PlatformConfiguration nodes by
matchCriteriaId (foreign key relationship).**

Recommended ingestion order:
  1. etl_cpe.py       → Create Platform nodes from CPE definitions
  2. etl_cpematch.py  → Create PlatformConfiguration nodes from match criteria
  3. etl_cve.py       → Create Vulnerability nodes (references existing configs)

Usage:
    python -m src.etl.etl_cve --input data/cve/raw/cve-api-response.json \
                              --output data/cve/samples/cve-output.ttl \
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

class CVEtoRDFTransformer:
    """Transform NVD CVE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        self.graph.bind('sec', SEC)
        self.graph.bind('ex', EX)
        self.graph.bind('xsd', XSD)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)

    def transform(self, cve_json: dict) -> Graph:
        """Transform CVE API JSON response to RDF."""
        if 'vulnerabilities' not in cve_json:
            raise ValueError("Expected 'vulnerabilities' key in CVE API response")

        for vuln_container in cve_json['vulnerabilities']:
            if 'cve' in vuln_container:
                self._add_vulnerability(vuln_container['cve'])

        return self.graph

    def _add_vulnerability(self, cve: dict):
        """Add a CVE entry as a sec:Vulnerability node with scores."""
        cve_id = cve.get('id', '')
        if not cve_id:
            return

        vuln_node = URIRef(f"{EX}vulnerability/{cve_id}")
        self.graph.add((vuln_node, RDF.type, SEC.Vulnerability))
        self.graph.add((vuln_node, SEC.cveId, Literal(cve_id, datatype=XSD.string)))

        if cve.get('published'):
            published = datetime.fromisoformat(cve['published'].replace('Z', '+00:00'))
            self.graph.add((vuln_node, SEC.published, Literal(published, datatype=XSD.dateTime)))

        if cve.get('lastModified'):
            modified = datetime.fromisoformat(cve['lastModified'].replace('Z', '+00:00'))
            self.graph.add((vuln_node, SEC.lastModified, Literal(modified, datatype=XSD.dateTime)))

        if cve.get('vulnStatus'):
            self.graph.add((vuln_node, SEC.vulnStatus, Literal(cve['vulnStatus'], datatype=XSD.string)))

        if cve.get('sourceIdentifier'):
            self.graph.add((vuln_node, SEC.sourceIdentifier, Literal(cve['sourceIdentifier'], datatype=XSD.string)))

        if cve.get('descriptions'):
            descriptions = [d['value'] for d in cve['descriptions'] if 'value' in d]
            if descriptions:
                desc_text = ' '.join(descriptions)
                self.graph.add((vuln_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        if cve.get('metrics'):
            self._add_cvss_scores(vuln_node, cve['metrics'])

        if cve.get('configurations'):
            self._add_configurations(vuln_node, cve['configurations'])

        if cve.get('references'):
            self._add_references(vuln_node, cve['references'])

    def _add_cvss_scores(self, vuln_node, metrics: dict):
        """Add CVSS scores as sec:VulnerabilityScore nodes."""
        for metric in metrics.get('cvssMetricV31', []):
            score_node = URIRef(f"{vuln_node}#cvss-v31-{hash(str(metric))}")
            self.graph.add((score_node, RDF.type, SEC.VulnerabilityScore))
            self.graph.add((vuln_node, SEC.scored_by, score_node))

            cvss_data = metric.get('cvssData', {})
            self.graph.add((score_node, SEC.cvssVersion, Literal('3.1', datatype=XSD.string)))

            if cvss_data.get('vectorString'):
                self.graph.add((score_node, SEC.vectorString, Literal(cvss_data['vectorString'], datatype=XSD.string)))

            if cvss_data.get('baseScore') is not None:
                score_value = float(cvss_data['baseScore'])
                self.graph.add((score_node, SEC.baseScore, Literal(score_value, datatype=XSD.decimal)))

            if cvss_data.get('baseSeverity'):
                self.graph.add((score_node, SEC.baseSeverity, Literal(cvss_data['baseSeverity'], datatype=XSD.string)))

    def _add_configurations(self, vuln_node, configurations: list):
        """Add affected platform configurations."""
        for config in configurations:
            nodes = config.get('nodes', [])
            for node in nodes:
                cpe_matches = node.get('cpeMatch', [])
                for match in cpe_matches:
                    if not match.get('vulnerable'):
                        continue
                    self._add_configuration(vuln_node, match)

    def _add_configuration(self, vuln_node, cpe_match: dict):
        """Reference an existing PlatformConfiguration by matchCriteriaId.
        
        This assumes the PlatformConfiguration has already been created by the
        CPEMatch ETL transformer. The CVE transformer simply links the vulnerability
        to the pre-existing configuration.
        """
        match_id = cpe_match.get('matchCriteriaId', '')
        if not match_id:
            return

        # Reference the PlatformConfiguration created by etl_cpematch.py
        config_node = URIRef(f"{EX}platformConfiguration/{match_id}")

        # Create the relationship: Vulnerability --(affected_by)--> PlatformConfiguration
        self.graph.add((config_node, SEC.affected_by, vuln_node))

    def _add_references(self, vuln_node, references: list):
        """Add external references."""
        for ref in references:
            ref_url = ref.get('url', '')
            if not ref_url:
                continue

            ref_node = URIRef(f"{EX}reference/{hash(ref_url)}")
            self.graph.add((ref_node, RDF.type, SEC.Reference))
            self.graph.add((ref_node, SEC.referenceUrl, Literal(ref_url, datatype=XSD.anyURI)))

            if ref.get('source'):
                self.graph.add((ref_node, SEC.referenceSource, Literal(ref['source'], datatype=XSD.string)))

            self.graph.add((vuln_node, SEC.references, ref_node))


def main():
    parser = argparse.ArgumentParser(description='ETL: NVD CVE JSON → RDF Turtle')
    parser.add_argument('--input', '-i', required=True, help='Input CVE API JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file')
    parser.add_argument('--validate', action='store_true', help='Run SHACL validation on output')
    parser.add_argument('--shapes', default='docs/ontology/shacl/cve-shapes.ttl', help='SHACL shapes file')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CVE JSON from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        cve_json = json.load(f)

    print("Transforming to RDF...")
    transformer = CVEtoRDFTransformer()
    graph = transformer.transform(cve_json)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    graph.serialize(destination=args.output, format='turtle')

    if args.validate:
        print("\nRunning SHACL validation...")
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
