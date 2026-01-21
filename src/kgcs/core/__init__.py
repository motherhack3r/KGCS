"""KGCS Core: Frozen ontology module.

Provides SHACL validation and schema enforcement for MITRE/NVD standards-aligned RDF data.
Core remains immutable; extensions reference and extend it.
"""

from kgcs.core.validation import validate_data, run_validator, load_graph

__all__ = ['validate_data', 'run_validator', 'load_graph']
