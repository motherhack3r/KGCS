#!/usr/bin/env python3
"""Normalize merged SHIELD JSON into schema expected by src.etl.etl_shield.

Reads: data/shield/raw/shield.json
Writes: data/shield/raw/shield.normalized.json
"""
import json
from pathlib import Path

in_path = Path("data/shield/raw/shield.json")
out_path = Path("data/shield/raw/shield.normalized.json")

if not in_path.exists():
    print(f"Input not found: {in_path}")
    raise SystemExit(2)

with in_path.open("r", encoding="utf-8") as fh:
    j = json.load(fh)

# Expecting j to be {"DeceptionTechniques": [...]} or a top-level object with that key.
if isinstance(j, dict) and "DeceptionTechniques" in j:
    items = j["DeceptionTechniques"]
elif isinstance(j, dict) and any(isinstance(v, list) for v in j.values()):
    # fallback: pick the first list value
    lists = [v for v in j.values() if isinstance(v, list)]
    items = lists[0] if lists else []
elif isinstance(j, list):
    items = j
else:
    items = []

out_items = []
for it in items:
    # it may use lowercase keys: 'id','name','description','techniques'
    if not isinstance(it, dict):
        continue
    shield_id = it.get("ID") or it.get("id") or it.get("Id") or ""
    name = it.get("Name") or it.get("name") or it.get("title") or ""
    description = it.get("Description") or it.get("description") or ""
    counters = []
    # techniques may be a list of dicts with 'technique_id' or similar
    techniques = it.get("CountersTechniques") or it.get("techniques") or it.get("technique") or []
    if isinstance(techniques, list):
        for t in techniques:
            if isinstance(t, str):
                counters.append(t)
            elif isinstance(t, dict):
                tid = t.get("ID") or t.get("id") or t.get("technique_id") or t.get("techniqueId")
                if tid:
                    counters.append(tid)
    # normalize to expected fields
    out_items.append({
        "ID": shield_id,
        "Name": name,
        "Description": description,
        "CountersTechniques": counters
    })

out = {"DeceptionTechniques": out_items}
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print(f"Wrote normalized SHIELD JSON: {out_path} (items: {len(out_items)})")
