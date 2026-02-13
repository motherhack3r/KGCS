from src.etl.rdf_to_neo4j import RDFtoNeo4jTransformer


def test_uri_label_inference_deception_and_engagement_aliases():
    transformer = RDFtoNeo4jTransformer("dummy.ttl")

    assert transformer._infer_label_from_uri("https://example.org/deception/SHIELD-DTE0001") == "DeceptionTechnique"
    assert transformer._infer_label_from_uri("https://example.org/engagement/ENGAGE-EAC0001") == "EngagementConcept"
