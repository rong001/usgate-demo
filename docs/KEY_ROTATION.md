# Key / secret rotation

Public repos never hold live secrets. Rotate offline; update private `.env` / vault only.

## Portal (`APP_SECRET_KEY`)

1. Generate a new long random value (≥64 chars).
2. Update private `.env` on the instance.
3. Restart portal unit — **all sessions invalidate** (expected).
4. Do not commit the new key.

## Bootstrap admin password

- Change via private `.env` `BOOTSTRAP_ADMIN_PASSWORD` **before first boot**, or reset user hash in DB / recreate admin carefully.
- Public MOCK demo uses disposable DEMO-ONLY admin password (documented in evidence) — rotate only if the demo is abused; prefer `demo-reset`.

## Session / CSRF cookies

Rotated automatically when `APP_SECRET_KEY` changes. Cookies: httponly session + double-submit CSRF; set `SESSION_HTTPS_ONLY=true` behind TLS.

## 3X-UI panel password / web path / sub base

**BLOCKED for automation** until the human operator confirms over a secure channel.

If automation previously rotated panel credentials without interactive confirm:

- Treat vault files under a private secrets directory as **temporary**.
- Do **not** mark `REAL_PANEL_ACCEPTANCE` PASS.
- Operator must confirm or set a new panel password out-of-band, then update private `.env` for any **non-public** live portal instance.
- Public `:8443` must remain `MOCK_XUI=true` and must **not** receive real panel credentials.

## Subscription tokens (per user)

User “Reset subscription token” / admin flows rotate the panel client sub id. Audit logs must stay free of full URLs. After rotation, old links fail (expected).

## Checklist

| Secret | Where stored | Git? |
|--------|--------------|------|
| `APP_SECRET_KEY` | private `.env` | never |
| Panel password | operator vault / secure channel | never |
| Sub URLs / UUIDs | panel + user device | never |
| DEMO mock passwords | public docs OK (disposable) | OK |
