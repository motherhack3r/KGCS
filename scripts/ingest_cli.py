#!/usr/bin/env python
"""CLI wrapper for KGCS Ingestion Pipeline.

This script provides backward compatibility and CLI entry point for ingesting RDF data
with pre-ingest SHACL validation. It delegates to kgcs.ingest.pipeline module.

Usage:
  python scripts/ingest_cli.py --file data/shacl-samples/t1_good.ttl
  python scripts/ingest_cli.py --dir data/shacl-samples
"""

import sys
import os

# Ensure src is on path so we can import kgcs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kgcs.ingest.pipeline import main

if __name__ == '__main__':
    main()
