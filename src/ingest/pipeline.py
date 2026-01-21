"""Ingestion pipeline orchestrator with pre-ingest validation gates.

Provides both programmatic and CLI interfaces for validating and ingesting RDF data.
"""

import argparse
import os
from kgcs.ingest import ingest_file, ingest_directory


def default_indexer(data_file: str) -> None:
    """Default indexer: simulates data ingestion (placeholder)."""
    print(f"  → Indexing {data_file} (simulated)")


def main():
    parser = argparse.ArgumentParser(
        description="KGCS Ingestion Pipeline with Pre-Ingest SHACL Validation",
        epilog="Examples:\n"
               "  python -m kgcs.ingest.pipeline --file data/shacl-samples/t1_good.ttl\n"
               "  python -m kgcs.ingest.pipeline --dir data/shacl-samples --shapes docs/ontology/shacl/kgcs-shapes.ttl",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--file', '-f', help='Single RDF/Turtle file to ingest')
    parser.add_argument('--dir', '-d', help='Directory of RDF/Turtle files to ingest')
    parser.add_argument('--shapes', '-s', default='docs/ontology/shacl/kgcs-shapes.ttl', help='SHACL shapes file')
    parser.add_argument('--output', '-o', default='artifacts', help='Output directory for validation reports')
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.error("Specify either --file or --dir")
    
    if args.file:
        # Single file ingestion
        print(f"Ingesting file: {args.file}")
        success = ingest_file(args.file, default_indexer, args.shapes, args.output)
        exit(0 if success else 1)
    elif args.dir:
        # Directory ingestion
        print(f"Ingesting directory: {args.dir}")
        success_count, fail_count = ingest_directory(args.dir, default_indexer, args.shapes, args.output)
        print(f"\nResults: {success_count} passed, {fail_count} failed")
        exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
