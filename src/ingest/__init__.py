"""Ingestion pipeline with pre-ingest SHACL validation gates.

Enforces validation before writes, aborts on invalid input, and logs to artifacts/.
"""

import os
from typing import Callable, Optional
from kgcs.core.validation import run_validator, load_graph


def validate_before_ingest(data_file: str, shapes_file: str = 'docs/ontology/shacl/kgcs-shapes.ttl', output: str = 'artifacts') -> bool:
    """Pre-ingest validation gate.
    
    Args:
        data_file: Path to RDF/Turtle file to validate
        shapes_file: Path to SHACL shapes file
        output: Directory for validation reports
        
    Returns:
        True if data conforms (safe to ingest), False otherwise
        
    Raises:
        ValueError: If shapes_file or data_file does not exist
    """
    if not os.path.exists(shapes_file):
        raise ValueError(f"SHACL shapes file not found: {shapes_file}")
    if not os.path.exists(data_file):
        raise ValueError(f"Data file not found: {data_file}")
    
    shapes = load_graph(shapes_file)
    conforms, report_path, _ = run_validator(data_file, shapes, output)
    
    if not conforms:
        print(f"[VALIDATION GATE] REJECTED: {data_file}")
        print(f"[VALIDATION GATE] Report written to {report_path}")
        return False
    
    print(f"[VALIDATION GATE] PASSED: {data_file}")
    return True


def ingest_file(
    data_file: str,
    indexer: Callable[[str], None],
    shapes_file: str = 'docs/ontology/shacl/kgcs-shapes.ttl',
    output: str = 'artifacts'
) -> bool:
    """Ingest a single RDF file with pre-ingest validation.
    
    Args:
        data_file: Path to RDF/Turtle file to ingest
        indexer: Callback function to handle validated data (e.g., load to graph DB)
        shapes_file: Path to SHACL shapes file
        output: Directory for validation reports
        
    Returns:
        True if ingestion succeeded, False if validation failed
    """
    if not validate_before_ingest(data_file, shapes_file, output):
        return False
    
    try:
        indexer(data_file)
        print(f"[INGEST] SUCCESS: {data_file}")
        return True
    except Exception as e:
        print(f"[INGEST] ERROR: {data_file} - {e}")
        return False


def ingest_directory(
    data_dir: str,
    indexer: Callable[[str], None],
    shapes_file: str = 'docs/ontology/shacl/kgcs-shapes.ttl',
    output: str = 'artifacts',
    pattern: str = '*.ttl'
) -> tuple[int, int]:
    """Ingest all RDF files in a directory with pre-ingest validation for each.
    
    Args:
        data_dir: Directory containing RDF/Turtle files
        indexer: Callback function to handle validated data
        shapes_file: Path to SHACL shapes file
        output: Directory for validation reports
        pattern: File pattern to match (default: *.ttl)
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    import glob
    
    if not os.path.isdir(data_dir):
        raise ValueError(f"Data directory not found: {data_dir}")
    
    pattern_path = os.path.join(data_dir, '**', pattern)
    files = glob.glob(pattern_path, recursive=True)
    
    success_count = 0
    fail_count = 0
    
    for file in sorted(files):
        if ingest_file(file, indexer, shapes_file, output):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count
