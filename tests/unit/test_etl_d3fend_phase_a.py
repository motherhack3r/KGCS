from rdflib import RDF, RDFS, URIRef

from src.etl.etl_d3fend import D3FENDtoRDFTransformer


def test_phase_a_typed_references_and_predicates():
    transformer = D3FENDtoRDFTransformer()

    data = {
        "@graph": [
            {
                "@id": "d3f:DefA",
                "@type": ["owl:Class", "d3f:DefensiveTechnique"],
                "d3f:d3fend-id": "D3-A",
                "rdfs:label": "Def A",
                "d3f:analyzes": {"@id": "d3f:DefB"},
                "d3f:kb-reference": {"@id": "d3f:Ref1"},
                "d3f:synonym": "Alias A",
                "rdfs:seeAlso": {"@id": "https://example.org/defa"},
            },
            {
                "@id": "d3f:DefB",
                "@type": ["owl:Class", "d3f:DefensiveTechnique"],
                "d3f:d3fend-id": "D3-B",
                "rdfs:label": "Def B",
            },
            {
                "@id": "d3f:Ref1",
                "@type": "d3f:AcademicPaperReference",
                "d3f:kb-reference-title": "Paper One",
                "d3f:kb-organization": "TestOrg",
                "rdfs:seeAlso": {"@id": "https://example.org/paper1"},
            },
        ]
    }

    g = transformer.transform(data)

    def_a = URIRef("https://example.org/deftech/D3-A")
    def_b = URIRef("https://example.org/deftech/D3-B")
    ref_1 = URIRef("https://example.org/reference/D3FEND-Ref1")

    assert (def_a, transformer.SEC.analyzes, def_b) in g
    assert (def_a, transformer.SEC.references, ref_1) in g

    assert (ref_1, RDF.type, transformer.SEC.Reference) in g
    assert (ref_1, transformer.SEC.referenceType, None) in g
    assert (ref_1, RDFS.label, None) in g
    assert (ref_1, transformer.SEC.url, None) in g

    assert (def_a, transformer.SEC.synonym, None) in g
    assert (def_a, transformer.SEC.sourceIdentifier, None) in g
