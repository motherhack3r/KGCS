"""Configuration for ETL pipeline"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class APIEndpoints:
    """API endpoints for cybersecurity standards"""
    
    # MITRE ATT&CK - multiple domains (Enterprise, ICS, Mobile, Pre-Attack)
    MITRE_ATTACK = [
        "https://raw.githubusercontent.com/mitre/cti/refs/heads/master/enterprise-attack/enterprise-attack.json",
        "https://raw.githubusercontent.com/mitre/cti/refs/heads/master/ics-attack/ics-attack.json",
        "https://raw.githubusercontent.com/mitre/cti/refs/heads/master/mobile-attack/mobile-attack.json",
        "https://raw.githubusercontent.com/mitre/cti/refs/heads/master/pre-attack/pre-attack.json"
    ]
    
    # MITRE CAPEC - single file
    MITRE_CAPEC = "https://capec.mitre.org/data/xml/capec_latest.xml"
    # MITRE CTI STIX CAPEC JSON (MITRE/CTI repository)
    MITRE_CTISTIX_CAPEC = "https://raw.githubusercontent.com/mitre/cti/refs/heads/master/capec/2.1/stix-capec.json"
    # MITRE CAPEC XSD schema
    MITRE_CAPEC_XSD = "https://capec.mitre.org/data/xsd/ap_schema_latest.xsd"
    
    # MITRE CAR - GitHub API endpoint for analytics directory
    MITRE_CAR_API = "https://api.github.com/repos/mitre-attack/car/contents/analytics"
    MITRE_CAR_RAW = "https://raw.githubusercontent.com/mitre-attack/car/refs/heads/master/analytics/"
    # Additional CAR directories
    MITRE_CAR_API_DATAMODEL = "https://api.github.com/repos/mitre-attack/car/contents/data_model"
    MITRE_CAR_RAW_DATAMODEL = "https://raw.githubusercontent.com/mitre-attack/car/refs/heads/master/data_model/"
    MITRE_CAR_API_SENSORS = "https://api.github.com/repos/mitre-attack/car/contents/sensors"
    MITRE_CAR_RAW_SENSORS = "https://raw.githubusercontent.com/mitre-attack/car/refs/heads/master/sensors/"
    # MITRE ENGAGE - GitHub API endpoint for Data/json directory and raw file base
    MITRE_ENGAGE_API = "https://api.github.com/repos/mitre/engage/contents/Data/json"
    MITRE_ENGAGE_RAW = "https://raw.githubusercontent.com/mitre/engage/refs/heads/main/Data/json/"
    
    # MITRE CWE - single zip file
    MITRE_CWE = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
    # MITRE CWE XSD schema
    MITRE_CWE_XSD = "https://cwe.mitre.org/data/xsd/cwe_schema_latest.xsd"
    
    # MITRE SHIELD - multiple JSON files
    MITRE_SHIELD = [
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/attack_groups.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/tactics.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/techniques.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/procedures.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/use_cases.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/opportunities.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/tactic_details.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/technique_details.json",
        "https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/attack_mapping.json"
    ]
    
    # NIST CPE - single zip file
    NIST_CPE = "https://nvd.nist.gov/feeds/json/cpe/2.0/nvdcpe-2.0.zip"
    # NIST CPE JSON Schema
    NIST_CPE_SCHEMA = "https://csrc.nist.gov/schema/nvd/api/2.0/cpe_api_json_2.0.schema"
    
    # NIST CPE Match - single zip file
    NIST_CPEMATCH = "https://nvd.nist.gov/feeds/json/cpematch/2.0/nvdcpematch-2.0.zip"
    # NIST CPEmatch JSON Schema
    NIST_CPEMATCH_SCHEMA = "https://csrc.nist.gov/schema/nvd/api/2.0/cpematch_api_json_2.0.schema"
    
    # NIST CVE - base URL, files are generated per year
    NIST_CVE_BASE = "https://nvd.nist.gov/feeds/json/cve/2.0/"
    # NIST CVE JSON Schema
    NIST_CVE_SCHEMA = "https://csrc.nist.gov/schema/nvd/api/2.0/cve_api_json_2.0.schema"
    # MITRE D3FEND - ontology base URL and default filenames
    MITRE_D3FEND_BASE = "https://d3fend.mitre.org/ontologies/d3fend/1.3.0/"
    MITRE_D3FEND_FILES = [
        "d3fend-full-mappings.json",
        "d3fend.json",
        "d3fend.owl",
        "d3fend.ttl",
    ]
    
    @staticmethod
    def get_cve_urls(start_year: int = 2002, end_year: Optional[int] = None) -> List[str]:
        """Generate CVE download URLs for each year.
        
        Args:
            start_year: Starting year (default 2002)
            end_year: Ending year (default current year)
            
        Returns:
            List of CVE download URLs
        """
        if end_year is None:
            end_year = datetime.now().year
        
        urls = []
        for year in range(start_year, end_year + 1):
            urls.append(f"{APIEndpoints.NIST_CVE_BASE}nvdcve-2.0-{year}.json.zip")
        
        return urls

@dataclass
class ETLConfig:
    """ETL configuration"""
    
    output_dir: str = "./data"
    log_level: str = "INFO"
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 1000
