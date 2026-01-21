#!/usr/bin/env python3
"""CLI wrapper for validate_shacl validation.

Entry point: python -m kgcs.cli.validate or python scripts/validate_shacl_cli.py
"""

import sys
import os

# Import from src modules
from src.core.validation import parse_args, run_validator, TEMPLATE_SHAPE_MAP

if __name__ == '__main__':
    args = parse_args()
    
    if args.list_templates:
        print('\n=== Available SHACL Templates ===')
        for tpl in sorted(TEMPLATE_SHAPE_MAP.keys()):
            print(f'  {tpl}')
        print()
        sys.exit(0)
    
    if not args.data:
        print('Error: --data <file> is required')
        sys.exit(1)
    
    conforms, report_path, results = run_validator(
        args.data, args.shapes or 'docs/ontology/shacl', args.template, args.owl, args.output
    )
    
    print(results)
    sys.exit(0 if conforms else 1)
