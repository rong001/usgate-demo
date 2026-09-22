# REVOKE_SEMANTICS

**Date (UTC):** 2026-09-22  
**Scope:** Proprietary USGate clients (Android today, Windows CLI scaffold, later macOS/iOS).  
**Mode:** Design acceptance bar + test skeletons. No claim of PASS on a real node.

## One-line bar

> **Rejecting re-login / subscription fetch ≠ killing a cached tunnel.**  
> **Real revoke must prove: cached local config is unusable AND any established session dies.**

## What MOCK / portal tests already prove

Portal INTERNAL closed loop (`portal/tests/e2e_internal_closed_loop.py`) correctly shows:

- admin disable/revoke user
- disabled user auth rejected
- subsequent subscription use rejected (enable gate)
- mock panel client `enable=false`

That is **portal reject semantics only**. It does **not** prove that a device which already imported a sub and started a tunnel has:

1. cleared or invalidated its **cached config**, and  
2. torn down the **live sing-box / liberbox session**.

## Proprietary client obligations

| Step | Required | Notes |
|------|----------|-------|
| Portal rejects new login | yes | necessary, not sufficient |
| Portal / panel rejects sub fetch | yes | necessary, not sufficient |
| Client clears cached config (disk + memory) | **yes** | e.g. delete `config.json` / prefs nodes |
| Client stops established tunnel process/session | **yes** | kill sing-box / liberbox box |
| Traffic / exit-IP proof tunnel is dead | **yes** for PASS | needs real device or Win TUN session |
| Third-party client behavior | **does not count** | acceptance is own clients only |

## Anti-patterns (do not mark PASS)

- “User cannot open dashboard anymore” → **not** revoke of tunnel.
- “Sub URL returns 403” while old `config.json` still runs → **FAIL** the bar.
- Emulator / MOCK-only session stop without real panel → document as dry-run only.
- Skipping the blocked test and treating suite green as real-node revoke PASS.

## Test skeletons (must FAIL or SKIP until real panel + device)

| Location | Behavior |
|----------|----------|
| `usgate-client-win/internal/revoke/semantics_test.go` → `TestRealNodeRevokeAcceptance_BLOCKED` | **`t.Skip`** with BLOCKED reason |
| `usgate-client/.../RevokeSemanticsTest.kt` | **`@Ignore` / assume** BLOCKED — not PASS |
| Portal ICL checks 7–10 | PASS for **portal reject only**; do not rename as full revoke |

Local dry-run (`ApplyRevoke` / `revoke-local`) may PASS for “cache cleared + session flag false” **without** `RealNodeProof`. `Acceptance.Satisfied()` stays **false** until real proof exists.

## Linkage

- Android closed-loop evidence: [`INTERNAL_ANDROID_CLOSED_LOOP.md`](./INTERNAL_ANDROID_CLOSED_LOOP.md)
- Device checklist (when hardware available): [`DEVICE_TEST_CHECKLIST.md`](./DEVICE_TEST_CHECKLIST.md)
- Win client scaffold: `/home/box/workspace/usgate-client-win/` (see its README)

## Still BLOCKED

```
panel_api=BLOCKED_NEED_USER_PASSWORD
physical Android device=BLOCKED
Windows live TUN + real panel revoke proof=BLOCKED
```

No password resets, no OAuth scope expansion, no secrets in git/chat.
