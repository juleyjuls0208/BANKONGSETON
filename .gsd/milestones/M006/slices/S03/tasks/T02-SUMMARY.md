---
id: T02
parent: S03
milestone: M006
provides:
  - Standalone Arduino + QR confirmation route contracts on port 5010 with API-key gating, heartbeat freshness status, and QR emit-before-clear lifecycle
key_files:
  - backend/cashier_app/routes/arduino.py
  - backend/cashier_app/app.py
  - tests/test_cashier_app_arduino_routes.py
  - .gsd/milestones/M006/slices/S03/S03-PLAN.md
key_decisions:
  - Reused standalone payment helper contracts inside QR confirm to preserve retry/rollback/offline-queue behavior and 402 insufficient-funds semantics
  - Formalized `/api/arduino/wifi-status` as canonical and retained `/api/arduino-wifi-status` alias with identical payload
patterns_established:
  - Verify emit-before-clear ordering by asserting token presence during `socketio.emit('qr_payment', ...)` in route-contract tests
  - Keep firmware-facing routes API-key protected while exposing cashier WiFi diagnostics through cashier JWT cookie auth
observability_surfaces:
  - /api/arduino/wifi-status
  - /api/arduino/qr-pending
  - SocketIO events: card_read, arduino_wifi_status, qr_payment
  - tests/test_cashier_app_arduino_routes.py
duration: 1h 28m
verification_result: passed
completed_at: 2026-03-19
blocker_discovered: false
---

# T02: Port Arduino heartbeat/card and QR confirmation contracts into standalone app

**Added a standalone Arduino+QR route blueprint with API-key auth, heartbeat/wifi status diagnostics, and QR confirm lifecycle guarantees, then validated it with dedicated route-contract tests.**

## What Happened

Implemented `backend/cashier_app/routes/arduino.py` with Arduino firmware routes (`/api/arduino/heartbeat`, `/api/arduino/card-read`, `/api/arduino/qr-pending`), WiFi status endpoints (`/api/arduino/wifi-status` + alias `/api/arduino-wifi-status`), and student QR endpoints (`/api/qr/<token>`, `/api/qr/confirm`).

Ported production semantics from dashboard routes into standalone app context: API-key enforcement, UID validation, QR token TTL handling, explicit 401/404/410/402 failure contracts, and QR confirm `socketio.emit('qr_payment', ...)` before `pending_qr_token` clear.

Reused standalone payment internals for debit retry/rollback/offline queue fallback so QR payments align with existing money-safe behavior introduced in T01.

Updated `backend/cashier_app/app.py` to register the new `arduino_bp` blueprint and expose `ARDUINO_API_KEY` through app config.

Added `tests/test_cashier_app_arduino_routes.py` covering API-key failures, heartbeat freshness/online-offline state, wifi-status alias parity, qr-pending lifecycle, student auth failures, QR token expiry/missing behavior, insufficient funds (402), and successful confirm clear lifecycle with emit-before-clear assertion.

Marked T02 complete in `.gsd/milestones/M006/slices/S03/S03-PLAN.md`.

## Verification

Ran task-level verification commands from T02 plan (compile + dedicated Arduino route tests), then executed all automated slice-level checks. All Python compile/test checks now pass for payment/arduino/pos route suites.

Executed runtime slice verification attempt with standalone server only and browser flow on `localhost:5010`; login/redirect to POS and no `:5003` resource dependency check passed, while full runtime assert bundle failed due current local POS product fetch failing with 500 (Google Sheets unavailable in this environment), which is outside T02 route-contract code changes.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile backend/cashier_app/routes/arduino.py` | 0 | ✅ pass | <1s |
| 2 | `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q` | 0 | ✅ pass | 1.16s |
| 3 | `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py` | 0 | ✅ pass | <1s |
| 4 | `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q` | 0 | ✅ pass | 1.19s |
| 5 | `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q` | 0 | ✅ pass | 1.19s |
| 6 | `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` | 0 | ✅ pass | 1.18s |
| 7 | `browser_batch: login -> POS load -> assertions` | 1 | ❌ fail | ~3s |
| 8 | `browser_assert + browser_get_network_logs + browser_get_console_logs` | 1 | ❌ fail | ~2s |
| 9 | `browser_evaluate("performance.getEntriesByType('resource').filter(:5003)")` | 0 | ✅ pass | <1s |

## Diagnostics

- `GET /api/arduino/wifi-status` and `GET /api/arduino-wifi-status` now expose heartbeat freshness and online/offline state consistently.
- `GET /api/arduino/qr-pending` reports token/url or `{token: null}` when missing/expired.
- `POST /api/arduino/card-read` emits `card_read`; `POST /api/arduino/heartbeat` emits `arduino_wifi_status`; `POST /api/qr/confirm` emits `qr_payment` before token clear.
- Route-contract tests assert explicit failure contracts: 401 bad API key/auth, 404 token-not-found, 410 token-expired, 402 insufficient funds.

## Deviations

None.

## Known Issues

- Runtime browser integration assertion currently fails in this local environment because `/api/products` returns 500 (Sheets unavailable), resulting in failed-request/console-error checks during POS page load.
- Full end-to-end RFID/QR/NFC runtime UAT (with healthy Sheets/hardware environment) remains to be completed in downstream slice tasks.

## Files Created/Modified

- `backend/cashier_app/routes/arduino.py` — new standalone blueprint for Arduino heartbeat/card/qr-pending + wifi status alias + student QR cart/confirm routes.
- `backend/cashier_app/app.py` — registered `arduino_bp` and added `ARDUINO_API_KEY` config wiring.
- `tests/test_cashier_app_arduino_routes.py` — new route-contract test suite for Arduino and QR token lifecycle behavior.
- `.gsd/milestones/M006/slices/S03/S03-PLAN.md` — marked T02 as complete (`[x]`).
