---
id: T01
parent: S03
milestone: M005
provides:
  - app.pending_qr_token = None init in web_app.py
  - _decode_student_jwt() JWT helper in web_app.py
  - GET /api/arduino/qr-pending route (X-API-Key auth, returns token or null)
  - GET /api/qr/<token> route (student Bearer JWT auth, returns cart)
  - jwt_token field in api_server.py login response
key_files:
  - backend/dashboard/web_app.py
  - backend/api/api_server.py
key_decisions:
  - import jwt as _pyjwt to avoid naming collision with any local 'jwt' variable in web_app.py (api_server.py already uses bare 'jwt')
  - _decode_student_jwt helper placed in a dedicated JWT HELPER section between the arduino route and the QR PAYMENT ROUTES section for readability
patterns_established:
  - QR pending state lives solely in app.pending_qr_token (web_app.py process); cashier_routes.py writes via current_app; web_app.py reads directly
  - qr-pending returns {token: null} for both None and expired (>300s) states — single machine-readable idle signal for OLED firmware
observability_surfaces:
  - GET /api/arduino/qr-pending with valid X-API-Key: null = idle/expired, non-null = active pending token
  - Expiry check (>300s) is inline in both qr-pending and qr/<token> — no cron cleanup needed
duration: 10m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T01: Add `pending_qr_token` init, JWT helper, `qr-pending` and `qr/<token>` routes — plus `jwt_token` in login

**Added in-memory QR payment state, student JWT decode helper, Arduino polling route, student cart-fetch route, and jwt_token field to login response.**

## What Happened

All 6 steps executed cleanly in two files:

1. `backend/dashboard/web_app.py`:
   - Added `import jwt as _pyjwt` (aliased to avoid collision with any local `jwt` variable)
   - Added `app.pending_qr_token = None` after `app.arduino_last_heartbeat = 0.0`
   - Added `_decode_student_jwt(token_str)` helper that wraps `_pyjwt.decode()` in try/except, returning None on any failure
   - Added `GET /api/arduino/qr-pending` route using the same `X-API-Key` auth pattern as `arduino_heartbeat`; returns `{token: null}` when state is None or expired (>300s)
   - Added `GET /api/qr/<token>` route using student Bearer JWT via `_decode_student_jwt`; returns 401/404/200 with cart snapshot

2. `backend/api/api_server.py`:
   - Added `'jwt_token': generate_jwt_token(student['StudentID'], role='student')` to the login `jsonify` response dict — `generate_jwt_token` was already defined at line ~151

Also applied the pre-flight fix to S03-PLAN.md: added a failure-path verification step documenting that `GET /api/arduino/qr-pending` returns `{token: null}` on expiry or None state, confirming the OLED idle-state signal is machine-readable.

## Verification

```
python -m py_compile backend/dashboard/web_app.py       → OK
python -m py_compile backend/api/api_server.py          → OK
grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py   → OK
grep -q 'qr-pending' backend/dashboard/web_app.py               → OK
grep -q "api/qr/" backend/dashboard/web_app.py                  → OK
grep -q 'jwt_token' backend/api/api_server.py                   → OK
```

All 6 must-have checks passed.

## Diagnostics

- Inspect active QR state: `GET /api/arduino/qr-pending` with `X-API-Key: <ARDUINO_API_KEY>` header. Returns `{"token": null}` when idle or expired; returns `{"token": "...", "url": "..."}` when active.
- Inspect student cart view: `GET /api/qr/<token>` with `Authorization: Bearer <student_jwt>`. Returns `{"items": [...], "total": ..., "cashier": "..."}` on success, 401 for bad JWT, 404 for missing/expired/mismatched token.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `backend/dashboard/web_app.py` — added `import jwt as _pyjwt`, `app.pending_qr_token = None`, `_decode_student_jwt()` helper, `GET /api/arduino/qr-pending` route, `GET /api/qr/<token>` route
- `backend/api/api_server.py` — added `jwt_token` field to login jsonify response
