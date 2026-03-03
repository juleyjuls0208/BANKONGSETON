---
phase: 07-cashier-payment-fix
plan: "01"
subsystem: payments
tags: [websocket, socketio, arduino, fcm, push-notifications, cashier, rfid, transactions]

# Dependency graph
requires:
  - phase: 04-student-app-notifications
    provides: FCM send_low_balance_push pattern from api_server.py

provides:
  - handle_cashier_request_card WebSocket handler in admin_dashboard.py
  - 8-column transaction row with BalanceBefore at col 4
  - FCM low-balance push notification in cashier complete_sale path
  - Frontend re-emit of cashier_request_card to complete WebSocket loop

affects: [cashier-pos, rfid-card-read, android-app-balance-display, fcm-notifications]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "WebSocket broadcast-then-re-emit pattern for server-to-Arduino trigger via client relay"
    - "FCM block mirroring api_server.py pattern: Settings threshold + Users FCM token lookup, non-blocking try/except"

key-files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/cashier/cashier_routes.py
    - backend/dashboard/cashier/templates/cashier_index.html

key-decisions:
  - "lambda uid: None callback is intentional — ArduinoBridge already calls socketio.emit('card_read') internally"
  - "sys.path.insert to backend/api/ inside try block for fcm_sender import — mirrors existing cashier_routes email_service pattern"
  - "flask_session.pop('pending_transaction') moved to before FCM block, removing duplicate from original location"

patterns-established:
  - "WebSocket server->client->server relay: server emits broadcast, client socket.on receives it and socket.emit re-emits back, server @socketio.on handler fires"
  - "FCM block always wrapped in outer try/except to never block or rollback main transaction response"

requirements-completed: [BUG-01, APP-02, APP-04, NOTF-01]

# Metrics
duration: 2min
completed: 2026-03-01
---

# Phase 7 Plan 01: Cashier Payment Fix Summary

**Wired cashier POS RFID card-read path end-to-end: server WebSocket handler, 8-column transaction row with BalanceBefore, and FCM low-balance push notification**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T08:18:38Z
- **Completed:** 2026-03-01T08:20:09Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `admin_dashboard.py`: Added `@socketio.on('cashier_request_card')` handler that calls `arduino_bridge.read_card_with_timeout(lambda uid: None, timeout=5)` with `getattr(app, 'arduino_bridge', None)` guard
- `cashier_routes.py`: Fixed transaction_row from 7 to 8 columns by inserting `current_balance` at index 4 (BalanceBefore); Android app will now show correct pre-transaction balance
- `cashier_routes.py`: Added FCM low-balance push notification block after transaction commit, mirroring `api_server.py` pattern with Settings threshold + Users FCM token lookup
- `cashier_index.html`: Added `socket.on('cashier_request_card')` handler that re-emits back to server, completing the WebSocket relay loop

## Task Commits

Each task was committed atomically:

1. **Task 1: Add cashier_request_card WebSocket handler in admin_dashboard.py** - `bc00c3f` (feat)
2. **Task 2: Fix cashier_routes.py — 8-column row, FCM block, frontend WebSocket re-emit** - `6d17437` (fix)

**Plan metadata:** `30a7327` (docs: complete plan)

## Self-Check: PASSED

- ✅ `.planning/phases/07-cashier-payment-fix/07-01-SUMMARY.md` exists
- ✅ `bc00c3f` (Task 1 commit) found in git log
- ✅ `6d17437` (Task 2 commit) found in git log
- ✅ All Python files parse without syntax errors
- ✅ `handle_cashier_request_card` present in admin_dashboard.py
- ✅ `current_balance, # col 4` present in cashier_routes.py
- ✅ `send_low_balance_push` call present in cashier_routes.py
- ✅ `cashier_request_card` re-emit handler present in cashier_index.html

## Files Created/Modified

- `backend/dashboard/admin_dashboard.py` - Added `handle_cashier_request_card` SocketIO handler before `handle_connect`
- `backend/dashboard/cashier/cashier_routes.py` - 8-column transaction_row + FCM low-balance push notification block
- `backend/dashboard/cashier/templates/cashier_index.html` - Added `cashier_request_card` re-emit handler in `initWebSocket()`

## Decisions Made

- `lambda uid: None` callback is intentional — ArduinoBridge already calls `socketio.emit('card_read', {'uid': uid})` internally; no additional callback logic needed
- `sys.path.insert(0, backend/api/)` inside the FCM try block mirrors the existing pattern for `email_service` in the same file
- `flask_session.pop('pending_transaction', None)` kept before the FCM block (no duplicate) to preserve correct session cleanup ordering

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - `cashier_routes.py` uses Thai Baht symbol (฿) which causes `cp1252` codec error when Python opens the file without explicit UTF-8 encoding. Worked around by passing `encoding='utf-8'` to the AST parse verification command. The file itself is unchanged and correctly encoded.

## Next Phase Readiness

- End-to-end cashier POS card-read path is wired: tap card → Arduino reads UID → SocketIO events propagate → `complete_sale()` records 8-column row → FCM push fires if balance below threshold
- Android app will now display correct BalanceBefore in transaction history
- Ready for further cashier/payment testing or next phase work

---
*Phase: 07-cashier-payment-fix*
*Completed: 2026-03-01*
