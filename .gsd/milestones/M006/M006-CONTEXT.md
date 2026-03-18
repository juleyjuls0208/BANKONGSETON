# M006: Standalone Cashier Web App

**Gathered:** 2026-03-18
**Status:** Ready for planning

## Project Description

A standalone cashier-only web application that runs on port 5010, separate from the admin dashboard. Cashiers go to a different URL and see only what they need — a clean POS interface with no admin noise.

## Why This Milestone

The cashier UI currently lives as a blueprint inside the admin dashboard Flask process. Cashiers interact with the same server as the admin, creating unnecessary coupling. A standalone app gives cashiers a dedicated, purpose-built URL and lets the two processes run (or fail) independently.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Open `localhost:5010` (or `<LAN_IP>:5010`), log in as cashier, and complete a full sale without the admin dashboard running
- Select products from a modern POS grid (category sidebar, color-coded cards), build an order, and pay via RFID card tap, QR scan, or NFC phone tap
- See the WiFi Arduino status badge and the offline queue indicator in the new UI

### Entry point / environment

- Entry point: `python backend/cashier_app/app.py` (or a `.bat` launcher)
- Environment: local dev / LAN (school canteen network)
- Live dependencies involved: Google Sheets (same credentials), SocketIO (own instance), Arduino WiFi heartbeat

## Completion Class

- Contract complete means: all three payment flows complete a real sale against Google Sheets; new UI renders correctly
- Integration complete means: RFID WiFi tap, QR flow, and NFC phone flow each close a pending_transaction in the standalone app's own SocketIO instance
- Operational complete means: app starts fresh on port 5010 with no dependency on the admin dashboard process

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Cashier opens `localhost:5010`, logs in with cashier credentials, builds an order, taps RFID card → sale completes, balance deducted in Google Sheets
- QR flow: cashier hits QR button → token generated → student scans → sale confirms
- App starts and functions when admin dashboard (port 5003) is NOT running

## Risks and Unknowns

- `pending_qr_token` is stored on `current_app` (in-memory, process-local) — the standalone app owns its own instance, so this is fine as long as the QR routes live in the new app, not the old one
- SocketIO `pending_transaction` session state — must verify Flask session works correctly across the new app's own session secret
- Arduino WiFi heartbeat currently handled by the admin dashboard's `/api/arduino/heartbeat` route — the standalone app needs its own heartbeat endpoint so the Arduino can keep reporting to whichever server is active

## Existing Codebase / Prior Art

- `backend/dashboard/cashier/cashier_routes.py` — existing Blueprint with all payment logic; will be extracted/reused
- `backend/dashboard/cashier/templates/cashier_index.html` — existing POS template; will be completely replaced
- `backend/dashboard/cashier/templates/cashier_login.html` — existing login; will be replaced
- `backend/dashboard/web_app.py` — reference for Flask + SocketIO bootstrap pattern; port 5003
- `backend/dashboard/arduino_bridge.py` — ArduinoBridge used by cashier_routes; same import path
- `backend/cache.py`, `backend/offline_queue.py` — shared backend modules; same import path

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R027 — QR payment flow (M005/S03 validated)
- R016 — Offline queue (M001/S05 validated)

## Scope

### In Scope

- New standalone Flask app at `backend/cashier_app/app.py`
- New UI: login page (modern POS aesthetic), POS screen (category sidebar + color-coded product grid + order panel + Charge button)
- Port 5010, own SocketIO instance, own session secret
- All three payment flows: RFID WiFi, QR, NFC phone
- Arduino WiFi status badge
- Offline queue status indicator
- A `run_cashier.bat` launcher for Windows

### Out of Scope / Non-Goals

- PythonAnywhere deployment — local/LAN only
- Admin features (fraud alerts, student management, cashier account management, exports)
- Product images in Google Sheets — color-coded category cards only
- Changes to the existing admin dashboard or its cashier blueprint

## Technical Constraints

- Must reuse `backend/dashboard/cashier/cashier_routes.py` logic (copy or import) — not reinvent payment logic
- Shares Google Sheets credentials (`credentials.json`) and `.env` variables
- Arduino WiFi heartbeat endpoint must exist in the new app (Arduino sends to one fixed URL; in LAN-only mode this will be the cashier app)
- Flask session secret must be set independently from admin dashboard

## Integration Points

- Google Sheets — same spreadsheet, same credentials.json
- Arduino UNO R4 WiFi — heartbeat and card-read events route to whichever Flask server the Arduino is configured to hit
- Twilio SMS, Firebase FCM — same env vars, same notification path post-sale
- SocketIO — own instance on port 5010; admin dashboard SocketIO on 5003 is unaffected

## Open Questions

- None — all decisions locked from discussion
