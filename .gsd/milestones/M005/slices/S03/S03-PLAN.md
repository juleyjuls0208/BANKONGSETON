# S03: Backend QR Payment Flow

**Goal:** Four new endpoints form the server-side backbone of QR payment: cashier generates a token, Arduino polls for it, student fetches cart and confirms payment, balance is debited and cashier sees a success modal — all verified by `scripts/verify-m005-s03.sh`.

**Demo:** `bash scripts/verify-m005-s03.sh` exits 0. Every grep check passes. All three modified Python files pass `python -m py_compile`. The contract is proven at the endpoint/grep level; live Sheets debit is confirmed by S04 end-to-end.

## Must-Haves

- `POST /cashier/api/qr-generate` (cashier JWT) creates UUID token, stores as `app.pending_qr_token`, returns `{token, url}`
- `GET /api/arduino/qr-pending` (API key) returns `{token, url}` when pending and not expired, `{token: null}` otherwise
- `GET /api/qr/<token>` (student JWT) returns `{items, total, cashier}` for the pending cart
- `POST /api/qr/confirm` (student JWT) validates token, debits balance via `complete_sale` pattern, emits `qr_payment` SocketIO event, clears `app.pending_qr_token`
- `socket.on('qr_payment', ...)` handler in `cashier_index.html` shows success modal and clears cart
- `app.pending_qr_token = None` initialized in `web_app.py` after `app.arduino_last_heartbeat`
- `jwt_token` field added to `api_server.py` login response so S04 apps can authenticate for `/api/qr/*`
- `SERVER_URL` env var consumed in `cashier_routes.py` and documented in `.env.example`

## Proof Level

- This slice proves: contract
- Real runtime required: no (verify script + py_compile sufficient)
- Human/UAT required: no (live debit verified in S04)

## Verification

- `bash scripts/verify-m005-s03.sh` — exits 0; all grep and py_compile checks pass
- All three Python files pass `python -m py_compile` individually
- Failure-path check: `GET /api/arduino/qr-pending` with valid `X-API-Key` returns `{"token": null}` when `app.pending_qr_token` is None or expired (>300s) — confirms the OLED idle/clear state is machine-readable and not stuck on stale data

## Observability / Diagnostics

- Runtime signals: `logger.info("event=qr_generate token=%s total=%.2f", token, total)` in `qr-generate`; `socketio.emit('qr_payment', {...})` in `qr/confirm`; `app.pending_qr_token` cleared on confirm or expiry
- Inspection surfaces: `GET /api/arduino/qr-pending` returns current token state (null = idle/expired); Flask log lines prefixed `event=qr_*`
- Failure visible: `qr-pending` returns `{token: null}` on 5-min expiry so OLED clears automatically; `qr/confirm` returns 404/410 for missing/expired tokens; balance-insufficient returns 402
- Redaction constraints: `jwt_token` values must not be logged; `JWT_SECRET` already guarded at startup

## Integration Closure

- Upstream surfaces consumed: `web_app.py` (existing `app.arduino_last_heartbeat` init pattern, `ARDUINO_API_KEY` auth, `socketio` object, `get_sheets_client`, `get_philippines_time`); `cashier_routes.py` (existing `complete_sale()` retry/rollback/offline-queue pattern, `@jwt_required` decorator, `current_app` pattern); `cashier_index.html` (`socket.on('nfc_payment')` as template for `socket.on('qr_payment')`)
- New wiring introduced: `app.pending_qr_token` dict shared between `cashier_routes.py` (write via `current_app`) and `web_app.py` (read); `_decode_student_jwt()` helper in `web_app.py` for `/api/qr/*` student auth
- What remains before milestone is truly usable end-to-end: S04 Android + iOS apps calling these endpoints; S02 OLED firmware polling `qr-pending` live

## Tasks

- [x] **T01: Add `pending_qr_token` init, JWT helper, `qr-pending` and `qr/<token>` routes — plus `jwt_token` in login** `est:45m`
  - Why: Establishes the in-memory QR state object, the student JWT decode helper, the Arduino polling route, and the cart-fetch route before the complex money-moving route is built. Also adds `jwt_token` to the api_server.py login response so S04 apps can authenticate.
  - Files: `backend/dashboard/web_app.py`, `backend/api/api_server.py`
  - Do: (1) In `web_app.py` line ~126, add `app.pending_qr_token = None` after `app.arduino_last_heartbeat = 0.0`. (2) Add `import jwt as _pyjwt` near the top of `web_app.py` (after existing imports). (3) Add `_decode_student_jwt(token_str)` helper that calls `_pyjwt.decode(token_str, _jwt_secret, algorithms=['HS256'])` wrapped in try/except returning None on failure. (4) Add `GET /api/arduino/qr-pending` route with `X-API-Key` auth (identical pattern to `arduino_heartbeat`): return `{token: null}` when `app.pending_qr_token` is None or expired (>300s), return `{token, url}` otherwise. (5) Add `GET /api/qr/<token>` route using `_decode_student_jwt`; return 401 if decode fails; return 404 if no pending token or token mismatch or expired (>300s); return `{items: t['cart_snapshot'], total: t['total'], cashier: t['cashier_username']}`. (6) In `api_server.py` login route, inside the existing `return jsonify({...})` block, add `'jwt_token': generate_jwt_token(student['StudentID'], role='student')` as a new field.
  - Verify: `python -m py_compile backend/dashboard/web_app.py && python -m py_compile backend/api/api_server.py && grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py && grep -q 'qr-pending' backend/dashboard/web_app.py && grep -q "api/qr/" backend/dashboard/web_app.py && grep -q 'jwt_token' backend/api/api_server.py`
  - Done when: Both files compile clean; all 4 grep checks pass.

- [x] **T02: Implement `qr/confirm` debit + `qr-generate` cashier route + `qr_payment` socket handler** `est:1h`
  - Why: Closes the payment round-trip: cashier generates token → student confirms → balance debited → cashier sees success. The `qr/confirm` route clones the `complete_sale()` retry/rollback/offline-queue pattern from `cashier_routes.py` to ensure consistent money-movement semantics.
  - Files: `backend/dashboard/web_app.py`, `backend/dashboard/cashier/cashier_routes.py`, `backend/dashboard/cashier/templates/cashier_index.html`
  - Do: (1) In `web_app.py`, add `POST /api/qr/confirm` route: decode student JWT with `_decode_student_jwt`; validate token matches `app.pending_qr_token['token']`; check expiry (>300s → clear token, return 410); look up student `MoneyCardNumber` from Users sheet via `student_id = payload['user_id']`; read Money Accounts fresh (no cache, D018); check balance >= total; debit cell with retry/rollback pattern (3 retries, same structure as `complete_sale()`); append 'QR Purchase' row to Transactions Log; call `socketio.emit('qr_payment', {'success': True, 'new_balance': new_balance, 'timestamp': timestamp, 'total': t['total'], 'cashier': t['cashier_username']})` BEFORE clearing token; set `app.pending_qr_token = None`; non-fatal FCM/SMS/email (wrapped in try/except, same as `complete_sale()`); return `{success: True, new_balance: ..., timestamp: ...}`. (2) In `cashier_routes.py`, add `import uuid` at the top if not present; add `POST /cashier/api/qr-generate` route decorated with `@jwt_required(roles=['cashier','admin'])`; read `items` and `total` from request JSON; validate non-empty items and total > 0; read `server_url = os.getenv('SERVER_URL','').rstrip('/')`, return 500 if blank; build `token = str(uuid.uuid4())`, `url = f"{server_url}/api/qr/{token}"`; set `current_app.pending_qr_token = {'token': token, 'url': url, 'cart_snapshot': items, 'total': float(total), 'created_at': time.time(), 'cashier_username': request.user.get('username','')}` (use `current_app`, NOT `app`); log `event=qr_generate`; return `{token, url}`. (3) In `cashier_index.html`, after the `socket.on('nfc_payment', ...)` block (line ~338), add `socket.on('qr_payment', function(data) { document.getElementById('paymentModal').style.display='flex'; document.getElementById('modalTitle').textContent='QR Payment Received!'; document.getElementById('modalMessage').textContent='New Balance: ₱'+data.new_balance.toFixed(2); cart=[]; renderCart(); checkQueueStatus(); setTimeout(function(){ closeModal(); }, 2000); });`
  - Verify: `python -m py_compile backend/dashboard/web_app.py && python -m py_compile backend/dashboard/cashier/cashier_routes.py && grep -q 'qr/confirm' backend/dashboard/web_app.py && grep -q 'qr_payment' backend/dashboard/web_app.py && grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py && grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py && grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py && grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html`
  - Done when: Both Python files compile clean; all 7 grep checks pass; `socket.on('qr_payment')` handler visible in cashier_index.html.

- [x] **T03: Write verify script, add SERVER_URL to .env.example and docs/DEPLOY.md** `est:20m`
  - Why: Closes the slice's objective stopping condition. The verify script is the authoritative proof artifact for S03 — it is what the milestone DoD checks.
  - Files: `scripts/verify-m005-s03.sh`, `.env.example`, `docs/DEPLOY.md`
  - Do: (1) Create `scripts/verify-m005-s03.sh` with shebang `#!/usr/bin/env bash`, `set -euo pipefail`, echo each check before it runs, and the following checks in order: `python -m py_compile backend/api/api_server.py`; `python -m py_compile backend/dashboard/web_app.py`; `python -m py_compile backend/dashboard/cashier/cashier_routes.py`; `grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py`; `grep -q 'qr-pending' backend/dashboard/web_app.py`; `grep -q 'pending_qr_token' backend/dashboard/web_app.py`; `grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py`; `grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py`; `grep -q "api/qr/" backend/dashboard/web_app.py`; `grep -q 'qr/confirm' backend/dashboard/web_app.py`; `grep -q 'qr_payment' backend/dashboard/web_app.py`; `grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html`; `grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py`; `grep -q 'jwt_token' backend/api/api_server.py`; end with `echo "All S03 checks passed."`. (2) In `.env.example`, add `SERVER_URL=https://your-username.pythonanywhere.com` (e.g. after the existing ARDUINO_API_KEY line). (3) In `docs/DEPLOY.md`, add `SERVER_URL` to the required env vars section with a note: "Full base URL of the web_app deployment (no trailing slash). Used to build QR payment URLs. Example: `https://juley2823.pythonanywhere.com`. Note: `app.pending_qr_token` is in-memory — it resets on process restart." (4) `chmod +x scripts/verify-m005-s03.sh`. (5) Run `bash scripts/verify-m005-s03.sh` and confirm it exits 0.
  - Verify: `bash scripts/verify-m005-s03.sh` exits 0; `grep -q 'SERVER_URL' .env.example`.
  - Done when: `verify-m005-s03.sh` exits 0 with "All S03 checks passed." printed; `SERVER_URL` appears in `.env.example` and `docs/DEPLOY.md`.

## Files Likely Touched

- `backend/dashboard/web_app.py`
- `backend/api/api_server.py`
- `backend/dashboard/cashier/cashier_routes.py`
- `backend/dashboard/cashier/templates/cashier_index.html`
- `scripts/verify-m005-s03.sh`
- `.env.example`
- `docs/DEPLOY.md`
