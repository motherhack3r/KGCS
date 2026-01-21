#!/usr/bin/env python3
"""CLI wrapper for consolidate_shacl_reports.

Entry point: python -m kgcs.cli.consolidate or python scripts/consolidate_cli.py
"""

import sys
import os

# Import from src modules
from src.utils.consolidate_shacl_reports import consolidate_reports

if __name__ == '__main__':
    consolidate_reports()
