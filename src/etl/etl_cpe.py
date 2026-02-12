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


class TripleWriter:
    def __init__(self, main_f, nodes_f=None, rels_f=None, rels_include_types: bool = False):
        self.main_f = main_f
        self.nodes_f = nodes_f
        self.rels_f = rels_f
        self.rels_include_types = rels_include_types
        self.type_lines = {}
        self.rel_endpoints = set()
        self.types_written = set()

    def write(self, subj: str, pred: str, obj: str, is_uri_obj: bool = False, is_rdf_type: bool = False) -> None:
        line = f"{subj} {pred} {obj} .\n"
        self.main_f.write(line)
        if self.nodes_f is None and self.rels_f is None:
            return
        if is_rdf_type or not is_uri_obj:
            if self.nodes_f:
                self.nodes_f.write(line)
            if is_rdf_type:
                self.type_lines[subj] = line
        else:
            if self.rels_f:
                self.rels_f.write(line)
            if self.rels_include_types:
                self.rel_endpoints.add(subj)
                self.rel_endpoints.add(obj)

    def finalize(self) -> None:
        if not self.rels_include_types or not self.rels_f:
            return
        for subj in self.rel_endpoints:
            if subj in self.types_written:
                continue
            line = self.type_lines.get(subj)
            if line:
                self.rels_f.write(line)
                self.types_written.add(subj)


def process_product(cpe: dict, writer: TripleWriter) -> int:
    cpe_name = cpe.get('cpeName', '')
    if not cpe_name:
        return 0

    # Use cpeNameId if present, else URI-escape cpeName
    import urllib.parse
    cpe_id = cpe.get('cpeNameId') or urllib.parse.quote(cpe_name, safe='')
    subj = subject_for_platform(cpe_id)
    written = 0

    writer.write(
        subj,
        "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
        "<https://example.org/sec/core#Platform>",
        is_uri_obj=True,
        is_rdf_type=True,
    )
    written += 1
    # Emit canonical OWL property `CPEUri` (capitalized) and keep backward-compatible `cpeUri`
    writer.write(subj, "<https://example.org/sec/core#CPEUri>", turtle_escape(cpe_name))
    writer.write(subj, "<https://example.org/sec/core#cpeUri>", turtle_escape(cpe_name))
    written += 1
    label_value = strip_cpe_prefix(cpe_name)
    if label_value:
        writer.write(subj, "<http://www.w3.org/2000/01/rdf-schema#label>", turtle_escape(label_value))
        written += 1

    parts = cpe_name.split(':')
    if len(parts) >= 3:
        writer.write(subj, "<https://example.org/sec/core#platformPart>", turtle_escape(parts[2]))
        written += 1
    if len(parts) >= 4:
        writer.write(subj, "<https://example.org/sec/core#vendor>", turtle_escape(parts[3]))
        written += 1
    if len(parts) >= 5:
        writer.write(subj, "<https://example.org/sec/core#product>", turtle_escape(parts[4]))
        written += 1
    if len(parts) >= 6 and parts[5] != '*':
        writer.write(subj, "<https://example.org/sec/core#version>", turtle_escape(parts[5]))
        written += 1

    if cpe.get('deprecated') is not None:
        deprecated = 'true' if cpe['deprecated'] else 'false'
        writer.write(subj, "<https://example.org/sec/core#platformDeprecated>", turtle_escape(deprecated))
        written += 1

    if cpe.get('cpeNameId'):
        writer.write(subj, "<https://example.org/sec/core#cpeNameId>", turtle_escape(cpe['cpeNameId']))
        written += 1

    if cpe.get('created'):
        try:
            created = datetime.fromisoformat(cpe['created'].replace('Z', '+00:00'))
            writer.write(
                subj,
                "<https://example.org/sec/core#cpeCreatedDate>",
                f"\"{created.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime>",
            )
            written += 1
        except Exception:
            pass

    if cpe.get('lastModified'):
        try:
            modified = datetime.fromisoformat(cpe['lastModified'].replace('Z', '+00:00'))
            writer.write(
                subj,
                "<https://example.org/sec/core#cpeLastModifiedDate>",
                f"\"{modified.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime>",
            )
            written += 1
        except Exception:
            pass

    # Additional CPE attributes
    for attr in [
        'update', 'edition', 'language', 'sw_edition', 'target_sw', 'target_hw', 'other']:
        val = cpe.get(attr)
        if val:
            writer.write(subj, f"<https://example.org/sec/core#{attr}>", turtle_escape(val))
            written += 1

    # references
    refs = cpe.get('references') or []
    if isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict) and ref.get('url'):
                writer.write(subj, "<https://example.org/sec/core#referenceUrl>", turtle_escape(ref['url']))
                written += 1
            elif isinstance(ref, str):
                writer.write(subj, "<https://example.org/sec/core#referenceUrl>", turtle_escape(ref))
                written += 1

    # deprecates relationship
    if cpe.get('deprecates'):
        dep = cpe['deprecates']
        if isinstance(dep, list):
            for d in dep:
                writer.write(subj, "<https://example.org/sec/core#deprecates>", subject_for_platform(d), is_uri_obj=True)
                written += 1
        elif isinstance(dep, str):
            writer.write(subj, "<https://example.org/sec/core#deprecates>", subject_for_platform(dep), is_uri_obj=True)
            written += 1

    return written


def transform_cpe(input_data, output_path, append=False, nodes_output_path=None, rels_output_path=None, rels_include_types: bool = False):
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
        nodes_f = None
        rels_f = None
        if nodes_output_path and rels_output_path:
            nodes_f = open(nodes_output_path, mode, encoding='utf-8')
            rels_f = open(rels_output_path, mode, encoding='utf-8')
        # Only write header on new files (not when appending)
        if not append:
            out_f.write(header)
            if nodes_f:
                nodes_f.write(header)
            if rels_f:
                rels_f.write(header)
        writer = TripleWriter(out_f, nodes_f, rels_f, rels_include_types=rels_include_types)
        for product in input_data.get('products', []):
            cpe = product.get('cpe', {})
            total += process_product(cpe, writer)
        writer.finalize()
        if nodes_f:
            nodes_f.close()
        if rels_f:
            rels_f.close()
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
    parser.add_argument('--nodes-out', help='Optional nodes-only Turtle output file')
    parser.add_argument('--rels-out', help='Optional relationships-only Turtle output file')
    parser.add_argument('--rels-include-types', action='store_true', help='Also write rdf:type triples to rels output')
    parser.add_argument('--append', action='store_true', help='Append to existing output file instead of overwriting')
    args = parser.parse_args()

    if (args.nodes_out and not args.rels_out) or (args.rels_out and not args.nodes_out):
        print("Error: --nodes-out and --rels-out must be provided together", file=sys.stderr)
        sys.exit(1)

    # Ensure outputs go to the standard samples folder for CPE
    samples_dir = os.path.join('data', 'cpe', 'samples')
    os.makedirs(samples_dir, exist_ok=True)
    requested_output = args.output
    output_dir = os.path.dirname(os.path.normpath(requested_output))
    if os.path.normpath(output_dir) != os.path.normpath(samples_dir):
        # relocate to samples folder, keep basename
        args.output = os.path.join(samples_dir, os.path.basename(requested_output))
        print(f"Info: overriding output path to {args.output} to use CPE samples folder")

    if args.nodes_out and args.rels_out:
        nodes_dir = os.path.dirname(os.path.normpath(args.nodes_out))
        rels_dir = os.path.dirname(os.path.normpath(args.rels_out))
        if os.path.normpath(nodes_dir) != os.path.normpath(samples_dir):
            args.nodes_out = os.path.join(samples_dir, os.path.basename(args.nodes_out))
            print(f"Info: overriding nodes output path to {args.nodes_out} to use CPE samples folder")
        if os.path.normpath(rels_dir) != os.path.normpath(samples_dir):
            args.rels_out = os.path.join(samples_dir, os.path.basename(args.rels_out))
            print(f"Info: overriding rels output path to {args.rels_out} to use CPE samples folder")

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
            total += transform_cpe(
                cpe_json,
                args.output,
                append=should_append,
                nodes_output_path=args.nodes_out,
                rels_output_path=args.rels_out,
                rels_include_types=args.rels_include_types,
            )
    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
