#!/usr/bin/env python3
"""
WireG - Modern WireGuard Client for Linux
Usage:
    python3 main.py
"""

import sys
from pathlib import Path

# Ensure root package is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from wireg.app import run_app

if __name__ == "__main__":
    sys.exit(run_app())
