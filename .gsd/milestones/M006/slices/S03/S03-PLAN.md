# S03: Payment flows — RFID, QR, NFC

**Goal:** Deliver standalone cashier payment runtime on port 5010 so RFID, QR, and NFC-compatible sale completion all execute inside `backend/cashier_app` (no dependency on admin dashboard routes/process).
**Demo:** With only `backend/cashier_app/app.py` running, cashier logs in at `http://localhost:5010`, builds an order, and completes payment via RFID WiFi tap, QR confirmation flow, and `/api/complete-sale-nfc` path while Arduino WiFi heartbeat status is visible.

## Must-Haves

- Advance **R053** by completing sale-capable standalone runtime (not UI-only)
- Add standalone payment APIs in `backend/cashier_app/routes/payment.py`: `/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`
- Add standalone Arduino + QR APIs in `backend/cashier_app/routes/arduino.py`: `/api/arduino/heartbeat`, `/api/arduino/card-read`, `/api/arduino/qr-pending`, `/api/arduino/wifi-status` (+ compatibility alias), `/api/qr/<token>`, `/api/qr/confirm`
- Preserve battle-tested money safety behavior (retry/rollback/offline queue fallback) from existing cashier flow logic
- Wire POS checkout UI to standalone payment routes and SocketIO events without breaking S02 product/cart architecture
- Keep firmware/mobile contracts intact for active QR/OLED flow continuity (`R027`, `R028`, `R029` behavior contracts)

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py`
- `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q`
- `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q`
- `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q`
- Runtime integration (admin dashboard off): start `rtk proxy python backend/cashier_app/app.py`, then verify login → cart → charge for RFID/QR/NFC path from `localhost:5010` and confirm no `:5003` resources via `performance.getEntriesByType('resource')`

## Observability / Diagnostics

- Runtime signals: SocketIO `cashier_request_card`, `sale_complete`, `sale_cancelled`, `qr_payment`, and Arduino WiFi heartbeat timestamp/state transitions
- Inspection surfaces: `/api/queue/status`, `/api/queue/sync`, `/api/arduino/wifi-status`, `/api/arduino/qr-pending`, POS payment-status/WiFi indicators, pytest route-contract assertions
- Failure visibility: route JSON errors for auth/API key/insufficient funds/Sheets outage; queue fallback state returned by payment endpoints; heartbeat freshness exposed in wifi-status response
- Redaction constraints: never log raw JWTs, `ARDUINO_API_KEY`, or full sensitive card/token values

## Integration Closure

- Upstream surfaces consumed: `backend/dashboard/cashier/cashier_routes.py`, `backend/dashboard/web_app.py`, `backend/offline_queue.py`, S01 auth middleware (`request.cashier_data`), S02 POS state/render pipeline
- New wiring introduced in this slice: standalone app blueprint registration for payment+arduino routes, `app.socketio` attachment, POS payment orchestration to standalone APIs and events
- What remains before the milestone is truly usable end-to-end: nothing beyond final live hardware UAT and operational launch using `run_cashier.bat`

## Tasks

- [x] **T01: Port standalone payment APIs and money-safe queue behavior** `est:1h 30m`
  - Why: Sale completion cannot happen in standalone mode until payment endpoints are ported with correct auth context and offline fallback semantics.
  - Files: `backend/cashier_app/app.py`, `backend/cashier_app/routes/payment.py`, `tests/test_cashier_app_payment_routes.py`, `backend/cashier_app/routes/auth.py`
  - Do: Create `payment.py` by adapting proven handlers from dashboard cashier routes; switch contracts to standalone paths/auth (`request.cashier_data`), keep retry/rollback/offline queue behavior, expose queue endpoints, and register blueprint/runtime wiring in `app.py` (including `app.socketio`).
  - Verify: `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py && rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q`
  - Done when: All standalone payment endpoints respond under cashier auth, queue fallback behavior is covered by tests, and payment route tests pass.

- [x] **T02: Port Arduino heartbeat/card and QR confirmation contracts into standalone app** `est:1h 20m`
  - Why: RFID WiFi + OLED QR flows depend on firmware-fixed Arduino routes and student QR confirmation endpoints being available on port 5010.
  - Files: `backend/cashier_app/routes/arduino.py`, `backend/cashier_app/app.py`, `tests/test_cashier_app_arduino_routes.py`, `arduino/bankongseton_r4/bankongseton_r4.ino`
  - Do: Implement Arduino API-key-gated heartbeat/card routes, qr-pending, wifi-status (+ compatibility alias), and student QR token/confirm endpoints with emit-then-clear ordering against `current_app.pending_qr_token`; register blueprint and keep heartbeat state on app object.
  - Verify: `rtk proxy python -m py_compile backend/cashier_app/routes/arduino.py && rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q`
  - Done when: Firmware and student-app route contracts are served by standalone app, heartbeat status is queryable, and Arduino/QR route tests pass.

- [x] **T03: Wire POS charge orchestration for RFID, QR, and NFC-compatible checkout** `est:1h 30m`
  - Why: Backend routes alone do not close R053 — cashier needs end-to-end checkout UX and event handling in the standalone POS.
  - Files: `backend/cashier_app/templates/pos.html`, `tests/test_cashier_app_pos_route.py`, `backend/cashier_app/routes/payment.py`, `backend/cashier_app/routes/arduino.py`
  - Do: Extend POS payment controls and status handling while preserving S02 cart/render architecture; wire checkout actions to standalone APIs (`process-sale`, `complete-sale`, `complete-sale-nfc`, `qr-generate`, cancel/queue status) and SocketIO events (`card_read`, `qr_payment`, completion/cancel + WiFi status) with explicit failure states.
  - Verify: `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` plus runtime UAT on `localhost:5010` with admin dashboard off for RFID/QR/NFC path and `performance.getEntriesByType('resource')` showing no `:5003` dependency.
  - Done when: Cashier can complete all three payment paths from standalone POS UI and automated route/template verifications pass.

## Files Likely Touched

- `backend/cashier_app/app.py`
- `backend/cashier_app/routes/payment.py`
- `backend/cashier_app/routes/arduino.py`
- `backend/cashier_app/templates/pos.html`
- `tests/test_cashier_app_payment_routes.py`
- `tests/test_cashier_app_arduino_routes.py`
- `tests/test_cashier_app_pos_route.py`
