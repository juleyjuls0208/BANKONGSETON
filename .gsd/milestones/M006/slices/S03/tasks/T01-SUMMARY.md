---
id: T01
parent: S03
milestone: M006
provides:
  - Standalone cashier payment API blueprint with RFID/QR/NFC-compatible sale completion and offline queue diagnostics
key_files:
  - backend/cashier_app/app.py
  - backend/cashier_app/routes/payment.py
  - tests/test_cashier_app_payment_routes.py
  - .gsd/milestones/M006/slices/S03/S03-PLAN.md
key_decisions:
  - Kept money-moving retry/rollback/offline-queue semantics while adapting auth context from request.user/jwt_token to request.cashier_data/cashier_token
  - Standardized insufficient-funds responses on money-moving routes to HTTP 402 with balance/required payload for clear operator handling
patterns_established:
  - Lazy-import dashboard helpers inside route handlers so standalone tests can patch contracts without admin-dashboard startup side effects
  - Emit sale_complete/sale_cancelled SocketIO signals from standalone payment routes with redacted identifiers
observability_surfaces:
  - /api/queue/status
  - /api/queue/sync
  - SocketIO events: cashier_request_card, sale_complete, sale_cancelled
  - Offline fallback payload includes queue snapshot metadata
duration: 1h 22m
verification_result: passed
completed_at: 2026-03-19
blocker_discovered: false
---

# T01: Port standalone payment APIs and money-safe queue behavior

**Added standalone cashier payment routes with retry/rollback queue safety, wired them into `cashier_app`, and validated the new payment route contract tests.**

## What Happened

Implemented `backend/cashier_app/routes/payment.py` as a standalone blueprint with `/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, `/api/queue/status`, and `/api/queue/sync`, using S01 cashier auth context (`request.cashier_data`, `cashier_token`) instead of dashboard assumptions.

Ported and preserved money-safe behavior from dashboard cashier flows: bounded retries, exponential backoff, rollback attempt on exhausted retries, and offline queue fallback via `offline_queue.get_offline_queue()` with queue snapshot returned in fallback responses.

Updated `backend/cashier_app/app.py` to register the new payment blueprint, attach `app.socketio = socketio`, and keep shared app state (`pending_qr_token`, heartbeat fields) available to route handlers.

Added `tests/test_cashier_app_payment_routes.py` route-contract coverage for auth gating, process-sale happy path/session state, complete-sale happy path, insufficient funds (402), Sheets outage offline fallback with queue metadata, cancel/reset flow, and queue status/sync surfaces.

Marked T01 complete in `.gsd/milestones/M006/slices/S03/S03-PLAN.md`.

## Verification

Ran task-level required checks and then executed slice-level automated checks to capture current progress status for downstream tasks.

Task-level checks both passed (`py_compile` for updated files and dedicated payment route tests).

Slice-level checks are partially passing at this stage: POS route tests pass; Arduino compile/test checks fail because `backend/cashier_app/routes/arduino.py` and `tests/test_cashier_app_arduino_routes.py` are intentionally part of T02 and not yet implemented in T01.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py` | 0 | ✅ pass | <1s |
| 2 | `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q` | 0 | ✅ pass | 1.09s |
| 3 | `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py` | 1 | ❌ fail | <1s |
| 4 | `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q` | 4 | ❌ fail | <1s |
| 5 | `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` | 0 | ✅ pass | 1.04s |

## Diagnostics

- `GET /api/queue/status` returns pending/failed/synced counters + last sync metadata for offline-write visibility.
- `POST /api/queue/sync` returns synced/failed counts plus updated queue snapshot.
- `POST /api/process-sale` emits `cashier_request_card`.
- `POST /api/complete-sale` and `/api/complete-sale-nfc` emit `sale_complete` with method and offline flag.
- `POST /api/cancel-sale` emits `sale_cancelled` and clears pending transaction/QR state.
- Fallback responses from money routes expose `offline: true` and queue status instead of a generic failure.

## Deviations

None.

## Known Issues

- Slice-level Arduino verification checks are expectedly failing in this task because `backend/cashier_app/routes/arduino.py` and `tests/test_cashier_app_arduino_routes.py` are scheduled for T02.
- Full runtime integration verification (RFID/QR/NFC flow with admin dashboard off) remains for later slice tasks (T02/T03).

## Files Created/Modified

- `backend/cashier_app/routes/payment.py` — new standalone payment blueprint with process/complete/cancel/queue routes and queue-safe retry/rollback fallback.
- `backend/cashier_app/app.py` — registered payment blueprint, attached `app.socketio`, and preserved shared runtime app state.
- `tests/test_cashier_app_payment_routes.py` — new route-contract tests for auth, happy/failure paths, offline queue fallback, cancel, and queue surfaces.
- `.gsd/milestones/M006/slices/S03/S03-PLAN.md` — marked T01 as complete (`[x]`).
