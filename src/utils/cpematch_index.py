import json
import os
from pathlib import Path
import ijson


def _iter_cpematch_files(path: str):
    if os.path.isdir(path):
        for p in sorted(Path(path).rglob('*.json')):
            yield str(p)
    else:
        yield path


def build_cpematch_index(path: str) -> dict:
    """Build a mapping from CPE match `criteria` -> `matchCriteriaId` by scanning cpematch JSON files."""
    criteria_to_match_id = {}
    for file_path in _iter_cpematch_files(path):
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='utf-8') as fh:
            for item in ijson.items(fh, 'matchStrings.item'):
                ms = item.get('matchString') if isinstance(item, dict) else None
                if not isinstance(ms, dict):
                    ms = item if isinstance(item, dict) else None
                if not ms:
                    continue
                criteria = ms.get('criteria')
                match_id = ms.get('matchCriteriaId')
                if criteria and match_id and criteria not in criteria_to_match_id:
                    criteria_to_match_id[criteria] = match_id
    return criteria_to_match_id


def save_index(path: str, index: dict) -> None:
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(index, fh)
    os.replace(tmp, path)


def load_index(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)
