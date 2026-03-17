---
id: T02
parent: S04
milestone: M002
provides:
  - tests/test_cashier_routes.py — 18 passing unit tests for api_login (5) and complete_sale (13)
  - conftest.py updated with backend/dashboard sys.path fix so cashier blueprint registers correctly
  - cashier_routes.py bugfix: transaction_row pre-built before retry loop (prevents UnboundLocalError in offline fallback)
key_files:
  - tests/test_cashier_routes.py
  - tests/conftest.py
  - backend/dashboard/cashier/cashier_routes.py
key_decisions:
  - Added backend/dashboard/ to sys.path in conftest.py flask_app fixture before admin_dashboard import (D022)
  - Moved transaction_row construction before retry loop in complete_sale to fix offline fallback UnboundLocalError (D023)
  - Used patch.dict(sys.modules) for email_service and notifications inline imports instead of patch() (D024)
  - jwt_required missing-token path returns 302 (redirect to login), not 401 — test asserts actual code behavior
patterns_established:
  - _ws_factory(**sheets) helper returns a side_effect function mapping sheet name → mock for clean per-test worksheet config
  - gspread.exceptions.APIError mock requires response.json() returning {"error": {"code": N, "message": ..., "status": ...}}
  - Inline sys.path.insert + from X import Y imports intercepted via patch.dict('sys.modules', {}) not patch('X.Y')
  - time.sleep patched globally (patch('time.sleep')) to skip exponential back-off in offline fallback test
observability_surfaces:
  - pytest tests/test_cashier_routes.py::TestCompleteSale::test_complete_sale_offline_fallback -v --tb=long — diagnoses offline queue path
  - mock_queue.enqueue.assert_called_once() — verifies offline fallback actually called enqueue (not just returned offline=True after a silent failure)
  - event=offline_queue_failed in logs — indicates transaction_row was undefined (pre-bugfix signature)
duration: 45m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Implement cashier route tests (~18 tests)

**18 unit tests written and passing (2.42s) across TestApiLogin (5) and TestCompleteSale (13) — plus a production bug fix in `complete_sale` exposed by the offline fallback test.**

## What Happened

### Step 1 — Source review
Read `cashier_routes.py` in full to map exact route URLs, `jwt_required` behavior (missing token → 302 redirect, not 401), `UID_PATTERN`, card status checks, retry loop structure, and offline fallback code path. Also read `offline_queue.py` for the `get_offline_queue()` / `enqueue()` signature.

### Step 2 — conftest.py gap discovered and fixed
The `flask_app` fixture imported `admin_dashboard` without `backend/dashboard/` in sys.path. `admin_dashboard.py` imports the cashier blueprint at module level via `from cashier.cashier_routes import cashier_bp`; without the path, `CASHIER_AVAILABLE = False` and the blueprint is never registered. All cashier route tests returned 404. Fixed by inserting `backend/dashboard/` into sys.path in the flask_app fixture before the import.

### Step 3 — TestApiLogin (5 tests)
- `test_login_success_via_sheets`: bcrypt hash in Cashier Accounts → 200 + jwt_token cookie
- `test_login_legacy_fallback`: get_all_records raises → falls through to username=cashier / password=cashier123 → 200
- `test_login_bad_credentials`: wrong bcrypt hash → 401
- `test_login_inactive_account`: Status=Inactive → 401 (actual code, not 403 as spec claimed)
- `test_login_missing_fields`: empty JSON → 401

### Step 4 — TestCompleteSale happy path and auth (4 tests)
- `test_complete_sale_success`: balance=500, total=50 → 200, new_balance=450.0, append_row called once
- `test_complete_sale_requires_jwt`: no cookie → 302 (jwt_required redirects to login, not 401)
- `test_complete_sale_no_pending_transaction`: valid JWT, no pending seeded, valid UID → 400
- `test_complete_sale_missing_card_uid`: valid JWT, pending seeded, POST {} → 400

### Step 5 — TestCompleteSale card status and balance guards (5 tests)
- `test_complete_sale_card_not_found`: empty Money Accounts → 404
- `test_complete_sale_invalid_uid_format`: card_uid='ZZZZZZZZ' (non-hex) → 400
- `test_complete_sale_suspended_card`: Status=suspended → 403
- `test_complete_sale_lost_card`: Status=lost → 403
- `test_complete_sale_insufficient_balance`: balance=30, total=50 → 400 with 'Insufficient' in error

### Step 6 — TestCompleteSale resilience paths (4 tests) + bugfix

**Production bug discovered**: `transaction_row` was built inside the retry loop after `update_cell`. When `update_cell` raises on all 3 attempts, `transaction_row` is never assigned, causing `UnboundLocalError` in the offline fallback enqueue call. The enqueue call was caught by an inner try/except, logging `event=offline_queue_failed`, and the route still returned 200 with `offline=True` — but the transaction was silently lost.

**Fix**: moved `transaction_row` construction before the retry loop (values are all available before the loop: `timestamp`, `normalized_card`, `total`, `new_balance`, `items`).

- `test_complete_sale_offline_fallback`: update_cell raises APIError on all 3 attempts; time.sleep patched; offline_queue.get_offline_queue patched to mock; asserts 200 + offline=True + enqueue called once
- `test_complete_sale_sms_failure_nonfatal`: SMS notifier raises; asserts 200 (non-fatal path)
- `test_complete_sale_blocked_card`: Status=blocked → 403
- `test_complete_sale_email_failure_nonfatal`: EmailService raises; asserts 200 (non-fatal path)

**email/notifications patching**: Both modules are imported via inline `sys.path.insert() + from X import Y` in cashier_routes.py. `patch('email_service.X')` fails because the module isn't importable from test context. Used `patch.dict('sys.modules', {'email_service': fake_mod})` which intercepts before the path search.

**gspread.exceptions.APIError**: constructor calls `response.json()["error"]["code"]`; MagicMock response must have `json.return_value = {"error": {"code": 429, "message": ..., "status": ...}}`.

## Verification

```
pytest tests/test_cashier_routes.py -v --tb=short
# → 18 passed in 2.42s (all green, < 5s target)
```

All must-haves confirmed:
- [x] All 18 tests pass
- [x] No real gspread HTTP calls (all worksheet mocks return configured data)
- [x] test_login_inactive_account asserts 401
- [x] test_complete_sale_offline_fallback mocks get_offline_queue (no SQLite file)
- [x] test_complete_sale_success asserts new_balance == 450.0
- [x] JWT cookie tests use _make_cashier_token() + client.set_cookie('jwt_token', token)
- [x] Pending transaction seeded via _set_pending() before complete_sale calls

Slice-level check partial (test_admin_critical.py is T03 — expected):
```
pytest tests/test_cashier_routes.py tests/test_admin_critical.py → ERROR: test_admin_critical.py not found
```

## Diagnostics

- `pytest tests/test_cashier_routes.py::TestCompleteSale::test_complete_sale_offline_fallback -v --tb=long` — full offline path trace
- If `mock_queue.enqueue.assert_called_once()` fails after test change → check that transaction_row is still built before the retry loop
- `event=offline_queue_failed` in captured logs → UnboundLocalError or other exception from enqueue (pre-fix signature)
- `SystemExit` during collection → env vars not set before admin_dashboard import
- 404 on all cashier routes → `backend/dashboard/` not in sys.path when flask_app fixture runs

## Deviations

1. **conftest.py modified** — plan expected no conftest changes for T02, but the cashier blueprint registration required adding `backend/dashboard/` to sys.path in the flask_app fixture. Minimal change, fully backward-compatible.
2. **cashier_routes.py modified** — production bugfix (transaction_row moved before retry loop). Test exposed a real UnboundLocalError in the offline fallback that would silently drop transactions in production.
3. **test_complete_sale_requires_jwt asserts 302 not 401** — plan said 401, but `jwt_required` decorator actually returns `redirect(url_for('cashier.login'))` (302). Test matches actual code per task plan guidance ("match actual code, not roadmap spec").

## Known Issues

None. All 18 tests pass cleanly.

## Files Created/Modified

- `tests/test_cashier_routes.py` — new file, 18 tests across TestApiLogin and TestCompleteSale
- `tests/conftest.py` — added `backend/dashboard/` sys.path insert in flask_app fixture (Step 2b)
- `backend/dashboard/cashier/cashier_routes.py` — moved transaction_row construction before retry loop (offline fallback bugfix)
- `.gsd/DECISIONS.md` — appended D022, D023, D024
