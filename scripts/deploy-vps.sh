#!/usr/bin/env bash
# Deploy USGate portal to a VPS — PLACEHOLDERS ONLY.
# Usage:
#   ./scripts/deploy-vps.sh            # print plan + optional local compose
#   ./scripts/deploy-vps.sh --remote   # rsync + ssh (requires env below)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-VPS_IP}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/opt/usgate-demo}"
SSH_PORT="${SSH_PORT:-22}"

usage() {
  cat <<USAGE
USGate demo deploy helper (no secrets baked in).

Environment (for --remote):
  REMOTE_HOST   default: VPS_IP
  REMOTE_USER   default: root
  REMOTE_DIR    default: /opt/usgate-demo
  SSH_PORT      default: 22

Steps this script documents/runs:
  1. Ensure portal/.env exists (from env.example)
  2. docker compose build && up on target
  3. curl healthz

Examples:
  # Local demo
  (cd "$ROOT/portal" && cp -n env.example .env && ./deploy.sh)

  # Remote (after you replace VPS_IP and have SSH keys)
  REMOTE_HOST=203.0.113.10 $0 --remote
USAGE
}

cmd="${1:-}"
if [[ "$cmd" == "-h" || "$cmd" == "--help" ]]; then
  usage
  exit 0
fi

echo "==> Plan"
echo "    Root:        $ROOT"
echo "    Remote:      ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR} (port ${SSH_PORT})"
echo "    Portal env:  $ROOT/portal/.env"

if [[ "$cmd" != "--remote" ]]; then
  echo ""
  echo "==> Local path: running portal/deploy.sh"
  (cd "$ROOT/portal" && ./deploy.sh)
  exit 0
fi

if [[ "$REMOTE_HOST" == "VPS_IP" ]]; then
  echo "ERROR: Set REMOTE_HOST to a real host (not placeholder VPS_IP)." >&2
  exit 1
fi

echo "==> Rsync portal (excludes .env from overwrite if present on remote — we copy example)"
rsync -az --delete \
  --exclude '.env' \
  --exclude 'data/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  -e "ssh -p ${SSH_PORT}" \
  "$ROOT/portal/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/portal/"

ssh -p "${SSH_PORT}" "${REMOTE_USER}@${REMOTE_HOST}" bash -s <<REMOTE
set -euo pipefail
cd "${REMOTE_DIR}/portal"
if [[ ! -f .env ]]; then
  cp env.example .env
  echo "Created .env from example — EDIT secrets on the server before production."
fi
chmod +x deploy.sh
./deploy.sh
REMOTE

echo "==> Done. Open http://${REMOTE_HOST}:8080/ or your PORTAL_DOMAIN via Caddy."
