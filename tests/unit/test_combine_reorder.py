from pathlib import Path
from scripts.combine_ttl_pipeline import _reorder_nodes_grouped


def test_reorder_nodes_grouped(tmp_path):
    nodes_file = tmp_path / "nodes.ttl"
    lines = [
        '@prefix sec: <https://example.org/sec/core#> .\n',
        '<https://example.org/s1> <https://example.org/prop1> "value1" .\n',
        '<https://example.org/s2> <https://example.org/prop1> "value2" .\n',
        '<https://example.org/s1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://example.org/sec/core#Type1> .\n',
        '<https://example.org/s2> a <https://example.org/sec/core#Type2> .\n'
    ]
    nodes_file.write_text(''.join(lines), encoding='utf-8')

    _reorder_nodes_grouped(str(nodes_file), buckets=8)

    out = nodes_file.read_text(encoding='utf-8').splitlines()
    # skip prefix line
    data_lines = [l for l in out if not l.startswith('@') and l.strip()]

    # Group lines by subject and assert type line is first for each subject
    groups = {}
    for l in data_lines:
        subj = l.split(' ', 1)[0]
        groups.setdefault(subj, []).append(l)

    for subj, glines in groups.items():
        first_pred = glines[0].split(' ', 2)[1]
        assert (first_pred == 'a') or ('#type' in first_pred.lower()) or ('rdf:type' in first_pred.lower())
