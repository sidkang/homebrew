#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$MODULE_DIR"
uv run build.py
uv run verify.py
