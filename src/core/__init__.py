"""KGCS Core: Frozen ontology module.

Provides SHACL validation and schema enforcement for MITRE/NVD standards-aligned RDF data.
Core remains immutable; extensions reference and extend it.
"""

from src.core.validation import run_validator

__all__ = ['run_validator']
