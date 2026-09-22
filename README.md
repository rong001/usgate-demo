# USGate Demo Monorepo

Public **demo** of the USGate personal VPN stack: FastAPI user/admin **portal**, Android client **docs**, deploy helpers, and acceptance evidence.

> **No live secrets.** Placeholders only (`VPS_IP`, `PANEL_PATH`, `SUB_PATH`, `CHANGE_ME_…`).  
> Clone this repo and you should **not** get panel passwords, subscription tokens, full UUIDs, or `.env` with production values.

**Related:** Public Android client source → **[rong001/usgate-client](https://github.com/rong001/usgate-client)** (cross-linked with this demo).  
Android CI / BLOCKED device matrix → [`docs/ANDROID_CI_STATUS.md`](docs/ANDROID_CI_STATUS.md).

---

## Live public MOCK demo (HTTPS)

**URL:** [https://117.55.227.224:8443/](https://117.55.227.224:8443/)

Trusted **Let's Encrypt** IP shortlived certificate (no browser warning when the LE root is in the trust store).  
Runs with **`MOCK_XUI=true`** only — isolated from any real 3X-UI panel on the same host (ports 2053/2096/443 untouched).

| Account | Password | Role | Notes |
|---------|----------|------|-------|
| `demo` | `demo1234` | user | **DEMO-ONLY** disposable credential |
| `admin` | `DemoAdmin!2026` | admin | **DEMO-ONLY** disposable credential |

Health: `GET /healthz` → `{ "ok": true, "mock_xui": true, "app": "USGate Portal Demo" }`

Evidence of deploy + flow proofs: **[docs/PORTAL_DEMO_EVIDENCE.md](docs/PORTAL_DEMO_EVIDENCE.md)**.

---

## What is USGate?

USGate is a small personal VPN stack built around:

- **Dataplane:** VLESS + REALITY (`xtls-rprx-vision`) on a VPS (typically managed by **3X-UI**)
- **Portal:** FastAPI app for user self-service (subscription link, traffic, reset token) and light admin (quotas, audit)
- **Android client:** public repo [`rong001/usgate-client`](https://github.com/rong001/usgate-client) — import HTTPS subscription / share links and tunnel device traffic

### Architecture sketch

```text
  Phone (USGate Android)          Browser (portal UI)
           |                              |
           | HTTPS sub URL                | HTTPS (Caddy / LE)
           v                              v
     3X-UI sub :2096              USGate Portal :8080
           |                              |
           |                              | panel API
           v                              v
        Xray :443  <──────────────  3X-UI panel :2053
     (VLESS Reality)
```

---

## Layout

```text
usgate-demo/
  portal/                 # FastAPI portal (Dockerfile, compose, Caddyfile, env.example)
  client-android/         # Pointers + build notes (no APK / no secrets)
  docs/
    SECURITY.md
    ACCEPTANCE.md
    ACCEPTANCE_EVIDENCE.md
    ACCEPTANCE_MATRIX.md
    DEVICE_TEST_CHECKLIST.md
    ANDROID_CI_STATUS.md   # client CI + BLOCKED device rows
    PORTAL_DEMO_EVIDENCE.md
    MOCK_E2E_RESULTS.md
    REAL_VS_MOCK.md
    REAL_PANEL_ACCEPTANCE.md
    DEPLOY_ROLLBACK.md
    CERT_RENEWAL.md
  scripts/
    deploy-vps.sh         # Local or remote deploy helper (no embedded secrets)
```

---

## Quick start — portal (mock 3X-UI)

No real panel required (`MOCK_XUI=true` by default).

```bash
cd portal
cp env.example .env
./deploy.sh
# or: docker compose up -d --build
# open http://127.0.0.1:8080/
```

| Account | Password | Role |
|---------|----------|------|
| `demo` | `demo1234` | seeded mock user |
| `admin` | `BOOTSTRAP_ADMIN_PASSWORD` from `.env` | admin |

Health: `GET /healthz` → `{ "ok": true, "mock_xui": true }`

MOCK E2E (must PASS before claiming readiness):

```bash
cd portal && ./scripts/e2e_mock.sh
```

Boundaries: **[docs/REAL_VS_MOCK.md](docs/REAL_VS_MOCK.md)**. Public demo must stay `MOCK_XUI=true`.

Without Docker:

```bash
cd portal
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env && mkdir -p data
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## Deploy to a VPS

```bash
# Print plan / run local portal deploy
./scripts/deploy-vps.sh

# Remote (set host; SSH keys on your machine — nothing baked into the script)
REMOTE_HOST=203.0.113.10 ./scripts/deploy-vps.sh --remote
```

On the server: edit `portal/.env` (from `env.example`), set `MOCK_XUI=false` and real `XUI_*` placeholders you fill privately. Optional HTTPS: uncomment Caddy in `portal/docker-compose.yml` and set `PORTAL_DOMAIN`.

---

## Security notes

- See **[docs/SECURITY.md](docs/SECURITY.md)**.
- Customer-facing HTTPS: **Let's Encrypt** short-lived certs via **Certbot 5.4+** (or Caddy ACME). Prefer DNS hostname; LE IP certs are short-lived where supported.
- **Do not** give customers self-signed panel/sub certificates.
- Subscription URLs and panel paths are credentials — never commit them; mask in UI and logs.
- `.gitignore` excludes `.env`, `*.pem`, databases, `.venv`, APKs, etc.

---

## Acceptance / evidence

| Doc | Purpose |
|-----|---------|
| [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) | Demo checklist template |
| [docs/ACCEPTANCE_EVIDENCE.md](docs/ACCEPTANCE_EVIDENCE.md) | Lab run evidence (PASS/FAIL; tokens prefix-masked; public IP `117.55.227.224` kept as infra fact) |
| [docs/DEVICE_TEST_CHECKLIST.md](docs/DEVICE_TEST_CHECKLIST.md) | Physical Android phone checklist |
| [portal/ACCEPTANCE.md](portal/ACCEPTANCE.md) | Portal-focused checklist |
| [docs/PORTAL_DEMO_EVIDENCE.md](docs/PORTAL_DEMO_EVIDENCE.md) | Live MOCK HTTPS demo on :8443 (PASS/FAIL curl proofs) |
| [docs/MOCK_E2E_RESULTS.md](docs/MOCK_E2E_RESULTS.md) | Automated MOCK E2E PASS/FAIL table |
| [docs/ACCEPTANCE_MATRIX.md](docs/ACCEPTANCE_MATRIX.md) | Full matrix (PASS/FAIL/BLOCKED) |
| [docs/REAL_VS_MOCK.md](docs/REAL_VS_MOCK.md) | Mode boundaries |
| [docs/REAL_PANEL_ACCEPTANCE.md](docs/REAL_PANEL_ACCEPTANCE.md) | Live panel steps (**BLOCKED** pending credentials) |
| [docs/DEPLOY_ROLLBACK.md](docs/DEPLOY_ROLLBACK.md) | Deploy & rollback |
| [docs/CERT_RENEWAL.md](docs/CERT_RENEWAL.md) | LE IP shortlived renew + Caddy hook |

---

## Android client

This monorepo only ships **docs** under [`client-android/`](client-android/). The **public** Android source is:

**https://github.com/rong001/usgate-client**

```bash
git clone https://github.com/rong001/usgate-client.git
cd usgate-client
./gradlew :app:fetchLibbox :app:assembleDebug
```

Do not commit APKs with production configs. See the client repo for Apache-2.0 / GPL third-party notices and `docs/BUILD_REPRO.md`.

---

## 中文简介

**USGate** 是一套个人向 VPN 演示栈：VPS 上 3X-UI / Xray（VLESS + REALITY）+ FastAPI 用户/管理门户 + Android 客户端（公开仓库 [usgate-client](https://github.com/rong001/usgate-client)）。

- 本仓库为 **公开演示**：仅占位符，无真实面板密码、订阅路径/令牌、完整 UUID、SSH 私钥或线上 `.env`。
- 本地试用：`cd portal && cp env.example .env && ./deploy.sh`，浏览器打开 `http://127.0.0.1:8080/`（mock 账号 `demo` / `demo1234`）。
- **线上 MOCK 演示（可信 HTTPS）：** https://117.55.227.224:8443/ （账号见上文 DEMO-ONLY 表；证据见 `docs/PORTAL_DEMO_EVIDENCE.md`）。
- 生产 HTTPS 请用 **Let's Encrypt / Certbot 5.4+**（或 Caddy ACME），**不要**给终端用户自签证书。
- 验收与安全说明见 `docs/`。

---

## License / use

Demo code for lab and documentation. Operate only where lawful. Do not publish real panel paths, subscription tokens, or credentials.
