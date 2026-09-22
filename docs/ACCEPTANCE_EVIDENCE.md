# USGate / 3X-UI — Acceptance Evidence Report

| Field | Value |
|---|---|
| VPS | `117.55.227.224` (hostname `vpn-us`) |
| Runner | Shared box (direct egress ≈ `140.248.50.x`) |
| Window | 2026-09-22 ≈ 02:40–02:45 UTC |
| Dataplane | VLESS + REALITY + `xtls-rprx-vision` on TCP **443** |
| Panel | 3X-UI **3.8.5** (`Starting x-ui 3.8.5`) |
| Client on box | Xray **26.9.9** |
| Secrets | Held in a sealed local store (not in this repo); evidence below uses **prefixes only** |

**Honesty:** Items 1–3 were measured with the **pre-rotation** `admin-test` UUID (`20bc6cff…`) while panel/sub were still plain HTTP. Another agent then enabled HTTPS, changed `webBasePath` / `subPath`, and rotated client IDs. Post-cutover checks are in §5 / Appendix. Passwords and full tokens are omitted (prefix only).

---

## Summary

| # | Item | Result |
|---|---|---|
| 1 | Exit IP via tunnel | **PASS** |
| 2 | Disconnect → restart → reconnect | **PASS** |
| 3 | Panel traffic counters after ~5 MB | **PASS** |
| 4 | Android error UI (physical phone) | **BLOCKED** (source inspection only) |
| 5 | Security (cleartext / ports / old sub) | **MIXED** — see §5 |

---

## 1. Exit IP — PASS

Temporary Xray on box: SOCKS `127.0.0.1:10808`, HTTP `127.0.0.1:10809`.  
Outbound: VLESS Reality → `117.55.227.224:443`, UUID prefix `20bc6cff…`, flow `xtls-rprx-vision`, SNI `www.microsoft.com`, fp `chrome`, pbk prefix `GyF6uhr4…`, sid prefix `8671495d…`.

```text
$ curl -sS --max-time 15 https://api.ipify.org
140.248.50.8

$ curl -sS --max-time 30 -x socks5h://127.0.0.1:10808 https://api.ipify.org
117.55.227.224

$ curl -sS --max-time 30 -x http://127.0.0.1:10809 https://api.ipify.org
117.55.227.224

$ curl -sS -o /dev/null -w '%{http_code}' --max-time 30 \
    -x socks5h://127.0.0.1:10808 https://www.google.com/generate_204
204
```

**Expected** exit IP `117.55.227.224`. **Observed** match on SOCKS and HTTP inbounds.

---

## 2. Disconnect recovery — PASS

```text
$ kill <xray-pid>
$ curl -sS --max-time 5 -x socks5h://127.0.0.1:10808 https://api.ipify.org
# while_down_rc=7
curl: (7) Failed to connect to 127.0.0.1 port 10808 after 0 ms: Could not connect to server

$ ./xray run -c ./config.json &    # restart
$ curl -sS --max-time 30 -x socks5h://127.0.0.1:10808 https://api.ipify.org
117.55.227.224
```

Second successful IP check after kill + restart.

---

## 3. Traffic stats — PASS

Panel API `GET …/panel/api/inbounds/list` after CSRF login (password not logged).

### Before ~5 MB transfer
```text
inbound_up=31456 inbound_down=10401148
client email=admin-test uuid_prefix=20bc6cff… up=7671 down=18596
client email=user1     uuid_prefix=c65b75e2… up=0    down=0
```

### Transfer (through SOCKS)
```text
transfer_start=2026-09-22T02:42:57Z
$ curl -sS --max-time 120 -x socks5h://127.0.0.1:10808 -o /tmp/xray-client/5mb.bin \
    "https://speed.cloudflare.com/__down?bytes=5242880" \
    -w "http_code=%{http_code} size_download=%{size_download} time_total=%{time_total}\n"
http_code=200 size_download=5242880 time_total=1.366464

$ curl -sS --max-time 60 -x socks5h://127.0.0.1:10808 -o /dev/null \
    -X POST --data-binary @/tmp/xray-client/5mb.bin "https://httpbin.org/post" \
    -w "upload_http=%{http_code} size_upload=%{size_upload}\n"
upload_http=200 size_upload=5242880
transfer_end=2026-09-22T02:43:02Z
```

### After (~8 s settle)
```text
inbound_up=5504280 inbound_down=21159734
client email=admin-test uuid_prefix=20bc6cff… up=5268928 down=10556875
client email=user1     uuid_prefix=c65b75e2… up=0       down=0
```

### VPS SQLite corroboration
```text
admin-test|5268928|10556875|214748364800
user1|0|0|53687091200
inbounds id=1|5504280|21159734
```

**Δ admin-test:** upload ≈ +5.26 MB, download ≈ +10.54 MB (5 MB file + earlier probes + POST response). Counters increased — **PASS**.

---

## 4. Android error prompts — BLOCKED (device) + source evidence

**PHYSICAL DEVICE TEST: BLOCKED** — no user phone attached to this environment.

### Source inspection — `usgate-client` (separate tree)

Strings (`app/src/main/res/values/strings.xml`):

| Resource | UI text |
|---|---|
| `subscription_required` | 请先填写订阅地址或粘贴分享链接 |
| `import_fail` | 导入失败：%1$s |
| `import_ok` | 订阅导入成功，共 %1$d 个节点 |
| `vpn_permission_required` | 需要 VPN 授权才能连接 |
| `need_node` | 请先选择节点 |
| `status_error` | 出错 |

**Bad / empty subscription** (`ui/SettingsFragment.kt`):

- Empty input → Toast `subscription_required`.
- `http(s)://…` → `SubscriptionImporter.importFromUrl`; non-2xx → `error("HTTP ${code}")` → `导入失败：HTTP …`.
- Non-URL text via `importFromText`; URL must start with `http://` or `https://`.

**VPN permission denied** (`ui/HomeFragment.kt`):

- `VpnService.prepare()` → activity result launcher.
- User cancels / denies → Toast `vpn_permission_required`: “需要 VPN 授权才能连接”.
- No custom full-screen dialog beyond the system VPN consent sheet.

---

## 5. Security checks — MIXED

### 5a. Panel / subscription cleartext?

| Phase | Evidence | Verdict |
|---|---|---|
| Start of run | Login + sub fetch over **`http://117.55.227.224:2053/…`** and **`http://117.55.227.224:2096/…`** succeeded (HTTP 200). | **FAIL** — cleartext at that time |
| After ~02:43–02:44 UTC cutover | Journal: `Web server running HTTPS on [::]:2053`, `Sub server running HTTPS on [::]:2096`. Certs under panel cert dir, self-signed `CN=117.55.227.224, O=USGate` (notBefore 2026-09-22, notAfter 2028-12-25). Plain TCP answers `HTTP/0.0 307` → `Location: https://…`. | Cleartext mitigated; **self-signed** only (lab). For customers use LE/Certbot — see `SECURITY.md`. |

### 5b. Open ports

VPS `ss -tlnp` (authoritative):

```text
*:22    sshd
*:443   xray-linux-amd64   (VLESS Reality)
*:2053  x-ui               (panel)
*:2096  x-ui               (subscription)
127.0.0.1:11111  xray      (API, local only)
127.0.0.1:62789  xray      (local only)
```

External probe from box: 22/443/2053/2096 reachable. Port **80** is **not** listening on VPS; `/dev/tcp` “OPEN” was a sandbox/egress false positive (`Server: Pingora`, HTTP 502).

### 5c. Old subscription URL after rotation?

Old credentials (prefix only; full values never published):

- Old sub path prefix: `4hou6fvc…`
- Old admin subId prefix: `8715df8c…`

```text
$ curl -sk -w "code=%{http_code} size=%{size_download}\n" \
    "https://117.55.227.224:2096/<OLD_SUB_PATH>/<OLD_SUB_ID>"
code=404 size=18
# body: 404 page not found
```

New path prefix `d1rpopwu…` + new subId prefix `d7401a88…` → **HTTP 200**, but decoded share link was broken:

```text
vless://1@117.55.227.224:443?flow=xtls-rprx-vision&…#…
```

Panel inbound JSON had `id` corrupted to `"1"` / `"2"` while live Xray clients used UUID prefixes `4eca9210…` / `14772bcd…` (journal showed failed client-update API calls during rotation).

| Question | Result |
|---|---|
| Old sub URL still valid? | **No (404)** — invalidation **PASS** |
| New sub export usable? | **FAIL** — exports UUID `1` |

### 5d. REALITY camouflage spot check

```text
$ openssl s_client -connect 117.55.227.224:443 -servername www.microsoft.com
subject=… CN=www.microsoft.com
issuer=… Microsoft TLS G2 RSA CA OCSP 04
```

---

## Appendix — Post-rotation tunnel spot check

Using rotated UUID from sealed store / live Xray (`4eca9210…`):

```text
new_uuid_proxy_ip=117.55.227.224    # PASS
old_uuid_proxy_ip=FAIL_AS_EXPECTED  # old 20bc6cff… rejected after rotation
```

---

## Artifacts (local box only; do not commit)

| Path | Notes |
|---|---|
| `/tmp/xray-client/test-run.log` | Raw tee log of commands/outputs |
| `/tmp/xray-client/config.json` | Pre-rotation client (contains UUID) |
| `/tmp/xray-client/config-new.json` | Post-rotation client (contains UUID) |
| `/tmp/xray-client/5mb.bin` | 5 242 880-byte download sample |

---

## Overall (honest)

- Dataplane acceptance (exit IP, reconnect, traffic counters): **PASS** on pre-rotation client.
- Android physical error UX: **BLOCKED**.
- Security: historical cleartext **FAIL**; after cutover HTTPS self-signed (lab only); old sub invalidated (**PASS**); **subscription currently advertises broken UUID `1` — do not distribute that link until panel client IDs match Xray.**
