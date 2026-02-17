#!/usr/bin/env python3
import glob
from pathlib import Path
files = sorted(glob.glob('data/cpe/raw/nvdcpe-2.0-chunks/*.json'))
if not files:
    print('No files found in nvdcpe-2.0-chunks')
    raise SystemExit(1)
print('First file:', files[0])
print('\n--- preview ---\n')
with open(files[0], 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f):
        print(line.rstrip())
        if i>50:
            break
