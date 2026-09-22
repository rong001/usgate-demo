#!/usr/bin/env bash
# Run MOCK E2E suite; write docs/MOCK_E2E_RESULTS.md when DOCS_OUT is set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export MOCK_XUI=true
export MOCK_XUI_FALLBACK=false
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
OUT="${E2E_OUT:-}"
set +e
"$PY" tests/e2e_mock.py | tee /tmp/usgate_e2e_mock.out
RC=${PIPESTATUS[0]}
set -e
if [[ -n "${DOCS_OUT:-}" ]]; then
  mkdir -p "$(dirname "$DOCS_OUT")"
  {
    echo "# MOCK_E2E_RESULTS"
    echo
    echo "**Date (UTC):** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "**Mode:** MOCK_XUI=true"
    echo "**Command:** \`scripts/e2e_mock.sh\` → \`tests/e2e_mock.py\`"
    echo
    # extract table from output
    awk '/^## MOCK E2E RESULTS/,0' /tmp/usgate_e2e_mock.out
    echo
    if [[ $RC -eq 0 ]]; then echo "**Overall:** PASS"; else echo "**Overall:** FAIL"; fi
  } > "$DOCS_OUT"
  echo "Wrote $DOCS_OUT"
fi
exit $RC
