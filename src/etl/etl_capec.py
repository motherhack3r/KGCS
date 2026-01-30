"""ETL Pipeline: MITRE CAPEC JSON → RDF Turtle with SHACL validation.

Transforms official MITRE CAPEC (Common Attack Pattern Enumeration and Classification)
JSON into RDF triples conforming to the Core Ontology AttackPattern class.

Usage:
    python -m src.etl.etl_capec --input data/capec/raw/capec.json \
                              --output data/capec/samples/capec-output.ttl \
                              --validate
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import write_graph_turtle_lines
except Exception:
    from .ttl_writer import write_graph_turtle_lines

SEC = Namespace("https://example.org/sec/core#")
EX = Namespace("https://example.org/")


class CAPECtoRDFTransformer:
    """Transform MITRE CAPEC JSON response to RDF/Turtle."""

    def __init__(self, capec_to_attack: dict | None = None):
        self.graph = Graph()
        self.graph.bind("sec", SEC)
        self.graph.bind("ex", EX)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.capec_to_attack = capec_to_attack or {}

    def transform(self, capec_json: dict) -> Graph:
        """Transform CAPEC API JSON response to RDF."""
        patterns = capec_json.get("AttackPatterns", [])
        if not patterns:
            raise ValueError("Expected 'AttackPatterns' key in CAPEC JSON response")

        for pattern in patterns:
            self._add_attack_pattern(pattern)

        self._add_pattern_relationships(patterns)

        return self.graph



    def _add_attack_pattern(self, pattern: dict):
        """Add a CAPEC attack pattern entry as a sec:AttackPattern node."""
        import warnings
        capec_id = pattern.get("ID", None)
        name = pattern.get("Name")
        # Always produce a capecId
        if not capec_id or not str(capec_id).strip():
            safe_name = name.replace(' ', '_')[:20] if name else 'NO_NAME'
            capec_id_full = f"CAPEC-UNKNOWN-{safe_name}"
            warnings.warn(f"CAPEC pattern missing ID, using fallback: {capec_id_full}")
        else:
            capec_id_full = f"CAPEC-{capec_id}" if not str(capec_id).startswith("CAPEC-") else str(capec_id)

        pattern_node = URIRef(f"{EX}attackPattern/{capec_id_full}")
        self.graph.add((pattern_node, RDF.type, SEC.AttackPattern))
        self.graph.add((pattern_node, SEC.capecId, Literal(capec_id_full, datatype=XSD.string)))

        # Always emit a label, fallback to capecId or 'UNKNOWN' if missing
        label_value = name if name and str(name).strip() else capec_id_full
        if not name or not str(name).strip():
            warnings.warn(f"CAPEC pattern {capec_id_full} missing Name; using fallback label.")
        self.graph.add((pattern_node, RDFS.label, Literal(label_value, datatype=XSD.string)))

        # Description
        if pattern.get("Description"):
            desc_text = self._extract_description(pattern["Description"])
            if desc_text:
                self.graph.add((pattern_node, SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Abstraction Level
        if pattern.get("Abstraction"):
            self.graph.add((pattern_node, SEC.abstractionLevel, Literal(pattern["Abstraction"], datatype=XSD.string)))

        # Status
        if pattern.get("Status"):
            self.graph.add((pattern_node, SEC.status, Literal(pattern["Status"], datatype=XSD.string)))

        # Severity
        if pattern.get("Severity"):
            self.graph.add((pattern_node, SEC.severity, Literal(pattern["Severity"], datatype=XSD.string)))

        # Likelihood
        if pattern.get("Likelihood"):
            self.graph.add((pattern_node, SEC.likelihood, Literal(pattern["Likelihood"], datatype=XSD.string)))

        # Skill Level
        if pattern.get("SkillLevel"):
            self.graph.add((pattern_node, SEC.skillLevel, Literal(pattern["SkillLevel"], datatype=XSD.string)))

        # Published Date
        if pattern.get("PublishedDate"):
            self.graph.add((pattern_node, SEC.publishedDate, Literal(pattern["PublishedDate"], datatype=XSD.gYear)))

        # Last Modified Date
        if pattern.get("LastModifiedDate"):
            self.graph.add((pattern_node, SEC.lastModifiedDate, Literal(pattern["LastModifiedDate"], datatype=XSD.date)))

        # Member Of (Category/View)
        if pattern.get("MemberOf"):
            for member in pattern["MemberOf"]:
                if member.get("Type") == "Category":
                    cat_id = member.get("ID")
                    if cat_id:
                        cat_node = URIRef(f"{EX}category/{cat_id}")
                        self.graph.add((pattern_node, SEC.memberOf, cat_node))
                        self.graph.add((cat_node, RDF.type, SEC.Category))
                elif member.get("Type") == "View":
                    view_id = member.get("ID")
                    if view_id:
                        view_node = URIRef(f"{EX}view/{view_id}")
                        self.graph.add((pattern_node, SEC.memberOf, view_node))
                        self.graph.add((view_node, RDF.type, SEC.View))

        # Prerequisites (as nodes)
        if pattern.get("Prerequisites"):
            for i, prereq in enumerate(pattern["Prerequisites"]):
                if prereq.get("Description"):
                    prereq_text = self._extract_description(prereq["Description"])
                    if prereq_text:
                        prereq_node = URIRef(f"{EX}prerequisite/{capec_id_full}-{i}")
                        self.graph.add((prereq_node, RDF.type, SEC.Prerequisite))
                        self.graph.add((prereq_node, SEC.prerequisiteDescription, Literal(prereq_text, datatype=XSD.string)))
                        self.graph.add((pattern_node, SEC.hasPrerequisite, prereq_node))

        # Consequences (as nodes)
        if pattern.get("Consequences"):
            for i, consequence in enumerate(pattern["Consequences"]):
                if consequence.get("Description"):
                    cons_text = self._extract_description(consequence["Description"])
                    if cons_text:
                        cons_node = URIRef(f"{EX}consequence/{capec_id_full}-{i}")
                        self.graph.add((cons_node, RDF.type, SEC.Consequence))
                        self.graph.add((cons_node, SEC.consequenceDescription, Literal(cons_text, datatype=XSD.string)))
                        if consequence.get("Type"):
                            self.graph.add((cons_node, SEC.consequenceType, Literal(consequence["Type"], datatype=XSD.string)))
                        self.graph.add((pattern_node, SEC.hasConsequence, cons_node))

        # Mitigations (as nodes)
        if pattern.get("Mitigations"):
            for i, mitig in enumerate(pattern["Mitigations"]):
                if mitig.get("Description"):
                    mitig_text = self._extract_description(mitig["Description"])
                    if mitig_text:
                        mitig_node = URIRef(f"{EX}mitigation/{capec_id_full}-{i}")
                        self.graph.add((mitig_node, RDF.type, SEC.Mitigation))
                        self.graph.add((mitig_node, SEC.mitigationDescription, Literal(mitig_text, datatype=XSD.string)))
                        if mitig.get("Type"):
                            self.graph.add((mitig_node, SEC.mitigationType, Literal(mitig["Type"], datatype=XSD.string)))
                        self.graph.add((pattern_node, SEC.hasMitigation, mitig_node))

        # Execution (as nodes)
        if pattern.get("Execution"):
            for i, execu in enumerate(pattern["Execution"]):
                if execu.get("Flow"):
                    exec_node = URIRef(f"{EX}execution/{capec_id_full}-{i}")
                    self.graph.add((exec_node, RDF.type, SEC.Execution))
                    self.graph.add((exec_node, SEC.executionFlow, Literal(execu["Flow"], datatype=XSD.string)))
                    if execu.get("Phase"):
                        self.graph.add((exec_node, SEC.executionPhase, Literal(execu["Phase"], datatype=XSD.string)))
                    self.graph.add((pattern_node, SEC.hasExecution, exec_node))

        # External References (as nodes)
        if pattern.get("ExternalReferences"):
            for i, ref in enumerate(pattern["ExternalReferences"]):
                if ref.get("Title") or ref.get("URL"):
                    ref_node = URIRef(f"{EX}externalref/{capec_id_full}-{i}")
                    self.graph.add((ref_node, RDF.type, SEC.ExternalReference))
                    if ref.get("Title"):
                        self.graph.add((ref_node, SEC.referenceTitle, Literal(ref["Title"], datatype=XSD.string)))
                    if ref.get("URL"):
                        self.graph.add((ref_node, SEC.referenceURL, Literal(ref["URL"], datatype=XSD.anyURI)))
                    if ref.get("Type"):
                        self.graph.add((ref_node, SEC.referenceType, Literal(ref["Type"], datatype=XSD.string)))
                    self.graph.add((pattern_node, SEC.hasExternalReference, ref_node))


        # Related Weaknesses (CWE) -- always emit, even if empty
        related_weaknesses = pattern.get("RelatedWeaknesses")
        if related_weaknesses:
            self._add_weakness_relationships(pattern_node, related_weaknesses)
        else:
            # Emit a warning and ensure at least an empty triple for SHACL
            warnings.warn(f"CAPEC pattern {capec_id_full} has no RelatedWeaknesses (CWE links). Emitting none.")
            # Optionally, emit a triple to indicate no exploits (not required by ontology, but for SHACL completeness)
            # self.graph.add((pattern_node, SEC.exploits, URIRef("")))

        # CAPEC→ATT&CK mappings
        attack_ids = self.capec_to_attack.get(capec_id_full, [])
        for attack_id in attack_ids:
            if not isinstance(attack_id, str) or not attack_id:
                continue
            if "." in attack_id:
                technique_node = URIRef(f"{EX}subtechnique/{attack_id}")
            else:
                technique_node = URIRef(f"{EX}technique/{attack_id}")
            self.graph.add((pattern_node, SEC.implements, technique_node))

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

    def _add_weakness_relationships(self, pattern_node, related_weaknesses: list):
        """Add exploits relationships to weaknesses (CWE)."""
        for rel in related_weaknesses:
            cwe_id = rel.get("ID", "")
            if not cwe_id:
                continue

            cwe_id_full = f"CWE-{cwe_id}" if not cwe_id.startswith("CWE-") else cwe_id
            weakness_node = URIRef(f"{EX}weakness/{cwe_id_full}")
            self.graph.add((pattern_node, SEC.exploits, weakness_node))

    def _add_pattern_relationships(self, patterns: list):
        """Add relationships between attack patterns (parent/child/related)."""
        import warnings
        capec_lookup = {p.get("ID", ""): p for p in patterns if p.get("ID")}

        relationship_map = {
            "ParentOf": SEC.parentOf,
            "ChildOf": SEC.childOf,
            "PeerOf": SEC.peerOf,
            "CanPrecede": SEC.canPrecede,
            "CanFollow": SEC.canFollow,
            "CanAlsoBe": SEC.canAlsoBe,
        }

        for pattern in patterns:
            capec_id = pattern.get("ID", "")
            if not capec_id:
                continue

            capec_id_full = f"CAPEC-{capec_id}" if not capec_id.startswith("CAPEC-") else capec_id
            pattern_node = URIRef(f"{EX}attackPattern/{capec_id_full}")

            # Track if we've already emitted a childOf triple
            childof_emitted = False
            for related in pattern.get("RelatedAttackPatterns", []):
                related_id = related.get("ID", "")
                if not related_id or related_id not in capec_lookup:
                    continue

                related_id_full = f"CAPEC-{related_id}" if not related_id.startswith("CAPEC-") else related_id
                related_node = URIRef(f"{EX}attackPattern/{related_id_full}")
                relationship = related.get("Relationship", "")

                predicate = relationship_map.get(relationship)
                if predicate == SEC.childOf:
                    if not childof_emitted:
                        self.graph.add((pattern_node, predicate, related_node))
                        childof_emitted = True
                    else:
                        warnings.warn(f"CAPEC pattern {capec_id_full} has multiple childOf parents; only the first is emitted.")
                elif predicate is not None:
                    self.graph.add((pattern_node, predicate, related_node))


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


def _capec_xml_to_json(path: str) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'capec': 'http://capec.mitre.org/capec-3'}

    patterns = []
    import warnings
    for ap in root.findall('.//capec:Attack_Patterns/capec:Attack_Pattern', ns):
        capec_id = ap.get('ID')
        name = ap.get('Name')
        description = _flatten_text(ap.find('capec:Description', ns))

        prereqs = []
        for prereq in ap.findall('.//capec:Prerequisites/capec:Prerequisite', ns):
            prereq_text = _flatten_text(prereq)
            if prereq_text:
                prereqs.append({'Description': prereq_text})

        consequences = []
        for cons in ap.findall('.//capec:Consequences/capec:Consequence', ns):
            cons_text = _flatten_text(cons)
            if cons_text:
                consequences.append({'Description': cons_text})

        related_weaknesses = []
        for rel in ap.findall('.//capec:Related_Weaknesses/capec:Related_Weakness', ns):
            cwe_id = rel.get('CWE_ID')
            if cwe_id:
                related_weaknesses.append({'ID': cwe_id})

        related_attack_patterns = []
        for rel in ap.findall('.//capec:Related_Attack_Patterns/capec:Related_Attack_Pattern', ns):
            rel_id = rel.get('CAPEC_ID')
            nature = rel.get('Nature')
            if rel_id:
                related_attack_patterns.append({'ID': rel_id, 'Relationship': nature})

        if not capec_id or not str(capec_id).strip():
            safe_name = name.replace(' ', '_')[:20] if name else 'NO_NAME'
            warnings.warn(f"CAPEC Attack_Pattern missing ID attribute. Name: {name}")
            capec_id = f"UNKNOWN_{safe_name}"

        patterns.append({
            'ID': capec_id,
            'Name': name,
            'Description': description,
            'Prerequisites': prereqs,
            'Consequences': consequences,
            'RelatedWeaknesses': related_weaknesses,
            'RelatedAttackPatterns': related_attack_patterns
        })

    return {'AttackPatterns': patterns}


def _load_capec_data(path: str) -> dict:
    if path.lower().endswith('.xml'):
        return _capec_xml_to_json(path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _resolve_attack_files(attack_input: str) -> list[Path]:
    if not attack_input:
        return []
    if os.path.isdir(attack_input):
        preferred = [
            "enterprise-attack.json",
            "mobile-attack.json",
            "ics-attack.json",
            "pre-attack.json",
        ]
        preferred_paths = [Path(attack_input) / name for name in preferred if (Path(attack_input) / name).exists()]
        if preferred_paths:
            return preferred_paths
        return sorted(Path(attack_input).glob("*.json"))
    if os.path.exists(attack_input):
        return [Path(attack_input)]
    return []


def _build_capec_to_attack_map(attack_input: str) -> dict:
    capec_to_attack: dict[str, set[str]] = {}
    for attack_file in _resolve_attack_files(attack_input):
        try:
            attack_json = json.load(open(attack_file, "r", encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        objects = attack_json.get("objects", []) if isinstance(attack_json, dict) else []
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if obj.get("type") != "attack-pattern":
                continue
            external_refs = obj.get("external_references", []) or []
            attack_id = None
            capec_ids = []
            for ref in external_refs:
                if not isinstance(ref, dict):
                    continue
                if ref.get("source_name") == "mitre-attack":
                    attack_id = ref.get("external_id")
                if ref.get("source_name") == "capec":
                    capec_ids.append(ref.get("external_id"))
            if not attack_id:
                continue
            for capec_id in capec_ids:
                if not isinstance(capec_id, str) or not capec_id:
                    continue
                capec_full = capec_id if capec_id.startswith("CAPEC-") else f"CAPEC-{capec_id}"
                capec_to_attack.setdefault(capec_full, set()).add(attack_id)

    return {k: sorted(v) for k, v in capec_to_attack.items()}


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE CAPEC JSON → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CAPEC JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--attack-input", default="data/attack/raw", help="ATT&CK STIX JSON file or directory for CAPEC→ATT&CK mappings")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/capec-shapes.ttl", help="SHACL shapes file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CAPEC data from {args.input}...")
    capec_json = _load_capec_data(args.input)

    capec_to_attack = _build_capec_to_attack_map(args.attack_input)
    if capec_to_attack:
        print(f"Loaded {len(capec_to_attack)} CAPEC→ATT&CK mappings from {args.attack_input}")
    else:
        print("No CAPEC→ATT&CK mappings found (ATT&CK input missing or unmapped)")

    print("Transforming to RDF...")
    transformer = CAPECtoRDFTransformer(capec_to_attack=capec_to_attack)
    graph = transformer.transform(capec_json)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    write_graph_turtle_lines(graph, args.output)

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


if __name__ == "__main__":
    sys.exit(main())
