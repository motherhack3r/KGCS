#!/usr/bin/env python3
"""Merge MITRE JSON fragments into a single JSON with a given top-level key.

Usage:
  python scripts/merge_mitre_jsons.py --key DeceptionTechniques --input-dir data/shield/raw --output data/shield/raw/shield.json
"""

import json
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Merge MITRE JSON fragments")
    parser.add_argument("--key", required=True, help="Top-level key (e.g., DeceptionTechniques or EngagementConcepts)")
    parser.add_argument("--input-dir", required=True, help="Directory containing JSON fragments")
    parser.add_argument("--output", required=True, help="Output combined JSON file")
    args = parser.parse_args()

    out = {args.key: []}
    p = Path(args.input_dir)
    if not p.exists():
        print(f"Input directory does not exist: {p}")
        return 2

    files = sorted(p.glob("*.json"))
    if not files:
        print(f"No JSON files found in {p}")

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                j = json.load(fh)
        except Exception as e:
            print(f"Skipping {f}: failed to parse JSON ({e})")
            continue

        if isinstance(j, dict) and args.key in j and isinstance(j[args.key], list):
            out[args.key].extend(j[args.key])
        elif isinstance(j, list):
            out[args.key].extend(j)
        else:
            # try to find array values to merge
            for v in j.values() if isinstance(j, dict) else []:
                if isinstance(v, list):
                    out[args.key].extend(v)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    print(f"Wrote combined JSON: {out_path} (items: {len(out[args.key])})")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
