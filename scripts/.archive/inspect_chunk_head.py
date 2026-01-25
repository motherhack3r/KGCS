#!/usr/bin/env python3
import glob
files = sorted(glob.glob('data/cpe/raw/nvdcpe-2.0-chunks/*.json'))
if not files:
    print('No files found')
    raise SystemExit(1)
f = files[0]
print('file:', f)
with open(f, 'rb') as fh:
    data = fh.read(200)
print(repr(data.decode('utf-8','replace')))
