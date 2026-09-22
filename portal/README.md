# USGate Portal / USGate 用户与管理门户

Demo-ready **user + admin portal** for a personal VPN stack backed by **3X-UI**.  
面向 3X-UI 的用户自助 + 管理后台（演示级可运行代码，仓库内无真实密钥）。

| | |
|---|---|
| Stack | Python **FastAPI** · Jinja2/HTMX-style forms · SQLite · bcrypt sessions |
| Panel API | 3X-UI (`panel/api/...`) with **MOCK_XUI** fallback |
| Deploy | `docker compose` · optional **Caddy** HTTPS · `deploy.sh` |

---

## Features / 功能

### User portal / 用户端
- Login (session cookie + bcrypt)
- Own **subscription link** (masked on page, one-click copy; **never logged**)
- Traffic used / remaining, expiry, online status
- Device/IP list when API allows (mock samples in demo)
- Self-service **reset subscription token**

### Admin / 管理端
- Create / disable / enable users (maps to 3X-UI client email)
- Set quotas (GB) and IP limits
- **Audit log** of admin + self-service actions

### Security / 安全
- No secrets in repo — use `env.example` → `.env`
- Login **rate limit**
- **CSRF** on all state-changing forms
- Subscription URLs redacted from logs

---

## Quick start (mock mode) / 快速开始（模拟面板）

```bash
cd usgate-portal
cp env.example .env
# MOCK_XUI=true is the default — no real panel needed
./deploy.sh
# or: docker compose up -d --build
```

Open `http://127.0.0.1:8080/`

| Account | Password | Role |
|---------|----------|------|
| `demo` | `demo1234` | user (seeded against mock client) |
| `admin` | value of `BOOTSTRAP_ADMIN_PASSWORD` in `.env` (default `changeme`) | admin |

Health: `GET /healthz` → `{ "ok": true, "mock_xui": true }`

### Local without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
mkdir -p data
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## Connect to a real 3X-UI panel / 对接真实面板

1. Copy `env.example` → `.env`
2. Set:
   - `MOCK_XUI=false`
   - `XUI_BASE_URL=http://VPS_IP:2053/PANEL_PATH`
   - `XUI_USERNAME` / `XUI_PASSWORD` (or `XUI_API_TOKEN`)
   - `XUI_INBOUND_ID=1`
   - `XUI_SUB_BASE_URL=http://VPS_IP:2096/SUB_PATH`
3. Harden: strong `APP_SECRET_KEY`, `BOOTSTRAP_ADMIN_PASSWORD`, `SESSION_HTTPS_ONLY=true` behind TLS
4. `./deploy.sh`

If the panel is unreachable, the app **falls back to mock** and keeps serving the UI.

API paths used (best-effort across 3X-UI versions):  
`/login`, `/panel/api/inbounds/list`, `/panel/api/inbounds/addClient`,  
`/panel/api/clients/update/{email}`, `/panel/api/clients/onlines`,  
`/panel/api/inbounds/clientIps/{email}`, …

Confirm against your panel’s Swagger: `…/panel/api-docs`.

---

## HTTPS (Caddy) / HTTPS 反代

1. DNS: `PORTAL_DOMAIN` → `VPS_IP`
2. Uncomment the `caddy` service in `docker-compose.yml`
3. Edit `Caddyfile` / set `PORTAL_DOMAIN` in `.env`
4. `docker compose up -d`

---

## Project layout / 目录

```
usgate-portal/
  app/                 # FastAPI app
    routers/           # auth, user, admin
    templates/         # Jinja2
    static/
    xui_client.py      # 3X-UI + mock
  docker-compose.yml
  Caddyfile
  deploy.sh
  env.example
  ACCEPTANCE.md
  README.md
```

---

## Acceptance / 验收

See [ACCEPTANCE.md](./ACCEPTANCE.md) for the evidence checklist.

---

## Disclaimer / 声明

Public **demo** code. Replace all placeholders (`VPS_IP`, `PANEL_PATH`, passwords).  
Do not commit `.env` or real panel credentials. Personal / lab use only where lawful.


## MOCK vs REAL

- `MOCK_XUI=true|false` is the single panel switch (see `env.example`).
- When `MOCK_XUI=false`, live failures raise structured errors; set `MOCK_XUI_FALLBACK=true` only if you explicitly want mock fallback (default **off**).
- Public demo must remain `MOCK_XUI=true`.
- Run `./scripts/e2e_mock.sh` before claiming mock readiness. Demo reset: `POST /admin/demo-reset` or `scripts/reset_mock_demo.py`.
