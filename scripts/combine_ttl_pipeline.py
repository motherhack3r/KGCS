#!/usr/bin/env python3
"""
Combine all 10 pipeline TTL stages into single file.

Usage:
    python scripts/combine_ttl_pipeline.py [--output tmp/combined-pipeline.ttl]
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def combine_ttl_files(output_path="tmp/combined-pipeline.ttl"):
    """Combine all 10 stage TTL files into single output."""
    
    # Find all pipeline stage files in order
    stage_files = []
    for i in range(1, 11):
        stage_file = f"tmp/pipeline-stage{i}-*.ttl"
        # Use glob to find exact file
        import glob
        matches = glob.glob(stage_file)
        if matches:
            stage_files.append(matches[0])
    
    if not stage_files:
        print("[ERROR] No pipeline stage files found in tmp/")
        return False
    
    print(f"Combining {len(stage_files)} TTL files into {output_path}...")
    print("")
    
    # Track statistics
    total_lines = 0
    file_stats = []
    headers_skipped = 0
    
    try:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            first_file = True
            
            for idx, input_file in enumerate(stage_files, 1):
                print(f"[{idx:2d}/10] Processing: {Path(input_file).name}")
                
                with open(input_file, 'r', encoding='utf-8') as in_f:
                    lines = in_f.readlines()
                    file_lines = len(lines)
                    
                    # Count header lines (prefix declarations)
                    header_lines = 0
                    for line in lines:
                        if line.startswith("@prefix "):
                            header_lines += 1
                        else:
                            break
                    
                    # Write headers only on first file
                    if first_file:
                        out_f.writelines(lines[:header_lines])
                        if header_lines > 0:
                            out_f.write("\n")
                        lines_to_write = lines[header_lines:]
                        first_file = False
                    else:
                        # Skip headers on subsequent files
                        lines_to_write = lines[header_lines:]
                        headers_skipped += header_lines
                    
                    # Write data triples
                    out_f.writelines(lines_to_write)
                    
                    data_lines = len(lines_to_write)
                    total_lines += file_lines
                    file_stats.append((Path(input_file).name, file_lines, data_lines))
                    
                    print(f"       Lines: {file_lines:,} (data: {data_lines:,})")
        
        print("")
        print("="*70)
        print("COMBINATION COMPLETE")
        print("="*70)
        print(f"Output file: {output_path}")
        print(f"Total input lines: {total_lines:,}")
        print(f"Header lines skipped: {headers_skipped:,}")
        
        # Show file breakdown
        print("")
        print("File breakdown:")
        for name, total, data in file_stats:
            pct = (data / total * 100) if total > 0 else 0
            print(f"  {name:40s} {total:10,} lines ({data:10,} data, {pct:5.1f}%)")
        
        # Show final size
        final_size_mb = os.path.getsize(output_path) / (1024*1024)
        print("")
        print(f"Final combined file size: {final_size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Combination failed: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Combine all pipeline TTL stages into single file")
    parser.add_argument("--output", "-o", default="tmp/combined-pipeline.ttl", help="Output file path")
    
    args = parser.parse_args()
    
    print("")
    print("="*70)
    print("COMBINING PIPELINE TTL FILES")
    print("="*70)
    print(f"Start time: {datetime.now().isoformat()}")
    print("")
    
    success = combine_ttl_files(args.output)
    
    if success:
        print(f"End time: {datetime.now().isoformat()}")
        print("[OK] Combination successful!")
        return 0
    else:
        print(f"End time: {datetime.now().isoformat()}")
        print("[FAIL] Combination failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
