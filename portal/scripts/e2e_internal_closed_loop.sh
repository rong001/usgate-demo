#!/usr/bin/env bash
# Run INTERNAL_CLOSED_LOOP MOCK suite; optional DOCS_OUT.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export MOCK_XUI=true
export MOCK_XUI_FALLBACK=false
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
set +e
"$PY" tests/e2e_internal_closed_loop.py | tee /tmp/usgate_icl.out
RC=${PIPESTATUS[0]}
set -e
if [[ -n "${DOCS_OUT:-}" ]]; then
  mkdir -p "$(dirname "$DOCS_OUT")"
  {
    echo "# INTERNAL_CLOSED_LOOP (portal slice)"
    echo
    echo "**Date (UTC):** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "**Mode:** MOCK_XUI=true"
    echo "**Command:** \`scripts/e2e_internal_closed_loop.sh\` → \`tests/e2e_internal_closed_loop.py\`"
    echo
    awk '/^## INTERNAL_CLOSED_LOOP RESULTS/,0' /tmp/usgate_icl.out
    echo
    if [[ $RC -eq 0 ]]; then echo "**Portal ICL Overall:** PASS"; else echo "**Portal ICL Overall:** FAIL"; fi
  } > "$DOCS_OUT"
  echo "Wrote $DOCS_OUT"
fi
exit $RC
