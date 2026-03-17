# S02: Phone NFC Cashier Payment — Research

**Date:** 2026-03-15

## Summary

S02 wires two missing pieces that sit on top of what S01 delivered: a new `POST /cashier/api/complete-sale-nfc` endpoint in `cashier_routes.py` that resolves a virtual card token → money card number → balance debit, and a `socket.on('nfc_payment', ...)` handler in `cashier_index.html` that calls it. Everything else — the `nfc_payment` SocketIO event emitter, the VirtualCards sheet, the Money Accounts debit pattern, the session-based pending transaction — already exists and is working.

The `nfc_payment` event fires from `/api/nfc/tap` in `dashboard_core.py` (line 2051: `socketio.emit("nfc_payment", {"token": token})`). S01 confirmed this endpoint is correctly hit by the firmware's `httpPostNFC()`. The event has always been emitted; the cashier UI simply never listened for it. Adding the listener and the backend endpoint is the complete scope of S02.

The implementation pattern is a direct clone of `complete_sale()` in `cashier_routes.py`, with the card UID lookup replaced by a VirtualCards sheet token lookup. The token lookup logic is directly mirrored from `nfc_pay()` in `api_server.py` (lines 750–766). No new libraries, no new patterns, no cross-process calls.

## Recommendation

Follow the `complete_sale()` clone approach exactly:
- Add `complete_sale_nfc()` immediately after `complete_sale()` in `cashier_routes.py` — same decorator pattern, same session read, same balance debit, same retry/rollback/offline-queue fallback, same email/SMS/FCM tail.
- VirtualCards lookup: `db.worksheet('VirtualCards').get_all_records()` (no retry wrapper — consistent with how `complete_sale()` accesses Money Accounts directly).
- Match token with `r.get("VirtualCardToken") == virtual_card_token and str(r.get("IsActive","")).upper() == "TRUE"` — exact field names from `nfc_pay()`.
- In the cashier UI: add `socket.on('nfc_payment', ...)` in `initWebSocket()` and an `async function completeNFCSale(token)` that mirrors `completeSale()`.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|-----------------|------------|
| Virtual card token → MoneyCardNumber lookup | `nfc_pay()` in `api_server.py` lines 750–766 | Exact sheet field names, IsActive check, None guard already proven |
| Balance debit + retry + rollback + offline queue | `complete_sale()` in `cashier_routes.py` lines 380–449 | Same Sheets path; same error classes; offline queue integration already tested |
| Helper imports in cashier_routes | `from admin_dashboard import get_sheets_client, normalize_card_uid, get_philippines_time` (inline sys.path pattern) | Existing pattern in `complete_sale()` line 327 — replicate exactly |
| Success/error modal display | `completeSale()` JS function lines 344–373 | Token-based variant needs identical UI behaviour; copy and adapt |

## Existing Code and Patterns

- `backend/dashboard/cashier/cashier_routes.py:320` — `complete_sale()` is the full implementation template; `complete_sale_nfc()` replaces the card UID lookup block (lines 329–370) with the VirtualCards token lookup, keeping everything else identical
- `backend/api/api_server.py:748–766` — VirtualCards lookup reference: `db.worksheet("VirtualCards").get_all_records()`, match on `VirtualCardToken` + `IsActive == "TRUE"`, extract `MoneyCardNumber`
- `backend/dashboard/dashboard_core.py:2026–2057` — `/api/nfc/tap` endpoint; emits `socketio.emit("nfc_payment", {"token": token})`; already wired, no changes needed here
- `backend/dashboard/cashier/templates/cashier_index.html:287–303` — `initWebSocket()` already has `socket.on('card_read', ...)` and `socket.on('card_timeout', ...)` and `socket.on('card_error', ...)`; add `socket.on('nfc_payment', ...)` in this block
- `backend/dashboard/cashier/templates/cashier_index.html:344–373` — `completeSale(cardUid)` is the JS template; `completeNFCSale(token)` posts to `/cashier/api/complete-sale-nfc` instead of `/cashier/api/complete-sale`
- `backend/dashboard/cashier/cashier_routes.py:278–317` — `process_sale()` stores `flask_session['pending_transaction'] = {items, total, cashier_id}` — same session key that `complete_sale_nfc()` reads
- `backend/dashboard/cashier/cashier_routes.py:16–23` — `cache` imported with try/except fallback; `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` must be called after successful debit (same as `complete_sale()` lines 409–410)

## Constraints

- `get_worksheet_with_retry` is **not** importable in `cashier_routes.py` — `admin_dashboard.py` wraps a module-level `db` global; the cashier pattern is `db = get_sheets_client()` then `db.worksheet('VirtualCards')` directly (no retry wrapper); acceptable for the VirtualCards lookup
- Money Accounts balance is in **column 3** — hardcoded in `complete_sale()` line 402 (`update_cell(account_row, 3, new_balance)`); `complete_sale_nfc()` must use the same; do not derive dynamically (breaks column-index drift assumption established by `complete_sale`)
- `pending_transaction` in `flask_session` is the gate — if no pending transaction exists when `nfc_payment` fires, backend must return 400; UI must handle this gracefully (show modal with error, not silent fail)
- `arduinoConnected` guard in `checkout()` and `quickPay()` — these still gate the "Pay Now" flow via serial; NFC tap bypasses this gate entirely (fires asynchronously from the phone); `completeNFCSale()` should **not** check `arduinoConnected` — it's an inbound event, not an outbound action
- `nfc_payment` socket event is broadcast to **all cashier clients** in the same Socket.IO namespace — session-based `pending_transaction` check is the safety gate; only the cashier that called `process-sale` first will have a valid session entry; others will get 400

## Common Pitfalls

- **VirtualCards field names are case-sensitive** — use `r.get("VirtualCardToken")` and `r.get("MoneyCardNumber")` and `r.get("IsActive")` exactly; these are the column headers in the Google Sheet; deviating causes silent None match
- **`str(...).upper() == "TRUE"` is required for IsActive** — the Sheets boolean TRUE comes back as the Python boolean `True` or the string `"TRUE"` depending on gspread version; the `str(...).upper() == "TRUE"` guard handles both; `api_server.py:759` already uses this pattern — copy it exactly
- **Transaction log column mismatch** — `complete_sale()` appends a 7-column row `[timestamp, card, 'Purchase', -total, new_balance, 'Success', items_json]` while the Transactions Log sheet header (from `admin_dashboard.py:204–205`) expects 12 columns; this pre-existing inconsistency means `complete_sale_nfc()` should use `'NFC Purchase'` in position 3 and follow the same 7-column format to stay consistent with `complete_sale()` output — do NOT attempt to "fix" the schema alignment here (out of scope)
- **NFC tap fires before "Pay Now" is clicked** — a student could tap before the cashier initiates checkout; backend returns 400 "No pending transaction"; the JS handler must show this error in the modal (open the modal if it's not already showing) rather than silently dropping it
- **`flask_session.pop('pending_transaction', None)`** after success — do not forget; if omitted, a subsequent NFC tap or card read will replay the previous sale amount against a different card
- **Email/SMS lookup in `complete_sale_nfc()` must match by `MoneyCardNumber`** — not by token; the NFC token is only in VirtualCards, not in Users or Money Accounts; after resolving `money_card_number` from VirtualCards, look up Users by `MoneyCardNumber` for email/SMS/FCM — same as `complete_sale()` lines 460–535

## Open Risks

- **VirtualCards sheet not yet accessed in cashier_routes.py** — the worksheet name `"VirtualCards"` is first used here; if the sheet doesn't exist (fresh deployment), `db.worksheet('VirtualCards')` raises `WorksheetNotFound`; the outer exception handler catches this as a 503, which is acceptable; document this in the endpoint docstring
- **Token length/format not validated** — `nfc_pay()` in api_server accepts any non-empty string; `complete_sale_nfc()` should do the same; avoid adding length or UUID-format checks that could reject legitimate tokens from future app versions
- **`nfc_payment` event delivery to multi-tab cashier** — if two cashier tabs are open (same session), both receive the event; only one will succeed (first to hit the backend wins the session lock implicitly via `flask_session` read); the second call returns 400 "No pending transaction"; acceptable edge case
- **Balance column 3 assumption** — `update_cell(account_row, 3, new_balance)` assumes Balance is always the 3rd column in Money Accounts; if a sheet admin inserts a column, this silently corrupts data; pre-existing risk, not introduced by S02, but worth noting

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Flask / gspread / Socket.IO | No dedicated skill needed — all patterns established in codebase | none required |

## Sources

- VirtualCards token lookup pattern (source: `backend/api/api_server.py:748–766`)
- `complete_sale()` full implementation including retry/rollback/offline-queue (source: `backend/dashboard/cashier/cashier_routes.py:320–553`)
- `nfc_payment` event emitter confirmed working post-S01 (source: `backend/dashboard/dashboard_core.py:2026–2057`)
- `initWebSocket()` and `completeSale()` UI patterns (source: `backend/dashboard/cashier/templates/cashier_index.html:287–373`)
- `flask_session['pending_transaction']` shape: `{items, total, cashier_id}` (source: `cashier_routes.py:293–297`)
- Balance column 3 hardcoded in cashier debit path (source: `cashier_routes.py:402`)
