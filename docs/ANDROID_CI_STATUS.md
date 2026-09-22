# Android CI status + device matrix (BLOCKED rows)

Public client: **[rong001/usgate-client](https://github.com/rong001/usgate-client)**  
Workflow file (local tip; **not yet on GitHub `main`**): `.github/workflows/android-ci.yml`  
Emulator notes: [`docs/EMULATOR_TEST.md`](https://github.com/rong001/usgate-client/blob/main/docs/EMULATOR_TEST.md)  
Results log: [`docs/CI_EMULATOR_RESULTS.md`](https://github.com/rong001/usgate-client/blob/main/docs/CI_EMULATOR_RESULTS.md)

## GitHub Actions push — BLOCKED

| Item | Detail |
|------|--------|
| Local commit with workflow | `f655058` on operator box (ahead of GitHub `main`) |
| GitHub `main` tip | `53a9afb` (docs only; no workflow file) |
| `git push` of workflow commit | **Rejected:** OAuth App cannot create/update workflow without `workflow` scope |
| Token scopes observed | `gist`, `read:org`, `repo` — **missing `workflow`** |
| `gh auth refresh -h github.com -s workflow` | Starts **device-flow** (browser one-time code) — cannot complete unattended; prior attempts hit rate limits / need human |

**Next user action:** interactively run `gh auth refresh -h github.com -s workflow`, complete the browser device flow, then `git push` from the client repo (commit already ready).

## What automation covers (once workflow is on GitHub)

| Area | Status |
|------|--------|
| JDK 17 + Gradle assembleDebug + libbox fetch | CI target (PASS when green) |
| Unit tests: subscription parse, UI state mock, error strings | CI target — **local PASS (9/9)** |
| Instrumentation smoke (no VPN tunnel) | Best-effort emulator job |
| Physical device E2E | **User-only** — not CI |

## Device matrix rows — keep BLOCKED until human sign-off

| Matrix row | CI / automation | Physical device |
|------------|-----------------|-----------------|
| Install + launch, status 未连接 | Smoke only (partial) | User checklist |
| Import subscription (placeholder / lab URL) | Parse unit tests only | User checklist |
| VPN permission deny toast | Not automated | User checklist |
| Connect → 已连接 | **BLOCKED** | User-only |
| Exit IP == VPS (`api.ipify.org`) | **BLOCKED — NOT PASS** | User-only |
| Disconnect → reconnect | **BLOCKED — NOT PASS** | User-only |
| Traffic / download through tunnel | **BLOCKED — NOT PASS** | User-only |

Checklist: [`DEVICE_TEST_CHECKLIST.md`](DEVICE_TEST_CHECKLIST.md).

**Statement:** physical Android exit IP / reconnect / traffic must remain **NOT PASS** in CI and in automated evidence. Emulator absence on this box = **EMULATOR BLOCKED**.
