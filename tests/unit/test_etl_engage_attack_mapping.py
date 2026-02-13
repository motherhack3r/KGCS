import json

from rdflib import URIRef

from src.etl.etl_engage import ENGAGEtoRDFTransformer, _load_engage_data


def test_engage_attack_mapping_rows_emit_disrupts(tmp_path):
    raw = tmp_path / "engage_raw"
    raw.mkdir()

    (raw / "activities.json").write_text(
        json.dumps(
            [
                {
                    "id": "EAC9001",
                    "name": "Test activity",
                    "description": "Test",
                }
            ]
        ),
        encoding="utf-8",
    )

    (raw / "attack_mapping.json").write_text(
        json.dumps(
            [
                {
                    "eac_id": "EAC9001",
                    "attack_id": "https://attack.mitre.org/techniques/T1566/001/",
                }
            ]
        ),
        encoding="utf-8",
    )

    data = _load_engage_data(str(raw))
    transformer = ENGAGEtoRDFTransformer()
    g = transformer.transform(data)

    subject = URIRef("https://example.org/engagement/ENGAGE-EAC9001")
    obj = URIRef("https://example.org/technique/T1566.001")

    assert (subject, transformer.SEC.disrupts, obj) in g
