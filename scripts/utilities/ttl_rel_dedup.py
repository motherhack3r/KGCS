#!/usr/bin/env python3
"""Deduplicate relationship triples in a TTL file.

This keeps only unique (subject, predicate, object) triples for relationships
and preserves prefix lines at the top of the output.
"""

from __future__ import annotations

import argparse
import sqlite3
import tempfile
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


def dedup_file(input_path: Path, output_path: Path, db_path: Path | None, keep_db: bool) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix_lines: list[str] = []

    created_temp_db = False
    if db_path is None:
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="ttl-dedup-", suffix=".sqlite")
        try:
            import os
            os.close(tmp_fd)
        except Exception:
            pass
        db_path = Path(tmp_name)
        created_temp_db = True

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("CREATE TABLE IF NOT EXISTS rels (s TEXT, p TEXT, o TEXT, PRIMARY KEY (s, p, o))")
        insert_sql = "INSERT OR IGNORE INTO rels (s, p, o) VALUES (?, ?, ?)"

        total = 0
        kept = 0
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
                total += 1
                conn.execute(insert_sql, triple)
        conn.commit()

        cursor = conn.execute("SELECT COUNT(*) FROM rels")
        kept = cursor.fetchone()[0]

        with output_path.open("w", encoding="utf-8", newline="\n") as out_fh:
            for pline in prefix_lines:
                out_fh.write(pline + "\n")
            if prefix_lines:
                out_fh.write("\n")
            for s, p, o in conn.execute("SELECT s, p, o FROM rels"):
                out_fh.write(f"{s} {p} {o} .\n")

        summary = {
            "input": str(input_path),
            "output": str(output_path),
            "total_rel_triples": total,
            "unique_rel_triples": kept,
            "sqlite_db": str(db_path),
        }
        return summary
    finally:
        conn.close()
        if created_temp_db and not keep_db:
            try:
                db_path.unlink(missing_ok=True)
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Deduplicate relationship triples in TTL files")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="One or more TTL files or glob patterns",
    )
    parser.add_argument(
        "--out-dir",
        default="artifacts",
        help="Output directory for deduplicated TTLs",
    )
    parser.add_argument(
        "--db-path",
        help="Optional SQLite db path (default: temporary file per input)",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep the SQLite db on disk when using a temporary path",
    )
    args = parser.parse_args()

    input_paths = iter_input_paths(args.inputs)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for path in input_paths:
        if not path.exists():
            print("MISSING", path)
            continue
        out_path = out_dir / f"{path.stem}-dedup.ttl"
        db_path = Path(args.db_path) if args.db_path else None
        summary = dedup_file(path, out_path, db_path, args.keep_db)
        summaries.append(summary)
        print("OK", path)
        print("  output:", summary["output"])
        print("  total_rel_triples:", summary["total_rel_triples"])
        print("  unique_rel_triples:", summary["unique_rel_triples"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
