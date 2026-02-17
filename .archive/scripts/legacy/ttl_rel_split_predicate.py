#!/usr/bin/env python3
"""Split relationship triples in a TTL file by predicate.

Writes one TTL per selected predicate and an optional remainder file.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Any


def iter_input_paths(patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = list(Path().glob(pattern))
        if matches:
            paths.extend(matches)
        else:
            p = Path(pattern)
            if p.exists():
                paths.append(p)
    seen = set()
    unique: list[Path] = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        unique.append(p)
    return unique


def parse_triple_line(line: str) -> tuple[str, str, str] | None:
    first_space = line.find(" ")
    if first_space == -1:
        return None
    second_space = line.find(" ", first_space + 1)
    if second_space == -1:
        return None

    subj = line[:first_space]
    pred = line[first_space + 1:second_space]
    obj = line[second_space + 1:]

    if obj.endswith(" ."):
        obj = obj[:-2]
    elif obj.endswith("."):
        obj = obj[:-1]

    if not obj or obj.startswith('"'):
        return None
    return subj, pred, obj


def sanitize_predicate(pred: str) -> str:
    safe = pred.replace("<", "").replace(">", "")
    safe = safe.replace("/", "_").replace("#", "_").replace(":", "_")
    return safe


def split_file(input_path: Path, out_dir: Path, predicates: set[str], other_out: Path | None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix_lines: list[str] = []
    handles: dict[str, Path] = {}
    output_handles: dict[str, Any] = {}
    counts: dict[str, int] = {p: 0 for p in predicates}
    other_count = 0
    other_handle = None

    def get_handle(pred: str):
        if pred not in handles:
            safe = sanitize_predicate(pred)
            out_path = out_dir / f"{input_path.stem}-{safe}.ttl"
            handles[pred] = out_path
        if pred not in output_handles:
            out_path = handles[pred]
            out_fh = out_path.open("w", encoding="utf-8", newline="\n")
            for pline in prefix_lines:
                out_fh.write(pline + "\n")
            if prefix_lines:
                out_fh.write("\n")
            output_handles[pred] = out_fh
        return output_handles[pred]

    def get_other_handle():
        nonlocal other_handle
        if other_out is None:
            return None
        if other_handle is None:
            other_out.parent.mkdir(parents=True, exist_ok=True)
            other_handle = other_out.open("w", encoding="utf-8", newline="\n")
            for pline in prefix_lines:
                other_handle.write(pline + "\n")
            if prefix_lines:
                other_handle.write("\n")
        return other_handle

    with input_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("@prefix") or line.startswith("PREFIX"):
                prefix_lines.append(raw_line.rstrip("\n"))
                continue
            if line.startswith("#"):
                continue

            triple = parse_triple_line(line)
            if not triple:
                continue
            _, pred, _ = triple

            if pred in predicates:
                out_fh = get_handle(pred)
                out_fh.write(raw_line if raw_line.endswith("\n") else raw_line + "\n")
                counts[pred] += 1
            elif other_out is not None:
                out_fh = get_other_handle()
                if out_fh is not None:
                    out_fh.write(raw_line if raw_line.endswith("\n") else raw_line + "\n")
                other_count += 1

    for fh in output_handles.values():
        fh.close()
    if other_handle is not None:
        other_handle.close()

    return {
        "input": str(input_path),
        "outputs": {p: str(handles[p]) for p in predicates},
        "counts": counts,
        "other_out": str(other_out) if other_out else None,
        "other_count": other_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Split TTL rels by predicate")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="One or more TTL files or glob patterns",
    )
    parser.add_argument(
        "--predicates",
        nargs="+",
        required=True,
        help="Predicate tokens to split (e.g., <https://example.org/sec/core#deprecates>)",
    )
    parser.add_argument(
        "--out-dir",
        default="artifacts",
        help="Output directory for split TTLs",
    )
    parser.add_argument(
        "--other-out",
        help="Optional output TTL for non-selected predicates",
    )
    args = parser.parse_args()

    input_paths = iter_input_paths(args.inputs)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    predicates = set(args.predicates)

    for path in input_paths:
        if not path.exists():
            print("MISSING", path)
            continue
        other_out = Path(args.other_out) if args.other_out else None
        summary = split_file(path, out_dir, predicates, other_out)
        print("OK", path)
        for pred, out_path in summary["outputs"].items():
            print("  predicate:", pred)
            print("  output:", out_path)
            print("  count:", summary["counts"].get(pred, 0))
        if summary["other_out"]:
            print("  other_out:", summary["other_out"])
            print("  other_count:", summary["other_count"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
