---
estimated_steps: 5
estimated_files: 4
---

# T02: Port Arduino heartbeat/card and QR confirmation contracts into standalone app

**Slice:** S03 — Payment flows — RFID, QR, NFC
**Milestone:** M006

## Description

Move Arduino-facing and student QR-confirmation endpoints into `backend/cashier_app` so firmware and mobile flows operate entirely against port 5010. Preserve API-key auth, token lifecycle, and emit-before-clear ordering used by existing production behavior.

Relevant skills to load: `fullstack-developer`, `test`.

## Steps

1. Create `backend/cashier_app/routes/arduino.py` with API-key-gated routes `/api/arduino/heartbeat`, `/api/arduino/card-read`, and `/api/arduino/qr-pending` adapted from `backend/dashboard/web_app.py`.
2. Implement WiFi status route as `/api/arduino/wifi-status` and keep compatibility alias `/api/arduino-wifi-status` returning the same payload shape.
3. Port QR student routes `/api/qr/<token>` and `/api/qr/confirm` to standalone app, using `current_app.pending_qr_token` and preserving `socketio.emit('qr_payment', ...)` before pending-token clear.
4. Add tests in `tests/test_cashier_app_arduino_routes.py` for API-key enforcement, heartbeat freshness reporting, qr-pending payload behavior, token expiry/not-found, insufficient funds (402), and confirm success clearing lifecycle.
5. Execute tests and adjust edge-case behavior until route contracts are stable.

## Must-Haves

- [ ] Standalone app serves firmware-required Arduino routes with API-key enforcement.
- [ ] `/api/arduino/wifi-status` contract is available and backward-compatible alias is retained.
- [ ] QR cart + confirm routes work in standalone app and preserve emit-then-clear ordering.
- [ ] Automated tests verify auth, status, and failure-path semantics for Arduino/QR routes.

## Verification

- `rtk proxy python -m py_compile backend/cashier_app/routes/arduino.py`
- `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q`

## Observability Impact

- Signals added/changed: heartbeat timestamps, online/offline computed status, `card_read` and `qr_payment` SocketIO emissions.
- How a future agent inspects this: query `/api/arduino/wifi-status` + `/api/arduino/qr-pending`, run Arduino route tests, inspect Flask logs for API-key and token-state failures.
- Failure state exposed: explicit 401 (bad API key), 404 (missing/expired token), and 402 (insufficient funds) become externally visible and test-asserted.

## Inputs

- `backend/dashboard/web_app.py` — Source of Arduino + QR route behavior and ordering constraints.
- `backend/cashier_app/app.py` — App-level state holder (`pending_qr_token`, heartbeat state, SocketIO instance).
- `arduino/bankongseton_r4/bankongseton_r4.ino` — Firmware-fixed endpoint/header contract to preserve.
- `.gsd/milestones/M006/slices/S03/S03-RESEARCH.md` — Known pitfalls: route naming drift, API-key mismatch, token clear race.

## Expected Output

- `backend/cashier_app/routes/arduino.py` — New standalone Arduino + QR route blueprint.
- `backend/cashier_app/app.py` — Blueprint registration/alias wiring if needed.
- `tests/test_cashier_app_arduino_routes.py` — New standalone route contract tests for Arduino and QR token lifecycle.
- `.gsd/DECISIONS.md` — Route contract clarification captured if alias/canonical naming is formalized during implementation.
