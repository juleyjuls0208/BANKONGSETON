# S02: Phone NFC Cashier Payment

**Goal:** Wire the already-emitted `nfc_payment` SocketIO event to a working sale — cashier UI listens for it and calls a new `/cashier/api/complete-sale-nfc` endpoint that resolves the phone token to a money card, debits the balance, and returns the same success payload as a physical card tap.

**Demo:** Student taps Android phone at Arduino → firmware POSTs `{"token":…}` to `/api/nfc/tap` → `nfc_payment` event fires → cashier UI calls `completeNFCSale(token)` → `POST /cashier/api/complete-sale-nfc` debits balance in Sheets → success modal shows new balance. Sale appears in Transactions Log as `NFC Purchase`.

## Must-Haves

- `POST /cashier/api/complete-sale-nfc` exists in `cashier_routes.py`, is JWT-protected, and returns 400 when no `pending_transaction` is in session
- VirtualCards token lookup uses exact field names `VirtualCardToken`, `MoneyCardNumber`, `IsActive`; `IsActive` checked with `str(...).upper() == "TRUE"`
- Transaction row logged as `'NFC Purchase'` (7-column format, same as `complete_sale()`)
- `flask_session.pop('pending_transaction', None)` called after successful debit — replay prevention
- Retry (3 attempts, exponential backoff) + rollback + offline-queue fallback — same logic as `complete_sale()`
- `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` called after successful Sheets write
- Email/SMS/FCM notifications sent by `MoneyCardNumber` lookup in Users sheet (same tail as `complete_sale()`)
- `socket.on('nfc_payment', ...)` added to `initWebSocket()` in `cashier_index.html`
- `async function completeNFCSale(token)` calls `/cashier/api/complete-sale-nfc`; shows error in modal if no pending transaction instead of silently failing
- `completeNFCSale` does **not** check `arduinoConnected` — it is an inbound event, not an outbound action
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0
- `bash scripts/verify-s02.sh` exits 0 (9 structural grep checks)

## Proof Level

- This slice proves: contract verification (py_compile + grep) + code-level integration (endpoint defined, event wired)
- Real runtime required: no (backend deploy not possible in this environment)
- Human/UAT required: yes — phone tap at real Arduino after deploy confirms end-to-end

## Verification

- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` — exits 0
- `bash scripts/verify-s02.sh` — 9/9 checks pass
- Failure-path check: `curl -s -X POST http://localhost:5000/cashier/api/complete-sale-nfc -H "Content-Type: application/json" -d "{}" | python -c "import sys,json; d=json.load(sys.stdin); assert d.get('error'), 'expected error field'"` — must return `{"error": "virtual_card_token required"}` (or a 401/JWT redirect), confirming the failure path is inspectable without a live session

## Observability / Diagnostics

- Runtime signals: `logger.info("event=nfc_sale_complete token_len=%d card=%s total=%.2f")` on success; `logger.warning("event=nfc_sale_no_pending")` on 400; existing retry/rollback logs carry through from `complete_sale()` pattern
- Inspection surfaces: Flask access log `POST /cashier/api/complete-sale-nfc 200/400/503`; browser DevTools Network tab for XHR; browser console for JS errors in `completeNFCSale`
- Failure visibility: 400 "No pending transaction" visible in modal; 401 "Invalid or inactive virtual card token" visible in modal; retry count in server log; offline-queue fallback returns `offline: true` in JSON
- Redaction constraints: token value must not appear in structured logs — log `token_len` only

## Integration Closure

- Upstream surfaces consumed: `nfc_payment` SocketIO event from `dashboard_core.py:2051` (pre-existing, confirmed working post-S01); `VirtualCards` worksheet (first access in cashier_routes.py); `complete_sale()` as implementation template
- New wiring introduced: `socket.on('nfc_payment', completeNFCSale)` in cashier UI; `POST /cashier/api/complete-sale-nfc` route registered on cashier blueprint
- What remains before the milestone is truly usable end-to-end: S03 (WiFi badge so Pay Now enables without COM port), S04 (powerbank hardening + docs)

## Tasks

- [x] **T01: Add `complete_sale_nfc()` backend endpoint** `est:45m`
  - Why: The `nfc_payment` event fires but there is no cashier-side endpoint to resolve the token and debit the balance — this is the missing half of R021
  - Files: `backend/dashboard/cashier/cashier_routes.py`
  - Do: Add `complete_sale_nfc()` immediately after `complete_sale()` (line ~553); clone the full function body; replace the `card_uid` lookup block with VirtualCards token lookup (exact field names from research); use `'NFC Purchase'` as transaction type; emit structured log `event=nfc_sale_complete` on success and `event=nfc_sale_no_pending` on 400; keep all retry/rollback/offline-queue/email/SMS/FCM tail identical to `complete_sale()`; do NOT check UID_PATTERN — token is not a UID
  - Verify: `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0
  - Done when: py_compile exits 0 and the function body includes VirtualCardToken lookup, IsActive guard, `'NFC Purchase'` label, retry loop, and `flask_session.pop`

- [x] **T02: Wire frontend NFC handler and write verify script** `est:30m`
  - Why: The backend endpoint is useless without a UI that calls it — the socket event must be caught and the modal must display results; the verify script is the slice's objective stopping condition
  - Files: `backend/dashboard/cashier/templates/cashier_index.html`, `scripts/verify-s02.sh`
  - Do: In `initWebSocket()` add `socket.on('nfc_payment', function(data) { completeNFCSale(data.token); });` after the `card_error` handler; add `async function completeNFCSale(token)` after `completeSale(cardUid)` — same structure, posts `{virtual_card_token: token}` to `/cashier/api/complete-sale-nfc`, shows error in modal on 400/failure (open modal if not open), clears cart and calls `checkQueueStatus()` on success, does NOT check `arduinoConnected`; write `scripts/verify-s02.sh` with 9 grep checks (see task plan)
  - Verify: `bash scripts/verify-s02.sh` exits 0; `python -m py_compile backend/dashboard/cashier/cashier_routes.py` still exits 0
  - Done when: verify-s02.sh 9/9 pass; modal correctly shows success/error for both the pending and no-pending cases

## Files Likely Touched

- `backend/dashboard/cashier/cashier_routes.py`
- `backend/dashboard/cashier/templates/cashier_index.html`
- `scripts/verify-s02.sh`
