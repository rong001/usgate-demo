# Deploy & rollback — portal

## Local / Docker

```bash
cd portal
cp env.example .env   # edit; never commit
./deploy.sh
# or: docker compose up -d --build
```

Rollback Docker: `docker compose down && git checkout <sha> -- portal && docker compose up -d --build`

## Public MOCK demo (VPS `117.55.227.224:8443`)

Path: `/opt/usgate-portal-demo/`  
Units: `usgate-portal-demo.service`, `usgate-portal-caddy.service`  
**Invariant:** `MOCK_XUI=true` always on this instance.

### Deploy (app only — keep Caddy/TLS)

```bash
# on operator machine (example)
# IMPORTANT: preserve VPS-only Caddyfile.demo (or ship portal/Caddyfile.demo from repo).
# Prefer --exclude over blind --delete of host-only TLS config.
rsync -a --delete \
  --exclude '.venv' --exclude 'data' --exclude '.env' \
  --exclude 'Caddyfile.demo' \
  portal/ root@117.55.227.224:/opt/usgate-portal-demo/
# If deploying Caddyfile.demo from repo instead:
# rsync -a portal/Caddyfile.demo root@117.55.227.224:/opt/usgate-portal-demo/Caddyfile.demo
ssh root@117.55.227.224 'cd /opt/usgate-portal-demo && .venv/bin/pip install -r requirements.txt && systemctl restart usgate-portal-demo'
# Do NOT restart x-ui. Reload Caddy only if Caddyfile.demo changed:
# systemctl reload usgate-portal-caddy   # or restart if reload unsupported
```

Verify:

```bash
curl -sS https://117.55.227.224:8443/healthz
# expect mock_xui:true
curl -sS -o /dev/null -w 'ssl_verify_result=%{ssl_verify_result}\n' https://117.55.227.224:8443/healthz
# expect 0
```

### Rollback

```bash
ssh root@117.55.227.224
cd /opt/usgate-portal-demo
# if you keep a sibling backup:
# rsync -a /opt/usgate-portal-demo.bak/ /opt/usgate-portal-demo/
# or: git checkout <previous-sha> in a deploy clone, then rsync
systemctl restart usgate-portal-demo
curl -sS https://127.0.0.1:8080/healthz   # via local bind
```

Keep `/opt/usgate-portal-demo/data/usgate.db` unless intentionally resetting MOCK data (`scripts/reset_mock_demo.py` or admin demo-reset).

## Live panel instance (separate from public demo)

1. Human confirms panel credentials via secure channel (see `REAL_PANEL_ACCEPTANCE.md`).
2. Copy `env.example` → private `.env`: `MOCK_XUI=false`, `MOCK_XUI_FALLBACK=false`, real `XUI_*`.
3. Deploy behind TLS; never expose panel ports to customers.
4. Rollback = restore previous app tree + previous `.env` backup (secrets stay off git).
