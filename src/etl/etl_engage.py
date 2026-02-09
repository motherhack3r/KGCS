"""ETL Pipeline: MITRE ENGAGE JSON -> RDF Turtle.

Engagement concepts for adversary interaction and strategic disruption.

Usage:
    python -m src.etl.etl_engage --input data/engage/raw/engage.json \
                              --output data/engage/samples/engage-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import write_graph_turtle_lines, write_graph_ntriples_lines
except Exception:
    from .ttl_writer import write_graph_turtle_lines, write_graph_ntriples_lines


class ENGAGEtoRDFTransformer:
    """Transform ENGAGE JSON to RDF."""

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def transform(self, json_data: dict) -> Graph:
        """Transform ENGAGE JSON to RDF graph."""
        if "EngagementConcepts" not in json_data:
            raise ValueError("JSON must contain 'EngagementConcepts' array")
        
        concepts = json_data["EngagementConcepts"]
        
        for concept in concepts:
            self._add_engagement_concept(concept)
        
        self._add_disruption_relationships(concepts)
        # Emit goals and references if present
        if json_data.get("Goals"):
            self._add_goals(json_data.get("Goals"))
        if json_data.get("References"):
            self._add_references(json_data.get("References"))

        return self.graph

    def _add_engagement_concept(self, concept: dict):
        """Add an ENGAGE engagement concept node."""
        engage_id = concept.get("ID", "")
        if not engage_id:
            return

        engage_id_full = f"ENGAGE-{engage_id}" if not engage_id.startswith("ENGAGE-") else engage_id
        concept_node = URIRef(f"{self.EX}engagement/{engage_id_full}")

        self.graph.add((concept_node, RDF.type, self.SEC.EngagementConcept))
        self.graph.add((concept_node, self.SEC.engageId, Literal(engage_id_full, datatype=XSD.string)))

        if concept.get("Name"):
            self.graph.add((concept_node, RDFS.label, Literal(concept["Name"], datatype=XSD.string)))

        if concept.get("Description"):
            desc_text = self._extract_description(concept["Description"])
            if desc_text:
                self.graph.add((concept_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))

        if concept.get("StrategicValue"):
            self.graph.add((concept_node, self.SEC.strategicValue, Literal(concept["StrategicValue"], datatype=XSD.string)))

        if concept.get("Category"):
            self.graph.add((concept_node, self.SEC.category, Literal(concept["Category"], datatype=XSD.string)))

    def _extract_description(self, description_obj) -> str:
        """Extract description text from potentially nested structure."""
        if isinstance(description_obj, str):
            return description_obj
        if isinstance(description_obj, dict):
            if "Description" in description_obj:
                return self._extract_description(description_obj["Description"])
            if "Text" in description_obj:
                return description_obj["Text"]
        if isinstance(description_obj, list) and len(description_obj) > 0:
            return self._extract_description(description_obj[0])
        return ""

    def _add_disruption_relationships(self, concepts: list):
        """Add disrupts relationships to ATT&CK techniques."""
        for concept in concepts:
            engage_id = concept.get("ID", "")
            if not engage_id:
                continue

            engage_id_full = f"ENGAGE-{engage_id}" if not engage_id.startswith("ENGAGE-") else engage_id
            concept_node = URIRef(f"{self.EX}engagement/{engage_id_full}")

            if concept.get("DisruptsTechniques"):
                for att_technique in concept["DisruptsTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((concept_node, self.SEC.disrupts, att_node))

    def _add_goals(self, goals):
        """Add Goal nodes and link to approaches or engagement concepts."""
        # goals may be a list or dict
        items = []
        if isinstance(goals, dict):
            # dict keyed by id
            for gid, g in goals.items():
                if isinstance(g, dict):
                    g.setdefault("id", gid)
                    items.append(g)
        elif isinstance(goals, list):
            items = goals
        else:
            return

        for g in items:
            gid = g.get("id") or g.get("ID") or g.get("goalId")
            if not gid:
                continue
            gid_full = gid if str(gid).startswith("ENGAGE-") else f"ENGAGE-{gid}"
            node = URIRef(f"{self.EX}goal/{gid_full}")
            self.graph.add((node, RDF.type, self.SEC.Goal))
            self.graph.add((node, self.SEC.goalId, Literal(gid_full, datatype=XSD.string)))
            if g.get("name") or g.get("Name"):
                self.graph.add((node, RDFS.label, Literal(g.get("name") or g.get("Name"), datatype=XSD.string)))
            if g.get("description") or g.get("Description"):
                desc = g.get("description") or g.get("Description")
                self.graph.add((node, self.SEC.description, Literal(desc, datatype=XSD.string)))
            # Link goal to approaches if mapping present
            approaches = g.get("approaches") or g.get("Approaches") or []
            if isinstance(approaches, list):
                for aid in approaches:
                    aid_str = aid if isinstance(aid, str) else aid.get("id") or aid.get("ID")
                    if not aid_str:
                        continue
                    ap_node = URIRef(f"{self.EX}approach/{aid_str}")
                    self.graph.add((node, self.SEC.relatedApproach, ap_node))

    def _add_references(self, refs):
        """Add Reference nodes (URLs/citations) and optionally link to goals or engagements."""
        items = []
        if isinstance(refs, dict):
            for rid, r in refs.items():
                if isinstance(r, dict):
                    r.setdefault("id", rid)
                    items.append(r)
        elif isinstance(refs, list):
            items = refs
        else:
            return

        import hashlib
        for r in items:
            rid = r.get("id") or r.get("ID") or r.get("referenceId")
            title = r.get("title") or r.get("Title")
            url = r.get("url") or r.get("URL")
            citation = r.get("citation") or r.get("Citation")

            # If no id, create a compact digest-based id from available content
            if not rid:
                id_source = (url or citation or title or "ref").strip()
                digest = hashlib.sha1(str(id_source).encode('utf-8')).hexdigest()[:12]
                rid = f"ref-{digest}"

            node = URIRef(f"{self.EX}reference/{rid}")
            self.graph.add((node, RDF.type, self.SEC.Reference))
            if title:
                self.graph.add((node, RDFS.label, Literal(title, datatype=XSD.string)))
            if url:
                self.graph.add((node, self.SEC.url, Literal(url, datatype=XSD.anyURI)))
            if citation:
                self.graph.add((node, self.SEC.citation, Literal(citation, datatype=XSD.string)))
            # If reference mentions a goal or engagement, attempt to link
            targets = r.get("targets") or r.get("related_goals") or r.get("goals") or []
            if isinstance(targets, list):
                for t in targets:
                    tid = t if isinstance(t, str) else t.get("id") or t.get("ID")
                    if not tid:
                        continue
                    # link to goal or engagement if ID pattern
                    if str(tid).upper().startswith("EAC") or str(tid).upper().startswith("ENGAGE-"):
                        tid_full = tid if str(tid).startswith("ENGAGE-") else f"ENGAGE-{tid}"
                        tgt_node = URIRef(f"{self.EX}engagement/{tid_full}")
                        self.graph.add((tgt_node, self.SEC.hasReference, node))
                    else:
                        tgt_node = URIRef(f"{self.EX}goal/{tid}")
                        self.graph.add((tgt_node, self.SEC.hasReference, node))


def _load_engage_data(input_path: str) -> dict:
    if os.path.isdir(input_path):
        # Merge all JSON files in the directory into a single EngagementConcepts array
        import glob
        normalized = []
        # Load helper dictionaries to enrich activities
        activities_map = {}
        approaches_map = {}
        approach_activity = {}
        attack_mappings = {}

        # First pass: read all files into memory keyed by filename
        file_datas = {}
        for file in glob.glob(os.path.join(input_path, "*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    file_datas[os.path.basename(file)] = json.load(f)
            except Exception:
                continue

        # Build activities map from activities.json or activity_details.json
        for key in ("activities.json", "activity_details.json"):
            data = file_datas.get(key)
            if not data:
                continue
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and (item.get("id") or item.get("ID")):
                        aid = item.get("id") or item.get("ID")
                        activities_map[aid] = item
            elif isinstance(data, dict):
                for aid, item in data.items():
                    activities_map[aid] = item

        # Build approaches map from approaches.json or approach_details.json
        for key in ("approaches.json", "approach_details.json"):
            data = file_datas.get(key)
            if not data:
                continue
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and (item.get("id") or item.get("ID")):
                        pid = item.get("id") or item.get("ID")
                        approaches_map[pid] = item
            elif isinstance(data, dict):
                for pid, item in data.items():
                    approaches_map[pid] = item

        # Build approach->activity mappings
        aam = file_datas.get("approach_activity_mappings.json")
        if isinstance(aam, list):
            for m in aam:
                aid = m.get("activity_id") or m.get("activityId")
                ap = m.get("approach_id") or m.get("approachId")
                if aid and ap:
                    approach_activity.setdefault(aid, []).append(ap)

        # Build attack mappings if present (activity -> [technique ids])
        am = file_datas.get("attack_mapping.json")
        if isinstance(am, dict):
            # expecting keys to be activity ids or approach ids
            for k, v in am.items():
                if isinstance(v, list):
                    attack_mappings[k] = v

        # Now normalize activities: prefer explicit activity maps, else scan files for items
        seen = set()
        # if activities_map present, iterate it
        if activities_map:
            for aid, item in activities_map.items():
                if aid in seen:
                    continue
                seen.add(aid)
                concept_id = aid
                name = item.get("name") or item.get("Name") or item.get("label")
                description = item.get("description") or item.get("Description") or item.get("long_description")
                # enrich
                approaches = approach_activity.get(aid, [])
                categories = [approaches_map.get(a, {}).get("type") or approaches_map.get(a, {}).get("name") for a in approaches]
                strategic_values = [approaches_map.get(a, {}).get("type") for a in approaches if approaches_map.get(a)]
                disrupts = attack_mappings.get(aid) or []
                normalized.append({
                    "ID": concept_id,
                    "Name": name,
                    "Description": description,
                    "Approaches": approaches,
                    "Category": categories[0] if categories else None,
                    "StrategicValue": strategic_values[0] if strategic_values else None,
                    "DisruptsTechniques": disrupts
                })
        else:
            # Fallback: scan all files for activity-like entries
            for data in file_datas.values():
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("EngagementConcepts") or data.get("activities") or data.get("Activities") or data.get("items") or []
                    if isinstance(items, dict):
                        items = [items]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    concept_id = item.get("id") or item.get("ID")
                    if not concept_id or concept_id in seen:
                        continue
                    seen.add(concept_id)
                    name = item.get("name") or item.get("Name")
                    description = item.get("description") or item.get("Description") or item.get("long_description")
                    approaches = approach_activity.get(concept_id, [])
                    categories = [approaches_map.get(a, {}).get("type") or approaches_map.get(a, {}).get("name") for a in approaches]
                    strategic_values = [approaches_map.get(a, {}).get("type") for a in approaches if approaches_map.get(a)]
                    disrupts = attack_mappings.get(concept_id) or []
                    normalized.append({
                        "ID": concept_id,
                        "Name": name,
                        "Description": description,
                        "Approaches": approaches,
                        "Category": categories[0] if categories else None,
                        "StrategicValue": strategic_values[0] if strategic_values else None,
                        "DisruptsTechniques": disrupts
                    })

        # Collect additional raw inputs so transformer can access them if needed
        result = {
            "EngagementConcepts": normalized,
            "RawFiles": file_datas,
            "Activities": file_datas.get("activities.json") or file_datas.get("activity_details.json"),
            "Approaches": file_datas.get("approaches.json") or file_datas.get("approach_details.json"),
            "ApproachDetails": file_datas.get("approach_details.json"),
            "ApproachActivityMappings": file_datas.get("approach_activity_mappings.json"),
            "ApproachMatrix": file_datas.get("approach_matrix.json"),
            "AttackMapping": file_datas.get("attack_mapping.json"),
            "AttackTacticsTechniques": file_datas.get("attack_tactics_techniques.json"),
            "Goals": file_datas.get("goals.json"),
            "GoalApproachMappings": file_datas.get("goal_approach_mappings.json"),
            "GoalDetails": file_datas.get("goal_details.json"),
            "References": file_datas.get("references.json")
        }

        return result
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE ENGAGE JSON -> RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input ENGAGE JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    
    args = parser.parse_args()
    
    try:
        json_data = _load_engage_data(args.input)
    except Exception as e:
        print(f"Error loading ENGAGE data: {e}")
        return 1
    
    try:
        print(f"Loading ENGAGE data from {args.input}...")
        transformer = ENGAGEtoRDFTransformer()
        print("Transforming to RDF...")
        transformer.transform(json_data)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing RDF to {args.output}...")
        if args.format == "nt":
            write_graph_ntriples_lines(transformer.graph, args.output)
        else:
            write_graph_turtle_lines(transformer.graph, args.output)
        
        print(f"Transformation complete: {args.output}")
        return 0
    
    except Exception as e:
        print(f"Transformation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
