from pathlib import Path

from src.etl.etl_cwe import EX, SEC, CWEtoRDFTransformer, _cwe_xml_to_json


def test_cwe_xml_enrichment_extraction_and_transform(tmp_path):
    xml_content = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Weakness_Catalog xmlns=\"http://cwe.mitre.org/cwe-7\">
  <Weaknesses>
    <Weakness ID=\"1234\" Name=\"Example Weakness\" Abstraction=\"Base\" Status=\"Stable\">
      <Description>Example CWE description.</Description>
      <Modes_Of_Introduction>
        <Introduction>
          <Phase>Implementation</Phase>
        </Introduction>
      </Modes_Of_Introduction>
      <Likelihood_Of_Exploit>Medium</Likelihood_Of_Exploit>
      <Common_Consequences>
        <Consequence Consequence_ID="CC-99">
          <Scope>Confidentiality</Scope>
          <Impact>Read Application Data</Impact>
          <Note>Data can be exposed.</Note>
        </Consequence>
      </Common_Consequences>
      <Detection_Methods>
        <Detection_Method Detection_Method_ID="DM-77">
          <Method>Automated Static Analysis</Method>
          <Description>Static analysis can identify this weakness.</Description>
          <Effectiveness>High</Effectiveness>
        </Detection_Method>
      </Detection_Methods>
      <Potential_Mitigations>
        <Mitigation Mitigation_ID="MIT-42">
          <Phase>Implementation</Phase>
          <Description>Apply strict input validation.</Description>
          <Effectiveness>High</Effectiveness>
        </Mitigation>
      </Potential_Mitigations>
      <Related_Attack_Patterns>
        <Related_Attack_Pattern CAPEC_ID=\"100\"/>
      </Related_Attack_Patterns>
      <Observed_Examples>
        <Observed_Example>
          <Reference>CVE-2024-1111</Reference>
          <Link>https://www.cve.org/CVERecord?id=CVE-2024-1111</Link>
        </Observed_Example>
      </Observed_Examples>
      <References>
        <Reference External_Reference_ID=\"REF-1\"/>
      </References>
    </Weakness>
  </Weaknesses>
  <External_References>
    <External_Reference Reference_ID=\"REF-1\">
      <Title>Example Reference</Title>
      <URL>https://example.org/reference</URL>
    </External_Reference>
  </External_References>
</Weakness_Catalog>
"""

    xml_file = tmp_path / "sample-cwe.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    cwe_json = _cwe_xml_to_json(str(xml_file))
    weakness = cwe_json["Weakness"][0]

    assert weakness["LikelihoodOfExploit"] == "Medium"
    assert weakness["ModesOfIntroduction"][0]["Phase"] == "Implementation"
    assert weakness["DetectionMethods"][0]["Method"] == "Automated Static Analysis"
    assert weakness["PotentialMitigations"][0]["Description"] == "Apply strict input validation."
    assert weakness["PotentialMitigations"][0]["MitigationID"] == "MIT-42"
    assert weakness["DetectionMethods"][0]["DetectionMethodID"] == "DM-77"
    assert weakness["Consequences"][0]["ConsequenceID"] == "CC-99"
    assert weakness["RelatedAttackPatterns"][0]["CAPEC_ID"] == "100"
    assert weakness["RelatedVulnerabilities"][0]["CVE_ID"] == "CVE-2024-1111"
    assert weakness["References"][0]["Title"] == "Example Reference"

    transformer = CWEtoRDFTransformer()
    graph = transformer.transform(cwe_json)

    weakness_node = EX["weakness/CWE-1234"]

    assert (weakness_node, SEC.mapsToCAPEC, EX["capec/CAPEC-100"]) in graph
    assert (weakness_node, SEC.mapsToVulnerability, EX["cve/CVE-2024-1111"]) in graph

    detection_nodes = list(graph.objects(weakness_node, SEC.hasDetectionMethod))
    mitigation_nodes = list(graph.objects(weakness_node, SEC.hasMitigation))
    consequence_nodes = list(graph.objects(weakness_node, SEC.hasConsequence))
    reference_nodes = list(graph.objects(weakness_node, SEC.hasReference))

    assert detection_nodes, "Expected detection method nodes from CWE Detection_Methods"
    assert mitigation_nodes, "Expected mitigation nodes from CWE Potential_Mitigations"
    assert consequence_nodes, "Expected consequence nodes from CWE Common_Consequences"
    assert reference_nodes, "Expected reference nodes from CWE References"

    assert EX["detection/CWE-1234-detection-DM-77"] in detection_nodes
    assert EX["mitigation/CWE-1234-mitigation-MIT-42"] in mitigation_nodes
    assert EX["consequence/CWE-1234-consequence-CC-99"] in consequence_nodes
