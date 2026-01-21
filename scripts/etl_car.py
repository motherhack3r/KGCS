#!/usr/bin/env python3
"""Wrapper: forward to `scripts/etl/etl_car.py` in the reorganized layout."""
import os
import sys
import subprocess


def main():
    script = os.path.join(os.path.dirname(__file__), 'etl', 'etl_car.py')
    return subprocess.call([sys.executable, script] + sys.argv[1:])


if __name__ == '__main__':
    sys.exit(main())
