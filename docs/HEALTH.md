# Health checks

## Public MOCK demo (`https://117.55.227.224:8443/`)

```bash
curl -sS https://117.55.227.224:8443/healthz
# {"ok":true,"mock_xui":true,"mock_xui_fallback":false,"app":"USGate Portal Demo"}

curl -sS -o /dev/null -w 'http_code=%{http_code} ssl_verify_result=%{ssl_verify_result}\n' \
  https://117.55.227.224:8443/healthz
# expect http_code=200 ssl_verify_result=0
```

Invariant: **`mock_xui` must stay `true`** on :8443 forever.

## Local / Docker

```bash
curl -fsS http://127.0.0.1:8080/healthz
```

Dockerfile `HEALTHCHECK` and `deploy.sh` use the same path.

## Fields

| Field | Meaning |
|-------|---------|
| `ok` | Process serving |
| `mock_xui` | Bound from `MOCK_XUI` at startup (`true` = in-memory mock) |
| `mock_xui_fallback` | Whether live mode may fall back to mock (default `false`) |
| `app` | `APP_NAME` |

## systemd (VPS)

```bash
systemctl is-active usgate-portal-demo usgate-portal-caddy
# do not treat x-ui health as portal health; leave x-ui alone for MOCK demo ops
```

## Failure signals

| Symptom | Likely cause |
|---------|--------------|
| TLS verify ≠ 0 | Cert expired / wrong SAN — see `CERT_RENEWAL.md` |
| `mock_xui:false` on :8443 | **Misconfig** — restore `MOCK_XUI=true` immediately |
| 502 from app behind Caddy | uvicorn down — `systemctl status usgate-portal-demo` |
