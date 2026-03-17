---
id: T02
parent: S03
milestone: M005
provides:
  - POST /cashier/api/qr-generate route (cashier JWT) in cashier_routes.py — creates UUID token, sets current_app.pending_qr_token, returns {token, url}
  - POST /api/qr/confirm route (student JWT) in web_app.py — validates token, debits balance via 3-retry/rollback/offline-queue pattern, emits qr_payment SocketIO event, clears token
  - socket.on('qr_payment', ...) handler in cashier_index.html — shows success modal with new balance, clears cart
key_files:
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/web_app.py
  - backend/dashboard/cashier/templates/cashier_index.html
key_decisions:
  - qr_generate uses current_app.pending_qr_token (not bare app.) because it runs inside the cashier blueprint; bare app. would be RuntimeError outside application context
  - json imported at module level in web_app.py (was missing); added alongside existing os/sys/logging/time imports
  - os.getenv used directly in qr_generate (os imported at module level in cashier_routes.py — no inner import needed)
  - socketio.emit('qr_payment') fires BEFORE app.pending_qr_token = None in all code paths to prevent timing edge case
patterns_established:
  - QR debit clones complete_sale() retry/rollback/offline-queue pattern exactly: 3-attempt loop, exponential backoff (2^attempt), rollback on balance_deducted, offline_queue fallback, emit+clear on all success paths
  - 402 used for insufficient-funds (not 400) so mobile apps can distinguish it from bad-request
  - "QR Purchase" transaction type distinguishes QR debit from NFC "Purchase" in audit trail
observability_surfaces:
  - Flask log: grep 'event=qr_generate' — fires on each successful token creation with token UUID and total
  - Flask log: grep 'event=qr_confirm' — fires on successful debit with student_id, total, new_balance
  - Flask log: grep 'event=qr_offline_queued' — fires when Sheets unavailable but transaction queued
  - Flask log: grep 'event=qr_offline_queue_failed' — fires when offline queue itself fails
  - SocketIO: cashier UI receives 'qr_payment' event with {success, new_balance, timestamp, total, cashier}
  - GET /api/arduino/qr-pending with X-API-Key: returns {token: null} after successful confirm (confirms token cleared)
duration: ~25 minutes
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T02: Implement `qr/confirm` debit + `qr-generate` cashier route + `qr_payment` socket handler

**Added QR payment money-moving layer: cashier generates token via `/cashier/api/qr-generate`, student confirms via `/api/qr/confirm` which debits balance with retry/rollback and emits `qr_payment` to cashier UI.**

## What Happened

Implemented all three components of the money-moving QR payment flow:

1. **`cashier_routes.py`**: Added `import uuid` at module level; added `POST /cashier/api/qr-generate` route that uses `current_app.pending_qr_token` (blueprint-safe), reads `SERVER_URL` from env (returns 500 if blank), generates UUID token, stores full cart snapshot, logs `event=qr_generate`.

2. **`web_app.py`**: Added `import json` at module level (was missing). Added `POST /api/qr/confirm` route that decodes student JWT via `_decode_student_jwt()`, validates token match and 5-min expiry, looks up student's MoneyCardNumber from Users sheet, reads Money Accounts fresh (D018), checks card status and balance, then runs the 3-retry debit loop with exponential backoff. On all-retries-exhausted: rolls back balance if deducted, queues to offline_queue, emits `qr_payment` with `offline: True`, clears token. On success: emits `qr_payment` BEFORE clearing `app.pending_qr_token`, logs `event=qr_confirm`, attempts non-fatal FCM push.

3. **`cashier_index.html`**: Inserted `socket.on('qr_payment', ...)` handler immediately after the `nfc_payment` handler. Shows "QR Payment Received!" modal with new balance formatted with peso sign (₱), clears cart, calls `checkQueueStatus()`, auto-closes after 2 seconds.

## Verification

All 8 task-level grep and compile checks passed:
```
PASS: web_app.py compiles
PASS: cashier_routes.py compiles
PASS: qr/confirm route exists
PASS: qr_payment emit exists
PASS: qr-generate route exists
PASS: pending_qr_token used in cashier_routes
PASS: SERVER_URL env read
PASS: socket handler added in cashier_index.html
```

All 8 must-have checks passed:
```
PASS: import uuid present
PASS: QR Purchase transaction type
PASS: 402 for insufficient funds
PASS: event=qr_generate logged
PASS: event=qr_confirm logged
PASS: uses current_app (not bare app) in blueprint
PASS: no bare app.pending_qr_token in cashier_routes
PASS: emit before clear in qr_confirm
```

Both Python files pass `python -m py_compile`. The slice verification script `scripts/verify-m005-s03.sh` does not yet exist — to be created by a subsequent task.

## Diagnostics

- Inspect pending QR state: `GET /api/arduino/qr-pending` with `X-API-Key: <ARDUINO_API_KEY>` — returns `{"token": null}` after successful confirm (confirms clear); returns `{"token": "...", "url": "..."}` when active
- Confirm route present: `grep 'event=qr_confirm' <flask_log>` — fires with student_id, total, new_balance on every successful debit
- Confirm token generation: `grep 'event=qr_generate' <flask_log>` — fires with token UUID and total
- Cashier UI: `qr_payment` SocketIO event visible in browser devtools WebSocket frame after student confirms

## Deviations

None — implementation matches the plan exactly. `os.getenv` used directly in `qr_generate` (no inner `import os as _os` needed since `os` is cleanly imported at module level). `import json` added at module level in `web_app.py` rather than inline per the plan's note to add it if missing.

## Known Issues

None.

## Files Created/Modified

- `backend/dashboard/cashier/cashier_routes.py` — added `import uuid`; added `POST /cashier/api/qr-generate` route
- `backend/dashboard/web_app.py` — added `import json`; added `POST /api/qr/confirm` route
- `backend/dashboard/cashier/templates/cashier_index.html` — added `socket.on('qr_payment', ...)` handler after `nfc_payment`
