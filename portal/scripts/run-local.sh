#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
[[ -f .env ]] || cp env.example .env
mkdir -p data
export MOCK_XUI="${MOCK_XUI:-true}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8080}" --reload
