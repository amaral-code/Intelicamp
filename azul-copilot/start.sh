#!/usr/bin/env bash
set -euo pipefail
PORT=${PORT:-5001}
cd "$(dirname "$0")"
python app.py
