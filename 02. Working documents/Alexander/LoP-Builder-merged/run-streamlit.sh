#!/usr/bin/env bash
# Run the LoP Streamlit app in *your own terminal* (Terminal.app / iTerm) so it
# keeps running. Starting it from a Cursor agent background job stops when that job ends.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Repo root = Gold Standard LOP Builder - Documents (three levels above this folder)
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON="${REPO_ROOT}/.venvs/hamdi-app/bin/python"
APP="${SCRIPT_DIR}/src/app.py"
if [[ ! -x "$PYTHON" ]]; then
  echo "Missing venv at: $PYTHON"
  echo "Create it from repo root: python3 -m venv .venvs/hamdi-app && .venvs/hamdi-app/bin/pip install -r \"$SCRIPT_DIR/src/requirements.txt\""
  exit 1
fi
exec "$PYTHON" -m streamlit run "$APP" --server.address 127.0.0.1 --server.port 8501
