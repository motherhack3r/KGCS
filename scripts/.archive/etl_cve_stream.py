#!/usr/bin/env python3
"""Streaming, lightweight CVE -> N-Triples writer.

Usage:
  python scripts/etl_cve_stream.py --input data/cve/raw/nvdcve-all.json --output data/cve/samples/cve-output.nt

Accepts either a single JSON file or a directory containing NVD JSON year files.
This is intentionally simple and writes N-Triples incrementally to avoid building a huge rdflib.Graph.
"""
import argparse
import json
import os
import sys
from datetime import datetime


def nt_escape(s: str) -> str:
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    return '"%s"' % s


def as_iri(url: str) -> str:
    return '<%s>' % url


def subject_for_cve(cve_id: str) -> str:
    # Use MITRE CVE name resolver as stable IRI
    return '<https://cve.mitre.org/cgi-bin/cvename.cgi?name=%s>' % cve_id


def process_vulnerability(item, out_f):
    # Try to be robust to different NVD JSON shapes
    cve_id = None
    if isinstance(item, dict):
        if 'cve' in item and isinstance(item['cve'], dict):
            cve_id = item['cve'].get('id') or item['cve'].get('CVE_data_meta', {}).get('ID')
        cve_id = cve_id or item.get('id') or item.get('cveId')

    if not cve_id:
        return 0

    subj = subject_for_cve(cve_id)
    triples_written = 0

    # label triple
    out_f.write(f"{subj} <http://www.w3.org/2000/01/rdf-schema#label> {nt_escape(cve_id)} .\n")
    triples_written += 1

    # description
    desc = None
    try:
        if 'cve' in item and isinstance(item['cve'], dict):
            c = item['cve']
            # common shapes: descriptions: list of {lang,value}
            descs = c.get('descriptions') or c.get('description') or c.get('descriptions', [])
            if isinstance(descs, list):
                for d in descs:
                    if isinstance(d, dict) and d.get('lang') in (None, 'en') and d.get('value'):
                        desc = d.get('value')
                        break
            elif isinstance(descs, str):
                desc = descs
        # fallback top-level
        if not desc:
            desc = item.get('description') or item.get('summary')
    except Exception:
        desc = None

    if desc:
        out_f.write(f"{subj} <http://purl.org/dc/terms/description> {nt_escape(desc)} .\n")
        triples_written += 1

    # dates
    pub = None
    for k in ('published', 'publishedDate', 'published_date', 'publishedTimestamp'):
        pub = item.get(k) or pub
    # sometimes nested
    if not pub and 'cve' in item and isinstance(item['cve'], dict):
        pub = item['cve'].get('published') or item['cve'].get('publishedDate')

    if pub:
        # try to normalize to date
        try:
            dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
            date_str = dt.date().isoformat()
            out_f.write(f"{subj} <http://purl.org/dc/terms/issued> \"{date_str}\"^^<http://www.w3.org/2001/XMLSchema#date> .\n")
            triples_written += 1
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
        # fallback top-level
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
            triples_written += 1

    return triples_written


def iter_vulnerabilities_from_file(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    # common NVD shapes: top-level 'vulnerabilities' or top-level list
    if isinstance(data, dict) and 'vulnerabilities' in data and isinstance(data['vulnerabilities'], list):
        for v in data['vulnerabilities']:
            # some wrappers place the actual record under 'cve' key
            yield v
    elif isinstance(data, list):
        for v in data:
            yield v
    elif isinstance(data, dict) and 'CVE_Items' in data and isinstance(data['CVE_Items'], list):
        for v in data['CVE_Items']:
            yield v
    else:
        # fallback: try to find list values
        for v in data.values():
            if isinstance(v, list):
                for item in v:
                    yield item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='Input JSON file or directory')
    parser.add_argument('--output', '-o', required=True, help='Output N-Triples file (.nt)')
    args = parser.parse_args()

    paths = []
    if os.path.isdir(args.input):
        # take all .json files sorted
        for fn in sorted(os.listdir(args.input)):
            if fn.lower().endswith('.json'):
                paths.append(os.path.join(args.input, fn))
    else:
        paths.append(args.input)

    total = 0
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as out_f:
        for p in paths:
            print('Processing', p, file=sys.stderr)
            for item in iter_vulnerabilities_from_file(p):
                total += process_vulnerability(item, out_f)
    print(f'Done — triples written: {total}', file=sys.stderr)


if __name__ == '__main__':
    main()
