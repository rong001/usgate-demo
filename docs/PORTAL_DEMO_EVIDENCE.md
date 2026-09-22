# PORTAL_DEMO_EVIDENCE — public MOCK HTTPS demo

**Date (UTC):** 2026-09-22  
**Operator:** Grok Bot (executor)  
**Environment:** `MOCK` (`MOCK_XUI=true`) — isolated from real 3X-UI  
**Demo URL:** https://117.55.227.224:8443/  
**Deploy path on VPS:** `/opt/usgate-portal-demo/`  
**TLS:** Let's Encrypt IP shortlived certs at `/etc/letsencrypt/live/117.55.227.224/` via Caddy on **:8443** → uvicorn `127.0.0.1:8080`  
**systemd:** `usgate-portal-demo.service`, `usgate-portal-caddy.service` (enabled)  
**Cert renew:** `/etc/letsencrypt/renewal-hooks/deploy/reload-usgate-portal-caddy.sh` (does not alter x-ui)

> **DEMO-ONLY accounts** (disposable; not production):

| Account | Password | Role |
|---------|----------|------|
| `demo` | `demo1234` | user |
| `admin` | `DemoAdmin!2026` | admin |

All `curl` below use **trusted HTTPS** (no `-k`). Real panel ports **2053 / 2096 / 443** were left untouched.

---

## 1. TLS (trusted LE IP cert) — PASS

```bash
echo | openssl s_client -connect 117.55.227.224:8443 -servername 117.55.227.224 2>/dev/null \
  | openssl x509 -noout -issuer -ext subjectAltName
# Issuer: C=US, O=Let's Encrypt, CN=YE2
# X509v3 Subject Alternative Name: critical
#     IP Address:117.55.227.224

echo | openssl s_client -connect 117.55.227.224:8443 -servername 117.55.227.224 2>&1 | grep 'Verify return code'
# Verify return code: 0 (ok)

curl -sS -o /dev/null -w 'http_code=%{http_code} ssl_verify_result=%{ssl_verify_result}\n' \
  https://117.55.227.224:8443/healthz
# http_code=200 ssl_verify_result=0
```

Cert validity observed: Not Before `Sep 22 01:51:13 2026 GMT` → Not After `Sep 28 17:51:12 2026 GMT` (shortlived IP profile).

**Result:** PASS

---

## 2. healthz shows mock mode — PASS

```bash
curl -sS https://117.55.227.224:8443/healthz
# {"ok":true,"mock_xui":true,"app":"USGate Portal Demo"}
# HTTP 200
```

**Result:** PASS

---

## 3. User login → dashboard (masked subscription) — PASS

```bash
# GET /login → 200; extract CSRF; POST login demo/demo1234 → 303 Location: /dashboard
# GET /dashboard → 200
```

Dashboard excerpts (safe):

- Title / section: “My subscription / 我的订阅”
- Traffic used: `6.00 GB`
- Remaining: `44.00 GB`
- Quota: `50.00 GB`
- Status: `Offline`
- Masked subscription display: `http://1…950de4ba` (full URL not logged here)

**Result:** PASS

---

## 4. Admin disable demo user → login blocked — PASS

```bash
# Admin login admin / DemoAdmin!2026 → 303 Location: /admin (200)
# POST /admin/users/2/disable (+ CSRF) → 303 Location: /admin?flash=disabled
# POST /login as demo/demo1234 → HTTP 401
# Body contains: "Invalid username or password / 用户名或密码错误"
```

After evidence capture, demo user was **re-enabled** so the public demo remains usable (`POST /admin/users/2/enable` → demo login again returns `303 Location: /dashboard`).

**Result:** PASS

---

## 5. Audit log shows disable — PASS

```bash
curl -sS -b admin.jar https://117.55.227.224:8443/admin/audit
# HTTP 200
```

Audit excerpt (IPs of proof runners omitted/abbreviated in narrative):

- `admin` · `disable_user` · target `demo` · detail `portal+panel disable`
- Also present: `bootstrap_admin`, `login` entries

**Result:** PASS

---

## 6. Not talking to real panel — PASS

```bash
curl -sS https://117.55.227.224:8443/healthz
# {"ok":true,"mock_xui":true,"app":"USGate Portal Demo"}

# Process environ (selected keys only):
# APP_NAME=USGate Portal Demo
# APP_BASE_URL=https://117.55.227.224:8443
# MOCK_XUI=true
# XUI_BASE_URL=http://127.0.0.1:9999/MOCK_UNUSED
```

Listeners after deploy (unchanged real stack + new demo):

| Port | Process |
|------|---------|
| 443 | xray (VLESS Reality) — untouched |
| 2053 | x-ui panel — untouched |
| 2096 | x-ui sub — untouched |
| 8080 | uvicorn (127.0.0.1 only) |
| 8443 | caddy (portal demo TLS) |

`systemctl is-active`: `x-ui` active · `usgate-portal-demo` active · `usgate-portal-caddy` active

**Result:** PASS

---

## Deploy notes

- No Docker; Python 3.12 venv under `/opt/usgate-portal-demo/.venv`
- ufw: `8443/tcp` allowed (comment: USGate portal demo HTTPS)
- Caddy uses existing LE files; certbot renew still restarts x-ui via renewal `renew_hook`; additional deploy-hook reloads portal Caddy only
- App binds `127.0.0.1:8080` only; public entry is HTTPS :8443

## Sign-off

- [x] Public URL loads with trusted cert (`ssl_verify_result=0`)
- [x] Evidence commands/results recorded
- [x] systemd units enabled (survive reboot)
- [x] Real 3X-UI on 2053/2096/443 untouched
- [x] `MOCK_XUI=true` proven via healthz + process env
