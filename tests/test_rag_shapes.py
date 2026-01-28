#!/usr/bin/env python3
"""RAG SHACL shape tests (positive/negative)."""

from pathlib import Path

from src.core.validation import load_graph, run_validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAG_SHAPES = PROJECT_ROOT / "docs" / "ontology" / "shacl" / "rag-shapes.ttl"

RAG_GOOD_TTL = """@prefix sec: <https://example.org/sec/core#> .
@prefix ex: <https://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:VULN-1 a sec:Vulnerability ;
  sec:caused_by ex:CWE-79 ;
  sec:scored_by ex:CVSS-1 .

ex:CVSS-1 a sec:Score ;
  sec:cvssVersion "3.1" .

ex:CWE-79 a sec:Weakness ;
  sec:exploited_by ex:CAPEC-1 .

ex:CAPEC-1 a sec:AttackPattern ;
  sec:implemented_as ex:T1059 .

ex:T1059 a sec:Technique ;
  sec:belongs_to ex:TA0002 ;
  sec:detected_by ex:CAR-1 ;
  sec:mitigated_by ex:D3-1 ;
  sec:countered_by ex:SHIELD-1 .

ex:TA0002 a sec:Tactic .
ex:CAR-1 a sec:DetectionAnalytic .
ex:D3-1 a sec:DefensiveTechnique .
ex:SHIELD-1 a sec:DeceptionTechnique .

ex:REF-1 a sec:Reference ;
  sec:referenceUrl "https://example.org/ref/1" .
"""

RAG_BAD_TTL = """@prefix sec: <https://example.org/sec/core#> .
@prefix ex: <https://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:VULN-2 a sec:Vulnerability .
ex:REF-2 a sec:Reference .
"""


def _write_tmp(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_rag_shapes_good(tmp_path: Path):
    shapes = load_graph(str(RAG_SHAPES))
    data_path = _write_tmp(tmp_path, "rag-good.ttl", RAG_GOOD_TTL)
    conforms, _, _ = run_validator(str(data_path), shapes, output=str(tmp_path))
    assert conforms is True


def test_rag_shapes_bad(tmp_path: Path):
    shapes = load_graph(str(RAG_SHAPES))
    data_path = _write_tmp(tmp_path, "rag-bad.ttl", RAG_BAD_TTL)
    conforms, _, _ = run_validator(str(data_path), shapes, output=str(tmp_path))
    assert conforms is False
