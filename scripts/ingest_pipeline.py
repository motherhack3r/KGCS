#!/usr/bin/env python
"""DEPRECATED: Use scripts/ingest_cli.py instead.

This module is kept for backward compatibility.
All ingestion logic has been moved to src/kgcs/ingest/pipeline.py
"""

import sys
import os
import warnings

warnings.warn(
    "scripts/ingest_pipeline.py is deprecated. Use scripts/ingest_cli.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Re-export for backward compatibility
from kgcs.ingest.pipeline import main

if __name__ == "__main__":
    main()
