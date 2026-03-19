---
id: T01
parent: S02
milestone: M006
provides:
  - Standalone cashier `/api/products` API route secured by cashier JWT cookie auth, backed by Google Sheets with cache import fallback.
key_files:
  - backend/cashier_app/routes/pos.py
  - tests/test_cashier_app_pos_route.py
  - .gsd/milestones/M006/slices/S02/S02-PLAN.md
key_decisions:
  - Reused the existing S01 `jwt_cookie_required` decorator from `backend/cashier_app/routes/ui.py` to enforce the same `cashier_token` cookie guard on `/api/products`.
patterns_established:
  - D017-style cache resilience pattern (`try` cache import, no-op fallback functions on `ImportError`) in standalone cashier route code.
observability_surfaces:
  - Logger events from `backend/cashier_app/routes/pos.py` (`event=products_cache_miss`, `event=products_invalid_price`, `event=products_fetch_failed`)
duration: 1h 10m
verification_result: passed
completed_at: 2026-03-19T06:23:00+08:00
blocker_discovered: false
---

# T01: Create backend `/api/products` route

**Added a JWT-cookie-protected standalone `/api/products` endpoint that reads active products from Google Sheets with cache fallback and test coverage for auth/data/error behavior.**

## What Happened

I replaced the existing `backend/cashier_app/routes/pos.py` implementation to align with the task contract: it now uses `@jwt_cookie_required`, performs D017-style cache import fallback (`cache.py` missing → no-op cache functions), pulls product rows from the `Products` worksheet via `get_sheets_client()`, filters to active/non-empty entries, normalizes prices, and returns a JSON list.

`backend/cashier_app/app.py` already had `pos_bp` imported and registered, so no additional wiring change was required there.

I also added focused tests in `tests/test_cashier_app_pos_route.py` to validate:
- unauthenticated requests are blocked (redirect to `/login`),
- authenticated requests return transformed active product JSON,
- Sheets failures emit `event=products_fetch_failed` and return HTTP 500.

I marked T01 complete in `.gsd/milestones/M006/slices/S02/S02-PLAN.md`.

## Verification

Task-level verification was run with syntax checks, endpoint runtime checks, and pytest route tests.

Slice-level verification checks were also exercised as an intermediate task:
- App startup: ✅
- Login + main POS page reachable: ✅
- Product-grid/cart interaction checks: ❌ (expected pending for T02/T03)
- `/api/products` request path on port 5010 and no port 5003 calls: ✅ for routing/port check
- Live Sheets-backed 200 response: ❌ in this environment (returned 500 due Sheets connectivity), while mocked route tests prove the success path contract.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile backend/cashier_app/routes/pos.py tests/test_cashier_app_pos_route.py backend/cashier_app/app.py` | 0 | ✅ pass | ~0.2s |
| 2 | `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py` | 0 | ✅ pass | 0.86s |
| 3 | `rtk proxy curl -i -s http://127.0.0.1:5010/api/products` (unauthenticated) | 0 | ✅ pass (302 redirect to `/login`) | ~0.2s |
| 4 | `rtk proxy curl -s -i -c /tmp/cashier_cookie.txt -H "Content-Type: application/json" -d '{"username":"cashier","password":"cashier123"}' http://127.0.0.1:5010/api/login` | 0 | ✅ pass (200 + `cashier_token`) | ~0.3s |
| 5 | `rtk proxy curl -s -i -b /tmp/cashier_cookie.txt http://127.0.0.1:5010/api/products` | 0 | ❌ fail (500 in current env; expected when Sheets unavailable) | ~0.2s |
| 6 | Browser flow: navigate `/login` → submit cashier credentials → assert POS shell content | 0 | ✅ pass | ~10s |
| 7 | Browser flow: fetch `/api/products` and inspect network logs for 5003 calls | 0 | ❌ fail (endpoint returned 500 in this environment; no 5003 calls observed) | ~2s |

## Diagnostics

- Route observability is exposed through `backend/cashier_app/routes/pos.py` logger messages:
  - `event=products_cache_miss ...` when cache is empty,
  - `event=products_invalid_price ...` for malformed sheet price values,
  - `event=products_fetch_failed ...` on Sheets/import/runtime failures.
- API failure shape is explicit: `500 {"error":"Failed to load products"}`.
- Auth guard behavior is explicit: unauthenticated `/api/products` redirects to `/login`.

## Deviations

- `backend/cashier_app/app.py` did not need modification because `pos_bp` import/registration was already present before execution.
- Added `tests/test_cashier_app_pos_route.py` to satisfy task-level verification and observability validation with deterministic mocks.

## Known Issues

- In the current runtime environment, live `/api/products` returned HTTP 500 because Google Sheets was unreachable/unavailable; this is handled with error response + logging and is covered by tests.
- Slice-level product rendering/cart behavior remains pending in T02/T03.

## Files Created/Modified

- `backend/cashier_app/routes/pos.py` — Implemented `/api/products` with JWT-cookie guard, Sheets read, active-row mapping, and cache import fallback.
- `tests/test_cashier_app_pos_route.py` — Added pytest coverage for auth protection, success mapping, and error-path logging.
- `.gsd/milestones/M006/slices/S02/S02-PLAN.md` — Marked T01 as complete (`[x]`).
- `.gsd/KNOWLEDGE.md` — Added RTK passthrough gotcha (`rtk proxy` for python/pytest/curl).
