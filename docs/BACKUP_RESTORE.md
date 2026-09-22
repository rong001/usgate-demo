# Backup & restore — portal

## What to back up

| Path / item | MOCK public demo | LIVE instance |
|-------------|------------------|---------------|
| App tree | `/opt/usgate-portal-demo/` (exclude `.venv` optional) | deploy path |
| SQLite DB | `data/usgate.db` | same relative path |
| Private `.env` | **off-git** vault only | **off-git** vault only |
| Caddyfile / systemd units | `/etc/systemd/system/usgate-portal-*.service`, Caddyfile | same pattern |
| LE certs | managed by certbot (`/etc/letsencrypt/`) | same |

Never commit `.env`, DB dumps with session secrets, or panel passwords.

## Backup (example)

```bash
# on VPS — MOCK demo
ts=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p /root/usgate-backups
tar -C /opt -czf /root/usgate-backups/portal-demo-app-$ts.tgz \
  --exclude='usgate-portal-demo/.venv' usgate-portal-demo
# keep .env out of shared tarballs when possible; copy separately with mode 600
install -m 600 /opt/usgate-portal-demo/.env /root/usgate-backups/portal-demo.env-$ts
```

## Restore

```bash
systemctl stop usgate-portal-demo
# restore app + data from tarball; restore .env with mode 600
tar -C /opt -xzf /root/usgate-backups/portal-demo-app-YYYYMMDD….tgz
install -m 600 /root/usgate-backups/portal-demo.env-YYYYMMDD… /opt/usgate-portal-demo/.env
# reinstall deps if .venv omitted
cd /opt/usgate-portal-demo && .venv/bin/pip install -r requirements.txt
systemctl start usgate-portal-demo
curl -sS https://117.55.227.224:8443/healthz   # expect mock_xui:true on public demo
```

## MOCK data reset (not a restore)

Admin `POST /admin/demo-reset` or `portal/scripts/reset_mock_demo.py` reseeds **synthetic** users only. Refused when `MOCK_XUI=false`.

## LIVE panel

Restoring portal DB does **not** recreate panel clients. After restore, reconcile portal users with 3X-UI (or re-run admin create) — see `REAL_PANEL_ACCEPTANCE.md` (BLOCKED until credentials confirmed).
