# ACCEPTANCE.md — USGate Portal evidence checklist

Fill this template when verifying a deployment. Attach screenshots / redacted logs as evidence.

**Environment:** `MOCK` / `LIVE` (circle one)  
**Date (UTC):** _______________  
**Operator:** _______________  
**Portal URL:** `https://PORTAL_DOMAIN/` or `http://VPS_IP:8080/`

---

## 1. Build & health

| # | Check | Pass? | Evidence |
|---|--------|-------|----------|
| 1.1 | `docker compose up -d --build` succeeds | ☐ | compose logs / image id |
| 1.2 | `GET /healthz` returns `ok: true` | ☐ | response JSON |
| 1.3 | No secrets in git (`env.example` only) | ☐ | `git grep` / review |
| 1.4 | `.env` not committed | ☐ | `.gitignore` + `git status` |

## 2. Auth & security

| # | Check | Pass? | Evidence |
|---|--------|-------|----------|
| 2.1 | Login with wrong password fails | ☐ | screenshot |
| 2.2 | Login rate-limit returns 429 after N tries | ☐ | response / screenshot |
| 2.3 | POST without CSRF token → 403 | ☐ | curl / screenshot |
| 2.4 | Session cookie is HttpOnly | ☐ | DevTools Application |
| 2.5 | Subscription URL **not** in server logs after Copy / Reset | ☐ | redacted log excerpt |

## 3. User portal

| # | Check | Pass? | Evidence |
|---|--------|-------|----------|
| 3.1 | User sees masked subscription link | ☐ | screenshot |
| 3.2 | Copy places full URL on clipboard | ☐ | note / video |
| 3.3 | Traffic used / remaining / expiry shown | ☐ | screenshot |
| 3.4 | Online status shown (or Offline in mock) | ☐ | screenshot |
| 3.5 | Device/IP list shown or empty state | ☐ | screenshot |
| 3.6 | Reset sub token rotates link; audit entry without full URL | ☐ | audit row |

## 4. Admin

| # | Check | Pass? | Evidence |
|---|--------|-------|----------|
| 4.1 | Create user → appears in list + mock/live client | ☐ | screenshot |
| 4.2 | Disable user → cannot login; panel client disabled (live) | ☐ | screenshot |
| 4.3 | Set quota / IP limit persists | ☐ | screenshot |
| 4.4 | Audit log lists create/disable/quota/login | ☐ | screenshot |

## 5. Live 3X-UI (skip if MOCK)

| # | Check | Pass? | Evidence |
|---|--------|-------|----------|
| 5.1 | `MOCK_XUI=false` and panel reachable | ☐ | healthz `mock_xui: false` |
| 5.2 | Created client visible in panel UI | ☐ | panel screenshot (redact secrets) |
| 5.3 | Subscription URL from portal fetches config | ☐ | HTTP 200 + userinfo header (redact body) |

## Sign-off

- [ ] Ready for demo  
- [ ] Ready for private production (secrets rotated)

**Notes:**

```
(free text)
```
