from src.etl.etl_capec import CAPECtoRDFTransformer, EX, SEC, _canonicalize_attack_technique_id


def test_canonicalize_attack_technique_id_variants():
    assert _canonicalize_attack_technique_id("1110") == "T1110"
    assert _canonicalize_attack_technique_id("T1148") == "T1148"
    assert _canonicalize_attack_technique_id("1574.010") == "T1574.010"
    assert _canonicalize_attack_technique_id("t1574.10") == "T1574.010"
    assert _canonicalize_attack_technique_id("bad-id") is None


def test_capec_transformer_emits_canonical_attack_uris():
    capec_json = {
        "AttackPatterns": [
            {
                "ID": "13",
                "Name": "Test Pattern",
                "AttackMappings": [
                    {"TechniqueID": "1574.10"},
                    {"TechniqueID": "1110"},
                    {"TechniqueID": "INVALID"},
                ],
            }
        ]
    }

    transformer = CAPECtoRDFTransformer(capec_to_attack={"CAPEC-13": ["T1148", "1499.003"]})
    graph = transformer.transform(capec_json)

    pattern_node = EX["attackPattern/CAPEC-13"]
    implemented = {str(obj) for obj in graph.objects(pattern_node, SEC.implemented_as)}

    assert "https://example.org/subtechnique/T1574.010" in implemented
    assert "https://example.org/technique/T1110" in implemented
    assert "https://example.org/technique/T1148" in implemented
    assert "https://example.org/subtechnique/T1499.003" in implemented
    assert not any(uri.endswith("/INVALID") for uri in implemented)
