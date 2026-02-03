#!/usr/bin/env python3
"""
Combine all enhanced pipeline stages into a single TTL file for Neo4j loading.
"""

import os
from pathlib import Path
from datetime import datetime

stage_files = [
    'tmp/pipeline-stage1-cpe.ttl',
    'tmp/pipeline-stage2-cpematch.ttl',
    'tmp/pipeline-stage3-cve.ttl',
    'tmp/pipeline-stage4-attack-enterprise.ttl',
    'tmp/pipeline-stage4-attack-ics.ttl',
    'tmp/pipeline-stage4-attack-mobile.ttl',
    'tmp/pipeline-stage4-attack-pre.ttl',
    'tmp/pipeline-stage5-d3fend.ttl',
    'tmp/pipeline-stage6-capec.ttl',  # Enhanced with XML Taxonomy_Mappings
    'tmp/pipeline-stage7-cwe.ttl',
    'tmp/pipeline-stage8-car.ttl',
    'tmp/pipeline-stage9-shield.ttl',
    'tmp/pipeline-stage10-engage.ttl',
]

output_file = 'tmp/combined-pipeline-enhanced-capec.ttl'

print(f"\n{'='*70}")
print(f"KGCS Combined Pipeline Generator (Enhanced CAPEC)")
print(f"{'='*70}")
print(f"[*] Start time: {datetime.now().isoformat()}")
print(f"[*] Combining to: {output_file}")
print(f"[*] Input files: {len(stage_files)}\n")

total_size = 0
found_files = 0
missing_files = []

# First pass: validate files exist and report sizes
for stage_file in stage_files:
    if os.path.exists(stage_file):
        size = os.path.getsize(stage_file)
        total_size += size
        found_files += 1
        print(f"  [✓] {Path(stage_file).name:40s} {size/1024/1024:8.2f} MB")
    else:
        missing_files.append(stage_file)
        print(f"  [✗] {Path(stage_file).name:40s} NOT FOUND")

if missing_files:
    print(f"\n[!] WARNING: {len(missing_files)} file(s) not found")
    for f in missing_files:
        print(f"     - {f}")
else:
    print(f"\n[✓] All files found")

# Second pass: combine files
print(f"\n[*] Combining {found_files} files...")

try:
    with open(output_file, 'w', encoding='utf-8') as out:
        lines_written = 0
        for stage_file in stage_files:
            if os.path.exists(stage_file):
                with open(stage_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        out.write(line)
                        lines_written += 1
    
    output_size = os.path.getsize(output_file)
    
    print(f"[✓] Combined successfully")
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Input files:      {found_files}")
    print(f"  Total input:      {total_size/1024/1024:.2f} MB")
    print(f"  Output file:      {output_file}")
    print(f"  Output size:      {output_size/1024/1024:.2f} MB")
    print(f"  Total lines:      {lines_written:,}")
    print(f"\n[✓] Pipeline ready for Neo4j loading")
    print(f"{'='*70}\n")

except Exception as e:
    print(f"\n[✗] ERROR: {e}\n")
    exit(1)
