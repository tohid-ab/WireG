#!/usr/bin/env bash
# Quick start script for WireG
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 main.py "$@"
