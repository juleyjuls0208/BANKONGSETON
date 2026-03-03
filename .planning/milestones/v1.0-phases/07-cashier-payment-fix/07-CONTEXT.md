# Phase 7: Fix Cashier Payment Path - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the gaps in the RFID → payment → notification chain so a card tap at the cashier POS
completes a full, correctly-recorded transaction with FCM notification. Specifically:

- Wire `cashier_request_card` WebSocket event to `ArduinoBridge.read_card_with_timeout()`
- Fix `complete_sale()` to write an 8-column transaction row (add `balance_before`)
- Wire FCM low-balance push notification into `cashier_routes.py complete_sale()`
- Fix Android `ReceiptActivity` to display timestamps as readable strings
- Call `migrate_users_schema()` at `api_server.py` module-level startup

New capabilities (threshold configuration UI, new notification types, etc.) are out of scope.

</domain>

<decisions>
## Implementation Decisions

### cashier_request_card WebSocket Wiring
- Add `@socketio.on('cashier_request_card')` handler in `admin_dashboard.py` alongside existing card event handlers
- Handler calls `arduino_bridge.read_card_with_timeout(callback, timeout=5)`
- On card read success: callback stores the UID in the Flask session so the subsequent `complete_sale` POST can consume it
- On timeout: reuse existing `card_timeout` event — frontend already listens and handles it; no new event needed
- On error: reuse existing `card_error` event

### Transaction Row Schema (complete_sale fix)
- `cashier_routes.py complete_sale()` must write an 8-column row matching the api_server pattern:
  `[timestamp, normalized_card, 'Purchase', -total, balance_before, new_balance, 'Success', json.dumps(items)]`
- Column 5 is `balance_before` (= `current_balance` captured before deduction)
- This matches the Transactions Log schema used by `api_server.py process_cashier_transaction()`

### FCM Notification in Cashier Path
- Add FCM block **inline** in `complete_sale()`, after the transaction is committed — mirror the exact try/except pattern from `api_server.py` lines 863–888
- To get the FCM token: look up the student from the Users sheet by normalized card UID (same approach api_server uses for email lookup)
- Threshold: try Settings sheet (`Key = 'low_balance_threshold'`) first; fall back to `LOW_BALANCE_THRESHOLD` env var; default 50
- On FCM failure or missing token: swallow the exception, log a warning — transaction response is `200 success` regardless
- FCM block never blocks or rolls back the transaction

### Android Receipt Timestamp Format
- Fix is **ReceiptActivity only** — transaction list timestamps are out of scope for this phase
- Parse the raw backend string `"2026-02-28 14:32:00"` (format: `yyyy-MM-dd HH:mm:ss`)
- Display as `"Feb 28, 2026 2:32 PM"` (12-hour, month name abbreviated)
- If parsing fails (malformed or empty string): display `"Invalid date"` as fallback

### migrate_users_schema Startup Behavior
- Call `migrate_users_schema()` at **module level** in `api_server.py`, alongside `db = get_sheets_client()` and `nfc_service = NFCService()`
- Runs on every startup — function is already idempotent (checks headers, skips if all columns exist)
- Import from `backend/migrate_transactions.py` directly via `sys.path.insert` (same pattern used elsewhere in api_server.py)
- If migration fails (Sheets API unavailable at startup): log a warning, continue startup — non-fatal

### Claude's Discretion
- Exact Kotlin date parsing library/method for ReceiptActivity (SimpleDateFormat vs DateTimeFormatter)
- Whether to extract the FCM lookup block into a named helper function within complete_sale or keep it flat

</decisions>

<specifics>
## Specific Ideas

No specific references beyond what's in the roadmap success criteria. Implementation should stay
close to the existing `api_server.py` patterns — don't invent new abstractions, mirror what's there.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ArduinoBridge.read_card_with_timeout(callback, timeout=5)` in `backend/dashboard/arduino_bridge.py:28` — call this from the new socketio handler
- `send_low_balance_push(fcm_token, balance)` in `backend/api/fcm_sender.py:37` — already used in api_server.py, import and call from complete_sale
- `migrate_users_schema()` in `backend/migrate_transactions.py:64` — import via sys.path and call at api_server module level
- `normalize_card_uid()` in `backend/utils.py` — already imported in cashier_routes.py; use for Users sheet lookup

### Established Patterns
- FCM block pattern: `api_server.py:863–888` — exact try/except structure to mirror in complete_sale
- `@socketio.on` handlers: all live in `admin_dashboard.py` — add cashier_request_card there
- Session storage: `flask_session['pending_transaction']` already used in process_sale; store card UID similarly
- Existing card events already used: `card_read`, `card_timeout`, `card_error` — reuse, don't create new ones

### Integration Points
- `admin_dashboard.py:90` — `socketio = SocketIO(app, ...)` and `app.socketio = socketio` — the socketio instance the handler will bind to
- `cashier_routes.py:307–315` — the transaction_row that needs `balance_before` inserted at position 4 (0-indexed)
- `api_server.py:81` — `db = get_sheets_client()` module-level; add `migrate_users_schema()` call after this block

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-cashier-payment-fix*
*Context gathered: 2026-03-01*
