#!/usr/bin/env python3
"""CLI wrapper for ingest pipeline.

Entry point: python -m kgcs.cli.ingest or python scripts/ingest_cli.py
"""

import sys
import os
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from kgcs.ingest.pipeline import ingest_file, ingest_directory

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Ingest RDF data with pre-ingest SHACL validation'
    )
    parser.add_argument('--file', help='Single file to ingest')
    parser.add_argument('--dir', help='Directory to ingest')
    parser.add_argument('--shapes', default='docs/ontology/shacl', help='SHACL shapes directory')
    parser.add_argument('--output', default='artifacts', help='Output directory for reports')
    
    args = parser.parse_args()
    
    if args.file:
        print(f'Ingesting {args.file}...')
        ingest_file(args.file, None, args.shapes, args.output)
    elif args.dir:
        print(f'Ingesting directory {args.dir}...')
        ingest_directory(args.dir, None, args.shapes, args.output)
    else:
        print('Error: --file or --dir required')
        sys.exit(1)
