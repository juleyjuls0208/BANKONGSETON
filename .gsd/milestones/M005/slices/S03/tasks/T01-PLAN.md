---
estimated_steps: 6
estimated_files: 2
---

# T01: Add `pending_qr_token` init, JWT helper, `qr-pending` and `qr/<token>` routes — plus `jwt_token` in login

**Slice:** S03 — Backend QR Payment Flow  
**Milestone:** M005

## Description

Establishes the foundational in-memory QR state and the two read-only routes before the money-moving code is introduced. This task also adds the `jwt_token` field to the api_server.py login response — a one-line change needed by S04 apps.

Changes are split across two files only: `web_app.py` (Flask app process that owns SocketIO and pending state) and `api_server.py` (student login). No money movement happens in this task.

**Critical architecture reminder:** `app.pending_qr_token` and `socketio` live in the `web_app.py` process only. The Arduino polling route (`qr-pending`) belongs here. The student cart-fetch route (`qr/<token>`) also belongs here. `cashier_routes.py` reads/writes `app.pending_qr_token` only via `current_app` (blueprint context).

## Steps

1. **`web_app.py` — init state:** On line ~126, after `app.arduino_last_heartbeat = 0.0`, add:
   ```python
   app.pending_qr_token = None
   ```

2. **`web_app.py` — add jwt import:** Near the top of the file (after existing imports), add:
   ```python
   import jwt as _pyjwt  # aliased to avoid collision with any local 'jwt' variable
   ```
   Note: `_jwt_secret` is already defined at line ~73 (`_jwt_secret = os.getenv("JWT_SECRET", "").strip()`). Do not redefine it.

3. **`web_app.py` — add `_decode_student_jwt` helper:** Add this helper function after the imports/startup section (before the route definitions, or in a helpers block):
   ```python
   def _decode_student_jwt(token_str: str):
       """Decode a student JWT. Returns payload dict or None on failure."""
       try:
           return _pyjwt.decode(token_str, _jwt_secret, algorithms=["HS256"])
       except Exception:
           return None
   ```

4. **`web_app.py` — add `GET /api/arduino/qr-pending` route:** Place in the `ARDUINO WIFI ROUTE` section near `arduino_heartbeat`. The auth pattern is identical to `arduino_heartbeat` (`X-API-Key` header against `ARDUINO_API_KEY`):
   ```python
   @app.route("/api/arduino/qr-pending", methods=["GET"])
   def arduino_qr_pending():
       api_key = request.headers.get("X-API-Key", "")
       if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
           return jsonify({"error": "Unauthorized"}), 401
       t = app.pending_qr_token
       if t is None or time.time() - t["created_at"] > 300:
           return jsonify({"token": None}), 200
       return jsonify({"token": t["token"], "url": t["url"]}), 200
   ```

5. **`web_app.py` — add `GET /api/qr/<token>` route:** Place after `arduino_qr_pending` or in a new `QR PAYMENT ROUTES` section:
   ```python
   @app.route("/api/qr/<token>", methods=["GET"])
   def qr_cart(token):
       auth_header = request.headers.get("Authorization", "")
       token_str = auth_header.replace("Bearer ", "").strip()
       payload = _decode_student_jwt(token_str)
       if not payload:
           return jsonify({"error": "Unauthorized"}), 401
       t = app.pending_qr_token
       if t is None or t["token"] != token or time.time() - t["created_at"] > 300:
           return jsonify({"error": "QR expired or not found"}), 404
       return jsonify({
           "items": t["cart_snapshot"],
           "total": t["total"],
           "cashier": t["cashier_username"],
       }), 200
   ```

6. **`api_server.py` — add `jwt_token` to login response:** Find the login route (`POST /api/auth/login`). Inside the `return jsonify({...})` block that currently returns `token`, `student: {...}` etc., add one field:
   ```python
   'jwt_token': generate_jwt_token(student['StudentID'], role='student'),
   ```
   `generate_jwt_token` is already defined at line ~151 of api_server.py. Add this field to the existing dict — do not restructure the response.

## Must-Haves

- [ ] `app.pending_qr_token = None` added after `app.arduino_last_heartbeat = 0.0` in `web_app.py`
- [ ] `import jwt as _pyjwt` added; `_decode_student_jwt(token_str)` helper defined
- [ ] `GET /api/arduino/qr-pending` route uses `X-API-Key` auth; returns `{token: null}` when None or expired (>300s)
- [ ] `GET /api/qr/<token>` route uses student JWT Bearer auth; returns 401, 404, or 200 with cart
- [ ] `jwt_token` field added to `api_server.py` login `jsonify` response
- [ ] Both files pass `python -m py_compile`

## Verification

```bash
python -m py_compile backend/dashboard/web_app.py
python -m py_compile backend/api/api_server.py
grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py
grep -q 'qr-pending' backend/dashboard/web_app.py
grep -q "api/qr/" backend/dashboard/web_app.py
grep -q 'jwt_token' backend/api/api_server.py
```

All commands must exit 0.

## Observability Impact

- Signals added: `GET /api/arduino/qr-pending` returns machine-readable `{token: null}` vs `{token, url}` — OLED firmware uses this to determine whether to render a QR or show idle screen
- Failure state exposed: expired token (>300s) returns `{token: null}` immediately, preventing OLED from showing a stale unclearable QR
- How a future agent inspects: hit `GET /api/arduino/qr-pending` with valid `X-API-Key` header — null means idle, non-null means pending

## Inputs

- `backend/dashboard/web_app.py` — existing file; `app.arduino_last_heartbeat = 0.0` at line ~125 (insert `app.pending_qr_token = None` immediately after); `ARDUINO_API_KEY` already bound; `_jwt_secret` already defined at line ~73; `time` already imported; `request`, `jsonify` already imported from Flask
- `backend/api/api_server.py` — existing file; `generate_jwt_token(user_id, role='student')` already defined at line ~151; login route at `POST /api/auth/login` already returns student info dict

## Expected Output

- `backend/dashboard/web_app.py` — modified: `app.pending_qr_token = None` init; `import jwt as _pyjwt`; `_decode_student_jwt()` helper; `arduino_qr_pending()` route; `qr_cart()` route
- `backend/api/api_server.py` — modified: login response includes `jwt_token` field
