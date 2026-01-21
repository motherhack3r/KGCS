"""KGCS: Knowledge Graph for Cybersecurity Standards.

A frozen core ontology mapping 1:1 to MITRE/NVD standards (CPE, CVE, CVSS, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE)
with extensible modules for temporal, contextual, and inference-driven use cases.
"""

__version__ = "0.3.0"
__author__ = "KGCS Team"

from kgcs.core.validation import validate_data, run_validator
from kgcs.ingest.pipeline import ingest_file, ingest_directory

__all__ = [
    'validate_data',
    'run_validator',
    'ingest_file',
    'ingest_directory',
]
