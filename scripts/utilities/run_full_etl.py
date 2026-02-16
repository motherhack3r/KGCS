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
    parser.add_argument("--standard", type=str, default=None, help="Run ETL for only one standard (e.g., d3fend, car, shield, engage, capec, attack, cwe, cpe, cve). If omitted, runs all.")
    args = parser.parse_args()

    # Determine standards to process
    all_standards = [
        'cpe', 'cpematch', 'cve', 'cwe', 'capec', 'attack', 'd3fend', 'car', 'shield', 'engage'
    ]
    if args.standard:
        selected_standards = [args.standard.strip().lower()]
        if selected_standards[0] not in all_standards:
            print(f"Unknown standard: {selected_standards[0]}")
            print(f"Allowed: {', '.join(all_standards)}")
            return 2
        print(f"[ETL] Running pipeline for standard: {selected_standards[0]}")
    else:
        selected_standards = all_standards
        print("[ETL] Running pipeline for all standards.")

    print("Starting full ETL pipeline...")

    # Only load and process the selected standard(s)
    print("Loading data for selected standard(s)...")
    data_items = {}
    if 'cpe' in selected_standards:
        print("Collecting CPE data...")
        cpe_items = _collect_all_items(_pick_files("data/cpe/raw/nvdcpe-2.0-chunks", "*.json"), "products.item")
        print(f"Loaded {len(cpe_items)} CPE items")
        data_items['cpe'] = cpe_items
    if 'cpematch' in selected_standards:
        print("Collecting CPEMatch data...")
        cpematch_items = _collect_all_items(_pick_files("data/cpe/raw/nvdcpematch-2.0-chunks", "*.json"), "matchStrings.item")
        print(f"Loaded {len(cpematch_items)} CPEMatch items")
        data_items['cpematch'] = cpematch_items
    if 'cve' in selected_standards:
        print("Collecting CVE data...")
        cve_items = _collect_all_items(_pick_files("data/cve/raw", "nvdcve-2.0-*.json"), "vulnerabilities.item")
        print(f"Loaded {len(cve_items)} CVE items")
        data_items['cve'] = cve_items
    if 'cwe' in selected_standards:
        print("Collecting CWE data...")
        cwe_items = _load_cwe_data(["data/cwe/raw/cwec_v4.19.1.xml"])
        print(f"Loaded {len(cwe_items)} CWE items")
        data_items['cwe'] = cwe_items
    if 'capec' in selected_standards:
        print("Collecting CAPEC data...")
        capec_items = _load_capec_data(["data/capec/raw/capec_latest.xml"])
        print(f"Loaded {len(capec_items)} CAPEC items")
        data_items['capec'] = capec_items
    if 'attack' in selected_standards:
        print("Collecting ATT&CK data...")
        attack_items = _collect_attack_techniques(_pick_files("data/attack/raw", "*.json"))
        print(f"Loaded {len(attack_items)} ATT&CK items")
        data_items['attack'] = attack_items
    if 'd3fend' in selected_standards:
        print("Collecting D3FEND data...")
        d3fend_items = _load_d3fend_data(["data/d3fend/raw/d3fend-full-mappings.json"])
        print(f"Loaded {len(d3fend_items)} D3FEND items")
        data_items['d3fend'] = d3fend_items
    if 'car' in selected_standards:
        print("Collecting CAR data...")
        car_items = _load_car_data(_pick_files("data/car/raw", "*.yaml"))
        print(f"Loaded {len(car_items)} CAR items")
        data_items['car'] = car_items
    if 'shield' in selected_standards:
        print("Collecting SHIELD data...")
        shield_items = _load_shield_data(_pick_files("data/shield/raw", "*.json"))
        print(f"Loaded {len(shield_items)} SHIELD items")
        data_items['shield'] = shield_items
    if 'engage' in selected_standards:
        print("Collecting ENGAGE data...")
        engage_items = _load_engage_data(_pick_files("data/engage/raw", "*.json"))
        print(f"Loaded {len(engage_items)} ENGAGE items")
        data_items['engage'] = engage_items

    print("Starting ETL transformations for selected standard(s)...")
    from rdflib import Graph
    if 'cpe' in selected_standards:
        from src.etl.etl_cpe import transform_cpe
        print("Running CPE ETL...")
        cpe_data = {"products": data_items['cpe']}
        transform_cpe(cpe_data, "tmp/pipeline-stage1-cpe.ttl")
    if 'cpematch' in selected_standards:
        from src.etl.etl_cpematch import transform_cpematch
        print("Running CPEMatch ETL...")
        cpematch_data = {"matches": data_items['cpematch']}
        transform_cpematch(cpematch_data, "tmp/pipeline-stage2-cpematch.ttl")
    if 'cve' in selected_standards:
        from src.etl.etl_cve import transform_cve
        print("Running CVE ETL...")
        cve_data = {"vulnerabilities": data_items['cve']}
        transform_cve(cve_data, "tmp/pipeline-stage3-cve.ttl")
    if 'attack' in selected_standards:
        print("Running ATT&CK ETL...")
        _run_etl_attack(data_items['attack'])
    if 'd3fend' in selected_standards:
        print("Running D3FEND ETL...")
        _run_etl_d3fend(data_items['d3fend'])
    if 'capec' in selected_standards:
        print("Running CAPEC ETL...")
        _run_etl_capec(data_items['capec'])
    if 'cwe' in selected_standards:
        print("Running CWE ETL...")
        _run_etl_cwe(data_items['cwe'])
    if 'car' in selected_standards:
        print("Running CAR ETL...")
        _run_etl_car(data_items['car'])
    if 'shield' in selected_standards:
        print("Running SHIELD ETL...")
        _run_etl_shield(data_items['shield'])
    if 'engage' in selected_standards:
        print("Running ENGAGE ETL...")
        _run_etl_engage(data_items['engage'])

    print("ETL pipeline for selected standard(s) complete!")


if __name__ == "__main__":
    main()