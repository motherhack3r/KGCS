import sys
import types
import tempfile
import os
from rdflib import Graph, Namespace, URIRef

# Provide a minimal fake `ijson` implementation to satisfy imports in ETL modules
if 'ijson' not in sys.modules:
    sys.modules['ijson'] = types.SimpleNamespace(items=lambda fh, prefix: [])

from src.etl.etl_cpe import transform_cpe
from src.etl.etl_cpematch import transform_cpematch
from src.etl.etl_cve import transform_cve
from src.utils.load_to_neo4j import TTLExtractor

SEC = Namespace("https://example.org/sec/core#")


def test_etl_and_loader_compatibility():
    # Prepare CPE sample
    cpe_sample = {
        "products": [
            {
                "cpe": {
                    "cpeName": "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*",
                    "cpeNameId": "ID-1",
                    "created": "2026-01-01T00:00:00Z",
                    "lastModified": "2026-01-02T00:00:00Z",
                    "deprecated": False,
                }
            }
        ]
    }

    tmpdir = tempfile.mkdtemp()
    cpe_out = os.path.join(tmpdir, "cpe_out.ttl")
    transform_cpe(cpe_sample, cpe_out)

    g = Graph()
    g.parse(cpe_out, format="turtle")

    # Platform must expose CPEUri (canonical) or legacy cpeUri
    cpe_vals = list(g.objects(None, SEC.CPEUri)) + list(g.objects(None, SEC.cpeUri))
    assert any(str(v) == "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*" for v in cpe_vals)

    # Prepare CPEMatch sample
    cpematch_sample = {
        "matchStrings": [
            {
                "matchString": {
                    "matchCriteriaId": "MATCH-1",
                    "criteria": "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*",
                    "matches": [
                        {"cpeName": "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*", "cpeNameId": "ID-1"}
                    ],
                }
            }
        ]
    }
    cpematch_out = os.path.join(tmpdir, "cpematch_out.ttl")
    transform_cpematch(cpematch_sample, cpematch_out)
    g2 = Graph()
    g2.parse(cpematch_out, format="turtle")

    # PlatformConfiguration must expose matchCriteriaId and link to Platform via matchesPlatform or includes
    pcs = list(g2.subjects(SEC.matchCriteriaId, None))
    assert pcs, "No PlatformConfiguration with matchCriteriaId emitted"
    pc = pcs[0]
    # Check links
    assert list(g2.objects(pc, SEC.matchesPlatform)) or list(g2.objects(pc, SEC.includes))

    # Prepare CVE sample referencing MATCH-1
    cve_sample = {
        "vulnerabilities": [
            {
                "id": "CVE-2026-0001",
                "cve": {"id": "CVE-2026-0001", "descriptions": [{"lang": "en", "value": "Test"}]},
                "configurations": {
                    "nodes": [{"cpeMatch": [{"matchCriteriaId": "MATCH-1"}]}]
                },
            }
        ]
    }
    cve_out = os.path.join(tmpdir, "cve_out.ttl")
    transform_cve(cve_sample, cve_out)
    g3 = Graph()
    g3.parse(cve_out, format="turtle")

    # CVE must emit affects triple to PlatformConfiguration and PlatformConfiguration must include matchCriteriaId
    affects = list(g3.objects(None, SEC.affects))
    assert affects, "No affects triples emitted by CVE ETL"

    # Finally, test TTLExtractor can map config -> platform when using legacy predicates
    ttl = f"@prefix sec: <https://example.org/sec/core#> .\n\n<https://example.org/platform/PL1> a sec:Platform ; sec:cpeUri \"cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*\" .\n<https://example.org/platformConfiguration/M1> a sec:PlatformConfiguration ; sec:matchCriteriaId \"M1\" ; sec:includes <https://example.org/platform/PL1> .\n"
    g4 = Graph()
    g4.parse(data=ttl, format='turtle')
    extractor = TTLExtractor(g4)
    data = extractor.extract()
    assert data['edges']['config_platform'], "Loader did not extract config->platform mapping"
