#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
cd "$SCRIPT_DIR"
uv run jupyter lab
