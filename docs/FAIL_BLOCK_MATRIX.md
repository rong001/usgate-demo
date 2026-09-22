# FAIL / BLOCK matrix (ToC track)

**Date (UTC):** 2026-09-22 (executor refresh)  
**Public demo:** https://117.55.227.224:8443/ (`MOCK_XUI=true`)

Legend: **PASS** / **FAIL** / **BLOCKED**

## MOCK / public demo

| ID | Check | Result |
|----|-------|--------|
| M-E2E | Local MOCK E2E (19 checks) | **PASS** — `MOCK_E2E_RESULTS.md` |
| D-TLS | LE IP cert, `ssl_verify_result=0` | **PASS** |
| D-HZ | `/healthz` → `mock_xui:true`, `mock_xui_fallback:false` | **PASS** |
| D-LABEL | Prominent MOCK / DEMO labeling on login + footer | **PASS** (post-banner deploy) |
| D-ISO | Public demo isolated from live panel | **PASS** |
| S-REPO | No real secrets in public git | **PASS** |

## Real 3X-UI portal instance

| ID | Check | Result |
|----|-------|--------|
| R-CRED | Human confirms panel password (secure channel) | **BLOCKED** |
| R1–R7 | Live create/disable/traffic/`mock_xui:false` | **BLOCKED** — `REAL_PANEL_ACCEPTANCE.md` |

Do **not** use auto-rotated vault passwords against the live panel for PASS without user confirm.

## Android client (`usgate-client`)

| ID | Check | Result |
|----|-------|--------|
| A-BUILD | `assembleDebug` | **PASS** (local) |
| A-UNIT | `testDebugUnitTest` (9 tests) | **PASS** (local) |
| A-CI | GitHub Actions `android-ci.yml` on `main` | **BLOCKED** — OAuth token lacks `workflow` scope; push rejected |
| A-EMU | Emulator / AVD instrumentation | **BLOCKED** — no AVD/system-image on this box |
| A-PHYS | Physical exit-IP / reconnect / traffic | **BLOCKED — NOT PASS** (user-only) |

## License

| Item | Status |
|------|--------|
| App sources Apache-2.0 | Accurate |
| sing-box / libbox GPL-3.0-or-later | Documented in `THIRD_PARTY_NOTICES.md` |

## Overall

| Track | Status |
|-------|--------|
| MOCK / public demo | **PASS** |
| Real panel ToC | **BLOCKED** |
| Android CI on GitHub | **BLOCKED** (scope) |
| Physical Android tunnel | **BLOCKED** |
