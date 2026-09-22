#!/usr/bin/env bash
# Deploy USGate Portal on a VPS (placeholders only — edit before use).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "==> Creating .env from env.example (edit secrets before production!)"
  cp env.example .env
  # Generate a random session secret if still placeholder
  if grep -q 'CHANGE_ME_TO_A_LONG_RANDOM_STRING' .env; then
    SECRET=$(openssl rand -hex 32)
    sed -i.bak "s/CHANGE_ME_TO_A_LONG_RANDOM_STRING_64chars_min/${SECRET}/" .env || \
      sed -i '' "s/CHANGE_ME_TO_A_LONG_RANDOM_STRING_64chars_min/${SECRET}/" .env
    rm -f .env.bak
  fi
  echo "    Edit .env: set MOCK_XUI=false, XUI_*, BOOTSTRAP_ADMIN_PASSWORD, APP_SECRET_KEY"
fi

echo "==> Building and starting portal (docker compose)"
docker compose pull || true
docker compose build
docker compose up -d

echo "==> Health check"
sleep 2
curl -fsS "http://127.0.0.1:${PORTAL_HOST_PORT:-8080}/healthz" || {
  echo "Health check failed — see: docker compose logs portal"
  exit 1
}

echo ""
echo "Portal is up."
echo "  Local:  http://127.0.0.1:${PORTAL_HOST_PORT:-8080}/"
echo "  Demo user (mock): demo / demo1234"
echo "  Admin:  BOOTSTRAP_ADMIN_USER / BOOTSTRAP_ADMIN_PASSWORD from .env"
echo ""
echo "For HTTPS: set PORTAL_DOMAIN, uncomment caddy in docker-compose.yml, re-run."
