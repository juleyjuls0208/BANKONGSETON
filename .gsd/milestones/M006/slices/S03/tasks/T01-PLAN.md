---
estimated_steps: 5
estimated_files: 4
---

# T01: Port standalone payment APIs and money-safe queue behavior

**Slice:** S03 — Payment flows — RFID, QR, NFC
**Milestone:** M006

## Description

Implement the standalone payment backend so `backend/cashier_app` can process and complete sales without calling admin-dashboard endpoints. Adapt proven logic from `backend/dashboard/cashier/cashier_routes.py` into a new standalone blueprint while preserving retry/rollback/offline queue safety semantics.

Relevant skills to load: `fullstack-developer`, `test`.

## Steps

1. Update `backend/cashier_app/app.py` runtime wiring: attach `app.socketio = socketio`, ensure shared state (`pending_qr_token`, heartbeat fields) remains available, and register the new payment blueprint.
2. Create `backend/cashier_app/routes/payment.py` with standalone routes: `/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`.
3. Adapt auth/request context from dashboard assumptions (`request.user`, old cookie naming) to standalone cashier context (`request.cashier_data` + existing S01 auth decorators), preserving money-moving guardrails and queue fallback behavior.
4. Add route-contract tests in `tests/test_cashier_app_payment_routes.py` for auth gating, happy path, insufficient funds, Sheets failure fallback to offline queue, cancel/reset path, and queue status/sync responses.
5. Run syntax + tests and fix contract mismatches until green.

## Must-Haves

- [ ] Payment blueprint exists and is registered in standalone app.
- [ ] All listed payment endpoints are implemented under `/api/*` in `cashier_app`.
- [ ] Offline queue fallback (including retry/rollback behavior) is preserved for sale completion failures.
- [ ] Automated tests cover both happy and failure paths for money-moving routes.

## Verification

- `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py`
- `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q`

## Observability Impact

- Signals added/changed: `sale_complete` / `sale_cancelled` emission paths, queue fallback state, and structured JSON error payloads from payment routes.
- How a future agent inspects this: Run `tests/test_cashier_app_payment_routes.py`; inspect `/api/queue/status` response and Flask logs for fallback/error traces.
- Failure state exposed: insufficient funds vs backend outage are distinguishable (`402`/`5xx` + queue metadata) instead of generic failure.

## Inputs

- `backend/dashboard/cashier/cashier_routes.py` — Source of proven payment + queue logic to adapt.
- `backend/offline_queue.py` — Queue contracts consumed by fallback and sync endpoints.
- `backend/cashier_app/routes/auth.py` — Existing standalone cashier auth decorators and request context.
- `.gsd/milestones/M006/slices/S03/S03-RESEARCH.md` — Port/adapt constraints (auth context mismatch, queue semantics, route paths).

## Expected Output

- `backend/cashier_app/routes/payment.py` — New standalone payment blueprint with full endpoint set.
- `backend/cashier_app/app.py` — Blueprint/runtime wiring updates required by payment handlers.
- `tests/test_cashier_app_payment_routes.py` — New standalone payment route contract tests.
- `tests/test_cashier_app_pos_route.py` — Optional fixture updates if shared auth/session helpers need extension.
