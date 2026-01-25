#!/usr/bin/env python3
"""Merge nvdcpe chunk JSON files into a single nvdcpe-2.0.json

Reads: data/cpe/raw/nvdcpe-2.0-chunks/*.json
Writes: data/cpe/raw/nvdcpe-2.0.json
"""
import json
import glob
from pathlib import Path

chunk_dir = Path('data/cpe/raw/nvdcpe-2.0-chunks')
out_path = Path('data/cpe/raw/nvdcpe-2.0.json')
if not chunk_dir.exists():
    print('Chunk dir not found:', chunk_dir)
    raise SystemExit(2)

files = sorted(chunk_dir.glob('*.json'))
if not files:
    print('No chunk files found in', chunk_dir)
    raise SystemExit(1)

products = []
meta = {}
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            j = json.load(fh)
    except Exception as e:
        print('Skipping', f, 'error:', e)
        continue
    if not meta:
        # copy helpful metadata
        for k in ('format','version','timestamp','totalResults'):
            if k in j:
                meta[k] = j[k]
    # collect products array
    p = j.get('products') or j.get('Products') or j.get('items')
    if isinstance(p, list):
        products.extend(p)

out = {}
out.update(meta)
out['products'] = products
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(out, fh)

print('Wrote merged CPE JSON:', out_path, 'products:', len(products))
