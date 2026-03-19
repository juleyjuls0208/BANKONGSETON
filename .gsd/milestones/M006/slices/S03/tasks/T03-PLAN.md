---
estimated_steps: 5
estimated_files: 3
---

# T03: Wire POS charge orchestration for RFID, QR, and NFC-compatible checkout

**Slice:** S03 — Payment flows — RFID, QR, NFC
**Milestone:** M006

## Description

Complete the cashier-facing payment flow in `pos.html` by wiring existing S02 cart state to standalone payment endpoints and SocketIO events. This task closes R053 at the user loop level: charge button action, payment progress/failure visibility, and standalone runtime proof with admin dashboard off.

Relevant skills to load: `fullstack-developer`, `agent-browser`, `test`.

## Steps

1. Extend `backend/cashier_app/templates/pos.html` payment controls/state (method selection, in-progress state, cancel/failure UI) while preserving S02 product hydration and cart-render architecture.
2. Wire checkout orchestration to standalone endpoints: start with `/api/process-sale`, then method-specific paths (`/api/complete-sale`, `/api/qr-generate`, `/api/complete-sale-nfc`, `/api/cancel-sale`, queue status/sync) plus auth-failure redirects.
3. Add/adjust SocketIO handlers in POS JS for `card_read`, `qr_payment`, `sale_complete`, `sale_cancelled`, and Arduino WiFi status events so the cashier sees deterministic payment state transitions.
4. Update `tests/test_cashier_app_pos_route.py` to assert payment hook presence (expected endpoint URLs/event handlers/status UI hooks) and prevent regressions in S02 cart behavior.
5. Run automated tests, then perform runtime verification on `localhost:5010` with admin dashboard process stopped, checking no accidental `:5003` dependencies.

## Must-Haves

- [ ] Charge flow uses standalone payment routes only (no dashboard port dependency).
- [ ] RFID, QR, and NFC-compatible method paths are reachable from the POS UI workflow.
- [ ] Payment status and failure states are visible to cashier and recoverable (cancel/retry path).
- [ ] Template/route tests cover payment hook contracts without breaking S02 cart math/render behavior.

## Verification

- `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q`
- Runtime UAT: `rtk proxy python backend/cashier_app/app.py` (admin dashboard off), login at `http://localhost:5010`, run charge flow, and verify via browser console `performance.getEntriesByType('resource')` that payment/resource traffic stays on port 5010.

## Observability Impact

- Signals added/changed: POS payment state transitions, queue fallback status rendering, WiFi connectivity badge/state updates.
- How a future agent inspects this: UI payment-status region + charge button state, browser console events, and route-call evidence in resource entries.
- Failure state exposed: insufficient funds, auth expiration, queue fallback, and card/QR timeout states surface as user-visible statuses (not silent failures).

## Inputs

- `backend/cashier_app/templates/pos.html` — S02 cart and product rendering baseline to preserve.
- `backend/cashier_app/routes/payment.py` — Standalone sale-processing API contracts from T01.
- `backend/cashier_app/routes/arduino.py` — Standalone Arduino + QR contracts and status/event surfaces from T02.
- `.gsd/milestones/M006/slices/S02/S02-SUMMARY.md` — Established render and auth-handling patterns (D059, D060) that must not regress.

## Expected Output

- `backend/cashier_app/templates/pos.html` — Payment-orchestrated POS UI with method flow handling and observable failure states.
- `tests/test_cashier_app_pos_route.py` — Expanded standalone POS contract tests including payment wiring assertions.
- `.gsd/milestones/M006/slices/S03/S03-SUMMARY.md` (future execution artifact) — Evidence of standalone payment UAT and verification outcomes.
