"""ETL Pipeline: MITRE CAR YAML → RDF Turtle.

Detection analytics that detect ATT&CK techniques.

Usage:
    python -m src.etl.etl_car --input data/car/raw \
                              --output data/car/samples/car-output.ttl \
                              --validate
"""

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import write_graph_turtle_lines, write_graph_ntriples_lines
except Exception:
    from .ttl_writer import write_graph_turtle_lines, write_graph_ntriples_lines


class CARtoRDFTransformer:
    """Transform CAR analytics to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")

        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, analytics: List[Dict[str, Any]]) -> Graph:
        """Transform CAR analytics into RDF graph."""
        for analytic in analytics:
            self._add_detection_analytic(analytic)

        self._add_detection_relationships(analytics)

        return self.graph

    def _add_detection_analytic(self, analytic: Dict[str, Any]) -> None:
        """Add a CAR detection analytic node, with all ontology fields."""
        car_id = _get_first_value(analytic, ["id", "ID", "carId", "car_id", "analytic_id", "analyticId"])
        if not car_id:
            return

        car_id_full = _normalize_car_id(str(car_id))
        analytic_node = URIRef(f"{self.EX}analytic/{car_id_full}")

        self.graph.add((analytic_node, RDF.type, self.SEC.DetectionAnalytic))
        self.graph.add((analytic_node, self.SEC.carId, Literal(car_id_full, datatype=XSD.string)))

        name = _get_first_value(analytic, ["name", "Name", "title", "Title"])
        if name:
            self.graph.add((analytic_node, RDFS.label, Literal(str(name), datatype=XSD.string)))

        desc_value = _get_first_value(analytic, ["description", "Description", "summary", "Summary"])
        if desc_value:
            desc_text = _extract_description(desc_value)
            if desc_text:
                self.graph.add((analytic_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Emit status if present
        status = _get_first_value(analytic, ["status", "Status"])
        if status:
            self.graph.add((analytic_node, self.SEC.status, Literal(str(status), datatype=XSD.string)))

        # Emit tags if present (as repeated sec:tag literals)
        tags = _get_first_value(analytic, ["tags", "Tags"])
        if tags:
            if isinstance(tags, str):
                self.graph.add((analytic_node, self.SEC.tag, Literal(tags, datatype=XSD.string)))
            elif isinstance(tags, list):
                for tag in tags:
                    if tag:
                        self.graph.add((analytic_node, self.SEC.tag, Literal(str(tag), datatype=XSD.string)))

        # Emit platform if present
        platform = _get_first_value(analytic, ["platform", "Platform"])
        if platform:
            self.graph.add((analytic_node, self.SEC.platform, Literal(str(platform), datatype=XSD.string)))

        # Emit references if present (as nodes, robust to string/dict/list)
        refs = []
        for key in ("references", "References"):
            val = analytic.get(key)
            if not val:
                continue
            if isinstance(val, list):
                refs.extend(val)
            else:
                refs.append(val)
        import hashlib
        for ref in refs:
            url = None
            ref_type = None
            ref_text = None
            if isinstance(ref, dict):
                url = ref.get("url") or ref.get("URL")
                ref_type = ref.get("referenceType") or ref.get("ReferenceType")
                # support free-text descriptions in dicts
                ref_text = ref.get("title") or ref.get("description") or ref.get("text")
            elif isinstance(ref, str):
                # If ref is a bare string, it may be a URL or a free-text citation
                if str(ref).startswith("http://") or str(ref).startswith("https://"):
                    url = ref
                else:
                    ref_text = ref
            if not (url or ref_type or ref_text):
                continue

            # Create a compact, safe reference id using a short hash of the reference content
            id_source = (url or ref_type or ref_text or "").strip()
            digest = hashlib.sha1(id_source.encode('utf-8')).hexdigest()[:12]
            ref_id = f"{car_id_full}-ref-{digest}"

            ref_node = URIRef(f"{self.EX}reference/{ref_id}")
            self.graph.add((ref_node, RDF.type, self.SEC.Reference))

            # Attach properties sensibly: URLs as xsd:anyURI, types as strings, free-text as rdfs:label
            if url:
                self.graph.add((ref_node, self.SEC.url, Literal(url, datatype=XSD.anyURI)))
            if ref_type:
                self.graph.add((ref_node, self.SEC.referenceType, Literal(ref_type, datatype=XSD.string)))
            if ref_text:
                # Use rdfs:label for brief free-text citations to avoid embedding raw text into URIs
                self.graph.add((ref_node, RDFS.label, Literal(ref_text, datatype=XSD.string)))

            self.graph.add((analytic_node, self.SEC.reference, ref_node))

    def _add_detection_relationships(self, analytics: List[Dict[str, Any]]) -> None:
        """Add detects and requires relationships to ATT&CK techniques and DataSources."""
        for analytic in analytics:
            car_id = _get_first_value(analytic, ["id", "ID", "carId", "car_id", "analytic_id", "analyticId"])
            if not car_id:
                continue

            car_id_full = _normalize_car_id(str(car_id))
            analytic_node = URIRef(f"{self.EX}analytic/{car_id_full}")

            for att_id in _extract_technique_ids(analytic):
                att_id_full = att_id if att_id.startswith("T") else f"T{att_id}"
                att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                self.graph.add((analytic_node, self.SEC.detects, att_node))

            # DataSource relationships
            ds_keys = ["data_sources", "DataSources", "dataSources", "dataSource"]
            for ds_key in ds_keys:
                ds_val = analytic.get(ds_key)
                if not ds_val:
                    continue
                if isinstance(ds_val, str):
                    ds_list = [ds_val]
                else:
                    ds_list = ds_val if isinstance(ds_val, list) else [ds_val]
                for ds in ds_list:
                    if not ds:
                        continue
                    ds_id = str(ds).replace(" ", "_")
                    ds_node = URIRef(f"{self.EX}datasource/{ds_id}")
                    self.graph.add((analytic_node, self.SEC.requires, ds_node))


def _get_first_value(obj: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return None


def _normalize_car_id(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    return value if value.startswith("CAR-") else f"CAR-{value}"


def _extract_technique_ids(analytic: Dict[str, Any]) -> Iterable[str]:
    keys = [
        "DetectsTechniques",
        "detects_techniques",
        "detectsTechniques",
        "techniques",
        "technique",
        "attack_techniques",
        "attck_techniques",
        "attackTechniques",
        "attack_technique_ids",
    ]
    seen = set()
    for key in keys:
        if key not in analytic:
            continue
        value = analytic.get(key)
        for item in _normalize_technique_items(value):
            if item and item not in seen:
                seen.add(item)
                yield item


def _normalize_technique_items(value: Any) -> Iterable[str]:
    if not value:
        return []
    if isinstance(value, list):
        for entry in value:
            item = _extract_technique_id(entry)
            if item:
                yield item
    else:
        item = _extract_technique_id(value)
        if item:
            yield item


def _extract_technique_id(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry.strip()
    if isinstance(entry, dict):
        for key in ("id", "ID", "technique_id", "techniqueId", "attack_id", "attackId"):
            if entry.get(key):
                return str(entry.get(key)).strip()
    return None


def _extract_description(description_obj: Any) -> str:
    if isinstance(description_obj, str):
        return description_obj
    if isinstance(description_obj, dict):
        if "Description" in description_obj:
            return _extract_description(description_obj["Description"])
        if "Text" in description_obj:
            return description_obj["Text"]
    if isinstance(description_obj, list) and description_obj:
        return _extract_description(description_obj[0])
    return ""


def _iter_analytics_from_yaml(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        docs = list(yaml.safe_load_all(fh))

    analytics: List[Dict[str, Any]] = []
    for doc in docs:
        analytics.extend(_collect_analytics(doc))
    return analytics


def _collect_analytics(doc: Any) -> List[Dict[str, Any]]:
    if doc is None:
        return []
    if isinstance(doc, list):
        items: List[Dict[str, Any]] = []
        for entry in doc:
            items.extend(_collect_analytics(entry))
        return items
    if isinstance(doc, dict):
        for key in ("DetectionAnalytics", "analytics"):
            if isinstance(doc.get(key), list):
                return [item for item in doc[key] if isinstance(item, dict)]
        if _get_first_value(doc, ["id", "ID", "carId", "car_id", "analytic_id", "analyticId"]):
            return [doc]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="ETL: MITRE CAR YAML → RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input CAR YAML file, glob, or directory")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--validate", action="store_true", help="Run SHACL validation on output")
    parser.add_argument("--shapes", default="docs/ontology/shacl/car-shapes.ttl", help="SHACL shapes file")
    parser.add_argument("--append", action="store_true", help="Append to output file instead of overwriting")
    parser.add_argument("--format", choices=["ttl","nt"], default="ttl", help="Output format (ttl or nt)")
    args = parser.parse_args()

    input_files: List[str] = []
    if os.path.isdir(args.input):
        input_files = sorted(glob.glob(os.path.join(args.input, "*.yml")))
        input_files += sorted(glob.glob(os.path.join(args.input, "*.yaml")))
    else:
        input_files = sorted(glob.glob(args.input)) or [args.input]

    if not any(os.path.exists(p) for p in input_files):
        print(f"❌ Error: Input not found: {args.input}")
        return 1

    analytics: List[Dict[str, Any]] = []
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Warning: {input_file} not found, skipping")
            continue
        try:
            analytics.extend(_iter_analytics_from_yaml(input_file))
        except Exception as e:
            print(f"Warning: Could not parse {input_file}: {e}")

    if not analytics:
        print("Warning: No CAR analytics with IDs found in input; output will be empty.")

    try:
        print(f"Loading CAR YAML from {args.input}...")
        transformer = CARtoRDFTransformer()
        print("Transforming to RDF...")
        transformer.transform(analytics)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing RDF to {args.output}...")
        if args.format == "nt":
            write_graph_ntriples_lines(transformer.graph, args.output, append=args.append)
        else:
            write_graph_turtle_lines(transformer.graph, args.output, include_prefixes=not args.append, append=args.append)

        if args.validate:
            print("\nRunning SHACL validation...")
            try:
                try:
                    from src.core.validation import run_validator, load_graph
                except Exception:
                    from core.validation import run_validator, load_graph
                shapes = load_graph(args.shapes)
                conforms, _, _ = run_validator(args.output, shapes)
                if conforms:
                    print("[OK] Validation passed!")
                else:
                    print("[FAIL] Validation failed!")
                    return 1
            except Exception as e:
                print(f"Warning: Could not run validation: {e}")

        print(f"[OK] Transformation complete: {args.output}")
        return 0

    except Exception as e:
        print(f"[ERROR] Transformation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
