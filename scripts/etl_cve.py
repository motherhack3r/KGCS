"""ETL Pipeline: NVD CVE JSON → RDF Turtle with SHACL validation.

Transforms official NVD CVE API JSON (2.0) into RDF triples conforming to the
Core Ontology Vulnerability/VulnerabilityScore classes, including relationships
to PlatformConfiguration (affected_by).

Usage:
    python scripts/etl_cve.py --input data/cve/raw/cve-api-response.json \
                              --output data/cve/samples/cve-output.ttl \
                              --validate

Reference:
    - NVD CVE API 2.0: https://nvd.nist.gov/products/cve-api-20
    - Core Ontology: docs/ontology/core-ontology-v1.0.md
    - SHACL Shapes: docs/ontology/shacl/cve-shapes.ttl
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

# Define namespaces
SEC = Namespace('https://example.org/sec/core#')
EX = Namespace('https://example.org/')

class CVEtoRDFTransformer:
    """Transform NVD CVE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        # Bind namespaces
        self.graph.bind('sec', SEC)
        self.graph.bind('ex', EX)
        self.graph.bind('xsd', XSD)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)

    def transform(self, cve_json: dict) -> Graph:
        """
        Transform CVE API JSON response to RDF.

        Expected JSON structure (NVD CVE API 2.0):
        {
          "resultsPerPage": int,
          "startIndex": int,
          "totalResults": int,
          "format": "NVD_CVE",
          "vulnerabilities": [
            {
              "cve": {
                "id": "CVE-2025-1234",
                "sourceIdentifier": "mitre@mitre.org",
                "published": "ISO datetime",
                "lastModified": "ISO datetime",
                "vulnStatus": "Analyzed",
                "descriptions": [...],
                "metrics": {
                  "cvssMetricV31": [...],
                  "cvssMetricV30": [...]
                },
                "weaknesses": [
                  {"source": "NVD", "type": "Primary", "description": [{"value": "CWE-XXX"}]}
                ],
                "configurations": [
                  {
                    "nodes": [
                      {
                        "operator": "OR",
                        "negate": false,
                        "cpeMatch": [
                          {
                            "vulnerable": true,
                            "criteria": "cpe:2.3:...",
                            "matchCriteriaId": "uuid",
                            "versionStartIncluding": "...",
                            "versionEndIncluding": "...",
                            ...
                          }
                        ]
                      }
                    ]
                  }
                ],
                "references": [...]
              }
            }
          ]
        }
        """
        if 'vulnerabilities' not in cve_json:
            raise ValueError("Expected 'vulnerabilities' key in CVE API response")

        for vuln_container in cve_json['vulnerabilities']:
            if 'cve' in vuln_container:
                self._add_vulnerability(vuln_container['cve'])

        return self.graph

    def _add_vulnerability(self, cve: dict):
        """Add a CVE entry as a sec:Vulnerability node with scores and configurations."""
        cve_id = cve.get('id', '')
        if not cve_id:
            return

        # Create Vulnerability node
        vuln_node = URIRef(f"{EX}vulnerability/{cve_id}")
        self.graph.add((vuln_node, RDF.type, SEC.Vulnerability))
        self.graph.add((vuln_node, SEC.cveId, Literal(cve_id, datatype=XSD.string)))

        # Add metadata
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

        # Add description (concatenate all descriptions)
        if cve.get('descriptions'):
            descriptions = [d['value'] for d in cve['descriptions'] if 'value' in d]
            if descriptions:
                desc_text = ' '.join(descriptions)
                self.graph.add((vuln_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Add CVSS scores
        if cve.get('metrics'):
            self._add_cvss_scores(vuln_node, cve['metrics'])

        # Add platform configurations (affected_by relationship)
        if cve.get('configurations'):
            self._add_configurations(vuln_node, cve['configurations'])

        # Add references
        if cve.get('references'):
            self._add_references(vuln_node, cve['references'])

    def _add_cvss_scores(self, vuln_node, metrics: dict):
        """Add CVSS scores as sec:VulnerabilityScore nodes."""
        # Process CVSS v3.1
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

            # Add individual metrics
            if cvss_data.get('attackVector'):
                self.graph.add((score_node, SEC.attackVector, Literal(cvss_data['attackVector'], datatype=XSD.string)))
            if cvss_data.get('attackComplexity'):
                self.graph.add((score_node, SEC.attackComplexity, Literal(cvss_data['attackComplexity'], datatype=XSD.string)))
            if cvss_data.get('privilegesRequired'):
                self.graph.add((score_node, SEC.privilegesRequired, Literal(cvss_data['privilegesRequired'], datatype=XSD.string)))
            if cvss_data.get('userInteraction'):
                self.graph.add((score_node, SEC.userInteraction, Literal(cvss_data['userInteraction'], datatype=XSD.string)))
            if cvss_data.get('scope'):
                self.graph.add((score_node, SEC.scope, Literal(cvss_data['scope'], datatype=XSD.string)))
            if cvss_data.get('confidentialityImpact'):
                self.graph.add((score_node, SEC.confidentialityImpact, Literal(cvss_data['confidentialityImpact'], datatype=XSD.string)))
            if cvss_data.get('integrityImpact'):
                self.graph.add((score_node, SEC.integrityImpact, Literal(cvss_data['integrityImpact'], datatype=XSD.string)))
            if cvss_data.get('availabilityImpact'):
                self.graph.add((score_node, SEC.availabilityImpact, Literal(cvss_data['availabilityImpact'], datatype=XSD.string)))

        # Process CVSS v3.0 similarly (separate version)
        for metric in metrics.get('cvssMetricV30', []):
            score_node = URIRef(f"{vuln_node}#cvss-v30-{hash(str(metric))}")
            self.graph.add((score_node, RDF.type, SEC.VulnerabilityScore))
            self.graph.add((vuln_node, SEC.scored_by, score_node))

            cvss_data = metric.get('cvssData', {})
            self.graph.add((score_node, SEC.cvssVersion, Literal('3.0', datatype=XSD.string)))
            if cvss_data.get('vectorString'):
                self.graph.add((score_node, SEC.vectorString, Literal(cvss_data['vectorString'], datatype=XSD.string)))
            if cvss_data.get('baseScore') is not None:
                score_value = float(cvss_data['baseScore'])
                self.graph.add((score_node, SEC.baseScore, Literal(score_value, datatype=XSD.decimal)))
            # (similar metrics as v3.1)

    def _add_configurations(self, vuln_node, configurations: list):
        """Add affected platform configurations."""
        for config in configurations:
            nodes = config.get('nodes', [])
            for node in nodes:
                cpe_matches = node.get('cpeMatch', [])
                for match in cpe_matches:
                    if not match.get('vulnerable'):
                        continue  # Skip non-vulnerable entries
                    self._add_configuration(vuln_node, match)

    def _add_configuration(self, vuln_node, cpe_match: dict):
        """Add a single PlatformConfiguration affected_by this vulnerability."""
        match_id = cpe_match.get('matchCriteriaId', '')
        if not match_id:
            return

        # Create PlatformConfiguration node
        config_node = URIRef(f"{EX}platformConfiguration/{match_id}")
        self.graph.add((config_node, RDF.type, SEC.PlatformConfiguration))
        self.graph.add((config_node, SEC.matchCriteriaId, Literal(match_id, datatype=XSD.string)))

        # Add CPE criteria
        cpe_criteria = cpe_match.get('criteria')
        if cpe_criteria:
            self.graph.add((config_node, SEC.configurationCriteria, Literal(cpe_criteria, datatype=XSD.string)))
            # Link configuration to a Platform node for matchesPlatform requirement
            platform_id = urllib.parse.quote(cpe_criteria, safe='')
            platform_node = URIRef(f"{EX}platform/{platform_id}")
            self.graph.add((platform_node, RDF.type, SEC.Platform))
            self.graph.add((platform_node, SEC.CPEUri, Literal(cpe_criteria, datatype=XSD.string)))
            self.graph.add((config_node, SEC.matchesPlatform, platform_node))

        # Add version ranges
        if cpe_match.get('versionStartIncluding'):
            self.graph.add((config_node, SEC.versionStartIncluding, Literal(cpe_match['versionStartIncluding'], datatype=XSD.string)))
        if cpe_match.get('versionEndIncluding'):
            self.graph.add((config_node, SEC.versionEndIncluding, Literal(cpe_match['versionEndIncluding'], datatype=XSD.string)))
        if cpe_match.get('versionStartExcluding'):
            self.graph.add((config_node, SEC.versionStartExcluding, Literal(cpe_match['versionStartExcluding'], datatype=XSD.string)))
        if cpe_match.get('versionEndExcluding'):
            self.graph.add((config_node, SEC.versionEndExcluding, Literal(cpe_match['versionEndExcluding'], datatype=XSD.string)))

        # Add the affected_by relationship
        self.graph.add((config_node, SEC.affected_by, vuln_node))

    def _add_references(self, vuln_node, references: list):
        """Add external references."""
        for ref in references:
            ref_url = ref.get('url', '')
            if not ref_url:
                continue

            # Create Reference node
            ref_node = URIRef(f"{EX}reference/{hash(ref_url)}")
            self.graph.add((ref_node, RDF.type, SEC.Reference))
            self.graph.add((ref_node, SEC.referenceUrl, Literal(ref_url, datatype=XSD.anyURI)))

            if ref.get('source'):
                self.graph.add((ref_node, SEC.referenceSource, Literal(ref['source'], datatype=XSD.string)))

            # Link to vulnerability
            self.graph.add((vuln_node, SEC.references, ref_node))


def validate_output(ttl_file: str, shapes_file: str = 'docs/ontology/shacl/cve-shapes.ttl') -> bool:
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
    parser = argparse.ArgumentParser(description='ETL: NVD CVE JSON → RDF Turtle')
    parser.add_argument('--input', '-i', required=True, help='Input CVE API JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file')
    parser.add_argument('--validate', action='store_true', help='Run SHACL validation on output')
    parser.add_argument('--shapes', default='docs/ontology/shacl/cve-shapes.ttl', help='SHACL shapes file')
    args = parser.parse_args()

    # Load input JSON
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CVE JSON from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        cve_json = json.load(f)

    # Transform
    print("Transforming to RDF...")
    transformer = CVEtoRDFTransformer()
    graph = transformer.transform(cve_json)

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
