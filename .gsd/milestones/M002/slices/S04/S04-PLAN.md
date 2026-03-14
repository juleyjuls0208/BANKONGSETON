# S04: Critical Path Unit Tests

**Goal:** ~35 unit tests covering `complete_sale`, `load_balance`, `void_transaction`, and cashier login auth — green, zero live Sheets calls, under 10 seconds.
**Demo:** `pytest tests/test_cashier_routes.py tests/test_admin_critical.py` passes with all tests green and no network I/O.

## Must-Haves

- `tests/test_cashier_routes.py` exists with ~18 tests covering `complete_sale` and `api_login`
- `tests/test_admin_critical.py` exists with ~17 tests covering `load_balance` and `void_transaction`
- Zero live Sheets calls — all gspread I/O intercepted by mocks
- `sys.modules['admin_dashboard']` registered so cashier inline imports hit the mocked module, not a fresh real import
- All tests pass in under 10 seconds
- `pytest` exit code 0

## Proof Level

- This slice proves: contract (unit-level mock assertions confirm money-moving code paths behave correctly under all key scenarios)
- Real runtime required: no (full mock)
- Human/UAT required: no

## Verification

```bash
pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
```

- Must exit 0
- Test count ≥ 35
- No `gspread` network calls (all patched — verified by mock assertion counts or absence of real HTTP)
- Wall time < 10 seconds

## Observability / Diagnostics

- Runtime signals: pytest `-v` output shows each test name and PASSED/FAILED; `--tb=short` surfaces the exact assertion and traceback on failure
- Inspection surfaces: `pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=long` for full context; `pytest -k <test_name>` to isolate a single failing test
- Failure visibility: if import guard fires (`sys.exit(1)` in `admin_dashboard.py`), pytest reports `SystemExit` — indicates env vars not set before import; if `from admin_dashboard import get_sheets_client` spawns a second unmocked import, test will raise credential error — indicates missing `sys.modules['admin_dashboard']` registration

## Integration Closure

- Upstream surfaces consumed: `backend/dashboard/admin_dashboard.py` (load_balance, void_transaction, app, startup guards), `backend/dashboard/cashier/cashier_routes.py` (api_login, complete_sale, JWT auth), `backend/offline_queue.py` (offline fallback path)
- New wiring introduced: `tests/conftest.py` extended with shared `flask_app` fixture that patches gspread at import time and registers `sys.modules['admin_dashboard']`; function-scoped `db` fixture enables per-test worksheet reconfiguration
- What remains before milestone end: S05 deployment runbook (docs/DEPLOY.md)

## Tasks

- [x] **T01: Wire test infrastructure in conftest.py** `est:45m`
  - Why: Both test files need the same module-import patch sequence; duplicating it per-module is fragile. The `sys.modules['admin_dashboard']` registration and gspread patch are the highest-risk steps — getting them right once in conftest.py is safer.
  - Files: `tests/conftest.py`
  - Do: Add module-scoped `flask_app` fixture with env var setup, gspread patch, `sys.modules['admin_dashboard']` registration, and `adm.db` replacement. Add function-scoped `db` fixture for per-test worksheet isolation. Add `_make_cashier_token` helper. Add `admin_client` and `finance_client` session fixtures.
  - Verify: `pytest tests/conftest.py --collect-only` exits 0; import of conftest succeeds without spawning real Sheets calls
  - Done when: conftest.py imports cleanly and `flask_app` fixture is discoverable by pytest without error

- [x] **T02: Implement cashier route tests (~18 tests)** `est:1h`
  - Why: `complete_sale` and `api_login` are the highest-risk cashier paths — money moves on every sale, and authentication guards the entire cashier terminal.
  - Files: `tests/test_cashier_routes.py`
  - Do: Write `TestApiLogin` (5 tests: Sheets-auth success, legacy fallback, bad creds, inactive account → 401, missing fields → 400) and `TestCompleteSale` (13 tests: success, suspended card → 403, lost card → 403, insufficient balance → 400, offline fallback → 200+offline, SMS failure nonfatal, no pending transaction → 400, card not found → 404, invalid UID format → 400, missing card UID → 400, unauthenticated → 401, card blocked status → 403, rollback path). Configure worksheet mocks per test via `db` fixture.
  - Verify: `pytest tests/test_cashier_routes.py -v --tb=short` exits 0, all ~18 tests green
  - Done when: all tests pass, no `gspread` HTTP calls, no SQLite files created unintentionally

- [x] **T03: Implement admin critical tests (~17 tests) and run full suite** `est:1h`
  - Why: `load_balance` and `void_transaction` are the only admin paths that move real money or restore balances — correctness here is the highest operational risk.
  - Files: `tests/test_admin_critical.py`
  - Do: Write `TestLoadBalance` (6 tests: success, SMS failure nonfatal, amount=0 → 400, negative amount → 400, card not found → 404, finance role can load → 200) and `TestVoidTransaction` (11 tests: success, double void rejected → 400, txn not found → 404, balance restoration correct value, load void reverses correctly, purchase void restores correctly, void requires admin role → 401/302, reason defaults to 'Voided by admin', void record appended with correct fields, invalidate_pattern called, void_id format). Run combined suite to confirm ≥35 tests, all green, under 10 seconds.
  - Verify: `pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short` exits 0; test count ≥ 35; elapsed time < 10s
  - Done when: full suite passes; R017 verified

## Files Likely Touched

- `tests/conftest.py`
- `tests/test_cashier_routes.py` (new)
- `tests/test_admin_critical.py` (new)
