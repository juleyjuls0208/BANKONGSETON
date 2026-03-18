# M006: Standalone Cashier Web App

**Vision:** A dedicated cashier-only web application on port 5010 — clean modern POS UI, fully isolated from the admin dashboard, with all three payment methods (RFID WiFi, QR, NFC) wired and working.

## Success Criteria

- Cashier opens `localhost:5010` in a browser, logs in, builds an order, and completes a sale — without the admin dashboard running
- New UI matches the reference: white background, category sidebar, color-coded product cards, right-side order panel, coral Charge button
- All three payment flows (RFID WiFi tap, QR, NFC phone) complete real sales against Google Sheets
- `run_cashier.bat` starts the app on Windows with a single double-click

## Key Risks / Unknowns

- Arduino WiFi heartbeat target — the R4 firmware is hardcoded to a URL; standalone app needs its own `/api/arduino/heartbeat` and `/api/arduino/card-read` routes so it works when the admin dashboard is off
- SocketIO + Flask session isolation — two apps on different ports, each must have independent session secrets and SocketIO instances

## Proof Strategy

- Arduino heartbeat risk → retire in S03 by verifying Arduino WiFi badge goes green when standalone app is running and admin dashboard is NOT running
- Session isolation → retire in S01 by verifying JWT auth sets cookie correctly and login redirects to POS screen

## Verification Classes

- Contract verification: login flow, product load, JWT decode, payment API responses
- Integration verification: real sale against Google Sheets completes; WiFi badge reflects heartbeat
- Operational verification: app starts on port 5010 with no dependency on port 5003 process
- UAT / human verification: cashier opens URL, builds order, pays — visually confirm new UI

## Milestone Definition of Done

This milestone is complete only when all are true:

- All three slices complete
- Login → POS → payment end-to-end works in the standalone app
- New UI (category sidebar, color-coded cards, coral Charge button) renders correctly
- App starts and functions with admin dashboard off
- `run_cashier.bat` exists and launches the app

## Requirement Coverage

- Covers: R027 (QR payment), R016 (offline queue)
- Partially covers: none
- Leaves for later: none
- Orphan risks: none

## Slices

- [ ] **S01: Standalone Flask app scaffold** `risk:medium` `depends:[]`
  > After this: `python backend/cashier_app/app.py` starts on port 5010; login page loads; JWT auth works; cashier reaches the POS screen (no products yet — product grid placeholder).

- [ ] **S02: New POS UI — product grid and order panel** `risk:low` `depends:[S01]`
  > After this: products load from Google Sheets with category sidebar; color-coded cards; clicking adds to order panel; total updates live; Charge button activates.

- [ ] **S03: Payment flows — RFID, QR, NFC** `risk:medium` `depends:[S02]`
  > After this: full sale end-to-end — RFID WiFi tap deducts balance; QR flow generates token and confirms on student scan; NFC phone tap completes sale. Arduino WiFi badge reflects heartbeat.

## Boundary Map

### S01 → S02

Produces:
- `backend/cashier_app/app.py` — Flask + SocketIO app on port 5010 with login route, JWT middleware, and POS index route
- `backend/cashier_app/templates/login.html` — new modern login page
- `backend/cashier_app/templates/pos.html` — skeleton POS page (layout only, no products yet)
- `backend/cashier_app/routes/auth.py` — `/login` GET, `/api/login` POST, `/api/logout` POST
- JWT auth middleware (jwt_required decorator)
- `run_cashier.bat` launcher

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- `backend/cashier_app/templates/pos.html` — complete POS UI: category sidebar, color-coded product grid, order panel, Charge button
- `backend/cashier_app/routes/pos.py` — `/api/products` GET, `/` GET
- SocketIO client wired to the standalone app's own SocketIO instance

Consumes from S01:
- `app.py` → Flask + SocketIO instance
- `routes/auth.py` → jwt_required decorator

### S02 → S03 (payment routes)

Produces:
- `backend/cashier_app/routes/payment.py` — `/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`
- `backend/cashier_app/routes/arduino.py` — `/api/arduino/heartbeat`, `/api/arduino/card-read`, `/api/arduino/qr-pending`, `/api/arduino/wifi-status`
- SocketIO events: `cashier_request_card`, `sale_complete`, `sale_cancelled`, `qr_payment`

Consumes from S02:
- pos.html → payment button handlers
- `routes/pos.py` → product state (items, total)
- S01 `app.py` → `current_app.pending_qr_token`, `current_app.arduino_last_heartbeat`
