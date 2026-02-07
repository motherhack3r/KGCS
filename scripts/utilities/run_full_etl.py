#!/usr/bin/env python3
"""Run full ETL pipeline by streaming all raw data coherently.

This script processes all raw NVD JSON files without sampling limits,
deriving downstream relationships across the causal chain:

    CPEMatch → CPE → CVE → CWE → CAPEC
    ATT&CK techniques → {D3FEND, CAR, SHIELD, ENGAGE}

Outputs TTL files to tmp/ matching the pipeline stages.

Usage:
    python scripts/utilities/run_full_etl.py [--cve-first|--attack-first]
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add project root to Python path to enable src imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import ijson
import yaml


def _pick_files(path: str, pattern: str) -> List[str]:
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        matches = sorted(str(p) for p in Path(path).rglob(pattern))
        return matches
    return []


def _collect_all_items(paths: List[str], prefix: str) -> List[dict]:
    """Collect all items without sampling."""
    items: List[dict] = []
    for path in paths:
        print(f"Loading {path}...")
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, prefix):
                items.append(item)
        print(f"Loaded {len(items)} items so far from {path}")
    return items


def _write_json(out_path: str, payload: dict) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)


def _write_yaml(out_path: str, payload: Any) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=True)


def _normalize_cpematch_item(item: dict) -> dict:
    if not isinstance(item, dict):
        return {}
    return item.get("matchString") or item


def _collect_related_ids(cpematch_items: List[dict]) -> Tuple[Set[str], Set[str], Set[str]]:
    match_ids: Set[str] = set()
    cpe_ids: Set[str] = set()
    criteria_values: Set[str] = set()
    for item in cpematch_items:
        ms = _normalize_cpematch_item(item)
        match_id = ms.get("matchCriteriaId")
        if match_id:
            match_ids.add(match_id)
        criteria = ms.get("criteria") or ms.get("cpe23Uri")
        if isinstance(criteria, str) and criteria:
            criteria_values.add(criteria)
        for match in ms.get("matches", []) or []:
            cpe_id = match.get("cpeNameId")
            if cpe_id:
                cpe_ids.add(cpe_id)
    return match_ids, cpe_ids, criteria_values


def _collect_cpes(paths: List[str], cpe_ids: Set[str]) -> List[dict]:
    if not cpe_ids:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, "products.item"):
                cpe = item.get("cpe") if isinstance(item, dict) else None
                if not isinstance(cpe, dict):
                    continue
                if cpe.get("cpeNameId") in cpe_ids:
                    items.append(item)
    return items


def _collect_cves(paths: List[str], match_ids: Set[str], criteria_values: Set[str]) -> List[dict]:
    if not match_ids and not criteria_values:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, "vulnerabilities.item"):
                if not isinstance(item, dict):
                    continue
                configs = None
                cve = item.get("cve") if isinstance(item.get("cve"), dict) else None
                if cve:
                    configs = cve.get("configurations")
                if configs is None:
                    configs = item.get("configurations")

                if _cve_has_match(configs, match_ids, criteria_values):
                    items.append(item)
    return items


def _normalize_config_nodes(configs: object) -> List[dict]:
    if not configs:
        return []
    if isinstance(configs, dict):
        nodes = configs.get("nodes") or configs.get("configurations") or []
    elif isinstance(configs, list):
        nodes = []
        for entry in configs:
            if isinstance(entry, dict) and isinstance(entry.get("nodes"), list):
                nodes.extend(entry.get("nodes") or [])
            else:
                nodes.append(entry)
    else:
        return []
    return [node for node in nodes if isinstance(node, dict)]


def _iter_cve_match_fields(configs: object) -> Iterable[Tuple[str | None, str | None]]:
    stack = _normalize_config_nodes(configs)
    while stack:
        node = stack.pop()
        for match in node.get("cpeMatch", []) or []:
            if isinstance(match, dict):
                yield match.get("matchCriteriaId"), match.get("criteria") or match.get("cpe23Uri")
        for match in node.get("cpe_match", []) or []:
            if isinstance(match, dict):
                yield match.get("matchCriteriaId"), match.get("criteria") or match.get("cpe23Uri")
        children = node.get("children") or []
        stack.extend([child for child in children if isinstance(child, dict)])


def _cve_has_match(configs: object, match_ids: Set[str], criteria_values: Set[str]) -> bool:
    for match_id, criteria in _iter_cve_match_fields(configs):
        if match_id in match_ids or (criteria and criteria in criteria_values):
            return True
    return False


def _extract_cwe_ids_from_cve_item(item: dict) -> Set[str]:
    cwe_ids: Set[str] = set()
    cve_obj = item.get("cve")
    if isinstance(cve_obj, dict):
        weaknesses = cve_obj.get("weaknesses") or item.get("weaknesses") or []
    else:
        weaknesses = item.get("weaknesses") or []
    for weakness in weaknesses:
        if isinstance(weakness, dict):
            description = weakness.get("description", [])
            for desc in description:
                if isinstance(desc, dict):
                    value = desc.get("value", "")
                    if value.startswith("CWE-"):
                        cwe_ids.add(value)
    return cwe_ids


def _collect_cwes(paths: List[str], cwe_ids: Set[str]) -> List[dict]:
    if not cwe_ids:
        return []
    items: List[dict] = []
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for weakness in root.findall(".//{http://cwe.mitre.org/cwe-7}Weakness"):
            cwe_id = weakness.get("ID")
            if cwe_id and f"CWE-{cwe_id}" in cwe_ids:
                items.append(_parse_cwe_xml(weakness))
    return items


def _parse_cwe_xml(weakness) -> dict:
    cwe_id = weakness.get("ID")
    name = weakness.get("Name", "")
    description = ""
    desc_elem = weakness.find(".//{http://cwe.mitre.org/cwe-7}Description")
    if desc_elem is not None:
        description = desc_elem.text or ""

    return {
        "id": f"CWE-{cwe_id}",
        "name": name,
        "description": description,
    }


def _collect_capecs(paths: List[str], cwe_ids: Set[str]) -> List[dict]:
    if not cwe_ids:
        return []
    items: List[dict] = []
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for attack_pattern in root.findall(".//{http://capec.mitre.org/capec-3}Attack_Pattern"):
            capec_id = attack_pattern.get("ID")
            if capec_id:
                related_cwes = []
                for related_weakness in attack_pattern.findall(".//{http://capec.mitre.org/capec-3}Related_Weakness"):
                    cwe_id = related_weakness.get("CWE_ID")
                    if cwe_id and f"CWE-{cwe_id}" in cwe_ids:
                        related_cwes.append(f"CWE-{cwe_id}")

                if related_cwes:
                    items.append(_parse_capec_xml(attack_pattern))
    return items


def _parse_capec_xml(attack_pattern) -> dict:
    capec_id = attack_pattern.get("ID")
    name = attack_pattern.get("Name", "")
    description = ""
    desc_elem = attack_pattern.find(".//{http://capec.mitre.org/capec-3}Description")
    if desc_elem is not None:
        description = desc_elem.text or ""

    return {
        "id": f"CAPEC-{capec_id}",
        "name": name,
        "description": description,
    }


def _collect_attack_techniques(paths: List[str]) -> List[dict]:
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if "objects" in data:
                for obj in data["objects"]:
                    if obj.get("type") == "attack-pattern":
                        items.append(obj)
    return items


def _collect_d3fend(paths: List[str], technique_ids: Set[str]) -> List[dict]:
    if not technique_ids:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if "D3FEND" in data:
                for technique in data["D3FEND"]:
                    if technique.get("d3f:id") in technique_ids:
                        items.append(technique)
    return items


def _collect_car(paths: List[str], technique_ids: Set[str]) -> List[dict]:
    if not technique_ids:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            if isinstance(data, dict) and "id" in data:
                if data["id"] in technique_ids:
                    items.append(data)
    return items


def _collect_shield(paths: List[str], technique_ids: Set[str]) -> List[dict]:
    if not technique_ids:
        return []
    items: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict) and data.get("id") in technique_ids:
                items.append(data)
    return items


def _load_cwe_data(paths: List[str]) -> List[dict]:
    items = []
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for weakness in root.findall(".//{http://cwe.mitre.org/cwe-7}Weakness"):
            items.append(_parse_cwe_xml(weakness))
    return items


def _load_capec_data(paths: List[str]) -> List[dict]:
    items = []
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for attack_pattern in root.findall(".//{http://capec.mitre.org/capec-3}Attack_Pattern"):
            items.append(_parse_capec_xml(attack_pattern))
    return items


def _load_d3fend_data(paths: List[str]) -> List[dict]:
    items = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if "results" in data and "bindings" in data["results"]:
                items.extend(data["results"]["bindings"])
    return items


def _load_car_data(paths: List[str]) -> List[dict]:
    items = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            if isinstance(data, dict):
                items.append(data)
    return items


def _load_shield_data(paths: List[str]) -> List[dict]:
    items = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                items.append(data)
    return items


def _load_engage_data(paths: List[str]) -> List[dict]:
    items = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                items.append(data)
    return items


def _run_etl_attack(items):
    from src.etl.etl_attack import ATTACKtoRDFTransformer
    data = {"objects": items}
    transformer = ATTACKtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage4-attack.ttl", format="turtle")

def _run_etl_d3fend(items):
    from src.etl.etl_d3fend import D3FENDtoRDFTransformer
    data = {"results": {"bindings": items}}
    transformer = D3FENDtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage5-d3fend.ttl", format="turtle")

def _run_etl_capec(items):
    from src.etl.etl_capec import CAPECtoRDFTransformer
    data = {"attackPatterns": items}
    transformer = CAPECtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage6-capec.ttl", format="turtle")

def _run_etl_cwe(items):
    from src.etl.etl_cwe import CWEtoRDFTransformer
    data = {"weaknesses": items}
    transformer = CWEtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage7-cwe.ttl", format="turtle")

def _run_etl_car(items):
    from src.etl.etl_car import CARtoRDFTransformer
    data = items
    transformer = CARtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage8-car.ttl", format="turtle")

def _run_etl_shield(items):
    from src.etl.etl_shield import SHIELDtoRDFTransformer
    data = {"DeceptionTechniques": items}
    transformer = SHIELDtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage9-shield.ttl", format="turtle")

def _run_etl_engage(items):
    from src.etl.etl_engage import ENGAGEtoRDFTransformer
    data = {"DeceptionTechniques": items}
    transformer = ENGAGEtoRDFTransformer()
    graph = transformer.transform(data)
    graph.serialize(destination="tmp/pipeline-stage10-engage.ttl", format="turtle")


def main():
    parser = argparse.ArgumentParser(description="Run full ETL pipeline")
    parser.add_argument("--cve-first", action="store_true", help="Derive from CVEs (default)")
    parser.add_argument("--attack-first", action="store_true", help="Derive from ATT&CK techniques")
    parser.add_argument("--workers", type=int, default=6, help="Number of parallel workers")
    args = parser.parse_args()

    print("Starting full ETL pipeline...")

    # Load data in parallel
    print("Loading data in parallel...")
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        
        # CPE - use chunks directory
        futures['cpe'] = executor.submit(_collect_all_items, _pick_files("data/cpe/raw/nvdcpe-2.0-chunks", "*.json"), "products.item")
        
        # CPEMatch - use chunks directory
        futures['cpematch'] = executor.submit(_collect_all_items, _pick_files("data/cpe/raw/nvdcpematch-2.0-chunks", "*.json"), "matchStrings.item")
        
        # CVE
        futures['cve'] = executor.submit(_collect_all_items, _pick_files("data/cve/raw", "nvdcve-2.0-*.json"), "vulnerabilities.item")
        
        # CWE - single file
        futures['cwe'] = executor.submit(_load_cwe_data, ["data/cwe/raw/cwec_v4.19.1.xml"])
        
        # CAPEC - single file
        futures['capec'] = executor.submit(_load_capec_data, ["data/capec/raw/capec_latest.xml"])
        
        # ATT&CK
        futures['attack'] = executor.submit(_collect_attack_techniques, _pick_files("data/attack/raw", "*.json"))
        
        # Defenses
        futures['d3fend'] = executor.submit(_load_d3fend_data, ["data/d3fend/raw/d3fend-full-mappings.json"])
        futures['car'] = executor.submit(_load_car_data, _pick_files("data/car/raw", "*.yaml"))
        futures['shield'] = executor.submit(_load_shield_data, _pick_files("data/shield/raw", "*.json"))
        futures['engage'] = executor.submit(_load_engage_data, _pick_files("data/engage/raw", "*.json"))
        
        # Collect results
        print("Collecting CPE data...")
        cpe_items = futures['cpe'].result()
        print(f"Loaded {len(cpe_items)} CPE items")
        
        print("Collecting CPEMatch data...")
        cpematch_items = futures['cpematch'].result()
        print(f"Loaded {len(cpematch_items)} CPEMatch items")
        
        print("Collecting CVE data...")
        cve_items = futures['cve'].result()
        print(f"Loaded {len(cve_items)} CVE items")
        
        print("Collecting CWE data...")
        cwe_items = futures['cwe'].result()
        print(f"Loaded {len(cwe_items)} CWE items")
        
        print("Collecting CAPEC data...")
        capec_items = futures['capec'].result()
        print(f"Loaded {len(capec_items)} CAPEC items")
        
        print("Collecting ATT&CK data...")
        attack_items = futures['attack'].result()
        print(f"Loaded {len(attack_items)} ATT&CK items")
        
        print("Collecting defense data...")
        d3fend_items = futures['d3fend'].result()
        car_items = futures['car'].result()
        shield_items = futures['shield'].result()
        engage_items = futures['engage'].result()

    print(f"Loaded data: CPE={len(cpe_items)}, CPEMatch={len(cpematch_items)}, CVE={len(cve_items)}, CWE={len(cwe_items)}, CAPEC={len(capec_items)}, ATT&CK={len(attack_items)}")
    print(f"Defense data: D3FEND={len(d3fend_items)}, CAR={len(car_items)}, SHIELD={len(shield_items)}, ENGAGE={len(engage_items)}")

    # Now run the ETL transformations
    print("Starting ETL transformations...")
    from rdflib import Graph
    from src.etl.etl_cpe import transform_cpe
    from src.etl.etl_cpematch import transform_cpematch
    from src.etl.etl_cve import transform_cve
    from src.etl.etl_cwe import CWEtoRDFTransformer
    from src.etl.etl_capec import CAPECtoRDFTransformer
    from src.etl.etl_attack import ATTACKtoRDFTransformer
    from src.etl.etl_d3fend import D3FENDtoRDFTransformer
    from src.etl.etl_car import CARtoRDFTransformer
    from src.etl.etl_shield import SHIELDtoRDFTransformer
    from src.etl.etl_engage import ENGAGEtoRDFTransformer

    # Sequential core chain
    # Stage 1: CPE
    print("Running CPE ETL...")
    cpe_data = {"products": cpe_items}
    transform_cpe(cpe_data, "tmp/pipeline-stage1-cpe.ttl")

    # Stage 2: CPEMatch
    print("Running CPEMatch ETL...")
    cpematch_data = {"matches": cpematch_items}
    transform_cpematch(cpematch_data, "tmp/pipeline-stage2-cpematch.ttl")

    # Stage 3: CVE
    print("Running CVE ETL...")
    cve_data = {"vulnerabilities": cve_items}
    transform_cve(cve_data, "tmp/pipeline-stage3-cve.ttl")

    # Parallel processing for remaining stages
    print("Running remaining ETLs in parallel...")
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        
        # Stage 4: ATT&CK
        futures['attack'] = executor.submit(_run_etl_attack, attack_items)
        
        # Stage 5: D3FEND
        futures['d3fend'] = executor.submit(_run_etl_d3fend, d3fend_items)
        
        # Stage 6: CAPEC
        futures['capec'] = executor.submit(_run_etl_capec, capec_items)
        
        # Stage 7: CWE
        futures['cwe'] = executor.submit(_run_etl_cwe, cwe_items)
        
        # Stage 8: CAR
        futures['car'] = executor.submit(_run_etl_car, car_items)
        
        # Stage 9: SHIELD
        futures['shield'] = executor.submit(_run_etl_shield, shield_items)
        
        # Stage 10: ENGAGE
        futures['engage'] = executor.submit(_run_etl_engage, engage_items)
        
        # Collect results
        for name, future in futures.items():
            future.result()
            print(f"Completed {name} ETL")

    print("Full ETL pipeline complete!")


if __name__ == "__main__":
    main()