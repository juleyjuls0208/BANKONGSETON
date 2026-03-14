---
estimated_steps: 5
estimated_files: 1
---

# T03: Implement admin critical tests (~17 tests) and run full suite

**Slice:** S04 — Critical Path Unit Tests
**Milestone:** M002

## Description

Write `tests/test_admin_critical.py` covering `load_balance` and `void_transaction` — the two admin paths that move real money. Then run the combined suite to confirm ≥35 tests pass, all green, in under 10 seconds. This task also validates R017.

Key mechanics:
- **`load_balance` is `@login_required` only** — finance role can call it. Use `finance_client` fixture.
- **`void_transaction` requires `@admin_only`** — finance role gets 401/302; only admin gets 200. Use `admin_client` fixture.
- **`load_balance` calls `money_sheet.find('Balance').col`** — `MagicMock` auto-chains `.find().col`, returning a MagicMock accepted by `update_cell`. No special setup needed.
- **`void_transaction` calls `get_sheets_client()`** at the top of the function — since `adm.get_sheets_client = lambda: mock_spreadsheet` is set by the `db` fixture, this resolves correctly.
- **`session.get('username', 'admin')` in void_transaction** — admin_client logs in via `/login`; the login route sets `session['admin_username']`, not `session['username']`, so `admin_user` in void records will be the default `'admin'`. Don't assert on the specific admin name in void records.
- **PHASE3_AVAILABLE gating** — `load_balance` and `void_transaction` attempt SMS/FCM if `PHASE3_AVAILABLE=True`. Mock `backend.dashboard.admin_dashboard.get_sms_notifier` to return a MagicMock to prevent Twilio network calls.

## Steps

1. **Set up module scaffold.** Import `pytest`, `os`, `sys`, `MagicMock`, `patch`. Import `flask_app`, `db`, `admin_client`, `finance_client` from conftest. Define `_make_money_account_ws(card, balance, status='Active')` helper that returns a configured MagicMock worksheet.

2. **Write `TestLoadBalance` (~6 tests).** For each: configure `db.worksheet('Money Accounts')` and `db.worksheet('Users')` and `db.worksheet('Transactions Log')` mocks; call `POST /api/load-balance` with `admin_client` or `finance_client`.
   - `test_load_balance_success` — card found, balance=500, amount=200. Assert 200, `new_balance=700`, `student_name` in response.
   - `test_load_balance_finance_role_allowed` — use `finance_client`. Assert 200 (not 403).
   - `test_load_balance_sms_failure_nonfatal` — patch `get_sms_notifier` to raise. Assert 200 (load still succeeds).
   - `test_load_balance_invalid_amount_zero` — POST `{amount: 0}`. Assert 400.
   - `test_load_balance_invalid_amount_negative` — POST `{amount: -50}`. Assert 400.
   - `test_load_balance_card_not_found` — Money Accounts returns empty list. Assert 404.

3. **Write `TestVoidTransaction` success and value correctness (~5 tests).** For each: configure Transactions Log records with a target transaction; configure Money Accounts with the card's current balance.
   - `test_void_transaction_success` — txn Purchase amount=-50, card balance=400. Assert 200, `restored_balance=450.0`, `void_id='VOID-TXN-001'`.
   - `test_void_transaction_load_reversal` — txn Load amount=100, card balance=600. Void restores to 500. Assert `restored_balance=500.0`.
   - `test_void_transaction_balance_restoration_correct_value` — Verify the math: for Purchase of 75 with current balance=425, restored should be 500. Assert exact value.
   - `test_void_transaction_void_record_appended` — assert `txn_sheet.append_row` was called once with row containing `'Void'` at the transaction type position.
   - `test_void_transaction_invalidates_cache` — patch `adm.invalidate_pattern`. Assert it's called with `'transactions'` and `'money_accounts'`.

4. **Write `TestVoidTransaction` guard cases (~6 tests).**
   - `test_void_transaction_not_found` — Transactions Log returns list without the target txn_id. Assert 404.
   - `test_void_transaction_double_void_rejected` — target row has `TransactionType='Void'`. Assert 400 with error containing `'already a void'`.
   - `test_void_transaction_requires_admin` — use `finance_client`. Assert 401 or 302 (not 200).
   - `test_void_transaction_requires_login` — unauthenticated client. Assert 401 or 302.
   - `test_void_transaction_money_card_not_found` — Transactions Log has the txn, but Money Accounts returns no matching card. Assert 404.
   - `test_void_transaction_reason_defaults` — POST `{}` (no reason). Assert 200 and void record appended (reason defaults to `'Voided by admin'`).

5. **Run combined suite and record R017 as met.** Run `pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short` and confirm: exit 0, ≥35 tests, < 10 seconds. Update R017 status.

## Must-Haves

- [ ] All ~17 tests exist and pass
- [ ] `test_void_transaction_requires_admin` uses `finance_client` and asserts non-200
- [ ] `test_void_transaction_balance_restoration_correct_value` asserts exact restored balance value
- [ ] `get_sms_notifier` is mocked in SMS-failure tests to prevent Twilio network calls
- [ ] No SQLite file creation (offline queue not triggered in admin tests)
- [ ] Combined suite: `pytest tests/test_cashier_routes.py tests/test_admin_critical.py` exits 0, ≥35 tests, < 10s

## Verification

```bash
# Admin critical tests alone
pytest tests/test_admin_critical.py -v --tb=short

# Full S04 suite — final R017 proof
pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
```

Both commands exit 0. Combined run shows ≥35 passed. Elapsed < 10 seconds.

## Observability Impact

- Signals added/changed: if `test_void_transaction_requires_admin` returns 200, `@admin_only` decorator is not working correctly — indicates session/role bug; if `test_load_balance_success` returns 503, the `get_worksheet_with_retry` mock is not returning the configured worksheet
- How a future agent inspects this: `pytest tests/test_admin_critical.py::TestVoidTransaction -v --tb=long`
- Failure state exposed: MagicMock auto-chaining means attribute errors in `.find().col` would surface as `TypeError` on `update_cell`; this would only happen if the mock is accidentally replaced with a non-Mock object

## Inputs

- `tests/conftest.py` (T01 output) — `flask_app`, `db`, `admin_client`, `finance_client` fixtures
- `tests/test_cashier_routes.py` (T02 output) — runs alongside in combined suite
- `backend/dashboard/admin_dashboard.py` — `load_balance` route (`/api/load-balance`), `void_transaction` route (`/api/admin/transactions/<txn_id>/void`), decorator chain, `invalidate_pattern` calls, `PHASE3_AVAILABLE` gating
- S04 Research: confirmed `session.get('username', 'admin')` behavior; confirmed void amount direction for Purchase vs Load types

## Expected Output

- `tests/test_admin_critical.py` — ~17 passing tests across `TestLoadBalance` and `TestVoidTransaction`
- R017 validated: combined pytest run exits 0, ≥35 tests, < 10 seconds, zero live Sheets calls
