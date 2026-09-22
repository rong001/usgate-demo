# REAL vs MOCK — boundaries

| Concern | MOCK (`MOCK_XUI=true`) | REAL (`MOCK_XUI=false`) |
|---------|------------------------|-------------------------|
| Panel | In-memory synthetic clients | Live 3X-UI panel API |
| Switch | Single env: `MOCK_XUI` | Same |
| Fallback | N/A (already mock) | **Off by default.** Set `MOCK_XUI_FALLBACK=true` only if you explicitly want silent mock on panel errors |
| Secrets | Placeholders / demo passwords only | Panel password & sub base via private `.env` (never git) |
| Public demo `:8443` | **MUST stay MOCK forever** | Do not point public demo at live panel |
| Demo reset | `POST /admin/demo-reset` or `scripts/reset_mock_demo.py` | Refused when live |
| Failures | Local mock data | Structured `XUIError` → HTTP 502 JSON `{error,message}` |
| Logs | Masked sub URLs / UUIDs / cookies | Same redaction rules |

## Portal auth model (both modes)

- Portal login is **independent** (bcrypt + signed session cookie).
- Each portal user maps to a panel client **email** (`xui_email`).
- Users see **own** traffic / expiry / **masked** subscription only (session UID — no cross-user IDOR).
- Admins create/disable/quota + audit (audit never stores passwords or full sub URLs).

## CSRF & sessions

- Double-submit CSRF (`usgate_csrf` cookie + form field) on all state-changing POSTs.
- Session cookie httponly, `SameSite=Lax`; set `SESSION_HTTPS_ONLY=true` behind TLS.

## What this monorepo never contains

- Real panel passwords, panel path secrets, subscription tokens, full client UUIDs, production `.env`.
