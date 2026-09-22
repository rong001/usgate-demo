# USGate Android Client (docs only)

This folder does **not** ship APK secrets or panel credentials.

## Source

Build from the sibling / separate repository:

- Repo name: `usgate-client`
- Local (lab): sibling directory `../usgate-client` if you keep both trees side-by-side

```bash
# Example — adjust path to your clone of usgate-client
cd ../usgate-client   # or: git clone <YOUR_PUBLIC_OR_PRIVATE_CLIENT_URL>
./gradlew :app:assembleDebug
```

## Importing a subscription (no secrets in this README)

1. Log into the **USGate Portal** as your user.
2. Copy the **subscription link** from the dashboard (masked on screen; copy = full URL).
3. In the Android client (v2rayNG / USGate fork / compatible app):
   - Add subscription → paste URL → update.
4. If you reset the token in the portal, update the subscription again.

## What must never be committed

- Real `VPS_IP`, panel base path, subscription path tokens
- `vless://` share links with live UUIDs from production
- Keystore passwords, `local.properties` with machine paths if sensitive
- Any `.env` from the portal

Use placeholders in public docs: `VPS_IP`, `PANEL_PATH`, `SUB_PATH`, `YOUR_SUB_ID`.

## Branding / landing

Optional marketing assets may live under the client repo (`landing/`, `branding-previews/`). They are not required to run the portal demo.
