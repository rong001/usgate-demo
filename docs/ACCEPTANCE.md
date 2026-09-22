# ACCEPTANCE.md — USGate Demo (monorepo)

Use this for an end-to-end demo review. Portal-specific rows are mirrored from `portal/ACCEPTANCE.md`.

**Date (UTC):** _______________  
**Mode:** MOCK / LIVE  

## A. Repository hygiene

| Check | Pass | Evidence |
|-------|------|----------|
| No `.env` committed | ☐ | `git status` |
| Placeholders only (`VPS_IP`, …) | ☐ | grep review |
| `docs/SECURITY.md` present | ☐ | path |

## B. Portal (mock)

| Check | Pass | Evidence |
|-------|------|----------|
| `portal/deploy.sh` or compose up | ☐ | logs |
| `/healthz` ok, `mock_xui: true` | ☐ | JSON |
| User login `demo` / `demo1234` | ☐ | screenshot |
| Admin bootstrap login | ☐ | screenshot |
| Masked sub link + copy | ☐ | screenshot |
| Reset sub → audit without URL | ☐ | audit |
| Create/disable user + quota | ☐ | screenshot |

## C. Android client docs

| Check | Pass | Evidence |
|-------|------|----------|
| `client-android/README.md` has no live secrets | ☐ | file review |
| Points to `usgate-client` build steps | ☐ | — |

## D. Deploy script dry-run

| Check | Pass | Evidence |
|-------|------|----------|
| `scripts/deploy-vps.sh --help` or dry-run prints plan | ☐ | terminal |

## Sign-off

- [ ] Demo ready for public GitHub (desensitized)
- [ ] Live panel acceptance deferred / completed (see portal/ACCEPTANCE.md §5)
