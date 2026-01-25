#!/usr/bin/env python3
"""Merge nvdcpematch chunk JSON files into a single nvdcpematch-2.0.json

Reads: data/cpe/raw/nvdcpematch-2.0-chunks/*.json
Writes: data/cpe/raw/nvdcpematch-2.0.json
"""
import json
import glob
from pathlib import Path

chunk_dir = Path('data/cpe/raw/nvdcpematch-2.0-chunks')
out_path = Path('data/cpe/raw/nvdcpematch-2.0.json')
if not chunk_dir.exists():
    print('Chunk dir not found:', chunk_dir)
    raise SystemExit(2)

files = sorted(chunk_dir.glob('*.json'))
if not files:
    print('No chunk files found in', chunk_dir)
    raise SystemExit(1)

matches = []
meta = {}
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            j = json.load(fh)
    except Exception as e:
        print('Skipping', f, 'error:', e)
        continue
    if not meta:
        for k in ('format','version','timestamp','totalResults'):
            if k in j:
                meta[k] = j[k]
    # possible keys: 'matchStrings' (array of {"matchString": {...}}) or 'matches'
    if 'matchStrings' in j and isinstance(j['matchStrings'], list):
        for ms in j['matchStrings']:
            if isinstance(ms, dict) and 'matchString' in ms:
                matches.append(ms['matchString'])
            else:
                matches.append(ms)
    else:
        p = j.get('matches') or j.get('Matches') or j.get('results')
        if isinstance(p, list):
            matches.extend(p)

out = {}
out.update(meta)
# ETL expects 'matchStrings' top-level key where each item is {"matchString": {...}}
out['matchStrings'] = [{'matchString': m} for m in matches]
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(out, fh)

print('Wrote merged CPEMatch JSON:', out_path, 'matches:', len(matches))
