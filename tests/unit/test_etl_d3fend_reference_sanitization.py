from rdflib import Graph
from src.etl.etl_d3fend import D3FENDtoRDFTransformer
from rdflib.namespace import RDFS

def test_d3fend_reference_sanitization():
    transformer = D3FENDtoRDFTransformer()
    # Construct a bad reference with long free text
    entry = {
        "DefensiveTechniques": [
            {
                "ID": "D3-TEST-1",
                "Name": "Test",
                "References": [
                    {"URL": "https://example.org/path/to/resource", "Title": "Some long title with [brackets] and punctuation."}
                ]
            }
        ]
    }
    g = transformer.transform(entry)
    refs = list(g.objects(predicate=transformer.SEC.references))
    assert refs, "No reference nodes created"
    ref = refs[0]
    labels = list(g.objects(ref, RDFS.label))
    assert labels and "long title" in str(labels[0])
    assert len(str(ref)) < 200
