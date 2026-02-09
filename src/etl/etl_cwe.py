"""ETL Pipeline: MITRE CWE JSON → RDF Turtle with SHACL validation.

Transforms official MITRE CWE (Common Weakness Enumeration) JSON into RDF triples
conforming to the Core Ontology Weakness class.

Usage:
    python -m src.etl.etl_cwe --input data/cwe/raw/cwe.json \
                              --output data/cwe/samples/cwe-output.ttl \
                              --validate
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import write_graph_turtle_lines, write_graph_ntriples_lines
except Exception:
    from .ttl_writer import write_graph_turtle_lines, write_graph_ntriples_lines

SEC = Namespace("https://example.org/sec/core#")
EX = Namespace("https://example.org/")


class CWEtoRDFTransformer:
    """Transform MITRE CWE JSON response to RDF/Turtle."""

    def __init__(self):
        self.graph = Graph()
        # Expose namespaces as instance attributes for tests and consistency with other transformers
        self.SEC = SEC
        self.EX = EX
        self.graph.bind("sec", self.SEC)
        self.graph.bind("ex", self.EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)

    def transform(self, cwe_json: dict) -> Graph:
        """Transform CWE API JSON response to RDF."""
        if "Weakness" not in cwe_json:
            raise ValueError("Expected 'Weakness' key in CWE JSON response")

        for weakness in cwe_json["Weakness"]:
            self._add_weakness(weakness)

        self._add_weakness_relationships(cwe_json.get("Weakness", []))

        return self.graph

    def _add_weakness(self, weakness: dict):
        """Add a CWE weakness entry as a sec:Weakness node, with all ontology fields."""
        cwe_id = weakness.get("ID", "")
        if not cwe_id:
            return

        cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
        weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")
        self.graph.add((weakness_node, RDF.type, SEC.Weakness))
        self.graph.add((weakness_node, SEC.cweId, Literal(cwe_id_full, datatype=XSD.string)))

        if weakness.get("Name"):
            self.graph.add((weakness_node, RDFS.label, Literal(weakness["Name"], datatype=XSD.string)))

        if weakness.get("Description"):
            desc_text = self._extract_description(weakness["Description"])
            if desc_text:
                self.graph.add((weakness_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        if weakness.get("WeaknessAbstraction"):
            self.graph.add(
                (weakness_node, SEC.weaknessAbstraction, Literal(weakness["WeaknessAbstraction"], datatype=XSD.string))
            )

        if weakness.get("Status"):
            self.graph.add((weakness_node, SEC.status, Literal(weakness["Status"], datatype=XSD.string)))

        if weakness.get("ApplicablePlatforms"):
            for platform in weakness["ApplicablePlatforms"]:
                platform_str = self._format_platform(platform)
                if platform_str:
                    self.graph.add(
                        (weakness_node, SEC.applicablePlatform, Literal(platform_str, datatype=XSD.string))
                    )

        # Consequences
        for cons in weakness.get("Consequences", []):
            scope = cons.get("Scope", "")
            impact = cons.get("Impact", "")
            if not (scope or impact):
                continue
            cons_id = f"{cwe_id_full}-consequence-{scope}-{impact}".replace(" ", "_")
            cons_node = URIRef(f"{EX}consequence/{cons_id}")
            self.graph.add((cons_node, RDF.type, SEC.Consequence))
            if scope:
                self.graph.add((cons_node, SEC.scope, Literal(scope, datatype=XSD.string)))
            if impact:
                self.graph.add((cons_node, SEC.impact, Literal(impact, datatype=XSD.string)))
            self.graph.add((weakness_node, SEC.hasConsequence, cons_node))

        # Mitigations
        for mit in weakness.get("PotentialMitigations", []):
            strategy = mit.get("Strategy", "")
            effectiveness = mit.get("Effectiveness", "")
            phase = mit.get("Phase", "")
            if not (strategy or effectiveness or phase):
                continue
            mit_id = f"{cwe_id_full}-mitigation-{strategy}-{phase}".replace(" ", "_")
            mit_node = URIRef(f"{EX}mitigation/{mit_id}")
            self.graph.add((mit_node, RDF.type, SEC.Mitigation))
            if strategy:
                self.graph.add((mit_node, SEC.strategy, Literal(strategy, datatype=XSD.string)))
            if effectiveness:
                self.graph.add((mit_node, SEC.effectiveness, Literal(effectiveness, datatype=XSD.string)))
            if phase:
                # Create phase node
                phase_id = f"{cwe_id_full}-phase-{phase}".replace(" ", "_")
                phase_node = URIRef(f"{EX}phase/{phase_id}")
                self.graph.add((phase_node, RDF.type, SEC.DevelopmentPhase))
                self.graph.add((phase_node, SEC.phase, Literal(phase, datatype=XSD.string)))
                self.graph.add((mit_node, SEC.appliesTo, phase_node))
            self.graph.add((weakness_node, SEC.hasMitigation, mit_node))

        # Detection Methods
        for det in weakness.get("DetectionMethods", []):
            method = det.get("Method", "")
            effectiveness = det.get("Effectiveness", "")
            if not (method or effectiveness):
                continue
            det_id = f"{cwe_id_full}-detection-{method}".replace(" ", "_")
            det_node = URIRef(f"{EX}detection/{det_id}")
            self.graph.add((det_node, RDF.type, SEC.DetectionMethod))
            if method:
                self.graph.add((det_node, SEC.method, Literal(method, datatype=XSD.string)))
            if effectiveness:
                self.graph.add((det_node, SEC.effectiveness, Literal(effectiveness, datatype=XSD.string)))
            self.graph.add((weakness_node, SEC.hasDetectionMethod, det_node))

        # References
        import hashlib
        for ref in weakness.get("References", []):
            url = ref.get("URL", "")
            ref_type = ref.get("ReferenceType", "")
            ref_text = ref.get("Title") or ref.get("title") or ref.get("Description") or ref.get("description")
            if not (url or ref_type or ref_text):
                continue
            id_source = (url or ref_type or ref_text or "").strip()
            digest = hashlib.sha1(id_source.encode('utf-8')).hexdigest()[:12]
            ref_id = f"{cwe_id_full}-ref-{digest}"
            ref_node = URIRef(f"{EX}reference/{ref_id}")
            self.graph.add((ref_node, RDF.type, SEC.Reference))
            if url:
                self.graph.add((ref_node, SEC.url, Literal(url, datatype=XSD.anyURI)))
            if ref_type:
                self.graph.add((ref_node, SEC.referenceType, Literal(ref_type, datatype=XSD.string)))
            if ref_text:
                self.graph.add((ref_node, RDFS.label, Literal(ref_text, datatype=XSD.string)))
            self.graph.add((weakness_node, SEC.hasReference, ref_node))

        # External mappings (CAPEC, CVE, WASC, OWASP, CERT, PCI, NVD, CISQ)
        for capec in weakness.get("RelatedAttackPatterns", []):
            capec_id = capec.get("CAPEC_ID", "")
            if capec_id:
                capec_node = URIRef(f"{EX}capec/CAPEC-{capec_id}")
                self.graph.add((weakness_node, SEC.mapsToCAPEC, capec_node))
        for cve in weakness.get("RelatedVulnerabilities", []):
            cve_id = cve.get("CVE_ID", "")
            if cve_id:
                cve_node = URIRef(f"{EX}cve/{cve_id}")
                self.graph.add((weakness_node, SEC.mapsToVulnerability, cve_node))
        # Add more mappings as needed for WASC, OWASP, CERT, PCI, NVD, CISQ
        # Category/View membership (if present)
        for cat in weakness.get("Categories", []):
            cat_id = cat.get("ID", "")
            if cat_id:
                cat_node = URIRef(f"{EX}category/{cat_id}")
                self.graph.add((weakness_node, SEC.memberOf, cat_node))
        for view in weakness.get("Views", []):
            view_id = view.get("ID", "")
            if view_id:
                view_node = URIRef(f"{EX}view/{view_id}")
                self.graph.add((weakness_node, SEC.memberOf, view_node))

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

    def _format_platform(self, platform_obj: dict) -> str:
        """Format platform information as a readable string."""
        parts = []
        if platform_obj.get("Language"):
            parts.append(platform_obj["Language"])
        if platform_obj.get("OperatingSystem"):
            parts.append(platform_obj["OperatingSystem"])
        return " ".join(parts) if parts else ""

    def _add_weakness_relationships(self, weaknesses: list):
        """Add parent/child relationships between weaknesses."""
        cwe_lookup = {w.get("ID", ""): w for w in weaknesses if w.get("ID")}

        relationship_map = {
            "ChildOf": SEC.childOf,
            "ParentOf": SEC.parentOf,
            "PeerOf": SEC.peerOf,
            "CanPrecede": SEC.canPrecede,
            "CanFollow": SEC.canFollow,
            "Requires": SEC.requires,
            "RequiredBy": SEC.requiredBy,
            "CanAlsoBe": SEC.canAlsoBe,
            "StartsWith": SEC.startsWith,
        }

        for weakness in weaknesses:
            cwe_id = weakness.get("ID", "")
            if not cwe_id:
                continue

            cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
            weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")

            for related in weakness.get("RelatedWeaknesses", []):
                related_id = related.get("ID", "")
                if not related_id or related_id not in cwe_lookup:
                    continue

                related_id_full = f"CWE-{related_id}" if not related_id.startswith("CWE-") else related_id
                related_node = URIRef(f"{EX}weakness/{related_id_full}")
                relationship = related.get("Relationship", "")

                predicate = relationship_map.get(relationship)
                if predicate is not None:
                    self.graph.add((weakness_node, predicate, related_node))


def _flatten_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    text_parts = []
    if element.text and element.text.strip():
        text_parts.append(element.text.strip())
    for child in element:
        child_text = _flatten_text(child)
        if child_text:
            text_parts.append(child_text)
        if child.tail and child.tail.strip():
            text_parts.append(child.tail.strip())
    return " ".join(text_parts).strip()


def _extract_platforms(weakness: ET.Element, ns: dict) -> list:
    platforms = []
    for lang in weakness.findall('.//cwe:Applicable_Platforms/cwe:Language', ns):
        value = lang.get('Name') or lang.get('Class')
        if value:
            platforms.append({'Language': value})
    for os_elem in weakness.findall('.//cwe:Applicable_Platforms/cwe:Operating_System', ns):
        value = os_elem.get('Name') or os_elem.get('Class')
        if value:
            platforms.append({'OperatingSystem': value})
    return platforms


def _cwe_xml_to_json(path: str) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'cwe': 'http://cwe.mitre.org/cwe-7'}

    weaknesses = []
    for weakness in root.findall('.//cwe:Weaknesses/cwe:Weakness', ns):
        cwe_id = weakness.get('ID')
        name = weakness.get('Name')
        abstraction = weakness.get('Abstraction')
        status = weakness.get('Status')

        description = _flatten_text(weakness.find('cwe:Description', ns))

        related = []
        for rel in weakness.findall('.//cwe:Related_Weaknesses/cwe:Related_Weakness', ns):
            rel_id = rel.get('CWE_ID')
            nature = rel.get('Nature')
            if rel_id:
                related.append({'ID': rel_id, 'Relationship': nature})

        weaknesses.append({
            'ID': cwe_id,
            'Name': name,
            'Description': description,
            'WeaknessAbstraction': abstraction,
            'Status': status,
            'ApplicablePlatforms': _extract_platforms(weakness, ns),
            'RelatedWeaknesses': related
        })

    return {'Weakness': weaknesses}


def _load_cwe_data(path: str) -> dict:
    if path.lower().endswith('.xml'):
        return _cwe_xml_to_json(path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE CWE JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CWE JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/cwe-shapes.ttl", help="SHACL shapes file")
    parser.add_argument("--format", choices=["ttl","nt"], default="ttl", help="Output format (ttl or nt)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CWE data from {args.input}...")
    cwe_json = _load_cwe_data(args.input)

    print("Transforming to RDF...")
    transformer = CWEtoRDFTransformer()
    graph = transformer.transform(cwe_json)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    if args.format == "nt":
        write_graph_ntriples_lines(graph, args.output)
    else:
        write_graph_turtle_lines(graph, args.output)

    if args.validate:
        print("\nRunning SHACL validation...")
        try:
            from core.validation import run_validator, load_graph
            shapes = load_graph(args.shapes)
            conforms, _, _ = run_validator(args.output, shapes)
            if conforms:
                print("[OK] Validation passed!")
                return 0
            else:
                print("[FAIL] Validation failed!")
                return 1
        except Exception as e:
            print(f"Warning: Could not run validation: {e}")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
