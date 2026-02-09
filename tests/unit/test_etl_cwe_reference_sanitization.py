from rdflib import Graph
from src.etl.etl_cwe import CWEtoRDFTransformer
from rdflib.namespace._RDFS import RDFS

def test_cwe_reference_sanitization():
    transformer = CWEtoRDFTransformer()
    weakness = {
        "ID": "123",
        "Name": "Some weakness",
        "References": [
            {"URL": "https://example.org/very/long/url/with/path?query=1", "Title": "Reference Title"}
        ]
    }
    # The transformer expects a 'Weakness' key wrapper
    g = transformer.transform({"Weakness": [weakness]})
    refs = list(g.objects(predicate=transformer.SEC.hasReference))
    assert refs, "No reference nodes created"
    ref = refs[0]
    labels = list(g.objects(ref, RDFS.label))
    assert labels and "Reference Title" in str(labels[0])
    assert len(str(ref)) < 200
