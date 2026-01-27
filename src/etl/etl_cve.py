"""ETL Pipeline: NVD CVE JSON → RDF Turtle with SHACL validation.

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


def turtle_escape(s: str) -> str:
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    return '"%s"' % s


def subject_for_cve(cve_id: str) -> str:
    return '<https://cve.mitre.org/cgi-bin/cvename.cgi?name=%s>' % cve_id


def process_vulnerability(item, out_f):
    cve_id = None
    if isinstance(item, dict):
        if 'cve' in item and isinstance(item['cve'], dict):
            cve_id = item['cve'].get('id') or item['cve'].get('CVE_data_meta', {}).get('ID')
        cve_id = cve_id or item.get('id') or item.get('cveId')

    if not cve_id:
        return 0

    subj = subject_for_cve(cve_id)
    triples = 0

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
        out_f.write(f"{subj} <http://purl.org/dc/terms/description> {turtle_escape(desc)} .\n")
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
            out_f.write(f"{subj} <http://purl.org/dc/terms/references> <{url}> .\n")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='Input JSON file or directory')
    parser.add_argument('--output', '-o', required=True, help='Output Turtle file (.ttl)')
    args = parser.parse_args()

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
        "@prefix dcterms: <http://purl.org/dc/terms/> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
    )

    with open(args.output, 'w', encoding='utf-8') as out_f:
        out_f.write(header)
        for p in paths:
            print('Processing', p, file=sys.stderr)
            for item in iter_vulnerabilities_from_file(p):
                total += process_vulnerability(item, out_f)

    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()

