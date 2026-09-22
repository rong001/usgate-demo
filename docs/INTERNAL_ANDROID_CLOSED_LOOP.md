# INTERNAL_ANDROID_CLOSED_LOOP

**Date (UTC):** 2026-09-22T14:00:00Z  
**Scope this round:** Android minimal closed loop for **internal use** (self + members). Proprietary Win/macOS/iOS later.  
**Mode:** MOCK portal + Android JVM unit/integration. No commercial publish. No CI workflow push.

## Summary matrix

| Slice | Result | Notes |
|-------|--------|-------|
| Portal MOCK: admin create → user sub UI → disable → auth rejected | **PASS** | `portal/tests/e2e_internal_closed_loop.py` (10/10) |
| Portal MOCK E2E regression | **PASS** | `portal/tests/e2e_mock.py` (19/19) |
| Android unit: parser + SingBoxConfigBuilder on synthetic fixture | **PASS** | `InternalClosedLoopTest` (4/4) + existing unit tests |
| Android debug APK rebuild (local) | **PASS** | see APK evidence below |
| Quiet real 3X-UI panel login (`panel.env`) | **panel_api=BLOCKED_NEED_USER_PASSWORD** | login HTTP 403; password not reset |
| Real panel admin create/list/disable test inbound | **BLOCKED** | blocked on panel_api |
| 真实专属客户端联网 / 管理端见真机设备 | **BLOCKED（无物理设备）** | Explicit — no physical Android device on box |
| Physical exit-IP / reconnect / traffic | **BLOCKED** | Must not mark PASS without device |
| MOCK public demo / third-party client / web / emulator as substitute | **Not accepted** | Documented only; not a substitute for proprietary real-device |

## Portal INTERNAL_CLOSED_LOOP (PASS)

Command:

```bash
cd portal && scripts/e2e_internal_closed_loop.sh
# or: .venv/bin/python tests/e2e_internal_closed_loop.py
```

| # | Check | Result |
|---|-------|--------|
| 1 | ICL admin login | PASS |
| 2 | ICL admin create user | PASS |
| 3 | ICL user login (enabled) | PASS |
| 4 | ICL user gets subscription UI (masked) | PASS |
| 5 | ICL synthetic sub material + mock client enabled | PASS |
| 6 | ICL client-parser fixture ready (Android unit sibling) | PASS |
| 7 | ICL admin disable/revoke user | PASS |
| 8 | ICL mock panel client enable=false | PASS |
| 9 | ICL disabled user auth rejected | PASS |
| 10 | ICL subsequent sub use rejected (enable gate) | PASS |

**Secrets:** test prints scrub hex32/UUIDs/sub URLs. No live subscription URLs/UUIDs/keys committed.

## Android client JVM closed-loop (PASS)

- Class: `com.usgate.client.integration.InternalClosedLoopTest`
- Covers: base64 synthetic sub → `SubscriptionParser` → `SingBoxConfigBuilder`; empty/garbage after revoke → empty nodes.
- Command: `./gradlew testDebugUnitTest`
- Result (this run): **all unit suites PASS** including InternalClosedLoopTest 4/4, SubscriptionParserTest 5/5, SingBoxConfigBuilderTest 1/1, ConnectionUiStateTest 3/3.

## APK evidence (local build)

| Field | Value |
|-------|-------|
| versionName | `0.2.1-branded` |
| versionCode | `3` |
| Build output | `app/build/outputs/apk/debug/app-debug.apk` |
| Stable copy | `/home/box/workspace/usgate-client/dist/USGate-0.2.1-debug.apk` |
| Size | 55959959 bytes |
| SHA256 | `632dc788d087fd3571b7257dad74e457870ba9f13196d593b507e04b6c517011` |
| Checksums file | `usgate-client/dist/SHA256SUMS.txt` (local; `dist/` gitignored) |

## panel_api

```
panel_api=BLOCKED_NEED_USER_PASSWORD
```

Quiet check against `usgate-secrets/panel.env` without echoing values. Login rejected (HTTP 403). **Did not** reset panel password or change admin credentials.

## Explicit BLOCKED (device)

> **真实专属客户端联网 / 管理端见真机设备 = BLOCKED（无物理设备）**

Physical Android exit-IP, reconnect, and traffic must remain **BLOCKED** until a real device runs the proprietary USGate APK against a live sub.

## Next (single user action)

See parent report: one concrete remaining action (provide working panel password **or** sideload APK on a physical Android and run device checklist).

## Revoke semantics (acceptance bar)

Canonical: [`docs/REVOKE_SEMANTICS.md`](./REVOKE_SEMANTICS.md)

- Portal ICL checks 7–10 = **reject login/sub** only — **not** full revoke of cached tunnel.
- Real revoke PASS requires: **cached config cleared** + **live session dead** + real panel/device proof.
- Skeletons (SKIP/Ignore, not PASS): `usgate-client` `RevokeSemanticsTest`; `usgate-client-win` `TestRealNodeRevokeAcceptance_BLOCKED`.

## Pointers

- Client docs pointer: `usgate-client/docs/INTERNAL_CLOSED_LOOP.md`
- Prior MOCK E2E: `docs/MOCK_E2E_RESULTS.md`
- Device checklist (when hardware available): `docs/DEVICE_TEST_CHECKLIST.md`
- Revoke semantics: `docs/REVOKE_SEMANTICS.md`
- Win client scaffold (local): `/home/box/workspace/usgate-client-win/`

## Commits (this round)

| Repo | SHA | Note |
|------|-----|------|
| usgate-demo | `f38d8c0` | ICL test + evidence doc |
| usgate-client | `798b1cb` | InternalClosedLoopTest + docs pointer |
| usgate-client workflow | `f655058` (local only) | Not pushed — GitHub Actions workflow remains local |
