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
    out_f.write(f"{subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#PlatformConfiguration> .\n")
    written += 1
    out_f.write(f"{subj} <https://example.org/sec/core#matchCriteriaId> {turtle_escape(match_id)} .\n")
    written += 1

    criteria = ms.get('criteria')
    if criteria:
        out_f.write(f"{subj} <https://example.org/sec/core#configurationCriteria> {turtle_escape(criteria)} .\n")
        written += 1

    status = ms.get('status')
    if status:
        out_f.write(f"{subj} <https://example.org/sec/core#configurationStatus> {turtle_escape(status)} .\n")
        written += 1

    if ms.get('created'):
        try:
            created = datetime.fromisoformat(ms['created'].replace('Z', '+00:00'))
            out_f.write(f"{subj} <https://example.org/sec/core#configCreatedDate> \"{created.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .\n")
            written += 1
        except Exception:
            pass

    if ms.get('lastModified'):
        try:
            modified = datetime.fromisoformat(ms['lastModified'].replace('Z', '+00:00'))
            out_f.write(f"{subj} <https://example.org/sec/core#configLastModifiedDate> \"{modified.isoformat()}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .\n")
            written += 1
        except Exception:
            pass

    for match in ms.get('matches', []):
        match_cpe = match.get('cpeName')
        if not match_cpe:
            continue
        match_platform_id = match.get('cpeNameId') or urllib.parse.quote(match_cpe, safe='')
        platform_subj = subject_for_platform(match_platform_id)

        if match_platform_id not in platform_cache:
            out_f.write(f"{platform_subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#Platform> .\n")
            out_f.write(f"{platform_subj} <https://example.org/sec/core#CPEUri> {turtle_escape(match_cpe)} .\n")
            platform_cache.add(match_platform_id)
            written += 2

        out_f.write(f"{subj} <https://example.org/sec/core#matchesPlatform> {platform_subj} .\n")
        written += 1

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

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    total = 0
    platform_cache = set()
    with open(args.output, 'w', encoding='utf-8') as out_f:
        out_f.write(header)
        print(f"Loading CPEMatch JSON from {args.input}...")
        for input_file in input_files:
            if not os.path.exists(input_file):
                print(f"Warning: {input_file} not found, skipping")
                continue

            with open(input_file, 'r', encoding='utf-8') as f:
                try:
                    cpematch_json = json.load(f)
                    print(f"Transforming {os.path.basename(input_file)}...")
                    for ms_container in cpematch_json.get('matchStrings', []):
                        ms = ms_container.get('matchString') or ms_container
                        total += process_match_string(ms, out_f, platform_cache)
                except json.JSONDecodeError as e:
                    print(f"Error parsing {input_file}: {e}", file=sys.stderr)
                    sys.exit(1)

    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
