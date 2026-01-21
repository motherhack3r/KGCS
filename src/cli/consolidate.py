#!/usr/bin/env python3
"""CLI wrapper for consolidate_shacl_reports.

Entry point: python -m kgcs.cli.consolidate or python scripts/consolidate_cli.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from kgcs.utils.consolidate_shacl_reports import consolidate_reports

if __name__ == '__main__':
    consolidate_reports()
