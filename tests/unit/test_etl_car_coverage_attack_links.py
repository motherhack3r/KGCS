from rdflib import URIRef

from src.etl.etl_car import CARtoRDFTransformer


def test_car_extracts_coverage_technique_and_subtechnique():
    analytic = {
        "id": "2026-01-001",
        "name": "Coverage test",
        "coverage": [
            {
                "technique": "T1553",
                "subtechniques": ["T1553.004"],
            }
        ],
    }

    transformer = CARtoRDFTransformer()
    g = transformer.transform([analytic])

    subject = URIRef("https://example.org/analytic/CAR-2026-01-001")
    technique = URIRef("https://example.org/technique/T1553")
    subtechnique = URIRef("https://example.org/technique/T1553.004")

    assert (subject, transformer.SEC.detects, technique) in g
    assert (subject, transformer.SEC.detects, subtechnique) in g
