# Certificate renewal — portal demo (LE IP shortlived)

## Layout (public MOCK demo)

| Item | Value |
|------|-------|
| Host | `117.55.227.224` |
| HTTPS | `:8443` (Caddy) → `127.0.0.1:8080` (uvicorn) |
| Cert path | `/etc/letsencrypt/live/117.55.227.224/` |
| Profile | Let's Encrypt **IP shortlived** |
| App unit | `usgate-portal-demo.service` |
| Caddy unit | `usgate-portal-caddy.service` |

Real 3X-UI / Xray TLS on **443 / 2053 / 2096** is separate — do not point portal renew hooks at those unless intentionally shared.

## Auto-renew

Certbot renew (systemd timer or cron) issues/renews the IP cert. A **deploy hook** reloads portal Caddy only:

Suggested path: `/etc/letsencrypt/renewal-hooks/deploy/reload-usgate-portal-caddy.sh`

```bash
#!/bin/bash
# Reload portal Caddy after LE renew — do not restart x-ui here.
systemctl reload usgate-portal-caddy 2>/dev/null || systemctl restart usgate-portal-caddy
```

`chmod +x` the hook. Confirm:

```bash
certbot renew --dry-run
echo | openssl s_client -connect 117.55.227.224:8443 -servername 117.55.227.224 2>&1 \
  | grep 'Verify return code'
# expect: Verify return code: 0 (ok)
```

## Manual reload after renew

```bash
systemctl reload usgate-portal-caddy || systemctl restart usgate-portal-caddy
curl -sS -o /dev/null -w 'http_code=%{http_code} ssl_verify_result=%{ssl_verify_result}\n' \
  https://117.55.227.224:8443/healthz
```

## Notes

- Shortlived IP certs renew frequently — keep the deploy hook enabled.
- Portal Caddyfile should reference the LE `fullchain.pem` / `privkey.pem` paths.
- Customer-facing product HTTPS should prefer a DNS hostname when possible; IP certs are acceptable for this lab demo.
