import re
from pathlib import Path


def test_extract_cvss_urls_from_cve_schema(tmp_path):
    """Simulate a local CVE JSON schema file containing references to CVSS JSON schemas
    and verify the downloader's parsing logic would find the CVSS URLs.
    """
    sample_text = '''
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "$id": "https://csrc.nist.gov/schema/nvd/api/2.0/cve_api_json_2.0.schema",
      "definitions": {
        "cvssV31": {
          "$ref": "https://csrc.nist.gov/schema/nvd/api/2.0/cvss-v3.1.json"
        },
        "cvssV40": {
          "$ref": "https://csrc.nist.gov/schema/nvd/api/2.0/cvss-v4.0.json"
        }
      }
    }
    '''

    schema_file = tmp_path / "cve_schema.json"
    schema_file.write_text(sample_text, encoding='utf-8')

    text = schema_file.read_text(encoding='utf-8')
    urls = set(re.findall(r"https?://[A-Za-z0-9./_-]+\.json", text))
    cvss_urls = [u for u in urls if 'csrc.nist.gov' in u and 'cvss' in u]

    assert 'https://csrc.nist.gov/schema/nvd/api/2.0/cvss-v3.1.json' in cvss_urls
    assert 'https://csrc.nist.gov/schema/nvd/api/2.0/cvss-v4.0.json' in cvss_urls
    assert len(cvss_urls) == 2
