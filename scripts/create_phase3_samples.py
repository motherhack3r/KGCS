#!/usr/bin/env python3
"""Create coherent sample files across standards.

This script streams large NVD JSON files and writes trimmed samples suitable
for quick ETL runs. It also derives downstream samples across the causal chain
where source data allows it:

    CPEMatch → CPE → CVE → CWE → CAPEC
    ATT&CK techniques → {D3FEND, CAR, SHIELD, ENGAGE}

Usage:
    python scripts/create_phase3_samples.py --count 200
"""
import argparse
import json
import os
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import ijson
import yaml


def _pick_file(path: str, pattern: str) -> Optional[str]:
    if os.path.isfile(path):
        return path
    if os.path.isdir(path):
        matches = sorted(str(p) for p in Path(path).rglob(pattern))
        return matches[0] if matches else None
    return None


def _reservoir_sample(path: str, prefix: str, limit: int, rng: random.Random) -> List[dict]:
    samples: List[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for idx, item in enumerate(ijson.items(fh, prefix), start=1):
            if len(samples) < limit:
                samples.append(item)
                continue
            j = rng.randint(1, idx)
            if j <= limit:
                samples[j - 1] = item
    return samples


def _reservoir_sample_multi(paths: List[str], prefix: str, limit: int, rng: random.Random) -> List[dict]:
    samples: List[dict] = []
    idx = 0
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, prefix):
                idx += 1
                if len(samples) < limit:
                    samples.append(item)
                    continue
                j = rng.randint(1, idx)
                if j <= limit:
                    samples[j - 1] = item
    return samples


def _write_sample(out_path: str, key: str, items: List[dict]) -> None:
    payload = {
        "resultsPerPage": len(items),
        "startIndex": 0,
        "totalResults": len(items),
        key: items,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)


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


def _collect_cves(paths: List[str], match_ids: Set[str], criteria_values: Set[str], max_items: int) -> List[dict]:
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
                    if max_items and len(items) >= max_items:
                        return items
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
                nodes.extend(entry.get("nodes"))
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


def _cve_has_configs(configs: object) -> bool:
    for match_id, criteria in _iter_cve_match_fields(configs):
        if match_id or criteria:
            return True
    return False


def _extract_cwe_ids_from_cve_item(item: dict) -> Set[str]:
    cwe_ids: Set[str] = set()
    cve = item.get("cve") if isinstance(item.get("cve"), dict) else {}
    weaknesses = cve.get("weaknesses") or item.get("weaknesses") or []
    for weakness in weaknesses:
        if not isinstance(weakness, dict):
            continue
        descriptions = weakness.get("description") or []
        if isinstance(descriptions, dict):
            descriptions = [descriptions]
        for desc in descriptions:
            value = desc.get("value") if isinstance(desc, dict) else desc
            if not isinstance(value, str):
                continue
            for match in re.findall(r"CWE-\d+", value):
                if match.startswith("CWE-"):
                    cwe_ids.add(match)
    return cwe_ids


def _collect_cves_with_cwe_and_configs(paths: List[str], max_items: int, rng: random.Random) -> List[dict]:
    samples: List[dict] = []
    idx = 0
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, "vulnerabilities.item"):
                if not isinstance(item, dict):
                    continue
                configs = item.get("configurations")
                if not configs:
                    cve = item.get("cve") if isinstance(item.get("cve"), dict) else None
                    configs = cve.get("configurations") if cve else None
                if not configs or not _cve_has_configs(configs):
                    continue

                if not _extract_cwe_ids_from_cve_item(item):
                    continue

                idx += 1
                if len(samples) < max_items:
                    samples.append(item)
                    continue
                j = rng.randint(1, idx)
                if j <= max_items:
                    samples[j - 1] = item
    return samples


def _collect_cpematch_by_criteria(paths: List[str], criteria_values: Set[str], max_items: int, rng: random.Random) -> List[dict]:
    if not criteria_values:
        return []
    samples: List[dict] = []
    idx = 0
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for item in ijson.items(fh, "matchStrings.item"):
                ms = _normalize_cpematch_item(item)
                criteria = ms.get("criteria") or ms.get("cpe23Uri")
                if criteria not in criteria_values:
                    continue
                idx += 1
                if len(samples) < max_items:
                    samples.append(item)
                    continue
                j = rng.randint(1, idx)
                if j <= max_items:
                    samples[j - 1] = item
    return samples


def _cve_has_match(configs: object, match_ids: Set[str], criteria_values: Set[str]) -> bool:
    if not configs:
        return False
    if isinstance(configs, dict):
        nodes = configs.get("nodes") or configs.get("configurations") or []
        return _nodes_have_match(nodes, match_ids, criteria_values)
    if isinstance(configs, list):
        nodes = []
        for entry in configs:
            if isinstance(entry, dict) and isinstance(entry.get("nodes"), list):
                nodes.extend(entry.get("nodes"))
            else:
                nodes.append(entry)
        return _nodes_have_match(nodes, match_ids, criteria_values)
    return False


def _nodes_have_match(nodes: Iterable, match_ids: Set[str], criteria_values: Set[str]) -> bool:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        for match in node.get("cpeMatch", []) or []:
            if isinstance(match, dict):
                if match.get("matchCriteriaId") in match_ids:
                    return True
                criteria = match.get("criteria") or match.get("cpe23Uri")
                if isinstance(criteria, str) and criteria in criteria_values:
                    return True
        for match in node.get("cpe_match", []) or []:
            if isinstance(match, dict):
                if match.get("matchCriteriaId") in match_ids:
                    return True
                criteria = match.get("criteria") or match.get("cpe23Uri")
                if isinstance(criteria, str) and criteria in criteria_values:
                    return True
        children = node.get("children") or []
        if _nodes_have_match(children, match_ids, criteria_values):
            return True
    return False


def _extract_cwe_ids_from_cves(cve_items: List[dict]) -> Set[str]:
    cwe_ids: Set[str] = set()
    for item in cve_items:
        cwe_ids.update(_extract_cwe_ids_from_cve_item(item))
    return cwe_ids


def _flatten_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    text_parts = []
    if element.text and element.text.strip():
        text_parts.append(element.text.strip())
    for child in element:
        child_text = _flatten_text(child)
        if child_text:
            text_parts.append(child_text)
        if child.tail and child.tail.strip():
            text_parts.append(child.tail.strip())
    return " ".join(text_parts).strip()


def _build_cwe_sample(cwe_path: str, cwe_ids: Set[str]) -> dict:
    tree = ET.parse(cwe_path)
    root = tree.getroot()
    ns = {"cwe": "http://cwe.mitre.org/cwe-7"}
    wanted_ids = {cwe_id.replace("CWE-", "") for cwe_id in cwe_ids}

    weaknesses: List[dict] = []
    for weakness in root.findall(".//cwe:Weaknesses/cwe:Weakness", ns):
        cwe_id = weakness.get("ID")
        if not cwe_id or cwe_id not in wanted_ids:
            continue
        name = weakness.get("Name")
        abstraction = weakness.get("Abstraction")
        status = weakness.get("Status")
        description = _flatten_text(weakness.find("cwe:Description", ns))

        related = []
        for rel in weakness.findall(".//cwe:Related_Weaknesses/cwe:Related_Weakness", ns):
            rel_id = rel.get("CWE_ID")
            nature = rel.get("Nature")
            if rel_id:
                related.append({"ID": rel_id, "Relationship": nature})

        weaknesses.append({
            "ID": cwe_id,
            "Name": name,
            "Description": description,
            "WeaknessAbstraction": abstraction,
            "Status": status,
            "RelatedWeaknesses": related,
        })

    return {"Weakness": weaknesses}


def _build_capec_sample(capec_path: str, cwe_ids: Set[str]) -> dict:
    tree = ET.parse(capec_path)
    root = tree.getroot()
    ns = {"capec": "http://capec.mitre.org/capec-3"}
    wanted_ids = {cwe_id.replace("CWE-", "") for cwe_id in cwe_ids}

    patterns: List[dict] = []
    for ap in root.findall(".//capec:Attack_Patterns/capec:Attack_Pattern", ns):
        capec_id = ap.get("ID")
        if not capec_id:
            continue

        related_weaknesses = []
        matched = False
        for rel in ap.findall(".//capec:Related_Weaknesses/capec:Related_Weakness", ns):
            cwe_id = rel.get("CWE_ID")
            if cwe_id:
                related_weaknesses.append({"ID": cwe_id})
                if cwe_id in wanted_ids:
                    matched = True

        if not matched:
            continue

        name = ap.get("Name")
        description = _flatten_text(ap.find("capec:Description", ns))

        prereqs = []
        for prereq in ap.findall(".//capec:Prerequisites/capec:Prerequisite", ns):
            prereq_text = _flatten_text(prereq)
            if prereq_text:
                prereqs.append({"Description": prereq_text})

        consequences = []
        for cons in ap.findall(".//capec:Consequences/capec:Consequence", ns):
            cons_text = _flatten_text(cons)
            if cons_text:
                consequences.append({"Description": cons_text})

        related_attack_patterns = []
        for rel in ap.findall(".//capec:Related_Attack_Patterns/capec:Related_Attack_Pattern", ns):
            rel_id = rel.get("CAPEC_ID")
            nature = rel.get("Nature")
            if rel_id:
                related_attack_patterns.append({"ID": rel_id, "Relationship": nature})

        patterns.append({
            "ID": capec_id,
            "Name": name,
            "Description": description,
            "Prerequisites": prereqs,
            "Consequences": consequences,
            "RelatedWeaknesses": related_weaknesses,
            "RelatedAttackPatterns": related_attack_patterns,
        })

    return {"AttackPatterns": patterns}


def _extract_attack_ids_from_defense(d3fend_mapping_path: str, car_path: str, shield_mapping_path: str, engage_mapping_path: str) -> Set[str]:
    attack_ids: Set[str] = set()

    if os.path.exists(d3fend_mapping_path):
        try:
            data = json.load(open(d3fend_mapping_path, "r", encoding="utf-8", errors="ignore"))
            results = data.get("results", []) if isinstance(data, dict) else []
            for entry in results:
                off_id = entry.get("off_tech_id", {})
                value = off_id.get("value") if isinstance(off_id, dict) else None
                if isinstance(value, str) and value.startswith("T"):
                    attack_ids.add(value)
        except Exception:
            pass

    if os.path.isdir(car_path):
        for file_path in sorted(Path(car_path).glob("*.yml")) + sorted(Path(car_path).glob("*.yaml")):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                    docs = list(yaml.safe_load_all(fh))
                for doc in docs:
                    if isinstance(doc, dict):
                        for key in ("techniques", "technique", "attack_techniques", "attackTechniques"):
                            value = doc.get(key)
                            if isinstance(value, list):
                                for entry in value:
                                    if isinstance(entry, str) and entry.startswith("T"):
                                        attack_ids.add(entry)
                                    elif isinstance(entry, dict):
                                        tech_id = entry.get("id") or entry.get("technique_id") or entry.get("techniqueId")
                                        if isinstance(tech_id, str) and tech_id.startswith("T"):
                                            attack_ids.add(tech_id)
            except Exception:
                continue

    for mapping_path in (shield_mapping_path, engage_mapping_path):
        if os.path.exists(mapping_path):
            try:
                data = json.load(open(mapping_path, "r", encoding="utf-8", errors="ignore"))
                if isinstance(data, list):
                    for entry in data:
                        attack_id = entry.get("attack_id")
                        if isinstance(attack_id, str) and attack_id.startswith("T"):
                            attack_ids.add(attack_id)
            except Exception:
                pass

    return attack_ids


def _sample_set(values: Set[str], limit: int, rng: random.Random) -> Set[str]:
    if not limit or len(values) <= limit:
        return set(values)
    return set(rng.sample(sorted(values), limit))


def _extract_attack_id_from_refs(external_refs: List[dict]) -> Optional[str]:
    for ref in external_refs:
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def _build_attack_samples(attack_dir: str, technique_ids: Set[str], output_root: str) -> int:
    count_written = 0
    for attack_file in sorted(Path(attack_dir).glob("*.json")):
        try:
            attack_json = json.load(open(attack_file, "r", encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        objects = attack_json.get("objects", []) if isinstance(attack_json, dict) else []

        selected_objects = []
        tactic_shortnames: Set[str] = set()
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if obj.get("type") != "attack-pattern":
                continue
            attack_id = _extract_attack_id_from_refs(obj.get("external_references", []) or [])
            if attack_id and attack_id in technique_ids:
                selected_objects.append(obj)
                for phase in obj.get("kill_chain_phases", []) or []:
                    phase_name = phase.get("phase_name")
                    if phase_name:
                        tactic_shortnames.add(phase_name)

        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if obj.get("type") != "x-mitre-tactic":
                continue
            shortname = obj.get("x_mitre_shortname")
            if shortname and shortname in tactic_shortnames:
                selected_objects.append(obj)

        if not selected_objects:
            continue

        sample_payload = {"type": attack_json.get("type", "bundle"), "objects": selected_objects}
        out_path = os.path.join(output_root, "attack", "samples", f"sample-{attack_file.name}")
        _write_json(out_path, sample_payload)
        count_written += 1

    return count_written


def _build_d3fend_sample(mapping_path: str, technique_ids: Set[str]) -> dict:
    techniques: Dict[str, dict] = {}
    if not os.path.exists(mapping_path):
        return {"DefensiveTechniques": []}
    data = json.load(open(mapping_path, "r", encoding="utf-8", errors="ignore"))
    results = []
    if isinstance(data, dict):
        raw_results = data.get("results")
        if isinstance(raw_results, dict) and isinstance(raw_results.get("bindings"), list):
            results = raw_results.get("bindings")
        elif isinstance(raw_results, list):
            results = raw_results
    for entry in results:
        off_id = entry.get("off_tech_id", {})
        off_value = off_id.get("value") if isinstance(off_id, dict) else None
        if not isinstance(off_value, str) or off_value not in technique_ids:
            continue

        def_tech = entry.get("def_tech", {})
        def_value = def_tech.get("value") if isinstance(def_tech, dict) else None
        if not isinstance(def_value, str):
            continue
        def_id = def_value.split("#")[-1]
        def_label = entry.get("def_tech_label", {})
        def_name = def_label.get("value") if isinstance(def_label, dict) else None

        if def_id not in techniques:
            techniques[def_id] = {
                "ID": def_id,
                "Name": def_name or def_id,
                "MitigatesTechniques": [],
            }
        mitigations = techniques[def_id]["MitigatesTechniques"]
        if off_value not in mitigations:
            mitigations.append(off_value)

    return {"DefensiveTechniques": list(techniques.values())}


def _extract_car_technique_ids(analytic: dict) -> Set[str]:
    ids: Set[str] = set()
    for key in (
        "DetectsTechniques",
        "detects_techniques",
        "detectsTechniques",
        "techniques",
        "technique",
        "attack_techniques",
        "attackTechniques",
    ):
        value = analytic.get(key) if isinstance(analytic, dict) else None
        if not value:
            continue
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str):
                    ids.add(entry)
                elif isinstance(entry, dict):
                    tech_id = entry.get("id") or entry.get("technique_id") or entry.get("techniqueId")
                    if isinstance(tech_id, str):
                        ids.add(tech_id)
        elif isinstance(value, str):
            ids.add(value)

    normalized: Set[str] = set()
    for tech_id in ids:
        if not isinstance(tech_id, str):
            continue
        tech_id = tech_id.strip()
        if not tech_id:
            continue
        if tech_id.startswith("T"):
            normalized.add(tech_id)
        else:
            normalized.add(f"T{tech_id}")
    return normalized


def _collect_car_analytics(doc: Any) -> List[Dict[str, Any]]:
    if doc is None:
        return []
    if isinstance(doc, list):
        analytics: List[Dict[str, Any]] = []
        for entry in doc:
            analytics.extend(_collect_car_analytics(entry))
        return analytics
    if isinstance(doc, dict):
        for key in ("DetectionAnalytics", "analytics"):
            if isinstance(doc.get(key), list):
                return [item for item in doc[key] if isinstance(item, dict)]
        if doc.get("id") or doc.get("ID") or doc.get("carId") or doc.get("car_id"):
            return [doc]
    return []


def _build_car_sample(car_path: str, technique_ids: Set[str]) -> List[dict]:
    analytics: List[dict] = []
    if not os.path.isdir(car_path):
        return analytics
    for file_path in sorted(Path(car_path).glob("*.yml")) + sorted(Path(car_path).glob("*.yaml")):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                docs = list(yaml.safe_load_all(fh))
        except Exception:
            continue
        for doc in docs:
            for analytic in _collect_car_analytics(doc):
                if _extract_car_technique_ids(analytic) & technique_ids:
                    analytics.append(analytic)
    return analytics


def _build_shield_sample(mapping_path: str, technique_ids: Set[str]) -> dict:
    techniques: Dict[str, dict] = {}
    if not os.path.exists(mapping_path):
        return {"DeceptionTechniques": []}
    data = json.load(open(mapping_path, "r", encoding="utf-8", errors="ignore"))
    if not isinstance(data, list):
        return {"DeceptionTechniques": []}
    for entry in data:
        attack_id = entry.get("attack_id")
        if attack_id not in technique_ids:
            continue
        technique = entry.get("technique") or {}
        tech_id = technique.get("id") or entry.get("technique_id")
        if not tech_id:
            continue
        name = technique.get("name") or technique.get("Name")
        description = technique.get("description") or technique.get("Description") or technique.get("long_description")
        if tech_id not in techniques:
            techniques[tech_id] = {
                "ID": tech_id,
                "Name": name,
                "Description": description,
                "CountersTechniques": [],
            }
        counters = techniques[tech_id]["CountersTechniques"]
        if attack_id not in counters:
            counters.append(attack_id)
    return {"DeceptionTechniques": list(techniques.values())}


def _build_engage_sample(mapping_path: str, technique_ids: Set[str]) -> dict:
    concepts: Dict[str, dict] = {}
    if not os.path.exists(mapping_path):
        return {"EngagementConcepts": []}
    data = json.load(open(mapping_path, "r", encoding="utf-8", errors="ignore"))
    if not isinstance(data, list):
        return {"EngagementConcepts": []}
    for entry in data:
        attack_id = entry.get("attack_id")
        if attack_id not in technique_ids:
            continue
        concept_id = entry.get("eac_id") or entry.get("eav_id")
        concept_name = entry.get("eac") or entry.get("eav")
        description = entry.get("eav")
        if not concept_id:
            continue
        if concept_id not in concepts:
            concepts[concept_id] = {
                "ID": concept_id,
                "Name": concept_name,
                "Description": description,
                "DisruptsTechniques": [],
            }
        disrupts = concepts[concept_id]["DisruptsTechniques"]
        if attack_id not in disrupts:
            disrupts.append(attack_id)
    return {"EngagementConcepts": list(concepts.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create small Phase 3 sample JSON files")
    parser.add_argument("--count", type=int, default=200, help="Number of CPEMatch entries to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument("--cpe-input", default="data/cpe/raw/nvdcpe-2.0-chunks", help="CPE input file or directory")
    parser.add_argument("--cpematch-input", default="data/cpe/raw/nvdcpematch-2.0-chunks", help="CPEMatch input file or directory")
    parser.add_argument("--cve-input", default="data/cve/raw", help="CVE input file or directory")
    parser.add_argument("--cwe-input", default="data/cwe/raw/cwec_latest.xml", help="CWE input file")
    parser.add_argument("--capec-input", default="data/capec/raw/capec_latest.xml", help="CAPEC input file")
    parser.add_argument("--attack-input", default="data/attack/raw", help="ATT&CK input directory")
    parser.add_argument("--d3fend-input", default="data/d3fend/raw/d3fend-full-mappings.json", help="D3FEND mappings input file")
    parser.add_argument("--car-input", default="data/car/raw", help="CAR input directory")
    parser.add_argument("--shield-input", default="data/shield/raw/attack_mapping.json", help="SHIELD mapping input file")
    parser.add_argument("--engage-input", default="data/engage/raw/attack_mapping.json", help="ENGAGE mapping input file")
    parser.add_argument("--output-root", default="data", help="Root output directory")
    parser.add_argument("--cve-max", type=int, default=None, help="Max CVE records to include (default: same as --count)")
    parser.add_argument("--cve-fallback-random", action=argparse.BooleanOptionalAction, default=True, help="When no linked CVEs found, fall back to random CVE sampling")
    parser.add_argument("--attack-max", type=int, default=None, help="Max ATT&CK techniques to include (default: same as --count)")
    parser.add_argument("--cve-first", action=argparse.BooleanOptionalAction, default=True, help="Sample CVEs with configs+CWE first, then derive CPEMatch/CPE")
    parser.add_argument("--cpematch-max", type=int, default=None, help="Max CPEMatch entries to include (default: same as --count)")
    args = parser.parse_args()

    cpe_files: List[str] = []
    if os.path.isdir(args.cpe_input):
        cpe_files = sorted(str(p) for p in Path(args.cpe_input).rglob("nvdcpe-2.0-chunk-*.json"))
    else:
        candidate = _pick_file(args.cpe_input, "nvdcpe-2.0-chunk-*.json")
        if candidate:
            cpe_files = [candidate]
    if not cpe_files:
        print("CPE input not found")
        return 1

    cpematch_files: List[str] = []
    if os.path.isdir(args.cpematch_input):
        cpematch_files = sorted(str(p) for p in Path(args.cpematch_input).rglob("nvdcpematch-2.0-chunk-*.json"))
    else:
        candidate = _pick_file(args.cpematch_input, "nvdcpematch-2.0-chunk-*.json")
        if candidate:
            cpematch_files = [candidate]
    if not cpematch_files:
        print("CPEMatch input not found")
        return 1

    cve_files: List[str] = []
    if os.path.isdir(args.cve_input):
        cve_files = sorted(str(p) for p in Path(args.cve_input).rglob("nvdcve-2.0-*.json"))
    else:
        candidate = _pick_file(args.cve_input, "nvdcve-2.0-*.json")
        if candidate:
            cve_files = [candidate]
    if not cve_files:
        print("CVE input not found")
        return 1

    print(f"Using CPE files: {len(cpe_files)}")
    print(f"Using CPEMatch files: {len(cpematch_files)}")
    print(f"Using CVE files: {len(cve_files)}")

    rng = random.Random(args.seed)
    cve_max = args.cve_max if args.cve_max is not None else args.count
    cpematch_max = args.cpematch_max if args.cpematch_max is not None else args.count

    if args.cve_first:
        cve_items = _collect_cves_with_cwe_and_configs(cve_files, cve_max, rng)
        if not cve_items:
            print("No CVEs with configs+CWE found; falling back to random CVE sampling")
            cve_items = _reservoir_sample_multi(cve_files, "vulnerabilities.item", cve_max, rng)

        criteria_values: Set[str] = set()
        match_ids: Set[str] = set()
        for item in cve_items:
            configs = item.get("configurations")
            if not configs:
                cve = item.get("cve") if isinstance(item.get("cve"), dict) else None
                configs = cve.get("configurations") if cve else None
            for match_id, criteria in _iter_cve_match_fields(configs):
                if match_id:
                    match_ids.add(match_id)
                if isinstance(criteria, str):
                    criteria_values.add(criteria)

        cpematch_items = _collect_cpematch_by_criteria(cpematch_files, criteria_values, cpematch_max, rng)
        if not cpematch_items:
            print("No CPEMatch entries matched CVE criteria; falling back to random CPEMatch sampling")
            cpematch_items = _reservoir_sample_multi(cpematch_files, "matchStrings.item", cpematch_max, rng)

        match_ids, cpe_ids, criteria_values = _collect_related_ids(cpematch_items)
        cpe_items = _collect_cpes(cpe_files, cpe_ids)
    else:
        cpematch_items = _reservoir_sample_multi(cpematch_files, "matchStrings.item", args.count, rng)
        match_ids, cpe_ids, criteria_values = _collect_related_ids(cpematch_items)

        cpe_items = _collect_cpes(cpe_files, cpe_ids)
        cve_items = _collect_cves(cve_files, match_ids, criteria_values, cve_max)
        if not cve_items and args.cve_fallback_random and cve_max:
            print("No linked CVEs found; falling back to random CVE sampling")
            cve_items = _reservoir_sample_multi(cve_files, "vulnerabilities.item", cve_max, rng)

    cpe_out = os.path.join(args.output_root, "cpe", "samples", "sample_cpe.json")
    cpematch_out = os.path.join(args.output_root, "cpe", "samples", "sample_cpematch.json")
    cve_out = os.path.join(args.output_root, "cve", "samples", "sample_cve.json")

    _write_sample(cpe_out, "products", cpe_items)
    _write_sample(cpematch_out, "matchStrings", cpematch_items)
    _write_sample(cve_out, "vulnerabilities", cve_items)

    print(f"Wrote {len(cpe_items)} CPE products to {cpe_out}")
    print(f"Wrote {len(cpematch_items)} CPEMatch entries to {cpematch_out}")
    print(f"Wrote {len(cve_items)} CVE entries to {cve_out}")

    cwe_ids = _extract_cwe_ids_from_cves(cve_items)
    cwe_input = args.cwe_input
    if not os.path.exists(cwe_input):
        if os.path.isdir(cwe_input):
            cwe_input = _pick_file(cwe_input, "cwec*.xml") or _pick_file(cwe_input, "cwe*.json")
        else:
            fallback_dir = os.path.join(args.output_root, "cwe", "raw")
            cwe_input = _pick_file(fallback_dir, "cwec*.xml") or _pick_file(fallback_dir, "cwe*.json")

    if cwe_ids and cwe_input and os.path.exists(cwe_input):
        cwe_payload = _build_cwe_sample(cwe_input, cwe_ids)
        cwe_out = os.path.join(args.output_root, "cwe", "samples", "sample_cwe.json")
        _write_json(cwe_out, cwe_payload)
        print(f"Wrote {len(cwe_payload.get('Weakness', []))} CWE entries to {cwe_out}")
    else:
        print("Skipping CWE sample (no CWE IDs or input missing)")

    if cwe_ids and os.path.exists(args.capec_input):
        capec_payload = _build_capec_sample(args.capec_input, cwe_ids)
        capec_out = os.path.join(args.output_root, "capec", "samples", "sample_capec.json")
        _write_json(capec_out, capec_payload)
        print(f"Wrote {len(capec_payload.get('AttackPatterns', []))} CAPEC entries to {capec_out}")
    else:
        print("Skipping CAPEC sample (no CWE IDs or input missing)")

    attack_candidates = _extract_attack_ids_from_defense(
        args.d3fend_input,
        args.car_input,
        args.shield_input,
        args.engage_input,
    )
    attack_max = args.attack_max if args.attack_max is not None else args.count
    attack_ids = _sample_set(attack_candidates, attack_max, rng)
    if not attack_ids:
        print("Skipping ATT&CK/defense samples (no technique IDs found)")
        return 0

    if os.path.isdir(args.attack_input):
        count_written = _build_attack_samples(args.attack_input, attack_ids, args.output_root)
        print(f"Wrote {count_written} ATT&CK sample file(s) to {os.path.join(args.output_root, 'attack', 'samples')}")
    else:
        print("Skipping ATT&CK sample (input missing)")

    d3fend_payload = _build_d3fend_sample(args.d3fend_input, attack_ids)
    d3fend_out = os.path.join(args.output_root, "d3fend", "samples", "sample_d3fend.json")
    _write_json(d3fend_out, d3fend_payload)
    print(f"Wrote {len(d3fend_payload.get('DefensiveTechniques', []))} D3FEND entries to {d3fend_out}")

    car_payload = _build_car_sample(args.car_input, attack_ids)
    car_out = os.path.join(args.output_root, "car", "samples", "sample_car.yaml")
    _write_yaml(car_out, car_payload)
    print(f"Wrote {len(car_payload)} CAR entries to {car_out}")

    shield_payload = _build_shield_sample(args.shield_input, attack_ids)
    shield_out = os.path.join(args.output_root, "shield", "samples", "sample_shield.json")
    _write_json(shield_out, shield_payload)
    print(f"Wrote {len(shield_payload.get('DeceptionTechniques', []))} SHIELD entries to {shield_out}")

    engage_payload = _build_engage_sample(args.engage_input, attack_ids)
    engage_out = os.path.join(args.output_root, "engage", "samples", "sample_engage.json")
    _write_json(engage_out, engage_payload)
    print(f"Wrote {len(engage_payload.get('EngagementConcepts', []))} ENGAGE entries to {engage_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
