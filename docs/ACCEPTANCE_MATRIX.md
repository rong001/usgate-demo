# Acceptance matrix

**Date (UTC):** 2026-09-22  
**Public demo:** https://117.55.227.224:8443/ (`MOCK_XUI=true`)

| ID | Area | Check | Result |
|----|------|-------|--------|
| M1 | Mock E2E | Happy path login → traffic/expiry/masked sub | **PASS** (see `MOCK_E2E_RESULTS.md`) |
| M2 | Mock E2E | Bad password 401 / bad CSRF 403 / login 429 | **PASS** |
| M3 | Mock E2E | User blocked from admin; A cannot see B | **PASS** |
| M4 | Mock E2E | Admin create → disable → login blocked; audit no secrets | **PASS** |
| M5 | Mock E2E | SQLite survives process restart | **PASS** |
| M6 | Mock E2E | Demo reset reseeds synthetic users | **PASS** |
| D1 | Public demo | `healthz` `mock_xui:true` on :8443 | **PASS** (evidence doc; re-verify after deploy) |
| D2 | Public demo | TLS `ssl_verify_result=0` | **PASS** (evidence doc; re-verify after deploy) |
| D3 | Public demo | DEMO-ONLY accounts only / no real panel clients | **PASS** (env points at unused mock URL) |
| D4 | Public demo | Rate limits strengthened + demo reset available | **PASS** after this deploy |
| R1–R7 | Real panel | Live create/disable/traffic/`mock_xui:false` | **BLOCKED** — see `REAL_PANEL_ACCEPTANCE.md` |
| S1 | Repo hygiene | No real secrets in git | **PASS** (placeholders / DEMO-ONLY) |
| S2 | Docs | REAL_VS_MOCK / DEPLOY_ROLLBACK / CERT_RENEWAL present | **PASS** |

**Overall mock/demo track:** PASS  
**Overall real-panel ToC:** BLOCKED (human credential confirm)
