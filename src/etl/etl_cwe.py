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
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import (
        write_graph_turtle_lines,
        write_graph_ntriples_lines,
        write_graph_turtle_split_lines,
        write_graph_ntriples_split_lines,
    )
except Exception:
    from .ttl_writer import (
        write_graph_turtle_lines,
        write_graph_ntriples_lines,
        write_graph_turtle_split_lines,
        write_graph_ntriples_split_lines,
    )

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

        description_parts = []
        if weakness.get("Description"):
            desc_text = self._extract_description(weakness["Description"])
            if desc_text:
                description_parts.append(desc_text)

        for background_detail in weakness.get("BackgroundDetails", []):
            bg_text = self._extract_description(background_detail)
            if bg_text:
                description_parts.append(f"Background Detail: {bg_text}")

        for note in weakness.get("Notes", []):
            note_text = self._extract_description(note.get("Text"))
            note_type = note.get("Type", "")
            if note_text:
                if note_type:
                    description_parts.append(f"Note ({note_type}): {note_text}")
                else:
                    description_parts.append(f"Note: {note_text}")

        intro_phases = [intro.get("Phase", "") for intro in weakness.get("ModesOfIntroduction", []) if intro.get("Phase")]
        if intro_phases:
            unique_phases = sorted(set(intro_phases))
            description_parts.append(f"Modes Of Introduction: {', '.join(unique_phases)}")

        if weakness.get("LikelihoodOfExploit"):
            description_parts.append(f"Likelihood Of Exploit (source): {weakness['LikelihoodOfExploit']}")

        if description_parts:
            self.graph.add((weakness_node, SEC.description, Literal("\n".join(description_parts), datatype=XSD.string)))

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
        common_consequences = set()
        for cons in weakness.get("Consequences", []):
            scope = cons.get("Scope", "")
            impact = cons.get("Impact", "")
            note = self._extract_description(cons.get("Note", ""))
            source_consequence_id = cons.get("ConsequenceID", "")
            if not (scope or impact):
                continue
            if scope:
                common_consequences.add(scope)
            if source_consequence_id:
                cons_id = f"{cwe_id_full}-consequence-{source_consequence_id}"
            else:
                cons_id = f"{cwe_id_full}-consequence-{scope}-{impact}"
            cons_id = cons_id.replace(" ", "_")
            cons_node = URIRef(f"{EX}consequence/{cons_id}")
            self.graph.add((cons_node, RDF.type, SEC.Consequence))
            if scope:
                self.graph.add((cons_node, SEC.scope, Literal(scope, datatype=XSD.string)))
            if impact:
                self.graph.add((cons_node, SEC.impact, Literal(impact, datatype=XSD.string)))
            if note:
                self.graph.add((cons_node, SEC.description, Literal(note, datatype=XSD.string)))
            self.graph.add((weakness_node, SEC.hasConsequence, cons_node))

        for common_consequence in sorted(common_consequences):
            self.graph.add((weakness_node, SEC.commonConsequence, Literal(common_consequence, datatype=XSD.string)))

        # Mitigations
        for mit in weakness.get("PotentialMitigations", []):
            strategy = mit.get("Strategy", "")
            mitigation_description = self._extract_description(mit.get("Description", ""))
            if not strategy and mitigation_description:
                strategy = mitigation_description
            effectiveness = mit.get("Effectiveness", "")
            effectiveness_notes = self._extract_description(mit.get("EffectivenessNotes", ""))
            source_mitigation_id = mit.get("MitigationID", "")
            phases = mit.get("Phases", [])
            if not phases and mit.get("Phase"):
                phases = [mit.get("Phase")]
            if not (strategy or effectiveness or phases or mitigation_description or effectiveness_notes):
                continue
            phase_token = "-".join(phases) if phases else "none"
            if source_mitigation_id:
                mit_id = f"{cwe_id_full}-mitigation-{source_mitigation_id}"
            else:
                mit_id = f"{cwe_id_full}-mitigation-{strategy}-{phase_token}"
            mit_id = mit_id.replace(" ", "_")
            mit_node = URIRef(f"{EX}mitigation/{mit_id}")
            self.graph.add((mit_node, RDF.type, SEC.Mitigation))
            if strategy:
                self.graph.add((mit_node, SEC.strategy, Literal(strategy, datatype=XSD.string)))
            if effectiveness:
                self.graph.add((mit_node, SEC.effectiveness, Literal(effectiveness, datatype=XSD.string)))
            mitigation_text_parts = []
            if mitigation_description:
                mitigation_text_parts.append(mitigation_description)
            if effectiveness_notes:
                mitigation_text_parts.append(f"Effectiveness Notes: {effectiveness_notes}")
            if mitigation_text_parts:
                self.graph.add((mit_node, SEC.description, Literal("\n".join(mitigation_text_parts), datatype=XSD.string)))
            for phase in phases:
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
            detection_description = self._extract_description(det.get("Description", ""))
            effectiveness = det.get("Effectiveness", "")
            effectiveness_notes = self._extract_description(det.get("EffectivenessNotes", ""))
            source_detection_method_id = det.get("DetectionMethodID", "")
            if not (method or effectiveness or detection_description or effectiveness_notes):
                continue
            if source_detection_method_id:
                det_id = f"{cwe_id_full}-detection-{source_detection_method_id}"
            else:
                det_id = f"{cwe_id_full}-detection-{method}"
            det_id = det_id.replace(" ", "_")
            det_node = URIRef(f"{EX}detection/{det_id}")
            self.graph.add((det_node, RDF.type, SEC.DetectionMethod))
            if method:
                self.graph.add((det_node, SEC.method, Literal(method, datatype=XSD.string)))
            if effectiveness:
                self.graph.add((det_node, SEC.effectiveness, Literal(effectiveness, datatype=XSD.string)))
            detection_text_parts = []
            if detection_description:
                detection_text_parts.append(detection_description)
            if effectiveness_notes:
                detection_text_parts.append(f"Effectiveness Notes: {effectiveness_notes}")
            if detection_text_parts:
                self.graph.add((det_node, SEC.description, Literal("\n".join(detection_text_parts), datatype=XSD.string)))
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
                if not related_id:
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
    for tech in weakness.findall('.//cwe:Applicable_Platforms/cwe:Technology', ns):
        value = tech.get('Name') or tech.get('Class')
        if value:
            platforms.append({'Technology': value})
    for arch in weakness.findall('.//cwe:Applicable_Platforms/cwe:Architecture', ns):
        value = arch.get('Name') or arch.get('Class')
        if value:
            platforms.append({'Architecture': value})
    return platforms


def _extract_external_references(root: ET.Element, ns: dict) -> dict[str, dict]:
    external_refs: dict[str, dict] = {}
    for reference in root.findall('.//cwe:External_References/cwe:External_Reference', ns):
        ref_id = reference.get('Reference_ID')
        if not ref_id:
            continue
        title = _flatten_text(reference.find('cwe:Title', ns))
        url = _flatten_text(reference.find('cwe:URL', ns))
        author = ", ".join([
            _flatten_text(author_elem)
            for author_elem in reference.findall('cwe:Author', ns)
            if _flatten_text(author_elem)
        ])
        external_refs[ref_id] = {
            'ReferenceType': 'CWE External Reference',
            'Title': title,
            'URL': url,
            'Author': author,
        }
    return external_refs


def _extract_modes_of_introduction(weakness: ET.Element, ns: dict) -> list:
    intro_modes = []
    for intro in weakness.findall('.//cwe:Modes_Of_Introduction/cwe:Introduction', ns):
        phase = _flatten_text(intro.find('cwe:Phase', ns))
        note = _flatten_text(intro.find('cwe:Note', ns))
        if phase or note:
            intro_modes.append({'Phase': phase, 'Note': note})
    return intro_modes


def _extract_common_consequences(weakness: ET.Element, ns: dict) -> list:
    consequences = []
    for consequence in weakness.findall('.//cwe:Common_Consequences/cwe:Consequence', ns):
        consequence_id = consequence.get('Consequence_ID', '')
        scopes = [_flatten_text(scope) for scope in consequence.findall('cwe:Scope', ns) if _flatten_text(scope)]
        impacts = [_flatten_text(impact) for impact in consequence.findall('cwe:Impact', ns) if _flatten_text(impact)]
        note = _flatten_text(consequence.find('cwe:Note', ns))

        if not scopes:
            scopes = [""]
        if not impacts:
            impacts = [""]

        for scope in scopes:
            for impact in impacts:
                if scope or impact or note:
                    consequences.append(
                        {
                            'Scope': scope,
                            'Impact': impact,
                            'Note': note,
                            'ConsequenceID': consequence_id,
                        }
                    )
    return consequences


def _extract_detection_methods(weakness: ET.Element, ns: dict) -> list:
    detection_methods = []
    for detection_method in weakness.findall('.//cwe:Detection_Methods/cwe:Detection_Method', ns):
        detection_method_id = detection_method.get('Detection_Method_ID', '')
        method = _flatten_text(detection_method.find('cwe:Method', ns))
        description = _flatten_text(detection_method.find('cwe:Description', ns))
        effectiveness = _flatten_text(detection_method.find('cwe:Effectiveness', ns))
        effectiveness_notes = _flatten_text(detection_method.find('cwe:Effectiveness_Notes', ns))
        if method or description or effectiveness or effectiveness_notes:
            detection_methods.append(
                {
                    'DetectionMethodID': detection_method_id,
                    'Method': method,
                    'Description': description,
                    'Effectiveness': effectiveness,
                    'EffectivenessNotes': effectiveness_notes,
                }
            )
    return detection_methods


def _extract_potential_mitigations(weakness: ET.Element, ns: dict) -> list:
    potential_mitigations = []
    for mitigation in weakness.findall('.//cwe:Potential_Mitigations/cwe:Mitigation', ns):
        mitigation_id = mitigation.get('Mitigation_ID', '')
        phases = [_flatten_text(phase) for phase in mitigation.findall('cwe:Phase', ns) if _flatten_text(phase)]
        strategy = _flatten_text(mitigation.find('cwe:Strategy', ns))
        description = _flatten_text(mitigation.find('cwe:Description', ns))
        effectiveness = _flatten_text(mitigation.find('cwe:Effectiveness', ns))
        effectiveness_notes = _flatten_text(mitigation.find('cwe:Effectiveness_Notes', ns))
        if phases or strategy or description or effectiveness or effectiveness_notes:
            potential_mitigations.append(
                {
                    'MitigationID': mitigation_id,
                    'Phases': phases,
                    'Phase': phases[0] if phases else '',
                    'Strategy': strategy,
                    'Description': description,
                    'Effectiveness': effectiveness,
                    'EffectivenessNotes': effectiveness_notes,
                }
            )
    return potential_mitigations


def _extract_related_attack_patterns(weakness: ET.Element, ns: dict) -> list:
    related_attack_patterns = []
    for related_attack_pattern in weakness.findall('.//cwe:Related_Attack_Patterns/cwe:Related_Attack_Pattern', ns):
        capec_id = related_attack_pattern.get('CAPEC_ID')
        if capec_id:
            related_attack_patterns.append({'CAPEC_ID': capec_id})
    return related_attack_patterns


def _extract_related_vulnerabilities(weakness: ET.Element, ns: dict) -> list:
    related_vulnerabilities = []
    for observed_example in weakness.findall('.//cwe:Observed_Examples/cwe:Observed_Example', ns):
        reference_text = _flatten_text(observed_example.find('cwe:Reference', ns))
        link_text = _flatten_text(observed_example.find('cwe:Link', ns))
        cve_candidate = reference_text or link_text
        cve_match = re.search(r'(CVE-\d{4}-\d+)', cve_candidate or '', re.IGNORECASE)
        if cve_match:
            related_vulnerabilities.append({'CVE_ID': cve_match.group(1).upper()})
    return related_vulnerabilities


def _extract_weakness_references(weakness: ET.Element, external_reference_map: dict[str, dict], ns: dict) -> list:
    references = []
    for reference in weakness.findall('.//cwe:References/cwe:Reference', ns):
        external_reference_id = reference.get('External_Reference_ID')
        if not external_reference_id:
            continue
        external_reference = external_reference_map.get(external_reference_id, {})
        reference_entry = {'ReferenceType': 'CWE External Reference ID', 'Title': external_reference_id}
        reference_entry.update({k: v for k, v in external_reference.items() if v})
        references.append(reference_entry)
    return references


def _extract_notes(weakness: ET.Element, ns: dict) -> list:
    notes = []
    for note in weakness.findall('.//cwe:Notes/cwe:Note', ns):
        note_text = _flatten_text(note)
        note_type = note.get('Type', '')
        if note_text:
            notes.append({'Type': note_type, 'Text': note_text})
    return notes


def _extract_background_details(weakness: ET.Element, ns: dict) -> list:
    details = []
    for detail in weakness.findall('.//cwe:Background_Details/cwe:Background_Detail', ns):
        detail_text = _flatten_text(detail)
        if detail_text:
            details.append(detail_text)
    return details


def _cwe_xml_to_json(path: str) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'cwe': 'http://cwe.mitre.org/cwe-7'}

    external_reference_map = _extract_external_references(root, ns)

    weaknesses = []
    for weakness in root.findall('.//cwe:Weaknesses/cwe:Weakness', ns):
        cwe_id = weakness.get('ID')
        name = weakness.get('Name')
        abstraction = weakness.get('Abstraction')
        status = weakness.get('Status')

        description = _flatten_text(weakness.find('cwe:Description', ns))
        extended_description = _flatten_text(weakness.find('cwe:Extended_Description', ns))
        if extended_description:
            description = f"{description}\n\n{extended_description}" if description else extended_description

        related = []
        for rel in weakness.findall('.//cwe:Related_Weaknesses/cwe:Related_Weakness', ns):
            rel_id = rel.get('CWE_ID')
            nature = rel.get('Nature')
            if rel_id:
                related.append(
                    {
                        'ID': rel_id,
                        'Relationship': nature,
                        'ViewID': rel.get('View_ID', ''),
                        'Ordinal': rel.get('Ordinal', ''),
                    }
                )

        weaknesses.append({
            'ID': cwe_id,
            'Name': name,
            'Description': description,
            'WeaknessAbstraction': abstraction,
            'Status': status,
            'ApplicablePlatforms': _extract_platforms(weakness, ns),
            'RelatedWeaknesses': related,
            'ModesOfIntroduction': _extract_modes_of_introduction(weakness, ns),
            'LikelihoodOfExploit': _flatten_text(weakness.find('cwe:Likelihood_Of_Exploit', ns)),
            'Consequences': _extract_common_consequences(weakness, ns),
            'DetectionMethods': _extract_detection_methods(weakness, ns),
            'PotentialMitigations': _extract_potential_mitigations(weakness, ns),
            'RelatedAttackPatterns': _extract_related_attack_patterns(weakness, ns),
            'RelatedVulnerabilities': _extract_related_vulnerabilities(weakness, ns),
            'References': _extract_weakness_references(weakness, external_reference_map, ns),
            'BackgroundDetails': _extract_background_details(weakness, ns),
            'Notes': _extract_notes(weakness, ns),
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
    parser.add_argument("--nodes-out", help="Optional nodes-only output file")
    parser.add_argument("--rels-out", help="Optional relationships-only output file")
    parser.add_argument("--rels-include-types", action="store_true", help="Also write rdf:type triples to rels output")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/cwe-shapes.ttl", help="SHACL shapes file")
    parser.add_argument("--format", choices=["ttl","nt"], default="ttl", help="Output format (ttl or nt)")
    args = parser.parse_args()

    if (args.nodes_out and not args.rels_out) or (args.rels_out and not args.nodes_out):
        print("Error: --nodes-out and --rels-out must be provided together", file=sys.stderr)
        sys.exit(1)

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

    if args.nodes_out and args.rels_out:
        os.makedirs(os.path.dirname(args.nodes_out) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(args.rels_out) or ".", exist_ok=True)
        if args.format == "nt":
            write_graph_ntriples_split_lines(
                graph,
                args.nodes_out,
                args.rels_out,
                rels_include_types=args.rels_include_types,
            )
        else:
            write_graph_turtle_split_lines(
                graph,
                args.nodes_out,
                args.rels_out,
                rels_include_types=args.rels_include_types,
            )

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
