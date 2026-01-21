#!/usr/bin/env python
"""CLI wrapper for KGCS SHACL validation.

This script provides backward compatibility and CLI entry point for validating TTL data.
It delegates to kgcs.core.validation module.

Usage:
  python scripts/validate_shacl_cli.py --data data/shacl-samples/t1_good.ttl
  python scripts/validate_shacl_cli.py --data data/shacl-samples/t1_bad.ttl --template T1
"""

import sys
import os

# Ensure src is on path so we can import kgcs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kgcs.core.validation import main

if __name__ == '__main__':
    main()
