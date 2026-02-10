#!/usr/bin/env python3
"""Compute relationship stats from Turtle files.

Counts relationship triples grouped by (source,target) and (source,predicate,target).
Writes per-file CSVs and a JSON summary for quick inspection.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


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
    # De-dup while preserving order
    seen = set()
    unique: list[Path] = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        unique.append(p)
    return unique


def parse_relationship_triples(path: Path) -> tuple[Counter, Counter, Counter, int]:
    """Return (pair_counts, triple_counts, predicate_counts, total_rels)."""
    pair_counts: Counter[tuple[str, str]] = Counter()
    triple_counts: Counter[tuple[str, str, str]] = Counter()
    predicate_counts: Counter[str] = Counter()
    total = 0

    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("@prefix") or line.startswith("PREFIX") or line.startswith("#"):
                continue

            first_space = line.find(" ")
            if first_space == -1:
                continue
            second_space = line.find(" ", first_space + 1)
            if second_space == -1:
                continue

            subj = line[:first_space]
            pred = line[first_space + 1:second_space]
            obj = line[second_space + 1:]

            if obj.endswith(" ."):
                obj = obj[:-2]
            elif obj.endswith("."):
                obj = obj[:-1]

            if not obj or obj.startswith('"'):
                continue

            pair_counts[(subj, obj)] += 1
            triple_counts[(subj, pred, obj)] += 1
            predicate_counts[pred] += 1
            total += 1

    return pair_counts, triple_counts, predicate_counts, total


def write_top_csv(out_path: Path, header: list[str], rows: Iterable[tuple]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute relationship stats from TTL files")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="One or more TTL files or glob patterns",
    )
    parser.add_argument(
        "--out-dir",
        default="artifacts",
        help="Output directory for summaries",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top rows to write for each report",
    )
    args = parser.parse_args()

    input_paths = iter_input_paths(args.inputs)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict] = {}

    for path in input_paths:
        if not path.exists():
            summary[str(path)] = {"missing": True}
            continue

        pair_counts, triple_counts, predicate_counts, total = parse_relationship_triples(path)

        pair_csv = out_dir / f"{path.stem}-pair-counts-top{args.top}.csv"
        triple_csv = out_dir / f"{path.stem}-triple-counts-top{args.top}.csv"
        pred_csv = out_dir / f"{path.stem}-predicate-counts-top{args.top}.csv"

        write_top_csv(
            pair_csv,
            ["source", "target", "count"],
            ((s, o, c) for (s, o), c in pair_counts.most_common(args.top)),
        )
        write_top_csv(
            triple_csv,
            ["source", "predicate", "target", "count"],
            ((s, p, o, c) for (s, p, o), c in triple_counts.most_common(args.top)),
        )
        write_top_csv(
            pred_csv,
            ["predicate", "count"],
            ((p, c) for p, c in predicate_counts.most_common(args.top)),
        )

        summary[str(path)] = {
            "missing": False,
            "total_rel_triples": total,
            "unique_source_target_pairs": len(pair_counts),
            "unique_source_predicate_target": len(triple_counts),
            "unique_predicates": len(predicate_counts),
            "pair_counts_csv": str(pair_csv),
            "triple_counts_csv": str(triple_csv),
            "predicate_counts_csv": str(pred_csv),
        }

    summary_path = out_dir / "ttl_rel_stats_summary.json"
    with summary_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2)

    print("Wrote summary to", summary_path)
    for p, info in summary.items():
        if info.get("missing"):
            print("MISSING", p)
        else:
            print("OK", p)
            print("  total_rel_triples:", info["total_rel_triples"])
            print("  unique_source_target_pairs:", info["unique_source_target_pairs"])
            print("  unique_source_predicate_target:", info["unique_source_predicate_target"])
            print("  unique_predicates:", info["unique_predicates"])
            print("  pair_counts_csv:", info["pair_counts_csv"])
            print("  triple_counts_csv:", info["triple_counts_csv"])
            print("  predicate_counts_csv:", info["predicate_counts_csv"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
