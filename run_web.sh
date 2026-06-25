#!/usr/bin/env bash
# Launch the NGS pipeline web UI. Must be run from the repo root.
set -euo pipefail
cd "$(dirname "$0")"
python -m web.app
