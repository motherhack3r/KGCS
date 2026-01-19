"""Simple ingest stub demonstrating pre-ingest SHACL validation gate.

Usage:
  python scripts/ingest_stub.py data/shacl-samples/good-example.ttl

If validation passes, the stub simulates indexing the data.
"""
import sys
import subprocess


def run_validator(data_file):
    res = subprocess.run(['python', 'scripts/validate_shacl.py', data_file], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode == 0:
        return True
    else:
        print('Validation failed. Aborting ingest.')
        print(res.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/ingest_stub.py <data-file.ttl>')
        sys.exit(2)
    data_file = sys.argv[1]
    ok = run_validator(data_file)
    if not ok:
        sys.exit(1)
    # Simulate indexing
    print(f'Indexing {data_file}... (simulated)')
    print('Done.')

if __name__ == '__main__':
    main()
