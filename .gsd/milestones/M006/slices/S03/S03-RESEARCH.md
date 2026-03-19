# M006/S03 — Research

**Date:** 2026-03-19

## Summary

S03 is the slice that closes **R053 (Standalone Cashier Web App)** by moving all payment-critical runtime behavior into `backend/cashier_app` so the cashier can complete sales with the admin dashboard process (port 5003) fully off. Right now, standalone has POS product/cart UI (`S02`) but **no payment routes, no Arduino WiFi routes, and no payment UI orchestration**.

The implementation landscape is already available in-repo: money-moving and queue logic in `backend/dashboard/cashier/cashier_routes.py`, and Arduino WiFi + QR student-confirm routes in `backend/dashboard/web_app.py`. This is a **port/adapt slice**, not a greenfield slice. Biggest adaptation points are auth/cookie differences (`cashier_token` vs `jwt_token`), request context differences (`request.cashier_data` vs `request.user`), and endpoint path differences (`/cashier/api/*` vs `/api/*`).

Two high-risk mismatches surfaced: (1) standalone currently binds `127.0.0.1` (not LAN-reachable), which blocks Arduino/mobile LAN traffic; (2) roadmap asks for NFC flow while project decisions around M005 retired phone NFC hardware flow, so NFC scope must be treated explicitly (compat route vs truly hardware-driven path).

## Recommendation

Take a **minimal-diff route port** approach:

1. Add `payment.py` and `arduino.py` under `backend/cashier_app/routes/` by adapting proven handlers from `cashier_routes.py` + `web_app.py`.
2. Keep route contracts expected by firmware/mobile (`/api/arduino/heartbeat`, `/api/arduino/card-read`, `/api/arduino/qr-pending`, `/api/qr/<token>`, `/api/qr/confirm`) even though `/api/qr/<token>` and `/api/qr/confirm` were omitted in the roadmap payment-route bullet list.
3. Update `pos.html` by preserving S02 cart/hydration architecture and layering payment orchestration on top (don’t rework S02 rendering pipelines).

Why: this reuses production-tested money and queue logic, preserves prior behavior (retry/rollback/offline queue), and minimizes regression risk while satisfying standalone isolation.

## Implementation Landscape

### Active Requirements This Slice Owns/Supports

- **Owns:** `R053` (Standalone cashier app end-to-end, including payment completion without admin dashboard running)
- **Supports continuity:** QR/OLED and Arduino polling flows previously established in M005 (`R027`, `R028`, `R029` behavior contracts)

### Key Files

- `backend/cashier_app/app.py` — Must register new payment/arduino blueprints; also needs app-level wiring for payment runtime (`app.socketio` missing, LAN bind currently localhost-only).
- `backend/cashier_app/templates/pos.html` — S02 cart/hydration UI exists; needs payment action wiring (checkout modal/status, route calls, socket event handlers, WiFi/queue indicators).
- `backend/cashier_app/routes/auth.py` — Current auth decorator sets `request.cashier_data`; copied payment logic using `request.user` must be adapted.
- `backend/dashboard/cashier/cashier_routes.py` — Primary source for `/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, queue status/sync, retry+rollback+offline queue patterns.
- `backend/dashboard/web_app.py` — Primary source for `/api/arduino/card-read`, `/api/arduino/heartbeat`, `/api/arduino/qr-pending`, `/api/qr/<token>`, `/api/qr/confirm` and emit-then-clear QR ordering.
- `backend/offline_queue.py` — Queue status/sync contract used by cashier payment fallback paths.
- `arduino/bankongseton_r4/bankongseton_r4.ino` — Hard route contracts from firmware (exact paths and headers) that standalone must satisfy.
- `tests/test_cashier_app_pos_route.py` — Existing standalone test style/convention; extend and mirror patterns for S03 tests.

### Natural Seams (Task Boundaries)

1. **Backend route port (cashier-auth routes):** process/complete/cancel/queue routes in new `backend/cashier_app/routes/payment.py`.
2. **Backend route port (device/student routes):** heartbeat/card-read/qr-pending/wifi-status + QR cart/confirm in new `backend/cashier_app/routes/arduino.py` (or split device vs QR if preferred).
3. **Frontend payment orchestration:** add payment method controls and socket/event flow to `backend/cashier_app/templates/pos.html` without touching S02 product/cart architecture.
4. **Regression tests:** add standalone-focused route tests (new test files), then update template hook assertions.

### Build Order

1. **Bootstrap correctness first (unblocks all integration):**
   - `backend/cashier_app/app.py`: register new blueprints, set `app.socketio = socketio`, keep `app.pending_qr_token` and `app.arduino_last_heartbeat`, and switch run host to LAN-capable binding for hardware/mobile tests.
2. **Port backend APIs before UI changes:**
   - Implement payment + Arduino/QR endpoints so frontend wiring has stable contracts.
3. **Wire frontend payment actions:**
   - Add checkout flow handlers that call new APIs and respond to `card_read`, `qr_payment`, status events.
4. **Add tests after endpoint stabilization:**
   - Route unit tests for auth, happy path, insufficient funds, offline fallback, API-key gating, QR token lifecycle.
5. **Runtime integration/UAT last:**
   - Validate with admin dashboard off and real route traffic on port 5010.

### Verification Approach

**Automated (contract):**

- `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py`
- `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q`
- `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q` *(new)*
- `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q` *(new)*

**Runtime (integration):**

- Start only standalone app on 5010 (admin dashboard off).
- Verify login → cart → checkout flow reaches `/api/process-sale` and `/api/complete-sale`.
- Verify Arduino heartbeat/card routes:
  - `POST /api/arduino/heartbeat` with `X-API-Key` updates WiFi status.
  - `POST /api/arduino/card-read` emits `card_read` and closes sale.
- Verify QR lifecycle:
  - cashier `POST /api/qr-generate`
  - Arduino `GET /api/arduino/qr-pending`
  - student `GET /api/qr/<token>` then `POST /api/qr/confirm`
  - cashier receives `qr_payment`; pending token is cleared after emit.
- Verify no accidental dependency on `:5003` resources (browser `performance.getEntriesByType('resource')` fallback pattern from project knowledge).

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Money debit + retry + rollback + queue fallback | `complete_sale` / `complete_sale_nfc` in `backend/dashboard/cashier/cashier_routes.py` | Already battle-tested for Sheets failures and offline queue semantics. |
| Arduino WiFi ingress contract | `arduino_card_read`, `arduino_heartbeat`, `arduino_qr_pending` in `backend/dashboard/web_app.py` | Matches R4 firmware route/header expectations exactly. |
| QR student confirmation semantics | `qr_cart` + `qr_confirm` in `backend/dashboard/web_app.py` | Preserves token expiry, insufficient-funds status code behavior, and cashier socket notify ordering. |

## Constraints

- **Firmware contract is fixed** by `arduino/bankongseton_r4/bankongseton_r4.ino`: exact paths `/api/arduino/card-read`, `/api/arduino/heartbeat`, `/api/arduino/qr-pending` + `X-API-Key` header.
- Standalone app currently runs on `127.0.0.1`; LAN/payment hardware needs network-reachable binding.
- Standalone auth currently uses `cashier_token` cookie + `request.cashier_data`; copied legacy handlers expecting `jwt_token`/`request.user` will break unless adapted.
- `SERVER_URL` is required for QR generation; missing value currently yields 500 in legacy logic.

## Common Pitfalls

- **Blind-copying cashier routes** — legacy code assumes `/cashier/api/*`, `jwt_token`, and `request.user`; adapt paths/cookie/request context for `cashier_app`.
- **Forgetting `app.socketio` attachment** — route code using `current_app.socketio.emit(...)` will fail unless `app.socketio` is set.
- **Clearing QR token too early** — preserve emit-then-clear ordering from `web_app.py` to avoid OLED/cashier race conditions.
- **Assuming heartbeat works without env setup** — `ARDUINO_API_KEY` mismatch/missing gives 401 and permanent red WiFi badge.
- **Route naming drift** — roadmap lists `/api/arduino/wifi-status`; existing prior-art route is `/api/arduino-wifi-status`. Decide one canonical path and optionally keep alias.

## Open Risks

- **NFC scope conflict:** M006 roadmap asks for NFC flow, while M005-era decisions/firmware trends indicate NFC phone tap path was retired/deprioritized. Need explicit execution decision for this slice (full NFC flow vs compatibility endpoint only).
- **Mobile local QR testing risk:** mobile clients currently use fixed API base URL patterns; local LAN standalone QR validation may require mobile config switch.
- **Environment drift:** `.env.example` documents `SERVER_URL` but not Arduino API key fields used by WiFi routes.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| POS web flow + API wiring | `fullstack-developer` | loaded/available |
| Verification strategy | `test` | loaded/available |
| Browser UAT automation | `agent-browser` | loaded/available |
| External skill discovery (`npx skills find`) | N/A | blocked in this environment (`npx` not found) |
