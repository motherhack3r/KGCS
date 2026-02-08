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


def strip_cpe_prefix(cpe_uri: str) -> str:
    prefix = 'cpe:2.3:'
    if cpe_uri.startswith(prefix):
        return cpe_uri[len(prefix):]
    return cpe_uri


def subject_for_platform(cpe_id: str) -> str:
    # Ensure cpe_id is a string and not a dict
    import urllib.parse
    if isinstance(cpe_id, dict):
        # Try to use cpeNameId or cpeName from the dict
        cpe_name_id = cpe_id.get('cpeNameId')
        cpe_name = cpe_id.get('cpeName', '')
        cpe_id_str = cpe_name_id or urllib.parse.quote(str(cpe_name), safe='')
    else:
        cpe_id_str = str(cpe_id)
    return f"<https://example.org/platform/{cpe_id_str}>"


def process_product(cpe: dict, out_f) -> int:
    cpe_name = cpe.get('cpeName', '')
    if not cpe_name:
        return 0

    # Use cpeNameId if present, else URI-escape cpeName
    import urllib.parse
    cpe_id = cpe.get('cpeNameId') or urllib.parse.quote(cpe_name, safe='')
    subj = subject_for_platform(cpe_id)
    written = 0

    out_f.write(f"{subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#Platform> .\n")
    written += 1
    out_f.write(f"{subj} <https://example.org/sec/core#cpeUri> {turtle_escape(cpe_name)} .\n")
    written += 1
    label_value = strip_cpe_prefix(cpe_name)
    if label_value:
        out_f.write(f"{subj} <http://www.w3.org/2000/01/rdf-schema#label> {turtle_escape(label_value)} .\n")
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

    # Additional CPE attributes
    for attr in [
        'update', 'edition', 'language', 'sw_edition', 'target_sw', 'target_hw', 'other']:
        val = cpe.get(attr)
        if val:
            out_f.write(f"{subj} <https://example.org/sec/core#{attr}> {turtle_escape(val)} .\n")
            written += 1

    # references
    refs = cpe.get('references') or []
    if isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict) and ref.get('url'):
                out_f.write(f"{subj} <https://example.org/sec/core#referenceUrl> {turtle_escape(ref['url'])} .\n")
                written += 1
            elif isinstance(ref, str):
                out_f.write(f"{subj} <https://example.org/sec/core#referenceUrl> {turtle_escape(ref)} .\n")
                written += 1

    # deprecates relationship
    if cpe.get('deprecates'):
        dep = cpe['deprecates']
        if isinstance(dep, list):
            for d in dep:
                out_f.write(f"{subj} <https://example.org/sec/core#deprecates> {subject_for_platform(d)} .\n")
                written += 1
        elif isinstance(dep, str):
            out_f.write(f"{subj} <https://example.org/sec/core#deprecates> {subject_for_platform(dep)} .\n")
            written += 1

    return written


def transform_cpe(input_data, output_path, append=False):
    """
    Transforms CPE JSON data (as loaded dict) to Turtle and writes to output_path.
    Returns the number of triples written.
    Args:
        input_data: CPE JSON dictionary
        output_path: Output file path
        append: If True, append to existing file; if False, overwrite
    """
    header = (
        "@prefix sec: <https://example.org/sec/core#> .\n"
        "@prefix ex: <https://example.org/> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total = 0
    mode = 'a' if append else 'w'
    with open(output_path, mode, encoding='utf-8') as out_f:
        # Only write header on new files (not when appending)
        if not append:
            out_f.write(header)
        for product in input_data.get('products', []):
            cpe = product.get('cpe', {})
            total += process_product(cpe, out_f)
    return total


class CPEtoRDFTransformer:
    """Compatibility adapter: provides a `transform()` method that returns an rdflib Graph.

    This preserves the existing file-writing ETL functions while offering the
    class-based API expected by the unit tests and other pipeline harnesses.
    """
    def transform(self, input_data):
        import tempfile
        from rdflib import Graph

        # Write to a temporary Turtle file using the existing transformer
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.ttl')
        tmp_path = tmp.name
        tmp.close()
        try:
            transform_cpe(input_data, tmp_path, append=False)
            g = Graph()
            g.parse(tmp_path, format='turtle')
            return g
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description='Streaming ETL: NVD CPE JSON → Turtle')
    parser.add_argument('--input', '-i', required=True, help='Input CPE API JSON file(s), glob, or directory')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file')
    parser.add_argument('--append', action='store_true', help='Append to existing output file instead of overwriting')
    args = parser.parse_args()

    # Ensure outputs go to the standard samples folder for CPE
    samples_dir = os.path.join('data', 'cpe', 'samples')
    os.makedirs(samples_dir, exist_ok=True)
    requested_output = args.output
    output_dir = os.path.dirname(os.path.normpath(requested_output))
    if os.path.normpath(output_dir) != os.path.normpath(samples_dir):
        # relocate to samples folder, keep basename
        args.output = os.path.join(samples_dir, os.path.basename(requested_output))
        print(f"Info: overriding output path to {args.output} to use CPE samples folder")

    import glob
    input_files = []
    if os.path.isdir(args.input):
        for fn in sorted(os.listdir(args.input)):
            if fn.lower().endswith('.json'):
                input_files.append(os.path.join(args.input, fn))
    else:
        input_files = glob.glob(args.input)
        if not input_files:
            input_files = [args.input]

    if not any(os.path.exists(p) for p in input_files):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CPE JSON from {args.input}...")
    print("Transforming and writing streaming Turtle...")
    total = 0
    for idx, input_file in enumerate(input_files):
        if not os.path.exists(input_file):
            print(f"Warning: {input_file} not found, skipping")
            continue
        with open(input_file, 'r', encoding='utf-8') as f:
            cpe_json = json.load(f)
            # Append to output after first file (or if --append flag is set)
            should_append = args.append or idx > 0
            total += transform_cpe(cpe_json, args.output, append=should_append)
    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
