#!/usr/bin/env python3
"""Normalize merged ENGAGE JSON into schema expected by src.etl.etl_engage.

Reads: data/engage/raw/engage.json
Writes: data/engage/raw/engage.normalized.json
"""
import json
from pathlib import Path

in_path = Path("data/engage/raw/engage.json")
out_path = Path("data/engage/raw/engage.normalized.json")

if not in_path.exists():
    print(f"Input not found: {in_path}")
    raise SystemExit(2)

with in_path.open("r", encoding="utf-8") as fh:
    j = json.load(fh)

if isinstance(j, dict) and "EngagementConcepts" in j:
    items = j["EngagementConcepts"]
elif isinstance(j, dict) and any(isinstance(v, list) for v in j.values()):
    lists = [v for v in j.values() if isinstance(v, list)]
    items = lists[0] if lists else []
elif isinstance(j, list):
    items = j
else:
    items = []

out_items = []
for it in items:
    if not isinstance(it, dict):
        continue
    engage_id = it.get("ID") or it.get("id") or ""
    name = it.get("Name") or it.get("name") or ""
    description = it.get("Description") or it.get("description") or ""
    strategic = it.get("StrategicValue") or it.get("strategicValue") or it.get("strategic_value") or ""
    category = it.get("Category") or it.get("category") or ""

    disrupts = []
    disruptions = it.get("DisruptsTechniques") or it.get("disrupts") or it.get("techniques") or []
    if isinstance(disruptions, list):
        for t in disruptions:
            if isinstance(t, str):
                disrupts.append(t)
            elif isinstance(t, dict):
                tid = t.get("ID") or t.get("id") or t.get("technique_id")
                if tid:
                    disrupts.append(tid)

    out_items.append({
        "ID": engage_id,
        "Name": name,
        "Description": description,
        "StrategicValue": strategic,
        "Category": category,
        "DisruptsTechniques": disrupts,
    })

out = {"EngagementConcepts": out_items}
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print(f"Wrote normalized ENGAGE JSON: {out_path} (items: {len(out_items)})")
