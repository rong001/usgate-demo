# USGate Android Client (docs pointer)

This folder does **not** ship APKs, secrets, or panel credentials.

## Public source (now available)

The Android client source is public:

- **Repository:** [https://github.com/rong001/usgate-client](https://github.com/rong001/usgate-client)
- Local lab sibling (optional): `../usgate-client`

```bash
git clone https://github.com/rong001/usgate-client.git
cd usgate-client
# create local.properties with sdk.dir=...
./gradlew :app:fetchLibbox :app:assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

License notes, sing-box/libbox GPL notices, and reproducible-build steps live in that repo (`LICENSE`, `THIRD_PARTY_NOTICES.md`, `docs/BUILD_REPRO.md`).

## Importing a subscription (no secrets in this README)

1. Log into the **USGate Portal** as your user.
2. Copy the **subscription link** from the dashboard (masked on screen; copy = full URL).
3. In the Android client:
   - Settings → paste URL → save → import subscription → pick a node → Connect.
4. If you reset the token in the portal, update the subscription again.

## What must never be committed

- Real `VPS_IP`, panel base path, subscription path tokens
- `vless://` share links with live UUIDs from production
- Keystore passwords, `local.properties` with machine paths if sensitive
- Any `.env` from the portal

Use placeholders in public docs: `VPS_IP`, `PANEL_PATH`, `SUB_PATH`, `YOUR_SUB_ID`.

## Branding / landing

Optional marketing assets live under the client repo (`landing/`, `branding-previews/`). They are not required to run the portal demo.

## Related

| Repo | Role |
|------|------|
| [rong001/usgate-demo](https://github.com/rong001/usgate-demo) | This monorepo — portal + docs |
| [rong001/usgate-client](https://github.com/rong001/usgate-client) | Public Android client source |
