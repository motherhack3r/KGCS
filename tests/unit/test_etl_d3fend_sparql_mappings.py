import json

from rdflib import URIRef

from src.etl.etl_d3fend import D3FENDtoRDFTransformer


def test_sparql_mappings_resolve_alias_to_canonical_deftech_id(tmp_path):
    d3fend_path = tmp_path / "d3fend.json"
    d3fend_path.write_text(
        json.dumps(
            {
                "@graph": [
                    {
                        "@id": "d3f:AccessModeling",
                        "d3f:d3fend-id": "D3-AM",
                        "rdfs:label": "Access Modeling",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    mappings_path = tmp_path / "d3fend-full-mappings.json"
    mappings_path.write_text("{}", encoding="utf-8")

    transformer = D3FENDtoRDFTransformer()
    data = {
        "results": {
            "bindings": [
                {
                    "def_tech": {"type": "uri", "value": "https://d3fend.mitre.org/ontologies/d3fend.owl#AccessModeling"},
                    "def_tech_label": {"type": "literal", "value": "Access Modeling"},
                    "off_tech_id": {"type": "literal", "value": "T1078"},
                }
            ]
        }
    }

    g = transformer.transform(data, source_path=str(mappings_path))

    expected_subject = URIRef("https://example.org/deftech/D3-AM")
    expected_object = URIRef("https://example.org/technique/T1078")

    assert (expected_subject, transformer.SEC.mitigates, expected_object) in g

    legacy_subject = URIRef("https://example.org/deftech/D3FEND-AccessModeling")
    assert (legacy_subject, transformer.SEC.mitigates, expected_object) not in g
