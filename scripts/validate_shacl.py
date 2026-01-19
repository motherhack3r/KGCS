"""Validate SHACL shapes against a target TTL using pyshacl.

Usage:
  python scripts/validate_shacl.py data/shacl-samples/good-example.ttl
  python scripts/validate_shacl.py data/shacl-samples/bad-example.ttl

Exit code: 0 = valid, 1 = invalid, 2 = error
"""
import sys
from rdflib import Graph
from pyshacl import validate
import json
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_shacl.py <data-file.ttl>")
        sys.exit(2)

    data_file = sys.argv[1]
    shapes = [
        'docs/ontology/shacl/core-shapes.ttl',
        'docs/ontology/shacl/rag-shapes.ttl',
        'docs/ontology/shacl/ai-strict-profile.ttl'
    ]

    data = Graph()
    try:
        data.parse(data_file, format='turtle')
    except Exception as e:
        print(f"Error parsing data file: {e}")
        sys.exit(2)

    sh = Graph()
    for s in shapes:
        try:
            sh.parse(s, format='turtle')
        except Exception as e:
            print(f"Error parsing shapes file {s}: {e}")
            sys.exit(2)

    try:
        conforms, results_graph, results_text = validate(data_graph=data, shacl_graph=sh, inference='rdfs', abort_on_first=False, serialize_report_graph=True)
        # Ensure artifacts dir
        os.makedirs('artifacts', exist_ok=True)
        report_path = os.path.join('artifacts', f'shacl-report-{os.path.basename(data_file)}.json')
        report = {
            'data_file': data_file,
            'conforms': bool(conforms),
            'results_text': results_text
        }
        with open(report_path, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, indent=2)
        print(results_text)
        print(f"Wrote report: {report_path}")
        if conforms:
            print("Validation: CONFORMS")
            sys.exit(0)
        else:
            print("Validation: DOES NOT CONFORM")
            sys.exit(1)
    except Exception as e:
        print(f"Error running pyshacl.validate: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
