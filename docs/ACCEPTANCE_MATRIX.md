# Acceptance matrix

**Date (UTC):** 2026-09-22  
**Public demo:** https://117.55.227.224:8443/ (`MOCK_XUI=true`)  
**Canonical FAIL/BLOCK table:** [`FAIL_BLOCK_MATRIX.md`](FAIL_BLOCK_MATRIX.md)

| ID | Area | Check | Result |
|----|------|-------|--------|
| M1 | Mock E2E | Happy path login → traffic/expiry/masked sub | **PASS** (see `MOCK_E2E_RESULTS.md`) |
| M2 | Mock E2E | Bad password 401 / bad CSRF 403 / login 429 | **PASS** |
| M3 | Mock E2E | User blocked from admin; A cannot see B | **PASS** |
| M4 | Mock E2E | Admin create → disable → login blocked; audit no secrets | **PASS** |
| M5 | Mock E2E | SQLite survives process restart | **PASS** |
| M6 | Mock E2E | Demo reset reseeds synthetic users | **PASS** |
| D1 | Public demo | `healthz` `mock_xui:true` on :8443 | **PASS** |
| D2 | Public demo | TLS `ssl_verify_result=0` (LE IP shortlived) | **PASS** |
| D3 | Public demo | DEMO-ONLY accounts only / no real panel clients | **PASS** |
| D4 | Public demo | Rate limits + demo reset + prominent MOCK labeling | **PASS** |
| R1–R7 | Real panel | Live create/disable/traffic/`mock_xui:false` | **BLOCKED** — `REAL_PANEL_ACCEPTANCE.md` |
| A1 | Android | Local `assembleDebug` + 9 unit tests | **PASS** |
| A2 | Android | GitHub Actions workflow on `main` | **BLOCKED** — OAuth lacks `workflow` scope |
| A3 | Android | Emulator AVD | **BLOCKED** — no AVD on box |
| A4 | Android | Physical exit-IP / reconnect / traffic | **BLOCKED — NOT PASS** |
| S1 | Repo hygiene | No real secrets in git | **PASS** |
| S2 | Docs | Deploy / cert / health / backup / key rotation / FAIL matrix | **PASS** |

**Overall mock/demo track:** PASS  
**Overall real-panel ToC:** BLOCKED (human credential confirm)  
**Overall Android GitHub CI:** BLOCKED (workflow scope)
