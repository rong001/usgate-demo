# Holder panel login (browser) — no secrets in chat

**Audience:** Operator who holds the 3X-UI / panel admin password.  
**Rule:** Never paste the panel password, tokens, subscription bodies, or UUIDs into chat, tickets, or git. Rotate in the panel UI; store only in a private vault / local `.env` that is gitignored.

Related: [`REVOKE_SEMANTICS.md`](./REVOKE_SEMANTICS.md) — portal reject ≠ killing a cached tunnel.

## Browser login (high level)

1. Open the panel URL in a browser on a trusted machine (operator-controlled).
2. Sign in with the **admin username** you already know.
3. Enter the **admin password** from your private vault / secure channel — not from this repo.
4. Confirm you are on the expected host (check TLS / IP / path you configured).
5. Do not share screenshots that show the password field filled in or live client UUIDs.

If login fails: check URL path, clock skew, and whether credentials were rotated. Do **not** ask an assistant to “try passwords” or dump vault files into chat.

## Rotate admin password (in panel UI)

1. While logged in as admin, open the panel **settings / account / security** section (wording varies by 3X-UI build).
2. Set a **new** strong admin password.
3. Save; sign out; sign in again with the new password to confirm.
4. Update your private vault / private `.env` only (`XUI_PASSWORD=…`). Never commit.
5. Invalidate any shared notes that still list the old password.

Optional API tokens: revoke/regenerate in the panel UI the same way; update private env; do not paste into chat.

## After rotation — revoke awareness

Rotating the admin password protects the **panel**. It does **not** by itself tear down client tunnels that already cached a subscription.

For proprietary clients, see [`REVOKE_SEMANTICS.md`](./REVOKE_SEMANTICS.md):

- disable/revoke the user on the portal/panel, **and**
- ensure the client clears cached config **and** stops the live session.

Windows local helper (when package is installed on a PC):

```bat
usgate.exe revoke-local -workdir %LOCALAPPDATA%\USGate
```

## Still do not mark PASS for

- Real panel acceptance without operator-confirmed credentials: see [`REAL_PANEL_ACCEPTANCE.md`](./REAL_PANEL_ACCEPTANCE.md)
- Windows physical TUN + real-node revoke proof (cross-compile ≠ device test)

No password resets performed by automation in this document.
