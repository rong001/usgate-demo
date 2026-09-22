# Android CI status + device matrix (BLOCKED rows)

Public client: **[rong001/usgate-client](https://github.com/rong001/usgate-client)**  
Workflow: [`.github/workflows/android-ci.yml`](https://github.com/rong001/usgate-client/blob/main/.github/workflows/android-ci.yml)  
Emulator notes: [`docs/EMULATOR_TEST.md`](https://github.com/rong001/usgate-client/blob/main/docs/EMULATOR_TEST.md)  
Results log: [`docs/CI_EMULATOR_RESULTS.md`](https://github.com/rong001/usgate-client/blob/main/docs/CI_EMULATOR_RESULTS.md)

## What automation covers

| Area | Status |
|------|--------|
| JDK 17 + Gradle assembleDebug + libbox fetch | CI target (PASS when green) |
| Unit tests: subscription parse, UI state mock, error strings | CI target |
| Instrumentation smoke (no VPN tunnel) | Best-effort emulator job |
| Physical device E2E | **User-only** — not CI |

## Device matrix rows — keep BLOCKED until human sign-off

Use placeholders (`VPS_IP`, `YOUR_SUB_URL`) in public notes. Do **not** commit live IPs/UUIDs into new evidence.

| Matrix row | CI / automation | Physical device |
|------------|-----------------|-----------------|
| Install + launch, status 未连接 | Smoke only (partial) | User checklist |
| Import subscription (placeholder / lab URL) | Parse unit tests only | User checklist |
| VPN permission deny toast | Not automated | User checklist |
| Connect → 已连接 | **BLOCKED** | User-only |
| Exit IP == VPS (`api.ipify.org`) | **BLOCKED — NOT PASS** | User-only |
| Disconnect → reconnect | **BLOCKED — NOT PASS** | User-only |
| Traffic / download through tunnel | **BLOCKED — NOT PASS** | User-only |

Checklist template: [`DEVICE_TEST_CHECKLIST.md`](DEVICE_TEST_CHECKLIST.md) (replace any lab-specific hosts with `VPS_IP` before publishing screenshots).

**Statement:** physical Android exit IP / reconnect / traffic must remain **NOT PASS** in CI and in this demo’s automated evidence.
