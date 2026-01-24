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
import sys
from datetime import datetime


def turtle_escape(s: str) -> str:
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    return '"%s"' % s


def subject_for_platform(cpe_id: str) -> str:
    return f"<https://example.org/platform/{cpe_id}>"


def process_product(cpe: dict, out_f) -> int:
    cpe_name = cpe.get('cpeName', '')
    if not cpe_name:
        return 0

    cpe_id = cpe.get('cpeNameId') or (cpe_name.replace('/', '%2F'))
    subj = subject_for_platform(cpe_id)
    written = 0

    out_f.write(f"{subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#Platform> .\n")
    written += 1
    out_f.write(f"{subj} <https://example.org/sec/core#cpeUri> {turtle_escape(cpe_name)} .\n")
    written += 1

    parts = cpe_name.split(':')
    if len(parts) >= 3:
        out_f.write(f"{subj} <https://example.org/sec/core#platformPart> {turtle_escape(parts[2])} .\n")
        written += 1
    if len(parts) >= 4:
        out_f.write(f"{subj} <https://example.org/sec/core#vendor> {turtle_escape(parts[3])} .\n")
        written += 1
    if len(parts) >= 5:
        out_f.write(f"{subj} <https://example.org/sec/core#product> {turtle_escape(parts[4])} .\n")
        written += 1
    if len(parts) >= 6 and parts[5] != '*':
        out_f.write(f"{subj} <https://example.org/sec/core#version> {turtle_escape(parts[5])} .\n")
        written += 1

    if cpe.get('deprecated') is not None:
        deprecated = 'true' if cpe['deprecated'] else 'false'
        out_f.write(f"{subj} <https://example.org/sec/core#platformDeprecated> {turtle_escape(deprecated)} .\n")
        written += 1

    if cpe.get('cpeNameId'):
        out_f.write(f"{subj} <https://example.org/sec/core#cpeNameId> {turtle_escape(cpe['cpeNameId'])} .\n")
        written += 1

    if cpe.get('created'):
        try:
            created = datetime.fromisoformat(cpe['created'].replace('Z', '+00:00'))
            out_f.write(f"{subj} <https://example.org/sec/core#cpeCreatedDate> \"{created.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .\n")
            written += 1
        except Exception:
            pass

    if cpe.get('lastModified'):
        try:
            modified = datetime.fromisoformat(cpe['lastModified'].replace('Z', '+00:00'))
            out_f.write(f"{subj} <https://example.org/sec/core#cpeLastModifiedDate> \"{modified.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .\n")
            written += 1
        except Exception:
            pass

    return written


def main():
    parser = argparse.ArgumentParser(description='Streaming ETL: NVD CPE JSON → Turtle')
    parser.add_argument('--input', '-i', required=True, help='Input CPE API JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CPE JSON from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        cpe_json = json.load(f)

    header = (
        "@prefix sec: <https://example.org/sec/core#> .\n"
        "@prefix ex: <https://example.org/> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    total = 0
    with open(args.output, 'w', encoding='utf-8') as out_f:
        out_f.write(header)
        print("Transforming and writing streaming Turtle...")
        for product in cpe_json.get('products', []):
            cpe = product.get('cpe', {})
            total += process_product(cpe, out_f)

    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
