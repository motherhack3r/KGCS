"""ETL Pipeline: NVD CPEMatch JSON → RDF Turtle with SHACL validation.

Transforms official NVD CPEMatch API JSON (2.0) into RDF triples conforming to the
Core Ontology PlatformConfiguration class.

This transformer creates PlatformConfiguration entities from matchString entries,
which are then referenced by CVE records via matchCriteriaId.

Usage:
    python -m src.etl.etl_cpematch --input data/cpe/raw/nvdcpematch-2.0/chunk-*.json \
                                   --output data/cpe/matches/cpe-matches-output.ttl \
                                   --validate
"""

import argparse
import json
import os
import sys
import urllib.parse
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


def subject_for_config(match_id: str) -> str:
    return f"<https://example.org/platformConfiguration/{match_id}>"


def subject_for_platform(cpe_id: str) -> str:
    # Ensure cpe_id is a string and not a dict
    import urllib.parse
    if isinstance(cpe_id, dict):
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


def process_match_string(ms: dict, writer: TripleWriter, platform_cache: set, include_orphans: bool = False) -> int:
    match_id = ms.get('matchCriteriaId')
    if not match_id:
        return 0

    subj = subject_for_config(match_id)
    written = 0
    includes_written = 0
    triples = []
    triples.append((subj, "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "<https://example.org/sec/core#PlatformConfiguration>", True, True))
    triples.append((subj, "<https://example.org/sec/core#matchCriteriaId>", turtle_escape(match_id), False, False))

    criteria = ms.get('criteria')
    if criteria:
        triples.append((subj, "<https://example.org/sec/core#configurationCriteria>", turtle_escape(criteria), False, False))
        label_value = strip_cpe_prefix(criteria)
        if label_value:
            triples.append((subj, "<http://www.w3.org/2000/01/rdf-schema#label>", turtle_escape(label_value), False, False))

    status = ms.get('status')
    if status:
        triples.append((subj, "<https://example.org/sec/core#configurationStatus>", turtle_escape(status), False, False))

    if ms.get('created'):
        try:
            created = datetime.fromisoformat(ms['created'].replace('Z', '+00:00'))
            triples.append((
                subj,
                "<https://example.org/sec/core#configCreatedDate>",
                f"\"{created.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime>",
                False,
                False,
            ))
        except Exception:
            pass

    if ms.get('lastModified'):
        try:
            modified = datetime.fromisoformat(ms['lastModified'].replace('Z', '+00:00'))
            triples.append((
                subj,
                "<https://example.org/sec/core#configLastModifiedDate>",
                f"\"{modified.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime>",
                False,
                False,
            ))
        except Exception:
            pass

    for match in ms.get('matches', []):
        match_cpe = match.get('cpeName')
        if not match_cpe:
            continue

        match_platform_id = match.get('cpeNameId') or urllib.parse.quote(match_cpe, safe='')
        platform_subj = subject_for_platform(match_platform_id)

        # Emit Platform node with canonical `cpeUri`
        triples.append((platform_subj, "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "<https://example.org/sec/core#Platform>", True, True))
        triples.append((platform_subj, "<https://example.org/sec/core#cpeUri>", turtle_escape(match_cpe), False, False))
        triples.append((platform_subj, "<https://example.org/sec/core#cpeNameId>", turtle_escape(match_platform_id), False, False))
        label_value = strip_cpe_prefix(match_cpe)
        if label_value:
            triples.append((platform_subj, "<http://www.w3.org/2000/01/rdf-schema#label>", turtle_escape(label_value), False, False))
        includes_written += 1
        # Link PlatformConfiguration -> Platform using canonical `matchesPlatform`
        triples.append((subj, "<https://example.org/sec/core#matchesPlatform>", platform_subj, True, False))

        if match.get('vulnerable') is not None:
            triples.append((
                subj,
                "<https://example.org/sec/core#vulnerable>",
                f"\"{str(match['vulnerable']).lower()}\"^^<http://www.w3.org/2001/XMLSchema#boolean>",
                False,
                False,
            ))

        for vfield in ['versionStartIncluding', 'versionStartExcluding', 'versionEndIncluding', 'versionEndExcluding']:
            if match.get(vfield):
                triples.append((subj, f"<https://example.org/sec/core#{vfield}>", turtle_escape(match[vfield]), False, False))

    if includes_written > 0 or include_orphans:
        for subj, pred, obj, is_uri_obj, is_rdf_type in triples:
            writer.write(subj, pred, obj, is_uri_obj=is_uri_obj, is_rdf_type=is_rdf_type)
            written += 1
    # If no includes and not including orphans, skip emitting this PlatformConfiguration
    return written
def transform_cpematch(
    input_data,
    output_path,
    append=False,
    nodes_output_path=None,
    rels_output_path=None,
    rels_include_types: bool = False,
    include_orphans: bool = False,
):
    """
    Transforms CPEMatch JSON data (as loaded dict) to Turtle and writes to output_path.
    Returns the number of triples written.
    Args:
        input_data: CPEMatch JSON dictionary
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
    platform_cache = set()
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
        # Support both 'matches' (old) and 'matchStrings' (NVD 2.3)
        match_list = input_data.get('matches')
        if match_list is None:
            # Try 'matchStrings' (list of dicts with 'matchString' key)
            match_list = [ms['matchString'] for ms in input_data.get('matchStrings', []) if 'matchString' in ms]
        for ms in match_list or []:
            total += process_match_string(ms, writer, platform_cache, include_orphans=include_orphans)
        writer.finalize()
        if nodes_f:
            nodes_f.close()
        if rels_f:
            rels_f.close()
    return total


def main():
    parser = argparse.ArgumentParser(description='Streaming Transform NVD CPEMatch JSON to Turtle')
    parser.add_argument('--input', required=True, help='Input CPEMatch JSON file(s) or glob')
    parser.add_argument('--output', required=True, help='Output Turtle file')
    parser.add_argument('--nodes-out', help='Optional nodes-only Turtle output file')
    parser.add_argument('--rels-out', help='Optional relationships-only Turtle output file')
    parser.add_argument('--rels-include-types', action='store_true', help='Also write rdf:type triples to rels output')
    parser.add_argument('--include-orphan-configs', action='store_true', help='Emit PlatformConfiguration nodes even if no includes are present')
    parser.add_argument('--exclude-orphan-configs', action='store_true', help='Skip PlatformConfiguration nodes with no includes')
    parser.add_argument('--append', action='store_true', help='Append to existing output file instead of overwriting')
    args = parser.parse_args()

    if (args.nodes_out and not args.rels_out) or (args.rels_out and not args.nodes_out):
        print("Error: --nodes-out and --rels-out must be provided together", file=sys.stderr)
        sys.exit(1)

    # Ensure outputs go to the standard samples folder for CPE (matches live with other CPE outputs)
    samples_dir = os.path.join('data', 'cpe', 'samples')
    os.makedirs(samples_dir, exist_ok=True)
    requested_output = args.output
    output_dir = os.path.dirname(os.path.normpath(requested_output))
    if os.path.normpath(output_dir) != os.path.normpath(samples_dir):
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
    input_files = glob.glob(args.input)
    if not input_files:
        input_files = [args.input]

    header = (
        "@prefix sec: <https://example.org/sec/core#> .\n"
        "@prefix ex: <https://example.org/> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )

    total = 0
    for idx, input_file in enumerate(input_files):
        print(f"Loading CPEMatch JSON from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                cpematch_json = json.load(f)
                print(f"Transforming {os.path.basename(input_file)}...")
                # Append to output after first file (or if --append flag is set)
                should_append = args.append or idx > 0
                include_orphans = True
                if args.exclude_orphan_configs:
                    include_orphans = False
                total += transform_cpematch(
                    cpematch_json,
                    args.output,
                    append=should_append,
                    nodes_output_path=args.nodes_out,
                    rels_output_path=args.rels_out,
                    rels_include_types=args.rels_include_types,
                    include_orphans=include_orphans,
                )
            except json.JSONDecodeError as e:
                print(f"Error parsing {input_file}: {e}", file=sys.stderr)
                sys.exit(1)

    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
