from rdflib import Graph
from src.etl.etl_car import CARtoRDFTransformer
from rdflib.namespace import RDFS

def test_car_reference_sanitization(tmp_path):
    # Construct a synthetic analytic with a Markdown-like reference (problematic in real world)
    analytic = {
        "id": "2020-08-001",
        "name": "Test Analytic",
        "references": [
            "The [LOLBAS project](https://lolbas-project.github.io/) is an amazing resource"
        ]
    }
    transformer = CARtoRDFTransformer()
    g = transformer.transform([analytic])

    # Ensure a reference node exists and that its rdfs:label contains the free-text (not in the URI)
    refs = list(g.objects(predicate=transformer.SEC.reference))
    assert refs, "No reference nodes produced"
    ref = refs[0]
    labels = list(g.objects(ref, RDFS.label))
    assert labels, "Reference node missing text label"
    label_text = str(labels[0])
    assert "LOLBAS" in label_text

    # Ensure ref URI is compact (contains digest, not full text)
    assert str(ref).startswith(str(transformer.EX) + "reference/" )
    assert len(str(ref)) < 200, "Reference URI too long"
