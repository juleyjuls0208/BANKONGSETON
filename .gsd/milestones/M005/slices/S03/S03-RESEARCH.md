# M005/S03 — Backend QR Payment Flow: Research

**Scope:** R029  
**Date:** 2026-03-17  
**Depth:** Targeted (known tech, new routes on existing Flask apps)

---

## Summary

S03 adds four net-new endpoints that form the server-side backbone of QR payment. No QR backend code exists yet — `pending_qr_token`, `qr-generate`, `qr-pending`, `qr/<token>`, and `qr/confirm` are all absent from every Python file. The slice is self-contained (no dependency on S01/S02 hardware).

The critical architectural finding: **api_server.py and web_app.py run as separate Flask processes** on PythonAnywhere. They share no memory. `app.pending_qr_token` must live in web_app.py — that is the process that owns SocketIO and the cashier UI. Therefore `GET /api/qr/<token>` and `POST /api/qr/confirm` also belong in web_app.py, not api_server.py. Putting confirm in api_server.py would require a cross-process HTTP call to emit `qr_payment` to the cashier — the existing heartbeat and card-read routes (both in web_app.py) confirm this is the right home.

Student auth for the QR endpoints uses the same `JWT_SECRET` shared across both processes. api_server.py already has `generate_jwt_token()` but the login route currently only returns a session token. One line must be added to the login response to issue a JWT that S04 apps can use for `/api/qr/*` calls.

---

## Recommendation

Put all four QR endpoints in exactly two files:

| Endpoint | File | Auth |
|---|---|---|
| `POST /cashier/api/qr-generate` | `cashier_routes.py` | cashier JWT (`@jwt_required`) |
| `GET /api/arduino/qr-pending` | `web_app.py` | API key (`X-API-Key`) |
| `GET /api/qr/<token>` | `web_app.py` | student JWT (`jwt.decode`) |
| `POST /api/qr/confirm` | `web_app.py` | student JWT (`jwt.decode`) |

Initialize `app.pending_qr_token = None` in web_app.py at line 126 (after `app.arduino_last_heartbeat = 0.0`). Add one line to api_server.py login response. Write verify script. Done.

---

## Implementation Landscape

### Key Files

- **`backend/dashboard/web_app.py`** — owns `/api/arduino/card-read` and `/api/arduino/heartbeat` (identical API-key auth pattern for `qr-pending`); `app.arduino_last_heartbeat = 0.0` at line 125 (pattern for `app.pending_qr_token`); module-level `socketio` object for emitting `qr_payment`; imports from `dashboard_core` (`get_sheets_client`, `get_philippines_time`). All four new web_app.py routes go in the `ARDUINO WIFI ROUTE` section or a new `QR PAYMENT ROUTES` section.

- **`backend/dashboard/cashier/cashier_routes.py`** — owns all `/cashier/api/*`; has `@jwt_required(roles=['cashier','admin'])` decorator; `complete_sale()` provides the retry/rollback/offline-queue pattern to clone for `qr/confirm` debit logic; uses `current_app` (not `app`) inside blueprint — this is essential for accessing `current_app.pending_qr_token`.

- **`backend/dashboard/cashier/templates/cashier_index.html`** — `socket.on('nfc_payment', ...)` at line 338 is the pattern; add `socket.on('qr_payment', ...)` immediately after it.

- **`backend/api/api_server.py`** — student login at `/api/auth/login`; `generate_jwt_token(user_id, role='student')` exists at line ~170; add `'jwt_token': generate_jwt_token(student['StudentID'], role='student')` to the login `jsonify` response.

- **`arduino/bankongseton_r4/bankongseton_r4.ino`** — `parseQrUrl()` already handles `{"token":null}` → returns `""`. `httpGetBody("/api/arduino/qr-pending")` already polls this path. No firmware changes needed for S03.

### `app.pending_qr_token` Schema

```python
# web_app.py line ~126
app.pending_qr_token = None   # add after app.arduino_last_heartbeat = 0.0

# When set by qr-generate:
app.pending_qr_token = {
    'token': str,          # uuid4 string
    'url': str,            # https://<SERVER_URL>/api/qr/<token>
    'cart_snapshot': list, # items from cashier cart
    'total': float,
    'created_at': float,   # time.time()
    'cashier_username': str,
}
```

`SERVER_URL` must be added as env var (`.env` and `.env.example`):
```
SERVER_URL=https://juley2823.pythonanywhere.com
```

### Endpoint Implementations

**`POST /cashier/api/qr-generate`** (cashier_routes.py):
```python
import uuid, time, os
from flask import current_app

@cashier_bp.route('/api/qr-generate', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def qr_generate():
    data = request.get_json() or {}
    items = data.get('items', [])
    total = float(data.get('total', 0))
    if not items or total <= 0:
        return jsonify({'error': 'Invalid cart'}), 400
    server_url = os.getenv('SERVER_URL', '').rstrip('/')
    if not server_url:
        return jsonify({'error': 'SERVER_URL not configured'}), 500
    token = str(uuid.uuid4())
    url = f"{server_url}/api/qr/{token}"
    current_app.pending_qr_token = {
        'token': token, 'url': url,
        'cart_snapshot': items, 'total': total,
        'created_at': time.time(),
        'cashier_username': request.user.get('username', ''),
    }
    logger.info("event=qr_generate token=%s total=%.2f", token, total)
    return jsonify({'token': token, 'url': url})
```

**`GET /api/arduino/qr-pending`** (web_app.py) — API key auth, identical to `arduino_heartbeat`:
```python
@app.route("/api/arduino/qr-pending", methods=["GET"])
def arduino_qr_pending():
    api_key = request.headers.get("X-API-Key", "")
    if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    t = app.pending_qr_token
    if t is None or time.time() - t['created_at'] > 300:
        return jsonify({"token": None}), 200
    return jsonify({"token": t['token'], "url": t['url']}), 200
```

**`GET /api/qr/<token>`** (web_app.py) — student JWT auth:
```python
@app.route("/api/qr/<token>", methods=["GET"])
def qr_cart(token):
    payload = _decode_student_jwt(request.headers.get('Authorization','').replace('Bearer ',''))
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    t = app.pending_qr_token
    if t is None or t['token'] != token or time.time() - t['created_at'] > 300:
        return jsonify({'error': 'QR expired or not found'}), 404
    return jsonify({'items': t['cart_snapshot'], 'total': t['total'], 'cashier': t['cashier_username']}), 200
```

**`POST /api/qr/confirm`** (web_app.py) — student JWT, clones `complete_sale()` debit pattern:
```python
@app.route("/api/qr/confirm", methods=["POST"])
def qr_confirm():
    payload = _decode_student_jwt(...)
    if not payload: return jsonify({'error':'Unauthorized'}), 401
    data = request.get_json() or {}
    token_param = data.get('token','')
    t = app.pending_qr_token
    if t is None or t['token'] != token_param:
        return jsonify({'error': 'QR expired or not found'}), 404
    if time.time() - t['created_at'] > 300:
        app.pending_qr_token = None
        return jsonify({'error': 'QR token expired'}), 410
    student_id = payload.get('user_id','')
    # 1. Look up student MoneyCardNumber from Users sheet
    # 2. Look up Money Accounts — direct Sheets read (no cache, D018)
    # 3. Check balance >= t['total']
    # 4. Debit with retry/rollback/offline-queue (clone complete_sale pattern)
    # 5. Log as 'QR Purchase' in Transactions Log
    # 6. socketio.emit('qr_payment', {...})
    # 7. app.pending_qr_token = None
    # 8. Non-fatal FCM/SMS/email (clone pattern)
    return jsonify({'success': True, 'new_balance': new_balance, 'timestamp': timestamp}), 200
```

**JWT helper** (web_app.py, near top or in a helpers section):
```python
import jwt as _pyjwt  # avoid name clash with cashier_routes' jwt var
def _decode_student_jwt(token_str: str):
    try:
        return _pyjwt.decode(token_str, _jwt_secret, algorithms=['HS256'])
    except Exception:
        return None
```
(`_jwt_secret = os.getenv('JWT_SECRET','').strip()` — already validated by startup guard)

**`socket.on('qr_payment')` in cashier_index.html** (after line 341):
```js
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

**api_server.py login** — one-line addition inside the `return jsonify(...)` block:
```python
'jwt_token': generate_jwt_token(student['StudentID'], role='student'),
```

### Build Order

1. `api_server.py` login — add `jwt_token` field (1-line, low risk, needed by S04)
2. `web_app.py` — init `app.pending_qr_token`, add JWT helper, add `qr-pending`, `qr/<token>`, `qr/confirm`
3. `cashier_routes.py` — add `qr-generate` (needs `current_app.pending_qr_token`)
4. `cashier_index.html` — add `socket.on('qr_payment', ...)` handler
5. `scripts/verify-m005-s03.sh` — grep checks + `python -m py_compile`
6. `.env.example` — add `SERVER_URL=` placeholder
7. `docs/DEPLOY.md` — add `SERVER_URL` to required env vars section; note `pending_qr_token` resets on process restart

### Verification Approach

`scripts/verify-m005-s03.sh` checks:

```bash
# Syntax
python -m py_compile backend/api/api_server.py
python -m py_compile backend/dashboard/web_app.py
python -m py_compile backend/dashboard/cashier/cashier_routes.py

# qr-pending in web_app.py (API key auth)
grep -q 'qr-pending' backend/dashboard/web_app.py
grep -q 'pending_qr_token' backend/dashboard/web_app.py

# qr-generate in cashier_routes.py
grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py
grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py

# qr/<token> and qr/confirm in web_app.py
grep -q "api/qr/" backend/dashboard/web_app.py
grep -q 'qr/confirm' backend/dashboard/web_app.py

# qr_payment SocketIO emit
grep -q 'qr_payment' backend/dashboard/web_app.py
grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html

# SERVER_URL consumed
grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py

# jwt_token in login response
grep -q 'jwt_token' backend/api/api_server.py

# app state init
grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py
```

---

## Constraints

- **Separate processes**: `app.pending_qr_token` and `socketio` live only in web_app.py's process. All QR endpoints that need either must be in web_app.py or its registered blueprints (cashier_routes).
- **`current_app` in blueprint**: Inside `cashier_routes.py`, `app` is not in scope — use `current_app.pending_qr_token`. The `app.socketio = socketio` assignment at line 124 of web_app.py makes `current_app.socketio` work in blueprints.
- **No cache on balance read**: D018 decision — Money Accounts must always be read fresh in payment flows. Do not use `get_cached()` in `qr/confirm`.
- **Imports in web_app.py**: `jwt` is already imported as `import jwt` at the top of cashier_routes.py. In web_app.py, the module uses `import jwt` is not present yet — must add. Alias as `_pyjwt` to avoid collision with any local variable named `jwt`.
- **`uuid` not yet in cashier_routes.py**: Add `import uuid` at the top.
- **Single-worker constraint (D013/R016)**: `app.pending_qr_token` as in-memory state is only valid under single-worker. The startup guard already enforces this (WEB_CONCURRENCY guard in web_app.py lines 77-85). No new guard needed.

## Common Pitfalls

- **`app` vs `current_app` in blueprint** — `qr-generate` is in cashier_routes.py (a blueprint). `app.pending_qr_token` will raise `RuntimeError: Working outside of application context`. Must use `current_app.pending_qr_token`.
- **`user_id` vs `student_id` in JWT payload** — `generate_jwt_token()` in api_server.py sets the key as `user_id`. When decoding in web_app.py `qr/confirm`, read `payload.get('user_id')`, not `payload.get('student_id')`.
- **Expired token not cleared** — `qr-pending` should return `{"token": null}` when expired (>300s) so the Arduino clears its OLED. If the expired check only runs in `qr/confirm`, the OLED stays stuck on an unclearable QR. Add the expiry check in `qr-pending` too.
- **Missing `import jwt` in web_app.py** — web_app.py does not currently import the `jwt` package. Add before the `_decode_student_jwt` helper.
- **SocketIO emit placement** — emit `qr_payment` AFTER the Sheets debit commits, BEFORE clearing `app.pending_qr_token`. If emit is after the clear, a timing edge case could leave cashier without a success notification.
