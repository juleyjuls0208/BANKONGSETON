---
estimated_steps: 6
estimated_files: 1
---

# T01: Add `complete_sale_nfc()` backend endpoint

**Slice:** S02 — Phone NFC Cashier Payment
**Milestone:** M003

## Description

Add `POST /cashier/api/complete-sale-nfc` to `cashier_routes.py`, immediately after `complete_sale()`. This endpoint resolves a virtual card token to a `MoneyCardNumber` via the VirtualCards sheet, then debits the balance using the exact same retry/rollback/offline-queue/email/SMS/FCM pattern as `complete_sale()`. This is the server-side half of R021 — the frontend socket handler (T02) calls it.

The implementation is a direct clone of `complete_sale()` with two substitutions: (1) the card UID lookup replaced by a VirtualCards token lookup, and (2) the transaction type changed from `'Purchase'` to `'NFC Purchase'`. Everything else — session read, balance debit, retry loop, rollback, offline queue, notifications — stays identical.

## Steps

1. Locate the end of `complete_sale()` in `cashier_routes.py` (line ~553). Insert the new route and function immediately after.

2. Add the route decorator and function signature:
   ```python
   @cashier_bp.route('/api/complete-sale-nfc', methods=['POST'])
   @jwt_required(roles=['cashier', 'admin'])
   def complete_sale_nfc():
       """Complete sale triggered by phone NFC tap.
       
       Resolves virtual_card_token → MoneyCardNumber via VirtualCards sheet,
       then debits balance with the same retry/rollback/offline-queue path as
       complete_sale(). Requires pending_transaction in session (set by process-sale).
       
       Returns 400 if no pending transaction or token is invalid/inactive.
       Returns 503 if Sheets is unreachable after retries.
       
       Note: VirtualCards worksheet must exist; if absent, raises WorksheetNotFound
       which the outer handler returns as 503.
       """
   ```

3. Token input + session guard (replace the `card_uid` block from `complete_sale()`):
   ```python
   from flask import session as flask_session, current_app
   import sys
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
   from admin_dashboard import get_sheets_client, get_philippines_time
   
   data = request.get_json()
   virtual_card_token = str(data.get('virtual_card_token', '')).strip()
   if not virtual_card_token:
       return jsonify({'error': 'virtual_card_token required'}), 400
   
   pending = flask_session.get('pending_transaction')
   if not pending:
       logger.warning("event=nfc_sale_no_pending")
       return jsonify({'error': 'No pending transaction'}), 400
   
   items = pending['items']
   total = pending['total']
   ```

4. VirtualCards token lookup (exact field names, IsActive guard):
   ```python
   db = get_sheets_client()
   vc_records = db.worksheet('VirtualCards').get_all_records()
   matched = next(
       (r for r in vc_records
        if r.get('VirtualCardToken') == virtual_card_token
        and str(r.get('IsActive', '')).upper() == 'TRUE'),
       None
   )
   if not matched:
       return jsonify({'error': 'Invalid or inactive virtual card token'}), 401
   money_card_number = str(matched.get('MoneyCardNumber', '')).strip()
   if not money_card_number:
       return jsonify({'error': 'Virtual card has no linked money card'}), 401
   ```

5. Balance debit: copy Money Accounts lookup and retry/rollback/offline-queue block verbatim from `complete_sale()` with these changes:
   - Use `money_card_number` (direct string match, no `normalize_card_uid()` — VirtualCards stores the canonical form)
   - Change transaction_row position 2: `'NFC Purchase'` instead of `'Purchase'`
   - After successful Sheets write: `logger.info("event=nfc_sale_complete token_len=%d card=%s total=%.2f", len(virtual_card_token), money_card_number, total)`
   - `flask_session.pop('pending_transaction', None)` immediately after breaking the retry loop on success (before notification tail)

6. Notification tail: copy email/SMS/FCM blocks verbatim from `complete_sale()` — all lookups use `money_card_number` (not the token). Return the same `{success, new_balance, timestamp}` payload (plus `offline: True` on queue fallback).

## Must-Haves

- [ ] Route `POST /cashier/api/complete-sale-nfc` registered with `@jwt_required(roles=['cashier', 'admin'])`
- [ ] Returns 400 when `virtual_card_token` is missing or `pending_transaction` is absent from session
- [ ] VirtualCards lookup uses `r.get('VirtualCardToken')`, `r.get('MoneyCardNumber')`, `r.get('IsActive')` — exact field names
- [ ] `IsActive` check: `str(r.get('IsActive', '')).upper() == 'TRUE'`
- [ ] Transaction row column 2 is `'NFC Purchase'` (7-column format, same as `complete_sale()`)
- [ ] `flask_session.pop('pending_transaction', None)` called after successful debit
- [ ] Retry loop (3 attempts, exponential backoff 2s/4s), rollback, offline-queue fallback — same as `complete_sale()`
- [ ] `invalidate_pattern("transactions")` and `invalidate_pattern("money_accounts")` called after Sheets write
- [ ] `logger.info("event=nfc_sale_complete ...")` logs `token_len` (not the token value), `card`, `total`
- [ ] `logger.warning("event=nfc_sale_no_pending")` logged on 400 no-pending case
- [ ] `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0

## Verification

- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` — must exit 0 with no output
- Grep checks (manual or via verify-s02.sh written in T02):
  - `grep -q "complete_sale_nfc" backend/dashboard/cashier/cashier_routes.py`
  - `grep -q "complete-sale-nfc" backend/dashboard/cashier/cashier_routes.py`
  - `grep -q "VirtualCardToken" backend/dashboard/cashier/cashier_routes.py`
  - `grep -q "IsActive" backend/dashboard/cashier/cashier_routes.py`
  - `grep -q "NFC Purchase" backend/dashboard/cashier/cashier_routes.py`
  - `grep -q "pending_transaction.*None" backend/dashboard/cashier/cashier_routes.py` (flask_session.pop)

## Observability Impact

- Signals added: `event=nfc_sale_complete token_len=N card=... total=...` on success; `event=nfc_sale_no_pending` on 400; existing retry/rollback log lines in `complete_sale()` are replicated
- How a future agent inspects this: Flask access log `POST /cashier/api/complete-sale-nfc 200/400/401/503`; `grep "nfc_sale" server logs`
- Failure state exposed: 400 body `{"error": "No pending transaction"}` distinguishes "NFC tap before checkout" from Sheets failures; 401 body distinguishes bad token from balance issues

## Inputs

- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale()` lines 318–553 are the implementation template; copy and adapt
- `backend/api/api_server.py:748–766` — VirtualCards token lookup reference for exact field names and `IsActive` guard pattern
- `S02-RESEARCH.md` — constraints section: balance column 3, 7-column transaction row, no UID_PATTERN check for tokens, `flask_session.pop` replay prevention

## Expected Output

- `backend/dashboard/cashier/cashier_routes.py` — new `complete_sale_nfc()` function (~120 lines) appended after `complete_sale()`; `py_compile` exits 0
