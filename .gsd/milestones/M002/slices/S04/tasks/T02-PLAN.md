---
estimated_steps: 5
estimated_files: 1
---

# T02: Implement cashier route tests (~18 tests)

**Slice:** S04 — Critical Path Unit Tests
**Milestone:** M002

## Description

Write `tests/test_cashier_routes.py` covering the two highest-risk cashier paths: `api_login` (JWT auth gate for all cashier operations) and `complete_sale` (the money-moving core of every sale). Each test configures its own worksheet mocks via the `db` fixture from conftest.py, sets up JWT cookies where needed, and seeds `pending_transaction` via `_set_pending` before calling `complete_sale`.

Key mechanics to handle correctly:
- **JWT cookie**: `complete_sale` and all cashier routes require `@jwt_required`. Use `_make_cashier_token()` + `client.set_cookie('jwt_token', token)` — no need to go through login.
- **Inline import interception**: `complete_sale` does `from admin_dashboard import get_sheets_client` at request time. With `sys.modules['admin_dashboard'] = adm` set by the `flask_app` fixture, this resolves to the mocked module automatically.
- **Offline fallback**: raise `gspread.exceptions.APIError(MagicMock(status_code=429, headers={}))` from `money_sheet.update_cell` on the first retry to trigger the offline queue path. Mock `get_offline_queue` to prevent SQLite file creation.
- **Status code for inactive cashier account**: code returns **401** (not 403) — match actual code, not roadmap spec.

## Steps

1. **Set up module scaffold.** Import `pytest`, `os`, `sys`, `json`, `jwt` from `PyJWT`, `MagicMock`, `patch`. Import `_make_cashier_token`, `_set_pending`, `flask_app`, `db`, `admin_client` from conftest (via pytest fixture discovery). Define `CASHIER_TOKEN_FIXTURE` helper.

2. **Write `TestApiLogin` (~5 tests).** For each test: configure `db.worksheet('Cashier Accounts').get_all_records()` to return a specific list. Call `POST /cashier/api/login` with JSON body.
   - `test_login_success_via_sheets` — Cashier Accounts has `{Username: 'testcashier', PasswordHash: bcrypt_hash, Status: 'Active'}`. Assert 200 and `jwt_token` cookie set.
   - `test_login_legacy_fallback` — worksheet raises `Exception` (no sheet). Call with `username=cashier, password=cashier123`. Assert 200.
   - `test_login_bad_credentials` — Cashier Accounts row with wrong hash. Assert 401.
   - `test_login_inactive_account` — `Status: 'Inactive'`. Assert **401** (not 403).
   - `test_login_missing_fields` — POST empty JSON. Assert 401 or 400.

3. **Write `TestCompleteSale` — happy path and auth (~4 tests).** Set JWT cookie on client before requests.
   - `test_complete_sale_success` — Active card, balance=500, total=50. Mock Money Accounts (status=active, balance=500), mock Transactions Log append. Seed `pending_transaction`. Assert 200, `new_balance=450`.
   - `test_complete_sale_requires_jwt` — no cookie set. Assert 401.
   - `test_complete_sale_no_pending_transaction` — valid JWT, no pending seeded. Assert 400.
   - `test_complete_sale_missing_card_uid` — valid JWT, pending seeded, POST `{}`. Assert 400.

4. **Write `TestCompleteSale` — card status and balance guards (~5 tests).**
   - `test_complete_sale_card_not_found` — Money Accounts returns empty list. Assert 404.
   - `test_complete_sale_invalid_uid_format` — POST `card_uid='ZZZZZZZZ'` (not hex). Assert 400.
   - `test_complete_sale_suspended_card` — card `Status='suspended'`. Assert 403.
   - `test_complete_sale_lost_card` — card `Status='lost'`. Assert 403.
   - `test_complete_sale_insufficient_balance` — balance=30, total=50. Assert 400 with `error` containing `'Insufficient'`.

5. **Write `TestCompleteSale` — resilience paths (~4 tests).**
   - `test_complete_sale_offline_fallback` — `money_sheet.update_cell` raises `gspread.exceptions.APIError(MagicMock(status_code=429, headers={}))` on all 3 retries. Mock `offline_queue.get_offline_queue`. Assert 200, `json['offline'] is True`. Assert `enqueue` was called.
   - `test_complete_sale_sms_failure_nonfatal` — Money Accounts success path; patch `notifications.get_sms_notifier` to raise `Exception`. Assert 200 (sale still succeeds).
   - `test_complete_sale_blocked_card` — card `Status='blocked'`. Assert 403.
   - `test_complete_sale_email_failure_nonfatal` — email service raises; assert 200 (non-fatal).

## Must-Haves

- [ ] All ~18 tests exist and pass
- [ ] No real gspread HTTP calls (all worksheet mocks return configured data)
- [ ] `test_login_inactive_account` asserts 401 (not 403)
- [ ] `test_complete_sale_offline_fallback` mocks `get_offline_queue` to prevent SQLite file creation
- [ ] `test_complete_sale_success` asserts `new_balance == 450.0` (or correct arithmetic)
- [ ] JWT cookie tests use `_make_cashier_token()` + `client.set_cookie('jwt_token', token)`
- [ ] Pending transaction seeded via `_set_pending(client, items, total)` before complete_sale calls

## Verification

```bash
pytest tests/test_cashier_routes.py -v --tb=short
```

Exit 0, all ~18 tests green, elapsed < 5 seconds.

## Observability Impact

- Signals added/changed: test failures in `test_complete_sale_offline_fallback` indicate offline queue mock not intercepting SQLite creation; `SystemExit` in output indicates `sys.modules['admin_dashboard']` not registered (second import triggered startup guard)
- How a future agent inspects this: `pytest tests/test_cashier_routes.py::TestCompleteSale::test_complete_sale_offline_fallback -v --tb=long`
- Failure state exposed: if `enqueue` mock isn't called in offline test, real SQLite fallback occurred

## Inputs

- `tests/conftest.py` (T01 output) — `flask_app`, `db`, `_make_cashier_token`, `_set_pending`, `admin_client` fixtures/helpers
- `backend/dashboard/cashier/cashier_routes.py` — route URLs (`/cashier/api/login`, `/cashier/api/complete-sale`), UID_PATTERN, card status checks, offline fallback logic, inline import pattern
- `backend/offline_queue.py` — `get_offline_queue()` factory, `enqueue(op, sheet, row)` signature

## Expected Output

- `tests/test_cashier_routes.py` — ~18 passing tests across `TestApiLogin` and `TestCompleteSale`
