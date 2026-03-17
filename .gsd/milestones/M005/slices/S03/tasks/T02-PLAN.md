---
estimated_steps: 8
estimated_files: 3
---

# T02: Implement `qr/confirm` debit + `qr-generate` cashier route + `qr_payment` socket handler

**Slice:** S03 — Backend QR Payment Flow  
**Milestone:** M005

## Description

Implements the money-moving half of the QR payment flow:

1. `POST /cashier/api/qr-generate` (cashier JWT) — in `cashier_routes.py`, creates a UUID token, sets `current_app.pending_qr_token`, returns `{token, url}`.
2. `POST /api/qr/confirm` (student JWT) — in `web_app.py`, validates the pending token, debits balance using the same retry/rollback/offline-queue pattern as `complete_sale()`, emits `qr_payment` SocketIO event, clears the token.
3. `socket.on('qr_payment', ...)` — in `cashier_index.html`, shows success modal and clears cart — identical UI surface as NFC payment success.

**Architecture constraints (critical):**
- `qr/confirm` is in `web_app.py` — not `cashier_routes.py` — because it needs direct access to `socketio` and `app.pending_qr_token`.
- `qr-generate` is in `cashier_routes.py` (cashier blueprint); access the app state with `current_app.pending_qr_token`, **never** `app.pending_qr_token` (that would be `RuntimeError: Working outside of application context`).
- Balance reads in `qr/confirm` must hit Sheets directly — no cache (D018).
- SocketIO `qr_payment` emit must happen **before** `app.pending_qr_token = None` to avoid timing edge case.
- `_decode_student_jwt()` from T01 is used in `qr/confirm` — T01 must be complete before this task.

## Steps

1. **`cashier_routes.py` — add `import uuid`** at the top (after `import time`, `import os`):
   ```python
   import uuid
   ```
   Confirm `time` and `os` are already imported (they are). Do not add duplicates.

2. **`cashier_routes.py` — add `POST /cashier/api/qr-generate` route:**
   Place this route with the other `/api/*` cashier routes. Use `@cashier_bp.route` and `@jwt_required(roles=['cashier', 'admin'])`:
   ```python
   @cashier_bp.route('/api/qr-generate', methods=['POST'])
   @jwt_required(roles=['cashier', 'admin'])
   def qr_generate():
       """Generate a QR payment token and store it as the pending QR."""
       import os as _os
       from flask import current_app
       data = request.get_json() or {}
       items = data.get('items', [])
       total = float(data.get('total', 0))
       if not items or total <= 0:
           return jsonify({'error': 'Invalid cart'}), 400
       server_url = _os.getenv('SERVER_URL', '').rstrip('/')
       if not server_url:
           return jsonify({'error': 'SERVER_URL not configured'}), 500
       token = str(uuid.uuid4())
       url = f"{server_url}/api/qr/{token}"
       current_app.pending_qr_token = {
           'token': token,
           'url': url,
           'cart_snapshot': items,
           'total': total,
           'created_at': time.time(),
           'cashier_username': request.user.get('username', ''),
       }
       logger.info("event=qr_generate token=%s total=%.2f", token, total)
       return jsonify({'token': token, 'url': url})
   ```
   Note: `os` is already imported at module level, but using `import os as _os` inside the function avoids any shadowing. Alternatively, if `os` is cleanly imported at module level with no collision, omit the inner import — use `os.getenv` directly.

3. **`web_app.py` — add `POST /api/qr/confirm` route:**
   Place after `qr_cart` (from T01) in the QR PAYMENT ROUTES section. This route does full debit via the same pattern as `complete_sale()` in `cashier_routes.py`:
   ```python
   @app.route("/api/qr/confirm", methods=["POST"])
   def qr_confirm():
       """Student confirms QR payment. Debits balance and notifies cashier."""
       import sys as _sys
       _sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

       auth_header = request.headers.get("Authorization", "")
       token_str = auth_header.replace("Bearer ", "").strip()
       payload = _decode_student_jwt(token_str)
       if not payload:
           return jsonify({"error": "Unauthorized"}), 401

       data = request.get_json() or {}
       token_param = data.get("token", "")
       t = app.pending_qr_token

       if t is None or t["token"] != token_param:
           return jsonify({"error": "QR expired or not found"}), 404
       if time.time() - t["created_at"] > 300:
           app.pending_qr_token = None
           return jsonify({"error": "QR token expired"}), 410

       student_id = str(payload.get("user_id", "")).strip()
       items = t["cart_snapshot"]
       total = t["total"]

       try:
           from dashboard_core import get_sheets_client, get_philippines_time
           db = get_sheets_client()

           # 1. Look up MoneyCardNumber from Users sheet
           users_sheet = db.worksheet("Users")
           user_records = users_sheet.get_all_records()
           money_card_number = None
           matched_user = None
           for user in user_records:
               if str(user.get("StudentID", "")).strip() == student_id:
                   money_card_number = str(user.get("MoneyCardNumber", "")).strip()
                   matched_user = user
                   break

           if not money_card_number:
               return jsonify({"error": "Student not found"}), 404

           # 2. Read Money Accounts fresh — no cache (D018)
           money_sheet = db.worksheet("Money Accounts")
           money_records = money_sheet.get_all_records()
           account_row = None
           current_balance = 0.0
           card_status = ""
           for idx, record in enumerate(money_records, start=2):
               if str(record.get("MoneyCardNumber", "")).strip() == money_card_number:
                   account_row = idx
                   current_balance = float(record.get("Balance", 0))
                   card_status = record.get("Status", "").strip().lower()
                   break

           if not account_row:
               return jsonify({"error": "Money account not found"}), 404
           if card_status == "lost":
               return jsonify({"error": "Card reported as lost"}), 403
           if card_status != "active":
               return jsonify({"error": f"Card is {card_status}"}), 403
           if current_balance < total:
               return jsonify({"error": "Insufficient funds", "balance": current_balance, "required": total}), 402

           # 3. Debit with retry + rollback (clones complete_sale pattern)
           MAX_RETRIES = 3
           new_balance = current_balance - total
           balance_deducted = False
           last_error = None
           timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
           transaction_row = [
               timestamp, money_card_number, "QR Purchase",
               -total, new_balance, "Success", json.dumps(items)
           ]

           for attempt in range(1, MAX_RETRIES + 1):
               try:
                   if not balance_deducted:
                       money_sheet.update_cell(account_row, 3, new_balance)
                       balance_deducted = True
                   trans_sheet = db.worksheet("Transactions Log")
                   trans_sheet.append_row(transaction_row)
                   last_error = None
                   break
               except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
                   last_error = e
                   logger.warning("qr_confirm attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)
                   if attempt < MAX_RETRIES:
                       time.sleep(2 ** attempt)
                   else:
                       if balance_deducted:
                           try:
                               money_sheet.update_cell(account_row, 3, current_balance)
                               logger.error("qr_confirm: rolled back balance for student %s", student_id)
                           except Exception as rollback_err:
                               logger.error("qr_confirm: CRITICAL rollback failed: %s", rollback_err)
                       try:
                           from offline_queue import get_offline_queue
                           q = get_offline_queue()
                           q.enqueue("append_row", "Transactions Log", transaction_row)
                           logger.info("event=qr_offline_queued student=%s total=%.2f", student_id, total)
                       except Exception as qe:
                           logger.error("event=qr_offline_queue_failed error=%s", qe)
                       # Even if offline-queued, emit to cashier and clear token
                       socketio.emit("qr_payment", {
                           "success": True, "new_balance": new_balance,
                           "timestamp": timestamp, "total": total,
                           "cashier": t["cashier_username"], "offline": True,
                       })
                       app.pending_qr_token = None
                       return jsonify({"success": True, "new_balance": new_balance,
                                       "timestamp": timestamp, "offline": True})

           if last_error:
               return jsonify({"error": "Service unavailable, please try again"}), 503

           # 4. Emit BEFORE clearing token (D050 analogy — emit then clear)
           socketio.emit("qr_payment", {
               "success": True, "new_balance": new_balance,
               "timestamp": timestamp, "total": total,
               "cashier": t["cashier_username"],
           })
           app.pending_qr_token = None
           logger.info("event=qr_confirm student=%s total=%.2f new_balance=%.2f", student_id, total, new_balance)

           # 5. Non-fatal FCM/SMS/email (clones complete_sale pattern)
           try:
               if matched_user:
                   fcm_token = str(matched_user.get("FCMToken", "")).strip()
                   if fcm_token:
                       from api.fcm_sender import send_purchase_push
                       send_purchase_push(fcm_token, total, new_balance)
           except Exception:
               pass

           return jsonify({"success": True, "new_balance": new_balance, "timestamp": timestamp})

       except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
               gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
           logger.error("Google Sheets unavailable in qr_confirm: %s", e)
           return jsonify({"error": "Service unavailable, please try again"}), 503
       except Exception as e:
           logger.error("Unexpected error in qr_confirm: %s", e, exc_info=True)
           return jsonify({"error": "An unexpected error occurred"}), 500
   ```
   
   **Import note for `web_app.py`:** The existing code imports from `dashboard_core` (not `admin_dashboard`) in web_app.py routes. Confirm by checking existing `/api/arduino/card-read` route — use whatever import path it uses for `get_sheets_client`. If web_app.py uses `from dashboard_core import get_sheets_client, get_philippines_time`, match that. If it does inline `sys.path.insert` + `from admin_dashboard import ...`, clone that pattern. Also confirm `gspread` is imported at the top of `web_app.py`; if not, add `import gspread`.
   
   **`json` import:** Needed for `json.dumps(items)` in transaction_row. Confirm `import json` exists in `web_app.py`; add if missing.

4. **`cashier_index.html` — add `socket.on('qr_payment')` handler:**
   Find the block starting at approximately line 338:
   ```javascript
   socket.on('nfc_payment', function(data) {
       completeNFCSale(data.token);
   });
   ```
   After this block (not replacing it — it still belongs to S05 for removal), add:
   ```javascript
   socket.on('qr_payment', function(data) {
       document.getElementById('paymentModal').style.display = 'flex';
       document.getElementById('modalTitle').textContent = 'QR Payment Received!';
       document.getElementById('modalMessage').textContent =
           'New Balance: \u20B1' + data.new_balance.toFixed(2);
       cart = [];
       renderCart();
       checkQueueStatus();
       setTimeout(function() { closeModal(); }, 2000);
   });
   ```

5. **Verify compile and grep checks:**
   ```bash
   python -m py_compile backend/dashboard/web_app.py
   python -m py_compile backend/dashboard/cashier/cashier_routes.py
   grep -q 'qr/confirm' backend/dashboard/web_app.py
   grep -q 'qr_payment' backend/dashboard/web_app.py
   grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py
   grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py
   grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py
   grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html
   ```

## Must-Haves

- [ ] `import uuid` added to `cashier_routes.py`
- [ ] `POST /cashier/api/qr-generate` decorated `@cashier_bp.route` + `@jwt_required(roles=['cashier','admin'])`; uses `current_app.pending_qr_token` (NOT `app.`); reads `SERVER_URL` from env; returns 500 if blank; logs `event=qr_generate`
- [ ] `POST /api/qr/confirm` in `web_app.py`; decodes student JWT via `_decode_student_jwt()`; checks token match + 5-min expiry; debits balance via 3-retry loop with rollback; emits `qr_payment` BEFORE clearing `app.pending_qr_token`; non-fatal FCM in try/except; logs `event=qr_confirm`
- [ ] `qr_payment` balance check returns 402 (not 400) on insufficient funds so apps can detect it as distinct from bad-request
- [ ] Transaction type logged as `"QR Purchase"` (not `"Purchase"`) for audit trail distinction
- [ ] `socket.on('qr_payment', ...)` handler added in `cashier_index.html` after `nfc_payment` handler; clears cart and shows modal
- [ ] Both Python files pass `python -m py_compile`

## Verification

```bash
python -m py_compile backend/dashboard/web_app.py
python -m py_compile backend/dashboard/cashier/cashier_routes.py
grep -q 'qr/confirm' backend/dashboard/web_app.py
grep -q 'qr_payment' backend/dashboard/web_app.py
grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py
grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py
grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py
grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html
```

All commands must exit 0.

## Observability Impact

- Signals added: `event=qr_generate`, `event=qr_confirm` log lines; `qr_payment` SocketIO event visible in cashier UI; `event=qr_offline_queued` on Sheets failure; `event=qr_offline_queue_failed` on queue failure
- How a future agent inspects: Flask log `grep 'event=qr'`; `GET /api/arduino/qr-pending` returns null after successful confirm (confirms token was cleared)
- Failure state exposed: 404 = no pending token or mismatch; 410 = expired; 402 = insufficient funds; 503 = Sheets unavailable; all paths log at WARNING or ERROR

## Inputs

- T01 must be complete: `app.pending_qr_token = None` init; `_decode_student_jwt()` helper; both defined in `web_app.py`
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale()` at line ~325 is the exact pattern to clone for the debit/retry/rollback/offline-queue logic; `@jwt_required(roles=['cashier','admin'])` decorator already defined; `current_app` usage pattern already present in the file (e.g. `current_app.socketio`, `current_app.arduino`); `logger`, `time`, `os`, `json`, `gspread` already imported
- `backend/dashboard/web_app.py` — `socketio` object at line ~121; `app.pending_qr_token` from T01; `ARDUINO_API_KEY` pattern for reference; `get_sheets_client` import pattern — check how existing web_app.py routes import it (likely `from dashboard_core import get_sheets_client` or inline sys.path approach)
- `backend/dashboard/cashier/templates/cashier_index.html` — `socket.on('nfc_payment', ...)` at line ~338 is insertion point; `paymentModal`, `modalTitle`, `modalMessage`, `renderCart`, `checkQueueStatus`, `closeModal` are already defined in the page

## Expected Output

- `backend/dashboard/cashier/cashier_routes.py` — modified: `import uuid`; `qr_generate()` route at `/api/qr-generate`
- `backend/dashboard/web_app.py` — modified: `qr_confirm()` route at `/api/qr/confirm`
- `backend/dashboard/cashier/templates/cashier_index.html` — modified: `socket.on('qr_payment', ...)` handler inserted after `nfc_payment` handler
