#!/usr/bin/env bash
set -euo pipefail
PORT=${PORT:-5001}
PORT_FALLBACK=${PORT_FALLBACK:-false}
export PORT PORT_FALLBACK
cd "$(dirname "$0")"
echo "Starting app in $(pwd) on PORT=${PORT} (PORT_FALLBACK=${PORT_FALLBACK})"
python app.py
