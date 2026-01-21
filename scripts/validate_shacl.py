#!/usr/bin/env python
"""DEPRECATED: Use scripts/validate_shacl_cli.py instead.

This module is kept for backward compatibility.
All validation logic has been moved to src/kgcs/core/validation.py
"""

import sys
import os
import warnings

warnings.warn(
    "scripts/validate_shacl.py is deprecated. Use scripts/validate_shacl_cli.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Re-export for backward compatibility
from kgcs.core.validation import main, run_validator, load_graph, extract_shape_subset, parse_args, TEMPLATE_SHAPE_MAP, validate_data



if __name__ == '__main__':
    main()


