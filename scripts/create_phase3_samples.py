#!/usr/bin/env python3
"""Create small sample JSON files for CPE, CPEMatch, and CVE.

This script streams large NVD JSON files and writes trimmed samples suitable
for quick ETL runs.

Usage:
  python scripts/create_phase3_samples.py --count 200

Optional:
  --cpe-input <file|dir>
  --cpematch-input <file|dir>
  --cve-input <file|dir>
  --output-root <dir>
"""
import argparse
import json
import os
import random
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

import ijson


def _pick_file(path: str, pattern: str) -> Optional[str]:
    if os.path.isfile(path):
        return path
    if os.path.isdir(path):
        matches = sorted(str(p) for p in Path(path).rglob(pattern))
        return matches[0] if matches else None
    return None


def _reservoir_sample(path: str, prefix: str, limit: int, rng: random.Random) -> List[dict]:
    samples: List[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for idx, item in enumerate(ijson.items(fh, prefix), start=1):
            if len(samples) < limit:
                samples.append(item)
                continue
            j = rng.randint(1, idx)
            if j <= limit:
                samples[j - 1] = item
    return samples


def _reservoir_sample_multi(paths: List[str], prefix: str, limit: int, rng: random.Random) -> List[dict]:
    samples: List[dict] = []
    idx = 0
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, prefix):
                idx += 1
                if len(samples) < limit:
                    samples.append(item)
                    continue
                j = rng.randint(1, idx)
                if j <= limit:
                    samples[j - 1] = item
    return samples


def _write_sample(out_path: str, key: str, items: List[dict]) -> None:
    payload = {
        "resultsPerPage": len(items),
        "startIndex": 0,
        "totalResults": len(items),
        key: items,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)


def _normalize_cpematch_item(item: dict) -> dict:
    if not isinstance(item, dict):
        return {}
    return item.get("matchString") or item


def _collect_related_ids(cpematch_items: List[dict]) -> Tuple[Set[str], Set[str], Set[str]]:
    match_ids: Set[str] = set()
    cpe_ids: Set[str] = set()
    criteria_values: Set[str] = set()
    for item in cpematch_items:
        ms = _normalize_cpematch_item(item)
        match_id = ms.get("matchCriteriaId")
        if match_id:
            match_ids.add(match_id)
        criteria = ms.get("criteria") or ms.get("cpe23Uri")
        if isinstance(criteria, str) and criteria:
            criteria_values.add(criteria)
        for match in ms.get("matches", []) or []:
            cpe_id = match.get("cpeNameId")
            if cpe_id:
                cpe_ids.add(cpe_id)
    return match_ids, cpe_ids, criteria_values


def _collect_cpes(paths: List[str], cpe_ids: Set[str]) -> List[dict]:
    if not cpe_ids:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, "products.item"):
                cpe = item.get("cpe") if isinstance(item, dict) else None
                if not isinstance(cpe, dict):
                    continue
                if cpe.get("cpeNameId") in cpe_ids:
                    items.append(item)
    return items


def _collect_cves(paths: List[str], match_ids: Set[str], criteria_values: Set[str], max_items: int) -> List[dict]:
    if not match_ids and not criteria_values:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, "vulnerabilities.item"):
                if not isinstance(item, dict):
                    continue
                configs = None
                cve = item.get("cve") if isinstance(item.get("cve"), dict) else None
                if cve:
                    configs = cve.get("configurations")
                if configs is None:
                    configs = item.get("configurations")

                if _cve_has_match(configs, match_ids, criteria_values):
                    items.append(item)
                    if max_items and len(items) >= max_items:
                        return items
    return items


def _cve_has_match(configs: object, match_ids: Set[str], criteria_values: Set[str]) -> bool:
    if not configs:
        return False
    if isinstance(configs, dict):
        nodes = configs.get("nodes") or configs.get("configurations") or []
        return _nodes_have_match(nodes, match_ids, criteria_values)
    if isinstance(configs, list):
        return _nodes_have_match(configs, match_ids, criteria_values)
    return False


def _nodes_have_match(nodes: Iterable, match_ids: Set[str], criteria_values: Set[str]) -> bool:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        for match in node.get("cpeMatch", []) or []:
            if isinstance(match, dict):
                if match.get("matchCriteriaId") in match_ids:
                    return True
                criteria = match.get("criteria") or match.get("cpe23Uri")
                if isinstance(criteria, str) and criteria in criteria_values:
                    return True
        for match in node.get("cpe_match", []) or []:
            if isinstance(match, dict):
                if match.get("matchCriteriaId") in match_ids:
                    return True
                criteria = match.get("criteria") or match.get("cpe23Uri")
                if isinstance(criteria, str) and criteria in criteria_values:
                    return True
        children = node.get("children") or []
        if _nodes_have_match(children, match_ids, criteria_values):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Create small Phase 3 sample JSON files")
    parser.add_argument("--count", type=int, default=200, help="Number of CPEMatch entries to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument("--cpe-input", default="data/cpe/raw/nvdcpe-2.0-chunks", help="CPE input file or directory")
    parser.add_argument("--cpematch-input", default="data/cpe/raw/nvdcpematch-2.0-chunks", help="CPEMatch input file or directory")
    parser.add_argument("--cve-input", default="data/cve/raw", help="CVE input file or directory")
    parser.add_argument("--output-root", default="data", help="Root output directory")
    parser.add_argument("--cve-max", type=int, default=None, help="Max CVE records to include (default: same as --count)")
    parser.add_argument("--cve-fallback-random", action=argparse.BooleanOptionalAction, default=True, help="When no linked CVEs found, fall back to random CVE sampling")
    args = parser.parse_args()

    cpe_files: List[str] = []
    if os.path.isdir(args.cpe_input):
        cpe_files = sorted(str(p) for p in Path(args.cpe_input).rglob("nvdcpe-2.0-chunk-*.json"))
    else:
        candidate = _pick_file(args.cpe_input, "nvdcpe-2.0-chunk-*.json")
        if candidate:
            cpe_files = [candidate]
    if not cpe_files:
        print("CPE input not found")
        return 1

    cpematch_files: List[str] = []
    if os.path.isdir(args.cpematch_input):
        cpematch_files = sorted(str(p) for p in Path(args.cpematch_input).rglob("nvdcpematch-2.0-chunk-*.json"))
    else:
        candidate = _pick_file(args.cpematch_input, "nvdcpematch-2.0-chunk-*.json")
        if candidate:
            cpematch_files = [candidate]
    if not cpematch_files:
        print("CPEMatch input not found")
        return 1

    cve_files: List[str] = []
    if os.path.isdir(args.cve_input):
        cve_files = sorted(str(p) for p in Path(args.cve_input).rglob("nvdcve-2.0-*.json"))
    else:
        candidate = _pick_file(args.cve_input, "nvdcve-2.0-*.json")
        if candidate:
            cve_files = [candidate]
    if not cve_files:
        print("CVE input not found")
        return 1

    print(f"Using CPE files: {len(cpe_files)}")
    print(f"Using CPEMatch files: {len(cpematch_files)}")
    print(f"Using CVE files: {len(cve_files)}")

    rng = random.Random(args.seed)
    cpematch_items = _reservoir_sample_multi(cpematch_files, "matchStrings.item", args.count, rng)
    match_ids, cpe_ids, criteria_values = _collect_related_ids(cpematch_items)

    cpe_items = _collect_cpes(cpe_files, cpe_ids)
    cve_max = args.cve_max if args.cve_max is not None else args.count
    cve_items = _collect_cves(cve_files, match_ids, criteria_values, cve_max)
    if not cve_items and args.cve_fallback_random and cve_max:
        print("No linked CVEs found; falling back to random CVE sampling")
        cve_items = _reservoir_sample_multi(cve_files, "vulnerabilities.item", cve_max, rng)

    cpe_out = os.path.join(args.output_root, "cpe", "samples", "sample_cpe.json")
    cpematch_out = os.path.join(args.output_root, "cpe", "samples", "sample_cpematch.json")
    cve_out = os.path.join(args.output_root, "cve", "samples", "sample_cve.json")

    _write_sample(cpe_out, "products", cpe_items)
    _write_sample(cpematch_out, "matchStrings", cpematch_items)
    _write_sample(cve_out, "vulnerabilities", cve_items)

    print(f"Wrote {len(cpe_items)} CPE products to {cpe_out}")
    print(f"Wrote {len(cpematch_items)} CPEMatch entries to {cpematch_out}")
    print(f"Wrote {len(cve_items)} CVE entries to {cve_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
