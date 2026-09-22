# SECURITY.md — USGate Demo

## Principles

1. **No secrets in git.** Passwords, API tokens, confidential panel/subscription paths, private keys, and full UUIDs stay in `.env`, a password manager, or a sealed secret store — never in this public repo.
2. **Subscription URLs are credentials.** Anyone with the URL can fetch the tunnel config. Never log them; mask in UI; rotate via portal “reset token”.
3. **Least privilege.** Portal admin ≠ panel root when possible; prefer 3X-UI API tokens with limited scope if available.
4. **TLS in production for customers.** Terminate HTTPS with a **public CA** certificate. Set `SESSION_HTTPS_ONLY=true`.
5. **Rate-limit authentication.** Login endpoints are throttled in the portal.
6. **CSRF** on cookie-authenticated form POSTs.

## TLS / certificates (customer-facing)

| Use case | Guidance |
|----------|----------|
| Portal / panel / subscription HTTPS for end users | **Let's Encrypt** (or other public CA) short-lived certs via **Certbot 5.4+** (or Caddy ACME). Prefer hostname + DNS A/AAAA; IP-based LE certs are short-lived and require a Certbot version that supports them. |
| Lab / smoke only | Self-signed is acceptable for operators testing on a private box. |
| **Customers** | **Do not** ship self-signed panel/sub certs. Browsers and many clients will warn or refuse; it trains users to ignore TLS warnings. |

Caddy (see `portal/Caddyfile`) obtains/renews ACME certs automatically when `PORTAL_DOMAIN` DNS points at the VPS. For 3X-UI panel/sub ports, install LE certs into the panel cert paths (or terminate TLS at a reverse proxy in front).

## Secret inventory (operators)

| Secret | Where it should live | Example placeholder |
|--------|----------------------|---------------------|
| Portal `APP_SECRET_KEY` | `.env` | random 64+ hex |
| Portal bootstrap admin password | `.env` | `CHANGE_ME_…` |
| 3X-UI admin password / API token | `.env` / password manager | `PANEL_ADMIN_PASSWORD` |
| Panel URL path (`webBasePath`) | `.env` | `PANEL_PATH` |
| Subscription base path | `.env` | `SUB_PATH` |
| VPS host | DNS / inventory | `VPS_IP` or hostname |
| REALITY **private** key | 3X-UI / Xray only | never in portal repo |
| Client UUIDs / subIds | panel DB | prefix-only in public docs |

## Logging redaction

- Portal must not write full subscription URLs to stdout/files.
- Audit log stores actions like `reset_sub_token` with target email only.
- Acceptance / evidence docs: mask tokens and UUIDs to **prefixes** (≈8 chars + `…`).

## Reporting

This is a demo monorepo. For a private deployment, define an internal contact for security issues. Do not file public issues that include live credentials.
