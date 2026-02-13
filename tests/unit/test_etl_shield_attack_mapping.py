import json

from rdflib import URIRef

from src.etl.etl_shield import SHIELDtoRDFTransformer, _load_shield_data


def test_shield_directory_attack_techniques_emit_counters(tmp_path):
    raw = tmp_path / "shield_raw"
    raw.mkdir()

    (raw / "technique_details.json").write_text(
        json.dumps(
            {
                "DTE9999": {
                    "name": "Test deception",
                    "description": "Test description",
                    "attack_techniques": [{"id": "T1059.001"}],
                }
            }
        ),
        encoding="utf-8",
    )

    data = _load_shield_data(str(raw))
    transformer = SHIELDtoRDFTransformer()
    g = transformer.transform(data)

    subject = URIRef("https://example.org/deception/SHIELD-DTE9999")
    obj = URIRef("https://example.org/technique/T1059.001")

    assert (subject, transformer.SEC.counters, obj) in g
