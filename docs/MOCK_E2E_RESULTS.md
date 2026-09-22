# MOCK_E2E_RESULTS

**Date (UTC):** 2026-09-22T06:54:15Z
**Mode:** MOCK_XUI=true
**Command:** `scripts/e2e_mock.sh` → `tests/e2e_mock.py`

## MOCK E2E RESULTS

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | healthz mock_xui true | PASS | {'ok': True, 'mock_xui': True, 'mock_xui_fallback': False, 'app': 'USGate Portal'} |
| 2 | login page + CSRF cookie | PASS | csrf=True |
| 3 | 1. happy path login demo | PASS | status=303 loc=/dashboard |
| 4 | 1. dashboard traffic/expiry/masked sub | PASS | traffic=True expiry=True |
| 5 | 2. bad password → 401 | PASS | status=401 |
| 6 | 2. missing/bad CSRF → 403 | PASS | status=403 |
| 7 | 2. rate-limit 429 | PASS | login hammer |
| 8 | 3. user cannot hit admin | PASS | status=303 |
| 9 | 3. user cannot hit admin audit | PASS | status=303 |
| 10 | 3. admin create alice | PASS | loc=/admin?flash=created |
| 11 | 3. admin create bob | PASS | loc=/admin?flash=created |
| 12 | 3. user A cannot see user B data | PASS | alice dashboard excludes bob |
| 13 | 4. admin disable user | PASS | alice_id=3 |
| 14 | 4. audit contains disable (no secrets) | PASS | secrets_clean=True |
| 15 | 4. disabled user login blocked | PASS | status=401 |
| 16 | 5. sqlite survives restart (users+audit) | PASS | demo_login=True audit=True |
| 17 | 6. admin demo-reset | PASS | loc=/admin?flash=demo_reset_ok |
| 18 | 6. after reset alice gone | PASS | status=401 |
| 19 | 6. after reset demo works | PASS | status=303 |

Total: 19  PASS: 19  FAIL: 0

**Overall:** PASS
