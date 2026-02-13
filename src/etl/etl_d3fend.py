"""ETL Pipeline: MITRE D3FEND JSON -> RDF Turtle.

Defensive techniques that mitigate ATT&CK techniques.

Usage:
    python -m src.etl.etl_d3fend --input data/d3fend/raw/d3fend.json \
                              --output data/d3fend/samples/d3fend-output.ttl
"""

import json
import argparse
from pathlib import Path
import sys
import os

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib import RDF, RDFS, XSD

try:
    from src.etl.ttl_writer import (
        write_graph_turtle_lines,
        write_graph_ntriples_lines,
        write_graph_turtle_split_lines,
        write_graph_ntriples_split_lines,
    )
except Exception:
    from .ttl_writer import (
        write_graph_turtle_lines,
        write_graph_ntriples_lines,
        write_graph_turtle_split_lines,
        write_graph_ntriples_split_lines,
    )


class D3FENDtoRDFTransformer:
    """Transform D3FEND JSON to RDF."""

    PHASE_A_DEFENSIVE_PREDICATES = {
        "analyzes": "analyzes",
        "monitors": "monitors",
        "hardens": "hardens",
        "filters": "filters",
        "isolates": "isolates",
        "restricts": "restricts",
        "enables": "enables",
        "blocks": "blocks",
    }

    def __init__(self):
        self.graph = Graph()
        self.SEC = Namespace("https://example.org/sec/core#")
        self.EX = Namespace("https://example.org/")
        self._def_tech_alias_to_id = {}
        self._def_tech_alias_index_loaded = False
        self._items_by_id = {}
        
        self.graph.bind("sec", self.SEC)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

    def _normalize_d3fend_id(self, id_value: str) -> str:
        """Normalize D3FEND IDs into safe local name for URI creation.

        - Replace namespace separators and whitespace with '-'
        - Remove any remaining unsafe characters
        - Ensure a D3FEND- or D3- prefix exists (preserve if starts with D3)
        - Fallback to a short sha1 digest if the result is empty
        """
        import re
        import hashlib

        if not id_value:
            digest = hashlib.sha1(b"").hexdigest()[:8]
            return f"D3FEND-UNKNOWN-{digest}"

        s = str(id_value).strip()
        # Replace colon, slash, backslash, whitespace with hyphen
        s = re.sub(r"[:/\\\s]+", "-", s)
        # Remove leading d3f/d3fend namespace fragments (they are noisy in IDs)
        s = re.sub(r'^(?:d3f(?:end)?-?)', '', s, flags=re.IGNORECASE)
        # Remove characters that are not generally safe in URL local names
        s = re.sub(r"[^A-Za-z0-9_.-]", "", s)
        # Collapse multiple hyphens
        s = re.sub(r"-+", "-", s).strip('-')

        if not s:
            digest = hashlib.sha1(str(id_value).encode('utf-8')).hexdigest()[:8]
            return f"D3FEND-UNKNOWN-{digest}"

        if not s.upper().startswith('D3'):
            s = f"D3FEND-{s}"

        return s

    def transform(self, json_data: dict, source_path: str | None = None) -> Graph:
        """Transform D3FEND JSON to RDF graph."""
        if "DefensiveTechniques" in json_data:
            techniques = json_data["DefensiveTechniques"]

            for technique in techniques:
                self._add_defensive_technique(technique)

            self._add_technique_relationships(techniques)
            self._add_mitigation_relationships(techniques)
            return self.graph

        if "@graph" in json_data:
            graph_items = json_data.get("@graph", [])
            self._index_graph_items(graph_items)
            self._transform_jsonld(graph_items)
            return self.graph

        # SPARQL full mappings format (results -> bindings)
        if "results" in json_data and isinstance(json_data.get("results"), dict):
            bindings = json_data.get("results", {}).get("bindings", [])
            self._transform_sparql_bindings(bindings, source_path=source_path)
            return self.graph

        raise ValueError("Unsupported D3FEND JSON format")

    def _transform_jsonld(self, graph_items: list) -> None:
        """Transform D3FEND JSON-LD (@graph) into DefensiveTechnique nodes."""
        for item in graph_items:
            if not isinstance(item, dict):
                continue
            if not self._is_defensive_technique(item):
                continue

            d3fend_id = self._get_value(item.get("d3f:d3fend-id")) or self._get_value(item.get("d3f:d3fendId"))
            label = self._get_value(item.get("rdfs:label"))
            definition = self._get_value(item.get("d3f:definition"))

            if not d3fend_id:
                fallback_id = self._get_value(item.get("@id"))
                if not fallback_id:
                    continue
                d3fend_id = fallback_id

            # Normalize ID for safe URI creation, but preserve original as a literal
            normalized = self._normalize_d3fend_id(d3fend_id)
            technique_node = URIRef(f"{self.EX}deftech/{normalized}")

            self.graph.add((technique_node, RDF.type, self.SEC.DefensiveTechnique))
            # Store the original (potentially namespaced) id as a literal for provenance
            self.graph.add((technique_node, self.SEC.d3fendId, Literal(str(d3fend_id), datatype=XSD.string)))

            if label:
                self.graph.add((technique_node, RDFS.label, Literal(label, datatype=XSD.string)))

            if definition:
                self._add_single_string_value(technique_node, self.SEC.description, definition)

            self._add_phase_a_properties(technique_node, item)
            self._add_typed_kb_references(technique_node, item)
            self._add_phase_a_defensive_predicates(technique_node, item)

    def _index_graph_items(self, graph_items: list) -> None:
        """Index JSON-LD items by @id and precompute aliases for defensive techniques."""
        for item in graph_items:
            if not isinstance(item, dict):
                continue

            item_id = item.get("@id")
            if isinstance(item_id, str) and item_id:
                self._items_by_id[item_id] = item

            d3fend_id = self._get_value(item.get("d3f:d3fend-id")) or self._get_value(item.get("d3f:d3fendId"))
            if not d3fend_id:
                continue

            if isinstance(item_id, str) and item_id:
                local = item_id.split(":", 1)[-1] if ":" in item_id else item_id
                self._def_tech_alias_to_id[local] = str(d3fend_id)

            label = self._get_value(item.get("rdfs:label"))
            if isinstance(label, str) and label:
                self._def_tech_alias_to_id[label] = str(d3fend_id)
                compact = "".join(ch for ch in label if ch.isalnum()).lower()
                if compact:
                    self._def_tech_alias_to_id[compact] = str(d3fend_id)

    def _reference_uri(self, ref_id: str) -> URIRef:
        """Create stable reference URI from D3FEND reference @id."""
        token = ref_id
        if token.startswith("http://") or token.startswith("https://"):
            token = token.rstrip("/").rsplit("/", 1)[-1]
        if ":" in token:
            token = token.split(":", 1)[-1]
        return URIRef(f"{self.EX}reference/{self._normalize_d3fend_id(token)}")

    def _resource_uri(self, item_id: str) -> URIRef:
        """Create stable URI for non-deftech D3FEND resources."""
        token = item_id
        if token.startswith("http://") or token.startswith("https://"):
            token = token.rstrip("/").rsplit("/", 1)[-1]
        if ":" in token:
            token = token.split(":", 1)[-1]
        return URIRef(f"{self.EX}d3fentity/{self._normalize_d3fend_id(token)}")

    def _ensure_resource_node(self, item_id: str) -> URIRef | None:
        """Ensure a target D3FEND resource node exists for explicit assertion relations."""
        target_item = self._items_by_id.get(item_id)
        if not isinstance(target_item, dict):
            return None

        resource_node = self._resource_uri(item_id)

        item_types = target_item.get("@type")
        type_values = [item_types] if isinstance(item_types, str) else item_types if isinstance(item_types, list) else []
        for t in type_values:
            if not isinstance(t, str):
                continue
            local = t.split(":", 1)[-1] if ":" in t else t
            if local:
                self.graph.add((resource_node, RDF.type, URIRef(f"{self.SEC}{local}")))

        # Always include a stable umbrella type for rels-only label inference
        self.graph.add((resource_node, RDF.type, URIRef(f"{self.SEC}D3fendResource")))

        label = self._get_value(target_item.get("rdfs:label"))
        if isinstance(label, str) and label:
            self.graph.add((resource_node, RDFS.label, Literal(label, datatype=XSD.string)))

        description = self._get_value(target_item.get("d3f:definition"))
        if isinstance(description, str) and description:
            self.graph.add((resource_node, self.SEC.description, Literal(description, datatype=XSD.string)))

        self.graph.add((resource_node, self.SEC.sourceIdentifier, Literal(item_id, datatype=XSD.string)))
        return resource_node

    def _add_phase_a_properties(self, technique_node: URIRef, item: dict) -> None:
        """Add selected Phase A properties for DefensiveTechnique nodes."""
        source_identifier = item.get("@id")
        if isinstance(source_identifier, str) and source_identifier:
            self._add_single_string_value(technique_node, self.SEC.sourceIdentifier, source_identifier)

        status = self._get_value(item.get("d3f:status"))
        if isinstance(status, str) and status:
            self.graph.add((technique_node, self.SEC.status, Literal(status, datatype=XSD.string)))

        kb_article = self._get_value(item.get("d3f:kb-article"))
        if isinstance(kb_article, str) and kb_article:
            self.graph.add((technique_node, self.SEC.kbArticle, Literal(kb_article, datatype=XSD.string)))

        synonyms = item.get("d3f:synonym")
        synonym_values = synonyms if isinstance(synonyms, list) else [synonyms] if synonyms else []
        for synonym in synonym_values:
            synonym_text = self._get_value(synonym)
            if isinstance(synonym_text, str) and synonym_text:
                self.graph.add((technique_node, self.SEC.synonym, Literal(synonym_text, datatype=XSD.string)))

        see_also = item.get("rdfs:seeAlso")
        see_also_values = see_also if isinstance(see_also, list) else [see_also] if see_also else []
        for entry in see_also_values:
            target = self._get_value(entry)
            if isinstance(target, str) and (target.startswith("http://") or target.startswith("https://")):
                self.graph.add((technique_node, self.SEC.url, Literal(target, datatype=XSD.anyURI)))

    def _add_single_string_value(self, subject: URIRef, predicate: URIRef, value: str) -> None:
        """Add a string literal only if no value for this predicate exists yet."""
        if not isinstance(value, str) or not value:
            return
        if any(True for _ in self.graph.objects(subject, predicate)):
            return
        self.graph.add((subject, predicate, Literal(value, datatype=XSD.string)))

    def _add_typed_kb_references(self, technique_node: URIRef, item: dict) -> None:
        """Add typed reference nodes from D3FEND kb-reference / kb-reference-of assertions."""
        ref_values = []
        for key in ("d3f:kb-reference", "d3f:kb-reference-of"):
            value = item.get(key)
            if isinstance(value, list):
                ref_values.extend(value)
            elif value is not None:
                ref_values.append(value)

        for ref in ref_values:
            ref_id = self._get_value(ref)
            if not isinstance(ref_id, str) or not ref_id:
                continue

            ref_item = self._items_by_id.get(ref_id)
            ref_node = self._reference_uri(ref_id)

            self.graph.add((ref_node, RDF.type, self.SEC.Reference))

            if isinstance(ref_item, dict):
                ref_type = ref_item.get("@type")
                if isinstance(ref_type, list):
                    ref_type = next((t for t in ref_type if isinstance(t, str) and t.startswith("d3f:")), None)
                if isinstance(ref_type, str):
                    self.graph.add((ref_node, self.SEC.referenceType, Literal(ref_type.split(":", 1)[-1], datatype=XSD.string)))

                title = self._get_value(ref_item.get("d3f:kb-reference-title")) or self._get_value(ref_item.get("rdfs:label"))
                if isinstance(title, str) and title:
                    self.graph.add((ref_node, RDFS.label, Literal(title, datatype=XSD.string)))

                ref_url = self._get_value(ref_item.get("rdfs:seeAlso")) or self._get_value(ref_item.get("rdfs:isDefinedBy"))
                if isinstance(ref_url, str) and (ref_url.startswith("http://") or ref_url.startswith("https://")):
                    self.graph.add((ref_node, self.SEC.url, Literal(ref_url, datatype=XSD.anyURI)))

                organization = self._get_value(ref_item.get("d3f:kb-organization"))
                if isinstance(organization, str) and organization:
                    self.graph.add((ref_node, self.SEC.referenceSource, Literal(organization, datatype=XSD.string)))

            # Ensure each reference has at least one human-readable identifier
            if not any(True for _ in self.graph.objects(ref_node, RDFS.label)) and not any(True for _ in self.graph.objects(ref_node, self.SEC.url)):
                fallback_label = ref_id.split(":", 1)[-1] if ":" in ref_id else ref_id
                if fallback_label:
                    self.graph.add((ref_node, RDFS.label, Literal(fallback_label, datatype=XSD.string)))

            self.graph.add((technique_node, self.SEC.references, ref_node))

    def _resolve_phase_a_target(self, target_value) -> URIRef | None:
        """Resolve a target @id to a concrete node URI for Phase A explicit relations."""
        target = self._get_value(target_value)
        if not isinstance(target, str) or not target:
            return None

        target_item = self._items_by_id.get(target)
        if isinstance(target_item, dict):
            target_id = self._get_value(target_item.get("d3f:d3fend-id")) or self._get_value(target_item.get("d3f:d3fendId"))
            if isinstance(target_id, str) and target_id:
                return URIRef(f"{self.EX}deftech/{self._normalize_d3fend_id(target_id)}")

            resource_node = self._ensure_resource_node(target)
            if resource_node is not None:
                return resource_node

        token = target.split(":", 1)[-1] if ":" in target else target
        resolved = self._def_tech_alias_to_id.get(token)
        if resolved:
            return URIRef(f"{self.EX}deftech/{self._normalize_d3fend_id(resolved)}")

        compact = "".join(ch for ch in token if ch.isalnum()).lower()
        if compact:
            resolved_compact = self._def_tech_alias_to_id.get(compact)
            if resolved_compact:
                return URIRef(f"{self.EX}deftech/{self._normalize_d3fend_id(resolved_compact)}")

        return None

    def _add_phase_a_defensive_predicates(self, technique_node: URIRef, item: dict) -> None:
        """Add selected explicit defensive predicates from JSON-LD assertions.

        Phase A scope is conservative: emit only deftech-to-deftech edges where
        target resolves to canonical d3fend-id.
        """
        for key, rel_name in self.PHASE_A_DEFENSIVE_PREDICATES.items():
            value = item.get(f"d3f:{key}")
            if value is None:
                continue

            values = value if isinstance(value, list) else [value]
            rel_predicate = URIRef(f"{self.SEC}{rel_name}")

            for candidate in values:
                target_node = self._resolve_phase_a_target(candidate)
                if not target_node:
                    continue
                self.graph.add((technique_node, rel_predicate, target_node))

    def _load_def_tech_alias_index(self, source_path: str | None = None) -> None:
        """Load mapping from D3FEND ontology local names/labels to canonical d3fend-id.

        Uses authoritative d3fend.json when present, preferably from the same directory
        as the source mappings file.
        """
        if self._def_tech_alias_index_loaded:
            return

        candidate_paths = []
        if source_path:
            src = Path(source_path)
            candidate_paths.append(src.parent / "d3fend.json")
        candidate_paths.append(Path("data/d3fend/raw/d3fend.json"))

        d3fend_json_path = None
        for candidate in candidate_paths:
            if candidate and candidate.exists():
                d3fend_json_path = candidate
                break

        self._def_tech_alias_index_loaded = True
        if not d3fend_json_path:
            return

        try:
            with open(d3fend_json_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
        except Exception:
            return

        graph_items = data.get("@graph", []) if isinstance(data, dict) else []
        for item in graph_items:
            if not isinstance(item, dict):
                continue

            d3fend_id = self._get_value(item.get("d3f:d3fend-id")) or self._get_value(item.get("d3f:d3fendId"))
            if not d3fend_id:
                continue

            id_value = item.get("@id")
            if isinstance(id_value, str) and id_value:
                local = id_value.split(":", 1)[-1] if ":" in id_value else id_value
                if local:
                    self._def_tech_alias_to_id[local] = str(d3fend_id)

            label = self._get_value(item.get("rdfs:label"))
            if isinstance(label, str) and label:
                self._def_tech_alias_to_id[label] = str(d3fend_id)
                self._def_tech_alias_to_id["".join(ch for ch in label if ch.isalnum()).lower()] = str(d3fend_id)

    def _resolve_def_tech_id(self, binding: dict) -> str | None:
        """Resolve canonical D3FEND id from a SPARQL binding row."""
        def_tech_id = None
        def_tech_alias = None

        if "def_tech" in binding and isinstance(binding["def_tech"], dict):
            def_tech_value = binding["def_tech"].get("value")
            if isinstance(def_tech_value, str) and def_tech_value.strip():
                token = def_tech_value.strip()
                if "#" in token:
                    token = token.rsplit("#", 1)[-1]
                elif "/" in token:
                    token = token.rstrip("/").rsplit("/", 1)[-1]
                def_tech_alias = token or None

        if "def_tech_id" in binding and isinstance(binding["def_tech_id"], dict):
            def_tech_id = binding["def_tech_id"].get("value") or def_tech_id

        if "d3fend_id" in binding and isinstance(binding["d3fend_id"], dict):
            def_tech_id = binding["d3fend_id"].get("value") or def_tech_id

        if not def_tech_id and def_tech_alias:
            def_tech_id = self._def_tech_alias_to_id.get(def_tech_alias)

        if not def_tech_id and "def_tech_label" in binding and isinstance(binding["def_tech_label"], dict):
            label = binding["def_tech_label"].get("value")
            if isinstance(label, str):
                compact = "".join(ch for ch in label if ch.isalnum()).lower()
                def_tech_id = self._def_tech_alias_to_id.get(label) or self._def_tech_alias_to_id.get(compact)

        if not def_tech_id and def_tech_alias:
            # Last-resort fallback for datasets that already use stable local IDs.
            def_tech_id = def_tech_alias

        return def_tech_id

    def _transform_sparql_bindings(self, bindings: list, source_path: str | None = None) -> None:
        """Transform SPARQL full mappings (D3FEND to ATT&CK) into mitigates relationships."""
        self._load_def_tech_alias_index(source_path=source_path)

        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            
            def_tech_id = self._resolve_def_tech_id(binding)
            
            att_tech_id = None
            if "off_tech_id" in binding and isinstance(binding["off_tech_id"], dict):
                att_tech_id = binding["off_tech_id"].get("value")
            
            # If we have both, create a mitigates relationship
            if def_tech_id and att_tech_id:
                # Normalize IDs
                att_id_full = f"{att_tech_id}" if str(att_tech_id).startswith("T") else f"T{att_tech_id}"
                def_tech_uri = self._normalize_d3fend_id(def_tech_id)

                def_tech_node = URIRef(f"{self.EX}deftech/{def_tech_uri}")
                att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                
                # Add the mitigates relationship
                self.graph.add((def_tech_node, self.SEC.mitigates, att_node))

    def _is_defensive_technique(self, item: dict) -> bool:
        types = item.get("@type")
        if isinstance(types, str):
            types = [types]

        if isinstance(types, list) and "d3f:DefensiveTechnique" in types:
            return True

        sub_classes = item.get("rdfs:subClassOf")
        if isinstance(sub_classes, dict):
            sub_classes = [sub_classes]

        if isinstance(sub_classes, list):
            for sub in sub_classes:
                if isinstance(sub, dict) and sub.get("@id") == "d3f:DefensiveTechnique":
                    return True

        # Some D3FEND JSON-LD represents techniques as owl:Class entries with
        # properties like d3f:d3fend-id or d3f:definition rather than explicit
        # type annotations. Treat presence of d3fend-id or definition as an
        # indicator of a defensive technique.
        if item.get("d3f:d3fend-id") or item.get("d3f:d3fendId"):
            return True
        if item.get("d3f:definition") or item.get("d3f:attack-id"):
            return True

        return False

    def _get_value(self, value):
        if isinstance(value, dict):
            return value.get("@value") or value.get("@id") or value.get("value")
        return value

    def _add_defensive_technique(self, technique: dict):
        """Add a D3FEND defensive technique node, with status, references, and tags."""
        d3fend_id = technique.get("ID", "")
        if not d3fend_id:
            return
        normalized = self._normalize_d3fend_id(d3fend_id)
        technique_node = URIRef(f"{self.EX}deftech/{normalized}")
        self.graph.add((technique_node, RDF.type, self.SEC.DefensiveTechnique))
        # preserve original as literal
        self.graph.add((technique_node, self.SEC.d3fendId, Literal(str(d3fend_id), datatype=XSD.string)))

        if technique.get("Name"):
            self.graph.add((technique_node, RDFS.label, Literal(technique["Name"], datatype=XSD.string)))

        if technique.get("Description"):
            desc_text = self._extract_description(technique["Description"])
            if desc_text:
                self.graph.add((technique_node, self.SEC.description, Literal(desc_text, datatype=XSD.string)))

        # Emit status if present
        if technique.get("Status"):
            self.graph.add((technique_node, self.SEC.status, Literal(technique["Status"], datatype=XSD.string)))

        # Emit tags if present (as repeated sec:tag literals)
        tags = technique.get("Tags")
        if tags:
            if isinstance(tags, str):
                self.graph.add((technique_node, self.SEC.tag, Literal(tags, datatype=XSD.string)))
            elif isinstance(tags, list):
                for tag in tags:
                    if tag:
                        self.graph.add((technique_node, self.SEC.tag, Literal(str(tag), datatype=XSD.string)))

        # Emit references if present (as nodes)
        import hashlib
        for ref in technique.get("References", []):
            url = ref.get("URL") or ref.get("url")
            ref_type = ref.get("ReferenceType") or ref.get("referenceType")
            ref_text = ref.get("title") or ref.get("Title") or ref.get("description") or ref.get("text")
            if not (url or ref_type or ref_text):
                continue
            id_source = (url or ref_type or ref_text or "").strip()
            digest = hashlib.sha1(id_source.encode('utf-8')).hexdigest()[:12]
            # Use normalized id for stable, safe reference node ids
            ref_parent = normalized if 'normalized' in locals() else self._normalize_d3fend_id(d3fend_id)
            ref_id = f"{ref_parent}-ref-{digest}"
            ref_node = URIRef(f"{self.EX}reference/{ref_id}")
            self.graph.add((ref_node, RDF.type, self.SEC.Reference))
            if url:
                self.graph.add((ref_node, self.SEC.url, Literal(url, datatype=XSD.anyURI)))
            if ref_type:
                self.graph.add((ref_node, self.SEC.referenceType, Literal(ref_type, datatype=XSD.string)))
            if ref_text:
                self.graph.add((ref_node, RDFS.label, Literal(ref_text, datatype=XSD.string)))
            self.graph.add((technique_node, self.SEC.references, ref_node))

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

    def _add_technique_relationships(self, techniques: list):
        """Add parent/child relationships between defensive techniques."""
        for technique in techniques:
            d3fend_id = technique.get("ID", "")
            if not d3fend_id:
                continue

            normalized = self._normalize_d3fend_id(d3fend_id)
            technique_node = URIRef(f"{self.EX}deftech/{normalized}")

            if technique.get("ParentID"):
                parent_id = technique["ParentID"]
                parent_norm = self._normalize_d3fend_id(parent_id)
                parent_node = URIRef(f"{self.EX}deftech/{parent_norm}")
                self.graph.add((technique_node, self.SEC.childOf, parent_node))
                self.graph.add((parent_node, self.SEC.parentOf, technique_node))

    def _add_mitigation_relationships(self, techniques: list):
        """Add mitigates relationships to ATT&CK techniques."""
        for technique in techniques:
            d3fend_id = technique.get("ID", "")
            if not d3fend_id:
                continue

            normalized = self._normalize_d3fend_id(d3fend_id)
            technique_node = URIRef(f"{self.EX}deftech/{normalized}")

            if technique.get("MitigatesTechniques"):
                for att_technique in technique["MitigatesTechniques"]:
                    att_id = att_technique if isinstance(att_technique, str) else att_technique.get("ID", "")
                    if att_id:
                        att_id_full = f"{att_id}" if att_id.startswith("T") else f"T{att_id}"
                        att_node = URIRef(f"{self.EX}technique/{att_id_full}")
                        self.graph.add((technique_node, self.SEC.mitigates, att_node))


def main():
    parser = argparse.ArgumentParser(description="ETL: MITRE D3FEND JSON -> RDF Turtle")
    parser.add_argument("--input", "-i", required=True, help="Input D3FEND JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output Turtle file")
    parser.add_argument("--nodes-out", help="Optional nodes-only output file")
    parser.add_argument("--rels-out", help="Optional relationships-only output file")
    parser.add_argument("--rels-include-types", action="store_true", help="Also write rdf:type triples to rels output")
    parser.add_argument("--append", action='store_true', help='Append to existing output file (suppress headers)')
    parser.add_argument('--validate', action='store_true', help='Validate output with SHACL')
    parser.add_argument('--shapes', help='SHACL shapes file (defaults to docs/ontology/shacl/d3fend-shapes.ttl)')
    parser.add_argument("--format", choices=["ttl","nt"], default="ttl", help="Output format (ttl or nt)")
    
    args = parser.parse_args()

    if (args.nodes_out and not args.rels_out) or (args.rels_out and not args.nodes_out):
        print("Error: --nodes-out and --rels-out must be provided together", file=sys.stderr)
        return 1
    
    # Accept either a single JSON file or a directory containing multiple D3FEND JSON files
    json_files = []
    if os.path.isdir(args.input):
        for p in sorted(Path(args.input).rglob('*.json')):
            # Skip per-directory metadata files (created by downloader)
            if p.name.lower() == 'metadata.json':
                continue
            json_files.append(str(p))
    else:
        json_files = [args.input]

    transformer = D3FENDtoRDFTransformer()
    any_loaded = False
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8', errors='replace') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Warning: Error loading JSON {jf}: {e}")
            continue
        any_loaded = True
        print(f"Transforming {os.path.basename(jf)} to RDF...")
        try:
            transformer.transform(json_data, source_path=jf)
        except Exception as e:
            print(f"Warning: transformation failed for {jf}: {e}")

    if not any_loaded:
        print(f"Error: no D3FEND JSON files loaded from {args.input}")
        return 1

    # Write the combined graph to output
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing RDF to {args.output}...")
    if args.format == "nt":
        write_graph_ntriples_lines(transformer.graph, args.output, append=args.append)
    else:
        write_graph_turtle_lines(transformer.graph, args.output, include_prefixes=not args.append, append=args.append)

    if args.nodes_out and args.rels_out:
        Path(args.nodes_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.rels_out).parent.mkdir(parents=True, exist_ok=True)
        if args.format == "nt":
            write_graph_ntriples_split_lines(
                transformer.graph,
                args.nodes_out,
                args.rels_out,
                append=args.append,
                rels_include_types=args.rels_include_types,
            )
        else:
            write_graph_turtle_split_lines(
                transformer.graph,
                args.nodes_out,
                args.rels_out,
                include_prefixes=not args.append,
                append=args.append,
                rels_include_types=args.rels_include_types,
            )

    # SHACL validation
    if args.validate:
        print(f"\nValidating {args.output}...")
        try:
            from src.core.validation import run_validator, load_graph
        except ImportError:
            from core.validation import run_validator, load_graph

        shapes_file = args.shapes or 'docs/ontology/shacl/d3fend-shapes.ttl'
        if os.path.exists(shapes_file):
            shapes = load_graph(shapes_file)
            conforms, _, _ = run_validator(args.output, shapes)
            if conforms:
                print(f"[OK] Validation passed!")
            else:
                print(f"[FAIL] Validation failed!")
                return 1
        else:
            print(f"Warning: Could not find shapes file: {shapes_file}")

    print(f"Transformation complete: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
