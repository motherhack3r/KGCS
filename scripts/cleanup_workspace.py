#!/usr/bin/env python3
"""
Workspace Cleanup Utility for KGCS

Removes temporary files, cached data, test reports, and other artifacts
accumulated during development and testing.

Usage:
  python scripts/cleanup_workspace.py              # List items to clean
  python scripts/cleanup_workspace.py --dry-run    # Show what would be deleted
  python scripts/cleanup_workspace.py --execute    # Actually delete files
  python scripts/cleanup_workspace.py --sources    # Include downloaded source data
  python scripts/cleanup_workspace.py --data       # Include transformed sample data

Categories cleaned:
  • tmp/                 - Temporary working files
  • artifacts/           - SHACL validation reports
  • logs/                - Application logs
  • __pycache__/         - Python bytecode cache
  • .pytest_cache/       - Pytest cache
  • .rdflib_default/     - RDFlib default store
  • *.pyc, *.pyo         - Python compiled files
  • .coverage            - Coverage reports
  • htmlcov/             - HTML coverage reports

Optional (with --sources):
  • data/*/raw/          - Downloaded source data (CPE, CVE, CWE, etc.)

Optional (with --data):
  • data/*/samples/      - Transformed sample data (CPE, CVE, CWE, etc.)
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple

# Define cleanup patterns: (path_pattern, description, always_clean)
CLEANUP_PATTERNS = [
    ("tmp/", "Temporary working files", True),
    ("artifacts/", "SHACL validation reports", True),
    ("logs/", "Application logs", True),
    (".pytest_cache/", "Pytest cache", True),
    (".rdflib_default/", "RDFlib default store", True),
    ("htmlcov/", "HTML coverage reports", True),
]

# Patterns that need glob matching
GLOB_PATTERNS = [
    ("**/__pycache__", "Python bytecode cache", True),
    ("**/*.pyc", "Python compiled files (.pyc)", True),
    ("**/*.pyo", "Python compiled files (.pyo)", True),
    ("**/.coverage*", "Coverage files", True),
]

# Optional patterns (only with --sources)
OPTIONAL_PATTERNS_SOURCES = [
    ("data/attack/raw/", "Downloaded ATT&CK source data", False),
    ("data/capec/raw/", "Downloaded CAPEC source data", False),
    ("data/car/raw/", "Downloaded CAR source data", False),
    ("data/cpe/raw/", "Downloaded CPE source data", False),
    ("data/cve/raw/", "Downloaded CVE source data", False),
    ("data/cwe/raw/", "Downloaded CWE source data", False),
    ("data/d3fend/raw/", "Downloaded D3FEND source data", False),
    ("data/engage/raw/", "Downloaded ENGAGE source data", False),
    ("data/shield/raw/", "Downloaded SHIELD source data", False),
]

# Optional patterns (only with --data)
OPTIONAL_PATTERNS_DATA = [
    ("data/attack/samples/", "Transformed ATT&CK sample data", False),
    ("data/capec/samples/", "Transformed CAPEC sample data", False),
    ("data/car/samples/", "Transformed CAR sample data", False),
    ("data/cpe/samples/", "Transformed CPE sample data", False),
    ("data/cve/samples/", "Transformed CVE sample data", False),
    ("data/cwe/samples/", "Transformed CWE sample data", False),
    ("data/d3fend/samples/", "Transformed D3FEND sample data", False),
    ("data/engage/samples/", "Transformed ENGAGE sample data", False),
    ("data/shield/samples/", "Transformed SHIELD sample data", False),
]


def find_cleanup_items(include_sources: bool = False, include_data: bool = False) -> Tuple[List[Path], dict]:
    """Find all items that should be cleaned.
    
    Args:
        include_sources: Include downloaded source data (data/*/raw/)
        include_data: Include transformed data samples (data/*/samples/)
    """
    items_to_remove = []
    stats = {
        "dirs": 0,
        "files": 0,
        "size_mb": 0.0,
    }

    project_root = Path.cwd()

    # Build patterns list
    all_patterns = CLEANUP_PATTERNS + GLOB_PATTERNS
    if include_sources:
        all_patterns.extend(OPTIONAL_PATTERNS_SOURCES)
    if include_data:
        all_patterns.extend(OPTIONAL_PATTERNS_DATA)

    # Check directory patterns
    for pattern, desc, _ in all_patterns:
        path = project_root / pattern.rstrip("/")
        if path.exists():
            items_to_remove.append((path, desc))
            if path.is_dir():
                stats["dirs"] += 1
                # Calculate directory size
                for item in path.rglob("*"):
                    if item.is_file():
                        stats["files"] += 1
                        stats["size_mb"] += item.stat().st_size / (1024 * 1024)
            else:
                stats["files"] += 1
                stats["size_mb"] += path.stat().st_size / (1024 * 1024)

    # Check glob patterns
    for pattern, desc, _ in GLOB_PATTERNS:
        for path in project_root.glob(pattern):
            if path.exists():
                items_to_remove.append((path, desc))
                if path.is_file():
                    stats["files"] += 1
                    stats["size_mb"] += path.stat().st_size / (1024 * 1024)
                else:
                    stats["dirs"] += 1
                    for item in path.rglob("*"):
                        if item.is_file():
                            stats["files"] += 1
                            stats["size_mb"] += item.stat().st_size / (1024 * 1024)

    return items_to_remove, stats


def list_items(items: List[Tuple[Path, str]], stats: dict) -> None:
    """Display items to be cleaned."""
    print("\n📋 Items to Clean:\n")

    for path, description in sorted(items, key=lambda x: str(x[0])):
        rel_path = path.relative_to(Path.cwd())
        size_info = ""
        if path.is_file():
            size_mb = path.stat().st_size / (1024 * 1024)
            size_info = f" ({size_mb:.2f} MB)"
        print(f"  • {rel_path}{size_info:<30} - {description}")

    print(f"\n📊 Summary:")
    print(f"  Directories: {stats['dirs']}")
    print(f"  Files: {stats['files']}")
    print(f"  Total size: {stats['size_mb']:.2f} MB")


def cleanup_execute(items: List[Tuple[Path, str]]) -> None:
    """Actually delete the items."""
    deleted_count = 0
    failed_count = 0

    for path, description in items:
        try:
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  ✅ Deleted: {path.relative_to(Path.cwd())}/")
            else:
                path.unlink()
                print(f"  ✅ Deleted: {path.relative_to(Path.cwd())}")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Failed: {path.relative_to(Path.cwd())} - {e}")
            failed_count += 1

    print(f"\n✅ Cleaned {deleted_count} items")
    if failed_count > 0:
        print(f"⚠️  Failed to clean {failed_count} items")


def main():
    parser = argparse.ArgumentParser(
        description="Clean temporary files, logs, cache, and test artifacts from KGCS workspace"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete the files (default is to list only)",
    )
    parser.add_argument(
        "--sources",
        action="store_true",
        help="Include downloaded source data (data/*/raw/)",
    )
    parser.add_argument(
        "--data",
        action="store_true",
        help="Include transformed sample data (data/*/samples/)",
    )

    args = parser.parse_args()

    # Find items
    items, stats = find_cleanup_items(include_sources=args.sources, include_data=args.data)

    if not items:
        print("✅ Workspace is clean! No items found to remove.")
        return

    # List items
    list_items(items, stats)

    # Execute or dry-run
    if args.execute:
        print("\n🗑️  Cleaning workspace...\n")
        cleanup_execute(items)
        print("\n✅ Cleanup complete!")
    elif args.dry_run:
        print("\n(Dry-run mode - no files deleted)")
    else:
        print("\n💡 Tip: Use --execute to actually delete, or --dry-run to preview")


if __name__ == "__main__":
    main()
