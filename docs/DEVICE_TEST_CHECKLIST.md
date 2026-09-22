# USGate Android — Device Test Checklist

Run this on your phone after installing the USGate APK. Check each box and note pass/fail.

> CI does **not** PASS exit-IP / reconnect / traffic. See [`ANDROID_CI_STATUS.md`](ANDROID_CI_STATUS.md).

**Server:** `VPS_IP` (lab only — do not commit real IPs)  
**Expected exit IP when connected:** `VPS_IP`  
**Do not screenshot full subscription URLs or UUIDs into chats; mask to first 8 chars if sharing.**

> After a secret rotation, use the **new** HTTPS subscription from the panel (or your operator’s sealed secret store). Old HTTP subscription paths (prefix `4hou6fvc…`) should **404**. If import shows a node whose UUID is literally `1` or `2`, the panel export is broken — ask for a repaired link before continuing.

---

## A. Install & first launch

- [ ] Install APK (debug/release build from `usgate-client`)
- [ ] App opens to 首页; status shows **未连接**
- [ ] Bottom nav: 首页 / 节点 / 设置 works

## B. Subscription import — happy path

- [ ] Open **设置**
- [ ] Paste subscription URL (HTTPS, current path/subId from panel)
- [ ] Tap **导入订阅**
- [ ] See **订阅导入成功，共 N 个节点** (N ≥ 1)
- [ ] Open **节点**; list is non-empty; select one (toast **已选择：…**)

## C. Subscription import — error paths

- [ ] Clear the field, tap **导入订阅** → Toast **请先填写订阅地址或粘贴分享链接**
- [ ] Paste a garbage URL like `http://127.0.0.1:9/nope` → **导入失败：** with connection/HTTP error text
- [ ] Paste old HTTP sub URL (path prefix `4hou6fvc…`) → expect fail / HTTP 404 (after rotation)
- [ ] Paste non-http text that is not a share link → fail or **0** nodes (record what you see)

## D. VPN permission denied

- [ ] Select a node, tap **连接**
- [ ] On system VPN consent dialog, tap **取消 / Deny**
- [ ] Expect Toast **需要 VPN 授权才能连接**
- [ ] Status remains **未连接**

## E. Connect success

- [ ] Tap **连接** again; **Allow** VPN permission
- [ ] Status → **连接中…** then **已连接**
- [ ] Persistent notification: **USGate** / **安全隧道运行中**
- [ ] In Chrome/Firefox open `https://api.ipify.org` → must show **`VPS_IP`**
- [ ] Open a US site (e.g. google.com) — page loads

## F. Disconnect & recover

- [ ] Tap **断开** → status **未连接**; notification clears
- [ ] `api.ipify.org` shows your normal cellular/Wi‑Fi IP (not the VPS)
- [ ] Tap **连接** again → **已连接**; `api.ipify.org` again **`VPS_IP`**

## G. Optional traffic sanity

- [ ] While connected, download a ~5–10 MB file
- [ ] In 3X-UI panel → inbound/client traffic for your email increased (ask operator if no panel access)

## H. Notes / failures

| Step | Pass/Fail | Notes |
|---|---|---|
| B happy import |  |  |
| C empty URL toast |  |  |
| C bad URL message |  |  |
| D VPN deny toast |  |  |
| E exit IP |  |  |
| F reconnect |  |  |

Device model / Android version: ______________________  
App version / build: ______________________  
Date: ______________________
