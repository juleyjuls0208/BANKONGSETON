# S04: Critical Path Unit Tests — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: All verification is automated via pytest with mocked dependencies. No live Sheets access, no running server, no human interaction required. The test suite itself is the UAT artifact — every scenario is encoded as a named test with an assertion.

## Preconditions

1. Python 3.x virtualenv with `pip install -r backend/dashboard/requirements.txt` and `pip install -r requirements-test.txt` completed (S01 guarantees this)
2. Working directory is project root (`/c/Users/admin/Desktop/projects/BANKONGSETON`)
3. No env vars required — the `flask_app` fixture sets all required vars internally
4. No network access required — all Sheets I/O is intercepted by mocks
5. No SQLite files required — offline_queue is patched in the offline fallback test

## Smoke Test

```bash
python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
```

**Expected:** `35 passed` in under 10 seconds, exit code 0. If this passes, all critical paths are green.

## Test Cases

### 1. Full suite passes green

```bash
python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
```

1. Run the command from the project root
2. **Expected:** Output ends with `35 passed in X.XXs` where X.XX < 10
3. **Expected:** Exit code 0 (`echo $?` → `0`)
4. **Expected:** No `FAILED`, `ERROR`, or `WARNING: PytestUnraisableExceptionWarning` lines in the output

---

### 2. Cashier login — Sheets-auth success

Test: `TestApiLogin::test_login_success_via_sheets`

1. Cashier Accounts worksheet mock returns a record with `Username=cashier1`, `Password=<bcrypt_hash>`, `Status=Active`
2. POST `/cashier/api/login` with `{"username": "cashier1", "password": "testpass"}`
3. **Expected:** HTTP 200
4. **Expected:** Response JSON contains `jwt_token` key

---

### 3. Cashier login — legacy fallback

Test: `TestApiLogin::test_login_legacy_fallback`

1. Cashier Accounts worksheet mock raises on `get_all_records` (simulates sheet unavailable)
2. POST `/cashier/api/login` with `{"username": "cashier", "password": "cashier123"}`
3. **Expected:** HTTP 200 (falls through to hardcoded legacy credentials)
4. **Expected:** Response JSON contains `jwt_token` key

---

### 4. Cashier login — bad credentials rejected

Test: `TestApiLogin::test_login_bad_credentials`

1. Cashier Accounts worksheet mock returns a record with `Username=cashier1`, `Password=<bcrypt_hash_for_testpass>`, `Status=Active`
2. POST `/cashier/api/login` with `{"username": "cashier1", "password": "wrongpassword"}`
3. **Expected:** HTTP 401

---

### 5. Cashier login — inactive account rejected

Test: `TestApiLogin::test_login_inactive_account`

1. Cashier Accounts worksheet mock returns a record with `Username=cashier1`, `Status=Inactive`
2. POST `/cashier/api/login` with correct credentials
3. **Expected:** HTTP 401 (inactive accounts are refused)

---

### 6. Complete sale — success, balance deducted correctly

Test: `TestCompleteSale::test_complete_sale_success`

1. Money Accounts mock: card `AABB1122` with balance=500.0, Status=active
2. Session seeded with pending transaction: items=[{name:"Lunch", price:50}], total=50
3. Valid JWT cashier token set in cookie
4. POST `/cashier/api/complete-sale` with `{"card_uid": "AABB1122"}`
5. **Expected:** HTTP 200
6. **Expected:** Response JSON `new_balance == 450.0`
7. **Expected:** `append_row` called once (transaction logged to Sheets)
8. **Expected:** Money Accounts `update_cell` called (balance updated)

---

### 7. Complete sale — suspended card rejected

Test: `TestCompleteSale::test_complete_sale_suspended_card`

1. Money Accounts mock: card `AABB1122` with Status=suspended
2. Session seeded with pending transaction, valid JWT
3. POST `/cashier/api/complete-sale` with `{"card_uid": "AABB1122"}`
4. **Expected:** HTTP 403

---

### 8. Complete sale — insufficient balance rejected

Test: `TestCompleteSale::test_complete_sale_insufficient_balance`

1. Money Accounts mock: card `AABB1122` with balance=30.0, Status=active
2. Session seeded with pending transaction total=50
3. POST `/cashier/api/complete-sale` with valid JWT and card
4. **Expected:** HTTP 400
5. **Expected:** Response JSON error message contains "Insufficient"

---

### 9. Complete sale — offline fallback on Sheets failure

Test: `TestCompleteSale::test_complete_sale_offline_fallback`

1. Money Accounts mock: card with sufficient balance, Status=active
2. `update_cell` raises `gspread.exceptions.APIError` on all 3 retry attempts
3. `time.sleep` is patched (no real delay)
4. `offline_queue.get_offline_queue` returns a mock queue
5. POST `/cashier/api/complete-sale` with valid JWT, pending seeded, card UID
6. **Expected:** HTTP 200
7. **Expected:** Response JSON `offline == True`
8. **Expected:** `mock_queue.enqueue` called exactly once (transaction enqueued, not dropped)

---

### 10. Complete sale — SMS failure is non-fatal

Test: `TestCompleteSale::test_complete_sale_sms_failure_nonfatal`

1. Money Accounts mock: card with sufficient balance, Status=active, Sheets writes succeed
2. SMS notifier mock raises `RuntimeError`
3. POST `/cashier/api/complete-sale` with valid setup
4. **Expected:** HTTP 200 (SMS failure does not abort the sale)

---

### 11. Load balance — success, balance increased correctly

Test: `TestLoadBalance::test_load_balance_success`

1. Admin client logged in (session with role=admin)
2. Money Accounts mock: card with balance=500.0
3. POST `/api/load-balance` with `{"card_uid": "...", "amount": 200}`
4. **Expected:** HTTP 200
5. **Expected:** Response JSON `new_balance == 700.0`
6. **Expected:** `update_cell` called (Sheets write)

---

### 12. Load balance — finance role allowed

Test: `TestLoadBalance::test_load_balance_finance_role_allowed`

1. Finance client logged in (session with role=finance)
2. POST `/api/load-balance` with valid card and amount
3. **Expected:** HTTP 200 (load_balance is `@login_required` only, not `@admin_only`)

---

### 13. Load balance — zero amount rejected

Test: `TestLoadBalance::test_load_balance_invalid_amount_zero`

1. Admin client logged in
2. POST `/api/load-balance` with `{"card_uid": "...", "amount": 0}`
3. **Expected:** HTTP 400

---

### 14. Load balance — negative amount rejected

Test: `TestLoadBalance::test_load_balance_invalid_amount_negative`

1. Admin client logged in
2. POST `/api/load-balance` with `{"card_uid": "...", "amount": -50}`
3. **Expected:** HTTP 400

---

### 15. Void transaction — success, balance restored

Test: `TestVoidTransaction::test_void_transaction_success`

1. Admin client logged in
2. Transactions Log mock: txn `TXN-001` type=Purchase, amount=50, CardUID=AABB1122
3. Money Accounts mock: card AABB1122 balance=400.0 (post-purchase state)
4. POST `/api/admin/transactions/TXN-001/void` with `{"reason": "Customer request"}`
5. **Expected:** HTTP 200
6. **Expected:** Response JSON contains void_id starting with "VOID-"
7. **Expected:** Restored balance = 400.0 + 50 = 450.0 in response

---

### 16. Void transaction — double void rejected

Test: `TestVoidTransaction::test_void_transaction_double_void_rejected`

1. Admin client logged in
2. Transactions Log mock: txn `TXN-001` type=Void (already voided)
3. POST `/api/admin/transactions/TXN-001/void`
4. **Expected:** HTTP 400
5. **Expected:** Response JSON error message contains "already a void" or similar

---

### 17. Void transaction — load reversal correct

Test: `TestVoidTransaction::test_void_transaction_load_reversal`

1. Admin client logged in
2. Transactions Log mock: txn `TXN-002` type=Load, amount=100, CardUID=AABB1122
3. Money Accounts mock: card balance=600.0 (post-load state)
4. POST `/api/admin/transactions/TXN-002/void`
5. **Expected:** HTTP 200
6. **Expected:** Restored balance = 600.0 - 100 = 500.0 (load reversal subtracts, not adds)

---

### 18. Void transaction — requires admin role

Test: `TestVoidTransaction::test_void_transaction_requires_admin`

1. Finance client logged in (role=finance)
2. POST `/api/admin/transactions/TXN-001/void`
3. **Expected:** Response status != 200 (actual: 403 — finance role is not admin)

---

### 19. Void transaction — cache invalidated

Test: `TestVoidTransaction::test_void_transaction_invalidates_cache`

1. Admin client logged in
2. `invalidate_pattern` patched via `patch.object`
3. POST `/api/admin/transactions/TXN-001/void` succeeds
4. **Expected:** `invalidate_pattern` called with 'transactions'
5. **Expected:** `invalidate_pattern` called with 'money_accounts'

---

### 20. Void transaction — reason defaults when omitted

Test: `TestVoidTransaction::test_void_transaction_reason_defaults`

1. Admin client logged in
2. POST `/api/admin/transactions/TXN-001/void` with empty body (no reason field)
3. **Expected:** HTTP 200
4. **Expected:** `append_row` called with a row containing 'Voided by admin'

---

## Edge Cases

### Complete sale — JWT required (unauthenticated redirects)

Test: `TestCompleteSale::test_complete_sale_requires_jwt`

1. No JWT cookie set
2. POST `/cashier/api/complete-sale`
3. **Expected:** HTTP 302 (redirect to login, not 401 — `jwt_required` redirects rather than returning 401)

---

### Complete sale — invalid UID format rejected

Test: `TestCompleteSale::test_complete_sale_invalid_uid_format`

1. Valid JWT, pending seeded
2. POST `/cashier/api/complete-sale` with `{"card_uid": "ZZZZZZZZ"}` (non-hex characters)
3. **Expected:** HTTP 400 (UID regex rejects non-hex)

---

### Complete sale — lost card rejected

Test: `TestCompleteSale::test_complete_sale_lost_card`

1. Money Accounts mock: card Status=lost
2. Valid JWT, pending seeded
3. POST `/cashier/api/complete-sale`
4. **Expected:** HTTP 403

---

### Complete sale — blocked card rejected

Test: `TestCompleteSale::test_complete_sale_blocked_card`

1. Money Accounts mock: card Status=blocked
2. Valid JWT, pending seeded
3. POST `/cashier/api/complete-sale`
4. **Expected:** HTTP 403

---

### Load balance — card not found

Test: `TestLoadBalance::test_load_balance_card_not_found`

1. Admin logged in; Money Accounts mock returns empty list
2. POST `/api/load-balance` with `{"card_uid": "UNKNOWN", "amount": 100}`
3. **Expected:** HTTP 404

---

### Void transaction — transaction not found

Test: `TestVoidTransaction::test_void_transaction_not_found`

1. Admin logged in; Transactions Log mock returns no matching txn_id
2. POST `/api/admin/transactions/NONEXISTENT/void`
3. **Expected:** HTTP 404

---

### Void transaction — card not found after txn found

Test: `TestVoidTransaction::test_void_transaction_money_card_not_found`

1. Admin logged in
2. Transactions Log mock returns matching txn record (CardUID=AABB1122)
3. Money Accounts mock returns empty list (card doesn't exist)
4. POST `/api/admin/transactions/TXN-001/void`
5. **Expected:** HTTP 404

---

## Failure Signals

- `FAILED` in pytest output with `AssertionError` → assertion mismatch; check the `--tb=long` output for the failing route response body
- `ERROR` in pytest output with `SystemExit` → env vars not set before `admin_dashboard` import; check flask_app fixture
- `ERROR` in pytest output with `ImportError` → `backend/dashboard/` not in sys.path; check conftest sys.path insert
- `404` on cashier routes → CASHIER_AVAILABLE=False; cashier blueprint not registered; sys.path issue
- `enqueue.assert_called_once()` fails in offline fallback test → `transaction_row` not pre-built before retry loop (regression of D023 bugfix)
- `InvalidSignatureError` → JWT_SECRET mismatch between `_make_cashier_token` and `cashier_routes.py`
- Test count < 35 → a test file failed to import; check collection with `--collect-only`

## Requirements Proved By This UAT

- R017 — Critical Path Unit Tests: 35 tests passing, exit 0, 2.40s, zero live Sheets calls. All money-moving paths (complete_sale, load_balance, void_transaction) and cashier auth paths (api_login) are covered with mock assertions that confirm correct behavior.

## Not Proven By This UAT

- Live Sheets connectivity — all Sheets I/O is mocked; actual gspread round-trips to Google APIs are not exercised
- End-to-end cashier terminal flow — no browser/UI interaction; route logic only
- Offline queue persistence — SQLite file creation and sync are patched; only the enqueue() call is verified
- FraudDetector integration paths — not covered by this suite
- Concurrent access behavior — single-threaded test execution; race conditions not testable this way
- PythonAnywhere deployment environment — these tests run locally; deployment-specific env differences are not validated

## Notes for Tester

- The entire suite is hermetic — no credentials, no network, no filesystem side effects. Run it anywhere Python is available.
- `pytest -k test_complete_sale_offline_fallback -v --tb=long` is the best diagnostic command if the offline path regresses — it shows the full retry loop trace.
- `pytest --collect-only -q` should show exactly 35 items. If fewer, a test file failed to import.
- The `db` fixture is function-scoped — each test gets a fresh worksheet mock. Cross-test state leaks are not possible through the db fixture.
- `test_login_inactive_account` asserts 401 (not 403) — the actual route code returns 401 for inactive accounts; this is intentional and matches code, not the original spec.
- `test_complete_sale_requires_jwt` asserts 302 (not 401) — `jwt_required` redirects to the login page rather than returning 401; this is intentional and matches code behavior.
