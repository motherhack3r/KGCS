# Ingestion pipeline stub
# This script demonstrates how to integrate SHACL validation into a data ingestion workflow.
# It walks a directory of RDF/Turtle files, validates each against the SHACL shapes,
# and if validation passes, simulates indexing the data.
#
# Usage:
#   python scripts/ingest_pipeline.py --data-dir data/shacl-samples
#
# The script will:
#   1. Load each .ttl file in the data directory.
#   2. Run the SHACL validator (scripts/validate_shacl.py).
#   3. If validation succeeds, call `index_data(file)` which currently just prints a message.
#   4. If validation fails, abort ingestion for that file.
#
# In a real system, `index_data` would push the data into a graph database or other storage.

import argparse
import subprocess
import sys
import os

# Try to import the validator helper directly for programmatic validation.
try:
    from scripts.validate_shacl import run_validator, load_graph
except Exception:
    # Fallback: ensure scripts directory is on sys.path and try again
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from validate_shacl import run_validator, load_graph
    except Exception:
        # If import still fails, we'll fallback to subprocess invocation in run_validator_subprocess
        run_validator = None
        load_graph = None


def run_validator_subprocess(data_file: str) -> bool:
    """Run the SHACL validator as a subprocess (fallback).
    Returns True if validation passes, False otherwise.
    """
    result = subprocess.run(
        [sys.executable, "scripts/validate_shacl.py", "--data", data_file],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Validation failed for {data_file}")
        return False
    return True


def index_data(data_file: str) -> None:
    """Placeholder for indexing logic.
    In production, this would load the RDF into a graph database.
    """
    print(f"Indexing {data_file}... (simulated)")


def main():
    parser = argparse.ArgumentParser(description="KGCS ingestion pipeline stub")
    parser.add_argument("--data-dir", default="data/shacl-samples", help="Directory containing RDF/Turtle files to ingest")
    args = parser.parse_args()

    for root, _, files in os.walk(args.data_dir):
        for f in files:
            if not f.lower().endswith(".ttl"):
                continue
            path = os.path.join(root, f)
            print(f"\nProcessing {path}")
            # Prefer programmatic validator when available
            if run_validator is not None and load_graph is not None:
                shapes_graph = load_graph('docs/ontology/shacl/kgcs-shapes.ttl')
                conforms, report_path, results_text = run_validator(path, shapes_graph, output='artifacts')
                print(results_text)
                if conforms:
                    index_data(path)
                else:
                    print(f"Skipping {path} due to validation errors (see {report_path})")
            else:
                # Fallback to subprocess invocation
                if run_validator_subprocess(path):
                    index_data(path)
                else:
                    print(f"Skipping {path} due to validation errors")

if __name__ == "__main__":
    main()
