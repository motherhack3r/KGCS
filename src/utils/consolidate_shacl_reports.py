"""Consolidate SHACL validation reports into a single summary."""

import json
import glob
import os

def consolidate_reports(report_dir: str = 'artifacts', output_file: str = 'artifacts/shacl-report-consolidated.json'):
    """Consolidate all SHACL reports in a directory into one file."""
    reports = sorted(glob.glob(os.path.join(report_dir, 'shacl-report-*.json')))
    out = []
    for p in reports:
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            data = {'_error': str(e)}
        out.append({'file': os.path.basename(p), 'data': data})

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=2)

    print(f'Wrote {output_file} with {len(out)} entries')
    return output_file


if __name__ == '__main__':
    consolidate_reports()
