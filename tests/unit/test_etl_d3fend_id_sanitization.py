from rdflib import Graph
from src.etl.etl_d3fend import D3FENDtoRDFTransformer
from rdflib.namespace import RDFS


def test_d3fend_id_sanitization_and_provenance():
    transformer = D3FENDtoRDFTransformer()
    data = {
        "DefensiveTechniques": [
            {
                "ID": "d3f:PhysicalKeyLock",
                "Name": "Physical Key Lock",
                "Description": "Test"
            },
            {
                "ID": "AML.T0051.000",
                "Name": "Some Action",
            }
        ]
    }
    g = transformer.transform(data)
    # Ensure subjects exist and URIs are normalized (no colon)
    found = False
    for s in g.subjects():
        s_str = str(s)
        if 'deftech' in s_str:
            local = s_str.split('/')[-1]
            assert ':' not in local, f"Normalized ID still contains ':' in {s_str}"
            # now assert we have the D3FEND- prefix for normalized ids
            assert local.upper().startswith('D3FEND-'), f"Normalized ID missing D3FEND- prefix: {local}"
            found = True
    assert found, "No deftech subjects found"
    # Provenance: ensure the original ID is present as d3fendId literal
    vals = list(g.objects(predicate=transformer.SEC.d3fendId))
    assert any('d3f:PhysicalKeyLock' in str(v) for v in vals)
    assert any('AML.T0051.000' in str(v) for v in vals)
