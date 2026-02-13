import json

from rdflib import URIRef

from src.etl.etl_d3fend import D3FENDtoRDFTransformer


def test_d3fend_sparql_uri_attack_id_is_normalized(tmp_path):
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
                    "off_tech_id": {"type": "uri", "value": "https://attack.mitre.org/techniques/T1078/004/"},
                }
            ]
        }
    }

    g = transformer.transform(data, source_path=str(mappings_path))

    subject = URIRef("https://example.org/deftech/D3-AM")
    obj = URIRef("https://example.org/technique/T1078.004")

    assert (subject, transformer.SEC.mitigates, obj) in g
