---
id: S03
parent: M005
milestone: M005
provides:
  - POST /cashier/api/qr-generate (cashier JWT) — creates UUID token, stores as app.pending_qr_token, returns {token, url}
  - GET /api/arduino/qr-pending (X-API-Key) — returns {token, url} when pending and not expired; {token: null} otherwise
  - GET /api/qr/<token> (student Bearer JWT) — returns {items, total, cashier} for the pending cart
  - POST /api/qr/confirm (student Bearer JWT) — validates token, debits balance via 3-retry/rollback/offline-queue pattern, emits qr_payment SocketIO event, clears token
  - socket.on('qr_payment', ...) handler in cashier_index.html — shows success modal, clears cart
  - app.pending_qr_token = None initialized in web_app.py; shared state written by cashier_routes.py via current_app
  - jwt_token field in api_server.py login response — enables student apps to authenticate to /api/qr/* endpoints
  - scripts/verify-m005-s03.sh — 14-check verification script (3 py_compile + 11 grep); exits 0
  - SERVER_URL env var documented in .env.example and docs/DEPLOY.md
requires:
  - slice: none
    provides: parallel to S01/S02; no runtime dependencies
affects:
  - S04: Android + iOS apps call GET /api/qr/<token> and POST /api/qr/confirm directly
  - S02: OLED firmware polls GET /api/arduino/qr-pending (now has a live backend to connect to)
  - S05: /api/nfc/* routes confirmed replaced by /api/qr/*; nfc_payment socket event will be removed
key_files:
  - backend/dashboard/web_app.py
  - backend/api/api_server.py
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/cashier/templates/cashier_index.html
  - scripts/verify-m005-s03.sh
  - .env.example
  - docs/DEPLOY.md
key_decisions:
  - import jwt as _pyjwt in web_app.py — avoids naming collision with any local 'jwt' variable; api_server.py keeps bare 'jwt'
  - current_app.pending_qr_token (not bare app.) in cashier_routes.py — blueprint context requires current_app proxy; bare app would be RuntimeError
  - socketio.emit('qr_payment') fires BEFORE app.pending_qr_token = None in all code paths — prevents timing race where OLED sees null token before cashier UI processes the event
  - 402 for insufficient-funds (not 400) — distinguishes from bad-request so mobile apps can show a meaningful message
  - "QR Purchase" transaction type — distinguishes from NFC "Purchase" in audit trail
  - qr-pending returns {token: null} for both None and expired (>300s) states — single machine-readable idle signal for OLED firmware; no separate expired vs missing distinction needed
  - import json added at module level in web_app.py (was missing); os.getenv used directly in qr_generate (already imported at module level in cashier_routes.py)
patterns_established:
  - QR pending state lives solely in app.pending_qr_token (web_app.py process); cashier_routes.py writes via current_app; web_app.py reads directly — no cross-process call
  - QR debit clones complete_sale() retry/rollback/offline-queue pattern exactly: 3-attempt loop, exponential backoff (2^attempt), rollback on balance_deducted, offline_queue fallback, emit+clear on all success paths
  - 5-minute expiry enforced inline in both qr-pending and qr/<token> and qr/confirm — no cron cleanup needed; OLED clears automatically when token expires
observability_surfaces:
  - GET /api/arduino/qr-pending (X-API-Key) — live QR state signal: null = idle/expired, non-null = active pending token; also confirms token cleared after confirm
  - Flask log grep 'event=qr_generate' — fires on each token creation with UUID and total
  - Flask log grep 'event=qr_confirm' — fires on successful debit with student_id, total, new_balance
  - Flask log grep 'event=qr_offline_queued' — fires when Sheets unavailable; transaction queued
  - Flask log grep 'event=qr_offline_queue_failed' — fires when offline queue itself fails
  - bash scripts/verify-m005-s03.sh — 14-check contract verification; exit 0 = slice complete; non-zero with specific grep pattern = regression
drill_down_paths:
  - .gsd/milestones/M005/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M005/slices/S03/tasks/T03-SUMMARY.md
duration: ~45 minutes total (T01: 10m, T02: 25m, T03: 10m)
verification_result: passed
completed_at: 2026-03-17
---

# S03: Backend QR Payment Flow

**Four new endpoints and one socket handler form the complete server-side QR payment backbone: cashier generates a short-lived token, Arduino polls for it, student fetches cart and confirms, balance is debited with retry/rollback/offline-queue, and cashier UI shows success — all 14 contract checks pass.**

## What Happened

Three tasks delivered the full QR payment server-side in ~45 minutes with no blockers.

**T01** established the in-memory QR state foundation in `web_app.py`: added `app.pending_qr_token = None` after the existing `arduino_last_heartbeat` init, aliased `import jwt as _pyjwt` to avoid naming collisions, added `_decode_student_jwt()` helper for student route auth, added `GET /api/arduino/qr-pending` (same X-API-Key pattern as arduino_heartbeat), and added `GET /api/qr/<token>` for student cart-fetch. In `api_server.py`, added `jwt_token` to the student login response — enabling S04 apps to call `/api/qr/*` endpoints without a separate auth flow.

**T02** delivered the money-moving layer. In `cashier_routes.py`: added `import uuid` and `POST /cashier/api/qr-generate` — reads `SERVER_URL` from env (returns 500 if blank), generates UUID token, stores full cart snapshot in `current_app.pending_qr_token`, logs `event=qr_generate`. In `web_app.py`: added `import json` (was missing) and `POST /api/qr/confirm` — decodes student JWT, validates token match and 5-min expiry, looks up student's `MoneyCardNumber`, reads Money Accounts fresh (D018), checks card status and balance, runs 3-retry debit loop with exponential backoff, rolls back on failure, queues to offline_queue if Sheets is down, emits `qr_payment` BEFORE clearing token, logs `event=qr_confirm`. In `cashier_index.html`: added `socket.on('qr_payment', ...)` handler that shows "QR Payment Received!" modal with new balance, clears cart, auto-closes after 2 seconds.

**T03** created `scripts/verify-m005-s03.sh` with 14 checks (3 py_compile + 11 grep), added `SERVER_URL` to `.env.example` in a dedicated `# QR Payment` section, and added `SERVER_URL` row to `docs/DEPLOY.md` section 4a table with the in-memory reset note. Script runs clean on first execution.

## Verification

`bash scripts/verify-m005-s03.sh` exits 0. All 14/14 checks pass:
- 3 Python syntax checks (api_server.py, web_app.py, cashier_routes.py) — OK
- 11 grep checks covering: `pending_qr_token` init, `qr-pending` route, `pending_qr_token` in web_app, `qr-generate` in cashier_routes, `pending_qr_token` in cashier_routes, `/api/qr/` route, `qr/confirm` route, `qr_payment` socketio.emit, `socket.on(qr_payment)`, `SERVER_URL` consumption, `jwt_token` in login — all OK

Additional spot-checked: `402` for insufficient funds, `"QR Purchase"` transaction type, `event=qr_generate` and `event=qr_confirm` log lines, `import uuid`, `current_app` (not bare `app`) in cashier_routes — all confirmed.

## Requirements Advanced

- R029 (Backend QR Payment Flow) — all four endpoints implemented; `app.pending_qr_token` state machine in place; contract verified by scripts/verify-m005-s03.sh

## Requirements Validated

- R029 — contract validation complete: `bash scripts/verify-m005-s03.sh` exits 0; all 14 checks pass; live Sheets debit deferred to S04 end-to-end

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- `.env.example` does not contain an `ARDUINO_API_KEY` section (T03 plan assumed it would for placement reference). `SERVER_URL` was placed before `# Production Settings` block instead — natural location for deploy-time env vars. No functional impact.
- `import json` was missing from `web_app.py` module-level imports; added at module level (not inline) per the cleaner pattern. No functional impact.

## Known Limitations

- `app.pending_qr_token` is in-memory only — resets on process restart. This is documented in `.env.example` and `docs/DEPLOY.md`. Acceptable for single-worker PythonAnywhere deployment; would need Redis or DB-backed storage for multi-worker.
- Only one pending QR token exists at a time system-wide. A second cashier hitting "Pay Now" overwrites the first token. Acceptable for current single-cashier-per-terminal school deployment.
- Live Sheets balance debit is not verified at this slice level — S04 end-to-end proves the actual money movement with real credentials.
- FCM push on QR confirm is non-fatal (wrapped in try/except) — push failure silently swallowed; logged at WARNING level but not surfaced to student.

## Follow-ups

- S04: Android app needs `QRPayActivity.kt` calling `GET /api/qr/<token>` and `POST /api/qr/confirm` using the `jwt_token` from login response
- S04: iOS app needs `QRPayView.swift` + `QRScannerView.swift` with AVFoundation, same endpoint calls
- S05: `socket.on('nfc_payment')` handler in `cashier_index.html` becomes dead code once NFC is retired — delete in S05

## Files Created/Modified

- `backend/dashboard/web_app.py` — added `import jwt as _pyjwt`, `import json`, `app.pending_qr_token = None`, `_decode_student_jwt()` helper, `GET /api/arduino/qr-pending`, `GET /api/qr/<token>`, `POST /api/qr/confirm`
- `backend/api/api_server.py` — added `jwt_token` field to login jsonify response
- `backend/dashboard/cashier/cashier_routes.py` — added `import uuid`, `POST /cashier/api/qr-generate`
- `backend/dashboard/cashier/templates/cashier_index.html` — added `socket.on('qr_payment', ...)` handler after `nfc_payment`
- `scripts/verify-m005-s03.sh` — new file; 14-check S03 contract verification script; chmod +x; exits 0
- `.env.example` — added `SERVER_URL` in `# QR Payment` section
- `docs/DEPLOY.md` — added `SERVER_URL` row to section 4a Dashboard env vars table

## Forward Intelligence

### What the next slice should know

- **JWT auth for /api/qr/* uses student Bearer token from login response.** The `jwt_token` field is now in the `POST /api/login` response from `api_server.py`. Android and iOS apps should store this on login and send it as `Authorization: Bearer <jwt_token>` to both `GET /api/qr/<token>` and `POST /api/qr/confirm`.
- **QR URL format is `https://<SERVER_URL>/api/qr/<token>`.** The full URL is returned by `POST /cashier/api/qr-generate` and encoded in the OLED QR bitmap. Apps should handle the URL by extracting the token from the last path segment.
- **`POST /api/qr/confirm` body is `{"token": "<token>"}`.** The student app sends the token extracted from the scanned URL; the server validates it against `app.pending_qr_token['token']`.
- **Cart data returned by `GET /api/qr/<token>` shape:** `{"items": [...], "total": <float>, "cashier": "<username>"}`. `items` is the raw `cart_snapshot` as stored by the cashier — same structure as the cashier's cart array.
- **402 means insufficient funds.** Apps should show a specific "insufficient balance" message, not a generic error.
- **5-minute expiry on all QR tokens.** If the student takes longer than 5 minutes to scan and confirm, `GET /api/qr/<token>` returns 404 and `POST /api/qr/confirm` returns 410 Gone. Apps should handle both and prompt re-scan.

### What's fragile

- **Single pending token globally.** If two cashiers are running simultaneously and both hit "Pay Now", the second `qr-generate` silently overwrites the first. The first cashier's OLED will start showing the second cashier's QR. Acceptable now but will need per-cashier token scoping if multi-station deployment occurs.
- **`current_app.pending_qr_token` write in cashier_routes.py.** This works only in single-worker deployment. In a multi-worker or multi-process setup, `current_app` writes to per-worker state and `web_app.py` reads would miss writes from another worker process. The in-memory architecture is documented and hard-blocked by the `WEB_CONCURRENCY > 1` guard in R016/D013.
- **Non-fatal FCM on QR confirm.** If FCM push fails (network issue, invalid device token), the student gets no push notification but the payment still succeeds. This is intentional (same pattern as `complete_sale()`) but means the student app must poll for balance updates if a push is missed.

### Authoritative diagnostics

- **QR token state:** `GET /api/arduino/qr-pending` with `X-API-Key` header — null = idle/expired, non-null = active. This is the ground truth for the OLED state machine.
- **Token generation confirm:** `grep 'event=qr_generate' <flask_log>` — shows UUID and total on every successful cashier "Pay Now" hit.
- **Debit confirm:** `grep 'event=qr_confirm' <flask_log>` — shows student_id, total, new_balance on every successful QR payment.
- **Offline queue:** `grep 'event=qr_offline_queued' <flask_log>` — fires when Sheets is down but transaction was queued; `event=qr_offline_queue_failed` fires if even the queue fails.
- **S03 regression:** `bash scripts/verify-m005-s03.sh` — exits 0 = all endpoints and state in place; specific failing grep line identifies the regression.

### What assumptions changed

- `import json` was assumed present in `web_app.py` — it was not. Added at module level. No impact on existing code.
- `ARDUINO_API_KEY` was assumed to exist in `.env.example` (T03 plan used it as placement anchor) — it was not present. `SERVER_URL` section placed before `# Production Settings` instead, which is equally logical for deploy-time env vars.
