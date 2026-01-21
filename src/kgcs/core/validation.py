"""Validate SHACL shapes against a target TTL using pyshacl.

This module supports selecting a subset of shapes by RAG template name
or by passing an explicit list of shape files. It writes a JSON report to
`artifacts/shacl-report-<data-file>.json`.

Usage:
  from kgcs.core.validation import run_validator, load_graph
  shapes = load_graph('docs/ontology/shacl/kgcs-shapes.ttl')
  conforms, report_path, results_text = run_validator('data/sample.ttl', shapes)

Exit codes: 0 = valid, 1 = invalid, 2 = error
"""

import argparse
import json
import os
import re
from rdflib import Graph, Namespace, URIRef, BNode
from rdflib.namespace import RDF
from pyshacl import validate


EX = Namespace('https://example.org/sec/core#')


TEMPLATE_SHAPE_MAP = {
    'T1': ['VulnerabilityShape', 'WeaknessShape', 'AttackPatternShape', 'TechniqueShape', 'TacticShape'],
    'T2': ['VulnerabilityShape', 'VulnerabilityScoreShape'],
    'T3': ['TechniqueShape', 'DetectionAnalyticShape'],
    'T4': ['TechniqueShape', 'DefensiveTechniqueShape'],
    'T5': ['TechniqueShape', 'TacticShape', 'DeceptionTechniqueShape'],
    'T6': ['VulnerabilityShape', 'ReferenceShape'],
    'T7': ['VulnerabilityShape', 'WeaknessShape', 'AttackPatternShape', 'TechniqueShape', 'DetectionAnalyticShape', 'DefensiveTechniqueShape']
}


def load_graph(path):
    """Load a Turtle file into an rdflib Graph."""
    g = Graph()
    g.parse(path, format='turtle')
    return g


def extract_shape_subset(full_shapes_graph: Graph, shape_local_names):
    """Return a new Graph containing only the node-shapes with the given local names.

    This performs a shallow copy of triples where the subject is the shape node
    and any directly referenced blank node property definitions (e.g., sh:property bnode).
    """
    out = Graph()
    for name in shape_local_names:
        node = EX[name]
        # copy triples where subject is node
        for s, p, o in full_shapes_graph.triples((node, None, None)):
            out.add((s, p, o))
            if isinstance(o, BNode):
                # copy bnode definition triples
                for ss, pp, oo in full_shapes_graph.triples((o, None, None)):
                    out.add((ss, pp, oo))
    return out

def run_validator(data_file: str, shapes_graph: Graph, output: str = 'artifacts', rule_catalog_path: str = 'docs/ontology/shacl/rule_catalog.json'):
    """Run pyshacl validation for the given data_graph/shapes_graph.

    Returns: (conforms: bool, report_path: str, results_text: str)
    """
    # Data graph
    data = Graph()
    data.parse(data_file, format='turtle')

    # Run validation
    conforms, results_graph, results_text = validate(data_graph=data, shacl_graph=shapes_graph, inference='rdfs', abort_on_first=False, serialize_report_graph=True)
    os.makedirs(output, exist_ok=True)
    report_path = os.path.join(output, f'shacl-report-{os.path.basename(data_file)}.json')
    # Load rule catalog if available
    catalog = {}
    if os.path.exists(rule_catalog_path):
        try:
            with open(rule_catalog_path, 'r', encoding='utf-8') as fh:
                catalog = json.load(fh)
        except Exception:
            catalog = {}
    # catalog loaded (used to map shapes -> rule_ids)

    # Extract structured violations from the results_graph
    SH = Namespace('http://www.w3.org/ns/shacl#')
    violations = []
    try:
        for r in results_graph.subjects(RDF.type, SH.ValidationResult):
            message = results_graph.value(r, SH.resultMessage)
            focus = results_graph.value(r, SH.focusNode)
            source_shape = results_graph.value(r, SH.sourceShape)
            result_path = results_graph.value(r, SH.resultPath)
            shape_key = None
            rule_id = None
            if source_shape is not None:
                s_str = str(source_shape)
                # local name fallback
                if '#' in s_str:
                    local = s_str.split('#')[-1]
                else:
                    local = s_str.split('/')[-1]
                shape_key = local
                entry = catalog.get(s_str) or catalog.get(local)
                if isinstance(entry, dict):
                    rule_id = entry.get('rule_id')
                elif isinstance(entry, str):
                    rule_id = entry
            violations.append({
                'rule_id': rule_id,
                'shape': shape_key,
                'message': str(message) if message is not None else '',
                'focus_node': str(focus) if focus is not None else None,
                'path': str(result_path) if result_path is not None else None
            })
    except Exception:
        # If parsing the results graph fails, leave violations empty
        violations = []

    # Fallback: if results_graph did not contain SH:ValidationResult nodes (older pyshacl/text output),
    # try to parse the human-readable `results_text` for one-off extraction of Source Shape and Message.
    if not violations and results_text:
        # Look for blocks like: "Source Shape: ex:CARDetectionShape" and "Message: ..."
        pattern = r"Source Shape:\s*(?P<shape>[^\n]+)\n[\s\S]*?Message:\s*(?P<message>.+?)\n"
        matches = re.finditer(pattern, results_text)
        for m in matches:
            shape_raw = m.group('shape').strip()
            msg = m.group('message').strip()
            # normalize shape local name
            if '#' in shape_raw:
                local = shape_raw.split('#')[-1]
            else:
                local = shape_raw.split(':')[-1] if ':' in shape_raw else shape_raw
            entry = catalog.get(shape_raw) or catalog.get(local)
            rule_id = entry if isinstance(entry, str) else (entry.get('rule_id') if isinstance(entry, dict) else None)
            violations.append({
                'rule_id': rule_id,
                'shape': local,
                'message': msg,
                'focus_node': None,
                'path': None
            })

    report = {
        'data_file': data_file,
        'conforms': bool(conforms),
        'results_text': results_text,
        'violations': violations
    }
    with open(report_path, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, indent=2)
    return bool(conforms), report_path, results_text


def validate_data(data_file: str, shapes_file: str = 'docs/ontology/shacl/kgcs-shapes.ttl', output: str = 'artifacts') -> bool:
    """Convenience function: load shapes and validate data.
    
    Returns True if data conforms, False otherwise.
    """
    shapes = load_graph(shapes_file)
    conforms, _, _ = run_validator(data_file, shapes, output)
    return conforms


def parse_args():
    p = argparse.ArgumentParser(description='Validate TTL data against SHACL shapes (KGCS)')
    p.add_argument('--data', '-d', help='Data file (Turtle) to validate')
    p.add_argument('--shapes', '-s', action='append', help='Path to SHACL shapes file (Turtle). Can be passed multiple times')
    p.add_argument('--template', '-t', choices=list(TEMPLATE_SHAPE_MAP.keys()), help='RAG template name to select a subset of shapes')
    p.add_argument('--owl', help='OWL module filename (e.g., attck-ontology-v1.0.owl) to auto-select mapped shape bundle')
    p.add_argument('--list-templates', action='store_true', help='List available RAG templates and exit')
    p.add_argument('--output', '-o', default='artifacts', help='Output folder for JSON reports')
    return p.parse_args()


def main():
    args = parse_args()
    if args.list_templates:
        print('Available RAG templates:')
        for k, v in TEMPLATE_SHAPE_MAP.items():
            print(f" - {k}: {', '.join(v)}")
        return

    data_file = args.data

    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        raise SystemExit(2)

    # Default shapes bundle
    default_shapes = ['docs/ontology/shacl/kgcs-shapes.ttl']

    # If explicit shapes provided, use them; else if --owl provided, map via manifest; otherwise use default
    shapes_paths = None
    if args.shapes:
        shapes_paths = args.shapes
    elif args.owl:
        # Prefer a machine manifest (JSON); fall back to the human-readable manifest.md
        json_manifest = 'docs/ontology/shacl/manifest.json'
        md_manifest = 'docs/ontology/shacl/manifest.md'
        mapping = {}
        if os.path.exists(json_manifest):
            try:
                with open(json_manifest, 'r', encoding='utf-8') as fh:
                    mapping = json.load(fh)
            except Exception as e:
                print(f"Error parsing JSON manifest {json_manifest}: {e}; falling back to markdown manifest")
                mapping = {}
        if not mapping and os.path.exists(md_manifest):
            try:
                with open(md_manifest, 'r', encoding='utf-8') as fh:
                    for line in fh:
                        line = line.strip()
                        # expect lines like: - `cpe-ontology-v1.0.owl` → `docs/ontology/shacl/cpe-shapes.ttl`
                        if line.startswith('- `') and '→' in line:
                            try:
                                left, right = line.split('→', 1)
                                owl_name = left.split('`')[1]
                                shapes_list = [s.strip(' `') for s in right.split(',')]
                                mapping[owl_name] = shapes_list
                            except Exception:
                                continue
            except FileNotFoundError:
                print(f"Manifest not found: {md_manifest}; falling back to default shapes")
                shapes_paths = default_shapes

        if shapes_paths is None:
            shapes_paths = mapping.get(args.owl)
            if not shapes_paths:
                print(f"No SHACL mapping found for {args.owl}; using default shapes bundle")
                shapes_paths = default_shapes
    else:
        shapes_paths = default_shapes

    # Load full shapes graph
    full_shapes = Graph()
    for sp in shapes_paths:
        try:
            full_shapes.parse(sp, format='turtle')
        except Exception as e:
            print(f"Error parsing shapes file {sp}: {e}")
            raise SystemExit(2)

    # If template specified, extract subset from full_shapes
    if args.template:
        template = args.template
        local_names = TEMPLATE_SHAPE_MAP.get(template, [])
        if not local_names:
            print(f"No shapes configured for template {template}")
            raise SystemExit(2)
        shapes_graph = extract_shape_subset(full_shapes, local_names)
    else:
        shapes_graph = full_shapes

    # Load data
    data = Graph()
    try:
        data.parse(data_file, format='turtle')
    except Exception as e:
        print(f"Error parsing data file: {e}")
        raise SystemExit(2)

    # Run validation via helper
    try:
        conforms, report_path, results_text = run_validator(data_file=data_file, shapes_graph=shapes_graph, output=args.output)
        print(results_text)
        print(f"Wrote report: {report_path}")
        if conforms:
            print("Validation: CONFORMS")
            raise SystemExit(0)
        else:
            print("Validation: DOES NOT CONFORM")
            raise SystemExit(1)
    except Exception as e:
        print(f"Error running pyshacl.validate: {e}")
        raise SystemExit(2)


if __name__ == '__main__':
    main()
