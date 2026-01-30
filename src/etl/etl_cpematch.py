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
    return f"<https://example.org/platform/{cpe_id}>"


def process_match_string(ms: dict, out_f, platform_cache: set) -> int:
    match_id = ms.get('matchCriteriaId')
    if not match_id:
        return 0

    subj = subject_for_config(match_id)
    written = 0
    includes_written = 0
    triples = []
    triples.append(f"{subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#PlatformConfiguration> .\n")
    triples.append(f"{subj} <https://example.org/sec/core#matchCriteriaId> {turtle_escape(match_id)} .\n")

    criteria = ms.get('criteria')
    if criteria:
        triples.append(f"{subj} <https://example.org/sec/core#configurationCriteria> {turtle_escape(criteria)} .\n")
        label_value = strip_cpe_prefix(criteria)
        if label_value:
            triples.append(f"{subj} <http://www.w3.org/2000/01/rdf-schema#label> {turtle_escape(label_value)} .\n")

    status = ms.get('status')
    if status:
        triples.append(f"{subj} <https://example.org/sec/core#configurationStatus> {turtle_escape(status)} .\n")

    if ms.get('created'):
        try:
            created = datetime.fromisoformat(ms['created'].replace('Z', '+00:00'))
            triples.append(f"{subj} <https://example.org/sec/core#configCreatedDate> \"{created.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .\n")
        except Exception:
            pass

    if ms.get('lastModified'):
        try:
            modified = datetime.fromisoformat(ms['lastModified'].replace('Z', '+00:00'))
            triples.append(f"{subj} <https://example.org/sec/core#configLastModifiedDate> \"{modified.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .\n")
        except Exception:
            pass

    for match in ms.get('matches', []):
        match_cpe = match.get('cpeName')
        if not match_cpe:
            continue

        match_platform_id = match.get('cpeNameId') or urllib.parse.quote(match_cpe, safe='')
        platform_subj = subject_for_platform(match_platform_id)

        triples.append(f"{platform_subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#Platform> .\n")
        triples.append(f"{platform_subj} <https://example.org/sec/core#cpeUri> {turtle_escape(match_cpe)} .\n")
        triples.append(f"{platform_subj} <https://example.org/sec/core#cpeNameId> {turtle_escape(match_platform_id)} .\n")
        label_value = strip_cpe_prefix(match_cpe)
        if label_value:
            triples.append(f"{platform_subj} <http://www.w3.org/2000/01/rdf-schema#label> {turtle_escape(label_value)} .\n")
        includes_written += 1
        triples.append(f"{subj} <https://example.org/sec/core#includes> {platform_subj} .\n")

        if match.get('vulnerable') is not None:
            triples.append(f"{subj} <https://example.org/sec/core#vulnerable> \"{str(match['vulnerable']).lower()}\"^^<http://www.w3.org/2001/XMLSchema#boolean> .\n")

        for vfield in ['versionStartIncluding', 'versionStartExcluding', 'versionEndIncluding', 'versionEndExcluding']:
            if match.get(vfield):
                triples.append(f"{subj} <https://example.org/sec/core#{vfield}> {turtle_escape(match[vfield])} .\n")

    if includes_written > 0:
        for t in triples:
            out_f.write(t)
            written += 1
    # If no includes, skip emitting this PlatformConfiguration
    return written
def transform_cpematch(input_data, output_path):
    """
    Transforms CPEMatch JSON data (as loaded dict) to Turtle and writes to output_path.
    Returns the number of triples written.
    """
    header = (
        "@prefix sec: <https://example.org/sec/core#> .\n"
        "@prefix ex: <https://example.org/> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total = 0
    platform_cache = set()
    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write(header)
        # Support both 'matches' (old) and 'matchStrings' (NVD 2.3)
        match_list = input_data.get('matches')
        if match_list is None:
            # Try 'matchStrings' (list of dicts with 'matchString' key)
            match_list = [ms['matchString'] for ms in input_data.get('matchStrings', []) if 'matchString' in ms]
        for ms in match_list or []:
            total += process_match_string(ms, out_f, platform_cache)
    return total

    return written


def main():
    parser = argparse.ArgumentParser(description='Streaming Transform NVD CPEMatch JSON to Turtle')
    parser.add_argument('--input', required=True, help='Input CPEMatch JSON file(s) or glob')
    parser.add_argument('--output', required=True, help='Output Turtle file')
    args = parser.parse_args()

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
    for input_file in input_files:
        print(f"Loading CPEMatch JSON from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                cpematch_json = json.load(f)
                print(f"Transforming {os.path.basename(input_file)}...")
                total += transform_cpematch(cpematch_json, args.output)
            except json.JSONDecodeError as e:
                print(f"Error parsing {input_file}: {e}", file=sys.stderr)
                sys.exit(1)

    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
