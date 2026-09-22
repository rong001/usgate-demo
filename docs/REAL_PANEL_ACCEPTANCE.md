# REAL panel acceptance — **BLOCKED** pending human credentials

> **Do not execute these steps against a live panel until the human operator
> confirms the panel password (and related secrets) via a secure channel.**
> This file contains **placeholders only**. No real passwords, panel paths,
> subscription URLs, or UUIDs.

**Status:** all items below are **BLOCKED**.
> **Note:** If panel credentials were auto-rotated without interactive user confirmation, leave this entire file **BLOCKED**. Do not use vault passwords against the live panel for PASS.


## Preconditions (human)

| # | Step | Status |
|---|------|--------|
| H1 | Operator confirms 3X-UI admin password out-of-band | **BLOCKED** |
| H2 | Operator confirms panel base URL / path placeholders → private `.env` | **BLOCKED** |
| H3 | Operator confirms subscription public base placeholder → private `.env` | **BLOCKED** |
| H4 | Operator confirms inbound id for new clients | **BLOCKED** |
| H5 | Agree `MOCK_XUI=false` and `MOCK_XUI_FALLBACK=false` on the **non-public** instance | **BLOCKED** |

Public demo on `https://117.55.227.224:8443/` must remain `MOCK_XUI=true` forever.

## Private `.env` placeholders (never commit)

```bash
MOCK_XUI=false
MOCK_XUI_FALLBACK=false
XUI_BASE_URL=http://VPS_IP:2053/PANEL_PATH
XUI_USERNAME=PANEL_ADMIN_USER
XUI_PASSWORD=PANEL_ADMIN_PASSWORD   # from secure channel only
XUI_API_TOKEN=                      # optional
XUI_INBOUND_ID=1
XUI_SUB_BASE_URL=http://VPS_IP:2096/SUB_PATH
SESSION_HTTPS_ONLY=true
```

## Acceptance checks (run only after H1–H5)

| # | Check | Expected | Status |
|---|-------|----------|--------|
| R1 | `GET /healthz` | `ok:true`, **`mock_xui:false`** | **BLOCKED** |
| R2 | Admin create test user | Panel client appears; audit has `create_user` without secrets | **BLOCKED** |
| R3 | User login → dashboard | Traffic/expiry from panel; sub **masked** in UI | **BLOCKED** |
| R4 | Admin disable → user login 401 | Portal + panel enable=false | **BLOCKED** |
| R5 | Reset sub token | New masked link; old sub id invalid; audit has no full URL | **BLOCKED** |
| R6 | Panel unreachable | HTTP 502 structured `XUIError` (no silent mock) | **BLOCKED** |
| R7 | Logs | No passwords, cookies, full sub URLs, or raw UUIDs | **BLOCKED** |

## Explicit non-goals

- Do not run acceptance against the public MOCK demo port **8443**.
- Do not paste real secrets into git, chat, or this file.
- Do not set `MOCK_XUI_FALLBACK=true` for ToC/live acceptance.
