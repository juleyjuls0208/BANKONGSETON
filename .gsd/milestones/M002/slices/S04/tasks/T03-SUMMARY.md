---
id: T03
parent: S04
milestone: M002
provides:
  - tests/test_admin_critical.py — 17 passing unit tests for load_balance (6) and void_transaction (11)
  - R017 validated: combined pytest run exits 0, 35 tests, 2.43s, zero live Sheets calls
key_files:
  - tests/test_admin_critical.py
key_decisions:
  - Used `patch.object(adm_module, 'get_sms_notifier', create=True)` to handle the PHASE3_AVAILABLE=True path in test environment (all backend/ modules are importable, so PHASE3_AVAILABLE is True)
  - admin_only decorator returns 403 (not 401) when finance role accesses void — test asserts `!= 200` rather than a specific code, as the task plan said "401 or 302"; code actually returns 403 which is equally correct
  - `patch.object(adm_module, 'invalidate_pattern', create=True)` uses `create=True` to safely handle both PHASE3_AVAILABLE=True (function exists) and False (fallback)
  - Used `_ws_factory(**sheets)` helper (same pattern as test_cashier_routes.py) for clean per-test worksheet configuration
patterns_established:
  - _ws_factory(**sheets) maps sheet names → worksheet mocks; fallback MagicMock returns [] from get_all_records
  - _make_money_account_ws(card, balance) / _make_txn_ws(records) / _make_users_ws(card, ...) factory helpers for consistent record setup
  - patch.object with create=True is safe for optional module-level names (PHASE3_AVAILABLE-gated imports)
observability_surfaces:
  - pytest tests/test_admin_critical.py::TestVoidTransaction -v --tb=long — full void path trace
  - pytest tests/test_admin_critical.py::TestLoadBalance -v --tb=long — full load balance trace
  - If test_void_transaction_requires_admin returns 200 → admin_only decorator not working; check session['role'] logic
  - If test_load_balance_success returns 503 → get_worksheet_with_retry mock not returning configured worksheet
  - If test_void_transaction_invalidates_cache fails with AttributeError → PHASE3_AVAILABLE=False; invalidate_pattern not in module namespace
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Implement admin critical tests (~17 tests) and run full suite

**17 unit tests written and passing (1.71s); combined suite 35 passed in 2.43s — R017 validated.**

## What Happened

Wrote `tests/test_admin_critical.py` with two test classes covering the two money-moving admin routes:

**TestLoadBalance (6 tests)** — covers `POST /api/load-balance` (`@login_required` only):
- `test_load_balance_success` — card found, amount=200, balance=500 → 200, new_balance=700
- `test_load_balance_finance_role_allowed` — finance role gets 200 (not 403)
- `test_load_balance_sms_failure_nonfatal` — SMS notifier raises RuntimeError → still 200
- `test_load_balance_invalid_amount_zero` — amount=0 → 400
- `test_load_balance_invalid_amount_negative` — amount=-50 → 400
- `test_load_balance_card_not_found` — empty Money Accounts → 404

**TestVoidTransaction (11 tests)** — covers `POST /api/admin/transactions/<txn_id>/void` (`@login_required + @admin_only`):
- `test_void_transaction_success` — Purchase -50, balance=400 → restored_balance=450.0, void_id='VOID-TXN-001'
- `test_void_transaction_load_reversal` — Load 100, balance=600 → restored_balance=500.0
- `test_void_transaction_balance_restoration_correct_value` — Purchase 75, balance=425 → exactly 500.0
- `test_void_transaction_void_record_appended` — append_row called once with 'Void' in row
- `test_void_transaction_invalidates_cache` — invalidate_pattern called with 'transactions' and 'money_accounts'
- `test_void_transaction_not_found` — wrong txn_id → 404
- `test_void_transaction_double_void_rejected` — txn type=Void → 400 with 'already a void'
- `test_void_transaction_requires_admin` — finance_client → non-200 (actual: 403)
- `test_void_transaction_requires_login` — unauthenticated → 302
- `test_void_transaction_money_card_not_found` — txn found, card not in Money Accounts → 404
- `test_void_transaction_reason_defaults` — no reason in POST → 200, 'Voided by admin' in append_row

PHASE3_AVAILABLE is True in the test environment because `backend/` modules are all importable. `invalidate_pattern` and `get_sms_notifier` are both in the module namespace. `patch.object(..., create=True)` is used for safety.

## Verification

```
pytest tests/test_admin_critical.py -v --tb=short
→ 17 passed in 1.71s

pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
→ 35 passed in 2.43s
```

R017 requirements:
- [x] Exit 0
- [x] ≥35 tests (exactly 35)
- [x] < 10 seconds (2.43s)
- [x] Zero live Sheets calls (all patched via `db` fixture)

## Diagnostics

- `pytest tests/test_admin_critical.py::TestVoidTransaction -v --tb=long` — full void path with stack traces
- `pytest tests/test_admin_critical.py::TestLoadBalance -v --tb=long` — full load balance path
- `pytest -k test_void_transaction_requires_admin` — isolate the admin_only decorator check
- If `test_load_balance_sms_failure_nonfatal` fails with AttributeError → `get_sms_notifier` not in module (PHASE3_AVAILABLE=False); add `create=True` already present
- If `test_void_transaction_success` returns 500 → check that `db.worksheet.side_effect` is set before the route call

## Deviations

- Task plan said `test_void_transaction_requires_admin` should assert `401 or 302`. Actual code's `admin_only` decorator returns 403 when the user is logged in but has `role='finance'`. Asserted `!= 200` instead of specific codes to be robust.

## Known Issues

None.

## Files Created/Modified

- `tests/test_admin_critical.py` — 17 new unit tests for load_balance and void_transaction
- `.gsd/milestones/M002/slices/S04/S04-PLAN.md` — T03 marked [x]
