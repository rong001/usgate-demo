# Holder: panel sign-in & password rotation (no chat secrets)

Use this when automation reports HTTP 403 on the panel login API and you need a human check.

## Rules
- Do **not** paste the admin password, subscription URLs, or UUID into chat, tickets, or public repos.
- Prefer the panel’s own browser UI on the machine/network you trust.
- Automation must use env-file probes (`panel_login_probe.py --env-file` (on the vault host; see usgate-secrets/bin/)) — never password on CLI argv.

## Shortest sign-in check
1. Open the panel HTTPS URL you already use (host + port + web base path).
2. Confirm the page title/sign-in form loads (TLS trusted).
3. Sign in with the current admin username/password in the browser only.
4. Note the result for the operator as one of: `browser_ok` / `browser_reject` / `browser_unreachable` — without sending the password.

## If browser works but API probe returns 403
- Tell the operator: browser OK + API 403 (possible API/CSRF/policy mismatch) — still **not** proof of wrong password by itself.
- Do not ask them to disable security controls casually.

## If browser also rejects
1. Use the panel’s local recovery path you already have on the VPS (official 3x-ui reset flow), **on the server console**, not via chat-pasted passwords.
2. Set a new admin password yourself.
3. Store it only in your password manager / `usgate-secrets/panel.env` (mode 600) via a secure channel — not in chat.
4. Re-run: `panel_login_probe.py --env-file <panel.env on vault host>` and keep only `http=` / `success_field=` lines.

## Rotation after accidental shell exposure
If a password may have appeared in an agent/SSH transcript as a mistaken shell token:
1. Rotate the panel admin password from a working browser session (or console recovery).
2. Update the local vault file only.
3. Revoke/rotate any test client subscriptions created under the old admin session if applicable.
4. Keep old evidence files; do not wipe logs solely to hide the incident.

## Related
- `docs/REVOKE_SEMANTICS.md` — login reject ≠ tunnel revoke
- Android APK integrity ≠ device network PASS
