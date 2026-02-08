"""ETL Pipeline: NVD CVE JSON -> RDF Turtle with SHACL validation.

Transforms official NVD CVE API JSON (2.0) into RDF triples conforming to the
Core Ontology Vulnerability/VulnerabilityScore classes.

**IMPORTANT: This transformer assumes PlatformConfiguration entities have been created
by etl_cpematch.py. CVE records reference existing PlatformConfiguration nodes by
matchCriteriaId (foreign key relationship).**

Recommended ingestion order:
  1. etl_cpe.py       → Create Platform nodes from CPE definitions
  2. etl_cpematch.py  → Create PlatformConfiguration nodes from match criteria
  3. etl_cve.py       → Create Vulnerability nodes (references existing configs)

Usage:
    python -m src.etl.etl_cve --input data/cve/raw/cve-api-response.json \
                              --output data/cve/samples/cve-output.ttl \
                              --validate
"""
























        
















#!/usr/bin/env python3
"""Streaming CVE ETL: write Turtle incrementally to avoid large in-memory graphs.

Usage:
  python src/etl/etl_cve.py --input data/cve/raw --output data/cve/samples/cve-output.ttl

This script accepts either a single NVD JSON file or a directory of per-year JSON files.
It writes Turtle triples incrementally, emitting a small header with prefixes and then
one triple-per-line Turtle statements for each CVE found.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import re

import ijson


def turtle_escape(s: str) -> str:
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    return '"%s"' % s


def subject_for_cve(cve_id: str) -> str:
    return '<https://cve.mitre.org/cgi-bin/cvename.cgi?name=%s>' % cve_id


def subject_for_config(match_id: str) -> str:
    return f"<https://example.org/platformConfiguration/{match_id}>"


def subject_for_weakness(cwe_id: str) -> str:
    cwe_id_full = cwe_id if cwe_id.startswith("CWE-") else f"CWE-{cwe_id}"
    return f"<https://example.org/weakness/{cwe_id_full}>"


def _extract_configs(item: dict):
    if not isinstance(item, dict):
        return None
    cve = item.get('cve') if isinstance(item.get('cve'), dict) else None
    if cve and isinstance(cve.get('configurations'), (list, dict)):
        return cve.get('configurations')
    return item.get('configurations')


def _iter_match_criteria_ids(configs, criteria_to_match_id=None):
    if not configs:
        return
    if isinstance(configs, dict):
        nodes = configs.get('nodes') or configs.get('configurations') or []
    elif isinstance(configs, list):
        nodes = []
        for entry in configs:
            if isinstance(entry, dict) and isinstance(entry.get('nodes'), list):
                nodes.extend(entry.get('nodes'))
            else:
                nodes.append(entry)
    else:
        return

    stack = list(nodes)
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        for match in node.get('cpeMatch', []) or []:
            if isinstance(match, dict):
                match_id = match.get('matchCriteriaId')
                if match_id:
                    yield match_id
                    continue
                if criteria_to_match_id:
                    criteria = match.get('criteria') or match.get('cpe23Uri')
                    if criteria:
                        mapped = criteria_to_match_id.get(criteria)
                        if mapped:
                            yield mapped
        for match in node.get('cpe_match', []) or []:
            if isinstance(match, dict):
                match_id = match.get('matchCriteriaId')
                if match_id:
                    yield match_id
                    continue
                if criteria_to_match_id:
                    criteria = match.get('criteria') or match.get('cpe23Uri')
                    if criteria:
                        mapped = criteria_to_match_id.get(criteria)
                        if mapped:
                            yield mapped
        children = node.get('children') or []
        if children:
            stack.extend(children)


def process_vulnerability(item, out_f, criteria_to_match_id=None):
    cve_id = None
    if isinstance(item, dict):
        if 'cve' in item and isinstance(item['cve'], dict):
            cve_id = item['cve'].get('id') or item['cve'].get('CVE_data_meta', {}).get('ID')
        cve_id = cve_id or item.get('id') or item.get('cveId')

    if not cve_id:
        return 0

    subj = subject_for_cve(cve_id)
    triples = 0

    # rdf:type
    out_f.write(f"{subj} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#Vulnerability> .\n")
    triples += 1

    # cveId
    out_f.write(f"{subj} <https://example.org/sec/core#cveId> {turtle_escape(cve_id)} .\n")
    triples += 1

    # rdfs:label
    out_f.write(f"{subj} <http://www.w3.org/2000/01/rdf-schema#label> {turtle_escape(cve_id)} .\n")
    triples += 1

    # description
    desc = None
    try:
        if 'cve' in item and isinstance(item['cve'], dict):
            c = item['cve']
            descs = c.get('descriptions') or c.get('description') or c.get('descriptions', [])
            if isinstance(descs, list):
                for d in descs:
                    if isinstance(d, dict) and d.get('lang') in (None, 'en') and d.get('value'):
                        desc = d.get('value')
                        break
            elif isinstance(descs, str):
                desc = descs
        if not desc:
            desc = item.get('description') or item.get('summary')
    except Exception:
        desc = None

    if desc:
        out_f.write(f"{subj} <https://example.org/sec/core#description> {turtle_escape(desc)} .\n")
        triples += 1

    # published date
    pub = None
    for k in ('published', 'publishedDate', 'published_date', 'publishedTimestamp'):
        pub = item.get(k) or pub
    if not pub and 'cve' in item and isinstance(item['cve'], dict):
        pub = item['cve'].get('published') or item['cve'].get('publishedDate')

    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
            ds = dt.date().isoformat()
            out_f.write(f"{subj} <http://purl.org/dc/terms/issued> \"{ds}\"^^<http://www.w3.org/2001/XMLSchema#date> .\n")
            triples += 1
        except Exception:
            pass

    # references
    refs = []
    try:
        if 'cve' in item and isinstance(item['cve'], dict):
            c = item['cve']
            r = c.get('references') or c.get('reference')
            if isinstance(r, list):
                for ref in r:
                    if isinstance(ref, dict):
                        url = ref.get('url') or ref.get('href')
                        if url:
                            refs.append(url)
                    elif isinstance(ref, str):
                        refs.append(ref)
        if not refs:
            for key in ('references', 'refs'):
                r = item.get(key)
                if isinstance(r, list):
                    for ref in r:
                        if isinstance(ref, dict) and ref.get('url'):
                            refs.append(ref.get('url'))
                        elif isinstance(ref, str):
                            refs.append(ref)
    except Exception:
        pass

    for url in refs:
        if not url:
            continue
        if url.startswith('http'):
            out_f.write(f"{subj} <https://example.org/sec/core#referenceUrl> {turtle_escape(url)} .\n")
            triples += 1

    # vulnStatus
    vuln_status = item.get('vulnStatus') or (item.get('cve', {}) or {}).get('vulnStatus')
    if vuln_status:
        out_f.write(f"{subj} <https://example.org/sec/core#vulnStatus> {turtle_escape(vuln_status)} .\n")
        triples += 1

    # CISA fields
    for cisa_field in [
        'cisaVulnerabilityName', 'cisaExploitAdd', 'cisaActionDue',
        'cisaRequiredAction', 'cisaKnownRansomwareCampaignUse']:
        val = item.get(cisa_field) or (item.get('cve', {}) or {}).get(cisa_field)
        if val:
            out_f.write(f"{subj} <https://example.org/sec/core#{cisa_field}> {turtle_escape(val)} .\n")
            triples += 1

    # CVSS scores
    impact = item.get('impact') or (item.get('cve', {}) or {}).get('impact')
    if impact:
        for metric, pred, version in [
            ('baseMetricV3', 'cvssV3Score', 'v3'),
            ('baseMetricV2', 'cvssV2Score', 'v2')]:
            m = impact.get(metric)
            if m and m.get(f'cvss{version.upper()}'):
                score = m[f'cvss{version.upper()}']
                for k, v in score.items():
                    out_f.write(f"{subj} <https://example.org/sec/core#{pred}_{k}> {turtle_escape(str(v))} .\n")
                    triples += 1

    # affects (PlatformConfiguration)
    configs = item.get('configurations') or (item.get('cve', {}) or {}).get('configurations')
    if configs:
        for match_id in _iter_match_criteria_ids(configs, criteria_to_match_id):
            if match_id:
                out_f.write(f"{subj} <https://example.org/sec/core#affects> {subject_for_config(match_id)} .\n")
                triples += 1

    # CWE relationships: CVE -> CWE (caused_by)
    weaknesses = []
    try:
        if isinstance(item.get("cve"), dict):
            weaknesses = item["cve"].get("weaknesses") or []
        if not weaknesses:
            weaknesses = item.get("weaknesses") or []
    except Exception:
        weaknesses = []

    cwe_ids = set()
    for weakness in weaknesses:
        if not isinstance(weakness, dict):
            continue
        descriptions = weakness.get("description") or []
        if isinstance(descriptions, dict):
            descriptions = [descriptions]
        for desc_entry in descriptions:
            value = desc_entry.get("value") if isinstance(desc_entry, dict) else desc_entry
            if not isinstance(value, str):
                continue
            for match in re.findall(r"CWE-\d+", value):
                cwe_ids.add(match)

    for cwe_id in sorted(cwe_ids):
        weakness_subj = subject_for_weakness(cwe_id)
        out_f.write(f"{subj} <https://example.org/sec/core#caused_by> {weakness_subj} .\n")
        triples += 1

    # configurations: link PlatformConfiguration -> Vulnerability via matchCriteriaId
    configs = _extract_configs(item)
    if configs:
        seen = set()
        for match_id in _iter_match_criteria_ids(configs, criteria_to_match_id):
            if match_id in seen:
                continue
            seen.add(match_id)
            config_subj = subject_for_config(match_id)
            out_f.write(f"{config_subj} <https://example.org/sec/core#affected_by> {subj} .\n")
            triples += 1

    return triples


def iter_vulnerabilities_from_file(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    if isinstance(data, dict) and 'vulnerabilities' in data and isinstance(data['vulnerabilities'], list):
        for v in data['vulnerabilities']:
            yield v
    elif isinstance(data, list):
        for v in data:
            yield v
    elif isinstance(data, dict) and 'CVE_Items' in data and isinstance(data['CVE_Items'], list):
        for v in data['CVE_Items']:
            yield v
    else:
        for v in data.values():
            if isinstance(v, list):
                for item in v:
                    yield item


def _iter_cpematch_files(path: str):
    if os.path.isdir(path):
        for p in sorted(Path(path).rglob('*.json')):
            yield str(p)
    else:
        yield path


def build_cpematch_index(path: str) -> dict:
    criteria_to_match_id = {}
    for file_path in _iter_cpematch_files(path):
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='utf-8') as fh:
            for item in ijson.items(fh, 'matchStrings.item'):
                ms = item.get('matchString') if isinstance(item, dict) else None
                if not isinstance(ms, dict):
                    ms = item if isinstance(item, dict) else None
                if not ms:
                    continue
                criteria = ms.get('criteria')
                match_id = ms.get('matchCriteriaId')
                if criteria and match_id and criteria not in criteria_to_match_id:
                    criteria_to_match_id[criteria] = match_id
    return criteria_to_match_id


def transform_cve(input_data, output_path, criteria_to_match_id=None):
    """
    Transforms CVE JSON data (as loaded dict) to Turtle and writes to output_path.
    Returns the number of triples written.
    """
    header = (
        "@prefix sec: <https://example.org/sec/core#> .\n"
        "@prefix dcterms: <http://purl.org/dc/terms/> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total = 0
    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write(header)
        for item in input_data.get('vulnerabilities', []):
            total += process_vulnerability(item, out_f, criteria_to_match_id)
    return total

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='Input JSON file or directory')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file (.ttl)')
    parser.add_argument('--cpematch-input', help='Optional CPEMatch JSON file/dir to resolve criteria -> matchCriteriaId')
    parser.add_argument('--validate', action='store_true', help='Validate output with SHACL')
    parser.add_argument('--shapes', help='SHACL shapes file (defaults to docs/ontology/shacl/cve-shapes.ttl)')
    parser.add_argument('--append', action='store_true', help='Append to existing output file instead of overwriting')
    args = parser.parse_args()

    # Ensure outputs go to the standard samples folder for CVE
    samples_dir = os.path.join('data', 'cve', 'samples')
    os.makedirs(samples_dir, exist_ok=True)
    requested_output = args.output
    output_dir = os.path.dirname(os.path.normpath(requested_output))
    if os.path.normpath(output_dir) != os.path.normpath(samples_dir):
        args.output = os.path.join(samples_dir, os.path.basename(requested_output))
        print(f"Info: overriding output path to {args.output} to use CVE samples folder")

    paths = []
    if os.path.isdir(args.input):
        for fn in sorted(os.listdir(args.input)):
            if fn.lower().endswith('.json'):
                paths.append(os.path.join(args.input, fn))
    else:
        paths.append(args.input)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    total = 0
    header = (
        "@prefix sec: <https://example.org/sec/core#> .\n"
        "@prefix dcterms: <http://purl.org/dc/terms/> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )

    criteria_to_match_id = None
    if args.cpematch_input:
        print(f"Building CPEMatch criteria index from {args.cpematch_input}...", file=sys.stderr)
        criteria_to_match_id = build_cpematch_index(args.cpematch_input)
        print(f"CPEMatch criteria index size: {len(criteria_to_match_id)}", file=sys.stderr)

    mode = 'a' if args.append else 'w'
    with open(args.output, mode, encoding='utf-8') as out_f:
        # Only write header on new files (not when appending)
        if not args.append:
            out_f.write(header)
        for p in paths:
            print('Processing', p, file=sys.stderr)
            for item in iter_vulnerabilities_from_file(p):
                total += process_vulnerability(item, out_f, criteria_to_match_id)

    print(f'Done — triples written: {total}', file=sys.stderr)

    # SHACL validation
    if args.validate:
        print(f"\nValidating {args.output}...")
        try:
            from src.core.validation import run_validator, load_graph
        except ImportError:
            from core.validation import run_validator, load_graph
        
        shapes_file = args.shapes or 'docs/ontology/shacl/cve-shapes.ttl'
        if os.path.exists(shapes_file):
            shapes = load_graph(shapes_file)
            conforms, _, _ = run_validator(args.output, shapes)
            if conforms:
                print(f"[OK] Validation passed!")
            else:
                print(f"[FAIL] Validation failed!")
                return 1
        else:
            print(f"Warning: Could not find shapes file: {shapes_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())

