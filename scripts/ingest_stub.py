#!/usr/bin/env python
"""Simple ingest stub demonstrating pre-ingest SHACL validation gate.

DEPRECATED: Use scripts/ingest_cli.py instead for full pipeline.
This keeps backward compatibility but delegates to the new pipeline.

Usage:
  python scripts/ingest_stub.py data/shacl-samples/good-example.ttl
"""

import sys
import os
import warnings

warnings.warn(
    "scripts/ingest_stub.py is deprecated. Use scripts/ingest_cli.py instead.",
    DeprecationWarning,
    stacklevel=2
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kgcs.ingest import ingest_file


def default_indexer(data_file: str) -> None:
    """Simulate indexing."""
    print(f'Indexing {data_file}... (simulated)')


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/ingest_stub.py <data-file.ttl>')
        sys.exit(2)
    data_file = sys.argv[1]
    ok = ingest_file(data_file, default_indexer)
    if not ok:
        sys.exit(1)
    print('Done.')


if __name__ == '__main__':
    main()
