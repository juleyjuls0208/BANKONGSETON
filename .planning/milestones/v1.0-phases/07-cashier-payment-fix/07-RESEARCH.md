# Phase 7: Fix Cashier Payment Path - Research

**Researched:** 2026-03-01
**Domain:** Flask-SocketIO event wiring, Google Sheets transaction schema, FCM notifications (Python), Android timestamp parsing (Kotlin)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### cashier_request_card WebSocket Wiring
- Add `@socketio.on('cashier_request_card')` handler in `admin_dashboard.py` alongside existing card event handlers
- Handler calls `arduino_bridge.read_card_with_timeout(callback, timeout=5)`
- On card read success: callback stores the UID in the Flask session so the subsequent `complete_sale` POST can consume it
- On timeout: reuse existing `card_timeout` event — frontend already listens and handles it; no new event needed
- On error: reuse existing `card_error` event

#### Transaction Row Schema (complete_sale fix)
- `cashier_routes.py complete_sale()` must write an 8-column row matching the api_server pattern:
  `[timestamp, normalized_card, 'Purchase', -total, balance_before, new_balance, 'Success', json.dumps(items)]`
- Column 5 is `balance_before` (= `current_balance` captured before deduction)
- This matches the Transactions Log schema used by `api_server.py process_cashier_transaction()`

#### FCM Notification in Cashier Path
- Add FCM block **inline** in `complete_sale()`, after the transaction is committed — mirror the exact try/except pattern from `api_server.py` lines 863–888
- To get the FCM token: look up the student from the Users sheet by normalized card UID (same approach api_server uses for email lookup)
- Threshold: try Settings sheet (`Key = 'low_balance_threshold'`) first; fall back to `LOW_BALANCE_THRESHOLD` env var; default 50
- On FCM failure or missing token: swallow the exception, log a warning — transaction response is `200 success` regardless
- FCM block never blocks or rolls back the transaction

#### Android Receipt Timestamp Format
- Fix is **ReceiptActivity only** — transaction list timestamps are out of scope for this phase
- Parse the raw backend string `"2026-02-28 14:32:00"` (format: `yyyy-MM-dd HH:mm:ss`)
- Display as `"Feb 28, 2026 2:32 PM"` (12-hour, month name abbreviated)
- If parsing fails (malformed or empty string): display `"Invalid date"` as fallback

#### migrate_users_schema Startup Behavior
- Call `migrate_users_schema()` at **module level** in `api_server.py`, alongside `db = get_sheets_client()` and `nfc_service = NFCService()`
- Runs on every startup — function is already idempotent (checks headers, skips if all columns exist)
- Import from `backend/migrate_transactions.py` directly via `sys.path.insert` (same pattern used elsewhere in api_server.py)
- If migration fails (Sheets API unavailable at startup): log a warning, continue startup — non-fatal

### Claude's Discretion
- Exact Kotlin date parsing library/method for ReceiptActivity (SimpleDateFormat vs DateTimeFormatter)
- Whether to extract the FCM lookup block into a named helper function within complete_sale or keep it flat

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUG-01 | Cashier POS app displays the product menu correctly (RFID card read path wired end-to-end) | SocketIO `cashier_request_card` handler wires `ArduinoBridge.read_card_with_timeout()` into the existing product/sale flow |
| APP-02 | Student can see a scrollable list of all their transactions (date, amount, type) | `complete_sale()` writing `balance_before` (col 5) ensures the transaction list row has correct pre-transaction balance |
| APP-03 | Student can tap a canteen purchase transaction and see the itemized receipt | `ReceiptActivity.formatDate()`/`formatTime()` fix parses `"yyyy-MM-dd HH:mm:ss"` backend format correctly |
| APP-04 | Student app shows balance update immediately after a transaction is processed | Correct `balance_before` in the 8-column row means `balanceBefore` field is non-zero in `Transaction` model |
| NOTF-01 | Student receives a push notification when their balance drops below a configurable threshold | FCM block mirrored from `api_server.py:863–888` fires from `complete_sale()` after transaction commit |
</phase_requirements>

---

## Summary

This phase is entirely a **bug-fix / gap-closure phase** — no new libraries, no new abstractions. Every fix has a clear template already in the codebase. The work splits cleanly into five surgical changes across three files plus one Kotlin file.

The most important finding: the codebase is internally consistent and the patterns are already proven. `api_server.py` has a working 8-column transaction write, a working FCM block, and a working `migrate_users_schema()` call pattern — `cashier_routes.py` and `admin_dashboard.py` just need to match it. The Android `ReceiptActivity` parses ISO 8601 format (`yyyy-MM-dd'T'HH:mm:ss`) but the backend sends `"yyyy-MM-dd HH:mm:ss"` (space separator, no `T`) — a one-character mismatch that breaks all timestamp parsing silently.

**Primary recommendation:** Copy patterns verbatim from `api_server.py` — don't invent, mirror.

---

## Standard Stack

### Core (already installed — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flask-socketio | installed | WebSocket event binding | `@socketio.on('event')` pattern used throughout admin_dashboard.py |
| gspread | installed | Google Sheets read/write | All Sheets operations use gspread across the project |
| firebase-admin | installed | FCM push notifications | Used in fcm_sender.py; `send_low_balance_push()` already works |
| python-jwt (PyJWT) | installed | Cashier auth | Used in cashier_routes.py JWT decorator |
| Android SimpleDateFormat | stdlib | Kotlin date parsing | Already imported in ReceiptActivity; no new dep needed |

### No new packages required
All five fixes use only what's already imported or installed. The `firebase-admin` package is already in the API server's requirements; `fcm_sender.py` is already importable from `cashier_routes.py` via the `sys.path.insert` pattern.

---

## Architecture Patterns

### Pattern 1: Flask-SocketIO Event Handler Registration
**What:** Bind a Python function to a WebSocket event name using `@socketio.on('event_name')`
**When to use:** Any time the browser/frontend emits a named WebSocket event and the server needs to react
**Example (from admin_dashboard.py:1983–1989):**
```python
# Source: admin_dashboard.py:1983
@socketio.on('connect')
def handle_connect():
    logger.debug("event=client_connected")

@socketio.on('disconnect')
def handle_disconnect():
    logger.debug("event=client_disconnected")
```
**New handler to add (right before the existing `connect`/`disconnect` handlers):**
```python
@socketio.on('cashier_request_card')
def handle_cashier_request_card(data):
    """Read card for cashier POS — wired into ArduinoBridge with 5s timeout."""
    from flask import session as flask_session
    arduino_bridge = getattr(app, 'arduino_bridge', None)
    if not arduino_bridge:
        socketio.emit('card_error', {'message': 'Arduino not connected'})
        return

    def on_card_read(uid):
        flask_session['cashier_card_uid'] = uid

    arduino_bridge.read_card_with_timeout(on_card_read, timeout=5)
```
**Critical note:** `ArduinoBridge.read_card_with_timeout(callback, timeout=5)` at `arduino_bridge.py:28` takes a callback and launches a background thread. The callback fires from that thread. Flask session writes from a background thread are **safe** here because Flask's session object is thread-local per request context — but the SocketIO handler IS a request context. The callback will be invoked from the background thread started inside `read_card_with_timeout`, which means `flask_session` won't be accessible from it. **This is a critical pitfall — see Common Pitfalls section.**

### Pattern 2: 8-Column Transaction Row (cashier_routes.py fix)
**What:** Insert `balance_before` (= `current_balance`) at index 4 in the transaction row
**Current (broken) row — `cashier_routes.py:307–314`:**
```python
transaction_row = [
    timestamp,       # col 0: Timestamp
    normalized_card, # col 1: MoneyCardNumber
    'Purchase',      # col 2: TransactionType
    -total,          # col 3: Amount
    new_balance,     # col 4: BalanceAfter  ← BUG: missing BalanceBefore
    'Success',       # col 5: Status
    json.dumps(items) # col 6: ItemsJson
]
```
**Fixed row (matching api_server.py:850–859):**
```python
transaction_row = [
    timestamp,        # col 0: Timestamp
    normalized_card,  # col 1: MoneyCardNumber
    'Purchase',       # col 2: TransactionType
    -total,           # col 3: Amount
    current_balance,  # col 4: BalanceBefore  ← NEW
    new_balance,      # col 5: BalanceAfter
    'Success',        # col 6: Status
    json.dumps(items) # col 7: ItemsJson
]
```
**`current_balance` is already captured at `cashier_routes.py:271`** — it just needs to be inserted before `new_balance` in the row.

### Pattern 3: FCM Low-Balance Block (mirror from api_server.py:863–888)
**What:** After `trans_sheet.append_row()` succeeds, check balance and optionally send push notification
**Template (from api_server.py:863–888):**
```python
# Low-balance push notification — fires after transaction is committed
# Never blocks or rolls back the transaction response
try:
    threshold = float(os.getenv('LOW_BALANCE_THRESHOLD', 50))
    try:
        settings_sheet = get_worksheet_with_retry('Settings')
        settings_records = settings_sheet.get_all_records()
        for row in settings_records:
            if str(row.get('Key', '')).strip().lower() == 'low_balance_threshold':
                threshold = float(row.get('Value', threshold))
                break
    except Exception as settings_err:
        logger.warning("event=settings_read_failed error=%s using_env_default=%.0f", settings_err, threshold)
    if new_balance < threshold:
        users_sheet2 = db.worksheet('Users')
        user_records2 = users_sheet2.get_all_records()
        for user in user_records2:
            if normalize_card_uid(user.get('MoneyCardNumber', '')) == normalized_card:
                fcm_token = str(user.get('FCMToken', '')).strip()
                if fcm_token:
                    from fcm_sender import send_low_balance_push
                    send_low_balance_push(fcm_token, new_balance)
                break
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
```
**Adaptation for cashier_routes.py:**
- Replace `get_worksheet_with_retry('Settings')` with `db.worksheet('Settings')` (cashier_routes uses `db` directly)
- The `fcm_sender` import path: `sys.path.insert` to `backend/api/` already set at top of cashier_routes.py; add to the sys.path if needed, or use the existing `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))` that's already there for `admin_dashboard` — then use `from api.fcm_sender import send_low_balance_push` or insert `backend/api` path specifically
- The lookup is by `normalized_card` (not `student_id`) — that's the correct approach since cashier_routes doesn't maintain a student_id at this point

### Pattern 4: migrate_users_schema() Module-Level Call
**What:** Call once at module level (not inside `__main__`) so it fires on every import
**Current api_server.py module-level block (lines 29–81):**
```python
from utils import normalize_card_uid
from nfc_payments import NFCService, ensure_virtual_cards_sheet
nfc_service = NFCService()

load_dotenv()
...
db = get_sheets_client()
```
**Addition (after `db = get_sheets_client()` at line 81):**
```python
# Run schema migration at startup (idempotent — skips if all columns exist)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from migrate_transactions import migrate_users_schema
    migrate_users_schema()
except Exception as _mig_err:
    logger.warning("event=migrate_users_startup_failed error=%s", _mig_err)
```
**Note:** `sys.path.insert` to `backend/` is already done at line 22 of api_server.py (`sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))`), so `migrate_transactions` is importable without any additional path insert.

### Pattern 5: Android Timestamp Parsing (ReceiptActivity fix)
**What:** Replace ISO 8601 input format with the actual backend format
**Current (broken) in ReceiptActivity.kt:44:**
```kotlin
val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
// Expects: "2026-02-28T14:32:00"
// Receives: "2026-02-28 14:32:00"  ← space, not T
```
**Fixed:**
```kotlin
private fun formatTimestamp(timestamp: String): String {
    return try {
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        val date = sdf.parse(timestamp) ?: return "Invalid date"
        SimpleDateFormat("MMM d, yyyy h:mm a", Locale.getDefault()).format(date)
    } catch (e: Exception) {
        "Invalid date"
    }
}
```
**Output:** `"Feb 28, 2026 2:32 PM"` — matches the locked decision format.

**Claude's Discretion: SimpleDateFormat vs DateTimeFormatter**
- `SimpleDateFormat` (Java): already imported in ReceiptActivity.kt, available on all Android API levels, used in existing `formatDate`/`formatTime` methods. No new imports needed.
- `DateTimeFormatter` (Java 8+): requires `minSdk 26` (Android 8.0). The project doesn't have an explicit `minSdkVersion` check visible in research, but targeting `minSdk 26+` is risky for a school project.
- **Recommendation: Keep `SimpleDateFormat`.** It's already imported, already used in ReceiptActivity, and works on all API levels. No justification to introduce DateTimeFormatter.

**Note on the current ReceiptActivity structure:** The current code calls separate `formatDate()` (returns `"dd MMM yyyy"`) and `formatTime()` (returns `"HH:mm"` in 24h) methods to set two separate TextViews. The locked decision wants `"Feb 28, 2026 2:32 PM"` as a single combined value. The fix should either:
1. Replace both methods with one `formatTimestamp()` that returns the combined string, or
2. Keep the two-TextView layout and update `formatDate()` to return `"Feb 28, 2026"` and `formatTime()` to return `"2:32 PM"` (12-hour)
Both approaches work. The cleanest: update both `formatDate` and `formatTime` in-place to parse the correct input format and emit the expected output format — preserves the layout XML unchanged.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FCM push send | Custom HTTP to FCM API | `send_low_balance_push()` in `fcm_sender.py` | Already handles firebase_admin init guard, token validation, error swallowing |
| Settings sheet threshold lookup | Inline dict search | Mirror the exact loop from `api_server.py:869–874` | Tested pattern; handles missing Settings sheet gracefully |
| Transaction row schema | Guess column order | `api_server.py:850–859` is the canonical template | Both servers must write the same schema for the Android app to read it |
| Date parsing in Kotlin | Custom regex | `SimpleDateFormat` | stdlib, already imported, handles locale/timezone correctly |

---

## Common Pitfalls

### Pitfall 1: Flask session not accessible from ArduinoBridge callback thread
**What goes wrong:** `ArduinoBridge.read_card_with_timeout(callback)` launches a background thread (`arduino_bridge.py:42`). The `callback(uid)` is called from that background thread. Flask's `flask_session` proxy requires an active request context, which is **not** present in a background thread — writing `flask_session['cashier_card_uid'] = uid` from the callback will raise a `RuntimeError: Working outside of request context`.
**Why it happens:** Flask session is a thread-local request context proxy. SocketIO handlers have a request context, but background threads spawned from them do not inherit it.
**How to avoid:** Use `socketio.emit('card_read', {'uid': uid})` from the callback (the ArduinoBridge already does this at `arduino_bridge.py:75–78`). The frontend then sends the UID back in the `complete_sale` POST body. The session storage of the UID is therefore **not needed** — `complete_sale` already accepts `card_uid` from the POST body.
**Alternative:** If session storage is truly needed, use `app.config` or a thread-safe in-memory dict keyed by session ID. But the existing flow already works: `process_sale` stores the transaction in `flask_session['pending_transaction']`, and `complete_sale` receives `card_uid` from the POST body (not from session).
**Warning signs:** `RuntimeError: Working outside of request context` in logs after card tap.

**Critical conclusion:** The `cashier_request_card` SocketIO handler does NOT need to store the UID in the session. Its only job is to call `arduino_bridge.read_card_with_timeout(callback)` where the callback emits `card_read` (which ArduinoBridge already does automatically). The frontend JS receives `card_read`, extracts the UID, and POSTs to `/cashier/api/complete-sale` with `card_uid` in the body.

### Pitfall 2: `arduino_bridge` attribute may not exist on `app`
**What goes wrong:** `app.arduino_bridge` is set in `connect_serial()` at `admin_dashboard.py:1116`. If no Arduino has been connected yet (e.g., fresh browser session), `hasattr(app, 'arduino_bridge')` returns False.
**Why it happens:** `arduino_bridge` is set conditionally on the `POST /api/serial/connect` call, not at module level.
**How to avoid:** In the `cashier_request_card` handler, use `getattr(app, 'arduino_bridge', None)` and emit `card_error` if None. This is already the pattern in `cashier_routes.py:121` (`if hasattr(current_app, 'arduino_bridge')`).
**Warning signs:** `AttributeError: 'Flask' object has no attribute 'arduino_bridge'`.

### Pitfall 3: fcm_sender import path from cashier_routes.py
**What goes wrong:** `fcm_sender.py` lives in `backend/api/`. `cashier_routes.py` does `sys.path.insert(0, backend/)` at line 16, but `from fcm_sender import send_low_balance_push` will fail because `fcm_sender` is not in `backend/` — it's in `backend/api/`.
**Why it happens:** `sys.path.insert` in cashier_routes points to `backend/` (two levels up from `cashier/`), not `backend/api/`.
**How to avoid:** Add a second `sys.path.insert` for `backend/api/` before the import, or use `from api.fcm_sender import send_low_balance_push` (works because `backend/` is already on the path and `api/` is a subdirectory with `__init__.py` if present). Check: `backend/api/` has no `__init__.py` (it's not a package), so relative imports won't work. **Safest:** insert path explicitly inside the try block: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))`.

### Pitfall 4: Android `SimpleDateFormat` thread safety
**What goes wrong:** `SimpleDateFormat` is not thread-safe if the same instance is shared. However, since `formatDate`/`formatTime` create new instances on every call, this is not an issue.
**How to avoid:** Create a new `SimpleDateFormat` instance per call (already the pattern in existing ReceiptActivity code).

### Pitfall 5: migrate_users_schema() import — already-on-path
**What goes wrong:** `api_server.py` already has `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))` at line 22, which adds `backend/` to the path. `migrate_transactions.py` lives in `backend/`. So `from migrate_transactions import migrate_users_schema` works without any additional path insertion.
**Why it matters:** Adding a redundant `sys.path.insert` is harmless but confusing. Don't add one.

---

## Code Examples

### cashier_request_card SocketIO Handler (admin_dashboard.py)
```python
# Source: verified against admin_dashboard.py:1981–1989 pattern
@socketio.on('cashier_request_card')
def handle_cashier_request_card(data):
    """Trigger ArduinoBridge card read for cashier POS (5s timeout)."""
    arduino_bridge = getattr(app, 'arduino_bridge', None)
    if not arduino_bridge:
        socketio.emit('card_error', {'message': 'Arduino not connected'})
        return
    # Callback is called from background thread — do NOT write to flask_session here.
    # ArduinoBridge already emits 'card_read' with uid on success,
    # 'card_timeout' on timeout, 'card_error' on error. No additional emit needed.
    arduino_bridge.read_card_with_timeout(lambda uid: None, timeout=5)
```

### Fixed transaction_row in complete_sale() (cashier_routes.py:307–314)
```python
# Source: verified against api_server.py:850–859 canonical schema
transaction_row = [
    timestamp,        # col 0: Timestamp
    normalized_card,  # col 1: MoneyCardNumber
    'Purchase',       # col 2: TransactionType
    -total,           # col 3: Amount
    current_balance,  # col 4: BalanceBefore  ← INSERT THIS
    new_balance,      # col 5: BalanceAfter
    'Success',        # col 6: Status
    json.dumps(items) # col 7: ItemsJson
]
```

### FCM block for cashier_routes.py (after trans_sheet.append_row)
```python
# Source: mirrored from api_server.py:863–888
try:
    threshold = float(os.getenv('LOW_BALANCE_THRESHOLD', 50))
    try:
        settings_sheet = db.worksheet('Settings')
        settings_records = settings_sheet.get_all_records()
        for row in settings_records:
            if str(row.get('Key', '')).strip().lower() == 'low_balance_threshold':
                threshold = float(row.get('Value', threshold))
                break
    except Exception as settings_err:
        logger.warning("event=settings_read_failed error=%s using_env_default=%.0f", settings_err, threshold)
    if new_balance < threshold:
        users_sheet2 = db.worksheet('Users')
        user_records2 = users_sheet2.get_all_records()
        for user in user_records2:
            if normalize_card_uid(user.get('MoneyCardNumber', '')) == normalized_card:
                fcm_token = str(user.get('FCMToken', '')).strip()
                if fcm_token:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
                    from fcm_sender import send_low_balance_push
                    send_low_balance_push(fcm_token, new_balance)
                break
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
```

### migrate_users_schema startup call (api_server.py, after line 81)
```python
# Source: verified against migrate_transactions.py:64–102
# sys.path already has backend/ from line 22 — no new insert needed
try:
    from migrate_transactions import migrate_users_schema
    migrate_users_schema()
except Exception as _mig_err:
    logger.warning("event=migrate_users_startup_failed error=%s", _mig_err)
```

### Fixed ReceiptActivity timestamp parsing (Kotlin)
```kotlin
// Source: verified against ReceiptActivity.kt:42–59 existing pattern
// Backend sends: "2026-02-28 14:32:00"  (space separator, not T)
// Display as:    "Feb 28, 2026 2:32 PM"

private fun formatDate(timestamp: String): String {
    return try {
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        val date = sdf.parse(timestamp) ?: return "Invalid date"
        SimpleDateFormat("MMM d, yyyy", Locale.getDefault()).format(date)
    } catch (e: Exception) {
        "Invalid date"
    }
}

private fun formatTime(timestamp: String): String {
    return try {
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        val date = sdf.parse(timestamp) ?: return "Invalid date"
        SimpleDateFormat("h:mm a", Locale.getDefault()).format(date)
    } catch (e: Exception) {
        "Invalid date"
    }
}
```
**Note:** Updates both `formatDate` and `formatTime` in-place (preserves `receiptDate` and `receiptTime` TextViews in the XML layout). No layout changes needed.

---

## File-by-File Change Map

| File | Change | Lines Affected |
|------|--------|----------------|
| `backend/dashboard/admin_dashboard.py` | Add `@socketio.on('cashier_request_card')` handler | After line 1989 (before `if __name__ == '__main__':`) |
| `backend/dashboard/cashier/cashier_routes.py` | Fix `transaction_row` to 8 columns + add FCM block | Lines 307–314 (row schema); after line 317 (FCM block) |
| `backend/api/api_server.py` | Add `migrate_users_schema()` call at module level | After line 81 (`db = get_sheets_client()`) |
| `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt` | Fix `formatDate()` and `formatTime()` input format | Lines 42–59 |

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `cashier_routes.py` writes 7-column row (no BalanceBefore) | Write 8-column row matching `api_server.py` schema | Single source of truth for schema |
| ReceiptActivity parses `"yyyy-MM-dd'T'HH:mm:ss"` | Parse `"yyyy-MM-dd HH:mm:ss"` (space, not T) | Backend never sends T-format |
| `cashier_request_card` event emitted but never handled server-side | `@socketio.on('cashier_request_card')` handler calls ArduinoBridge | Closes the missing wiring gap |
| `migrate_users_schema()` only called by running migration script manually | Called at `api_server.py` module level on every startup | Idempotent — safe to run always |

---

## Open Questions

1. **The `cashier_request_card` event flow is broken by design — frontend must emit it**
   - **What we know (verified from `cashier_index.html:284–296`):** The frontend JS only listens for `card_read`, `card_timeout`, `card_error`. It has NO `socket.on('cashier_request_card')` listener, and it does NOT re-emit `cashier_request_card` back to the server.
   - **Current broken flow:**
     1. Frontend POSTs to `/cashier/api/process-sale`
     2. `process_sale()` calls `current_app.socketio.emit('cashier_request_card', ...)` — broadcasts to clients
     3. Frontend receives `cashier_request_card` but ignores it (no handler)
     4. Nothing calls `arduino_bridge.read_card_with_timeout()` — card never gets read
   - **Why `@socketio.on('cashier_request_card')` won't work as-is:** Flask-SocketIO server-side `socketio.emit()` sends to CLIENTS, not to server-side `@socketio.on` handlers. A server-side handler is only triggered when a CLIENT emits the event.
   - **The fix has two valid approaches:**
     - **Option A (CONTEXT.md approach):** Add `socket.emit('cashier_request_card', data)` in the **frontend JS** after receiving the server broadcast, which then triggers the `@socketio.on('cashier_request_card')` server handler. Requires a frontend JS change in `cashier_index.html`.
     - **Option B (no frontend change):** Replace `current_app.socketio.emit('cashier_request_card', ...)` in `process_sale()` with a direct call to `arduino_bridge.read_card_with_timeout()` from within `process_sale()` itself.
   - **Recommendation:** Option A preserves the CONTEXT.md locked decision and requires a minimal one-line JS change. Option B is simpler (no SocketIO round-trip) but changes the architecture slightly.
   - **Both approaches require the `@socketio.on('cashier_request_card')` handler in admin_dashboard.py for Option A.** The planner must decide which option to take.
   - **HIGH confidence** — verified from actual frontend source.

2. **What does `client_uid` need for `complete_sale` — session or POST body?**
   - **What we know:** `complete_sale()` already reads `card_uid = data.get('card_uid', '')` from the POST body (line 241). The frontend JS handles the `card_read` WebSocket event and POSTs the UID. Session storage of the UID is not needed.
   - **Verdict (HIGH confidence):** No session write needed in the SocketIO handler. The callback only needs to trigger `arduino_bridge.read_card_with_timeout`, and ArduinoBridge already emits `card_read` with the UID on success.

---

## Sources

### Primary (HIGH confidence)
- `backend/dashboard/admin_dashboard.py` — socketio instance, existing handlers, arduino_bridge wiring pattern (lines 90–93, 1110–1116, 1981–1989)
- `backend/dashboard/arduino_bridge.py` — `read_card_with_timeout()` signature and threading behavior (lines 28–46)
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale()` current schema, process_sale session pattern (lines 189–384)
- `backend/api/api_server.py` — canonical 8-column row, FCM block, module-level init pattern (lines 80–82, 850–888)
- `backend/api/fcm_sender.py` — `send_low_balance_push()` signature and behavior (lines 37–72)
- `backend/migrate_transactions.py` — `migrate_users_schema()` idempotent check (lines 64–102)
- `mobile/student_app_v2/.../ReceiptActivity.kt` — current broken format string (lines 42–59)
- `mobile/student_app_v2/.../Models.kt` — `Transaction.balanceBefore` field mapping (line 40)

### Secondary (MEDIUM confidence)
- Flask-SocketIO docs: `@socketio.on()` handlers receive events from clients, not from `socketio.emit()` on the same server. Server-to-self emit does NOT trigger handlers.
- Kotlin `SimpleDateFormat`: thread-unsafe if shared, but per-call instantiation (current pattern) is safe.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, verified from imports
- Architecture: HIGH — all patterns verified from actual source files
- Pitfalls: HIGH — identified from actual code analysis, not speculation
- Open Question 1 (socketio emit direction): MEDIUM — requires frontend JS inspection to confirm

**Research date:** 2026-03-01
**Valid until:** 2026-04-01 (stable codebase — no fast-moving dependencies)
