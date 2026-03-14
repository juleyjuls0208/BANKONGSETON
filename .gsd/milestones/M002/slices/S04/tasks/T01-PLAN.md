---
estimated_steps: 5
estimated_files: 1
---

# T01: Wire test infrastructure in conftest.py

**Slice:** S04 — Critical Path Unit Tests
**Milestone:** M002

## Description

Both `test_cashier_routes.py` and `test_admin_critical.py` need a Flask test client with mocked Sheets and the critical `sys.modules['admin_dashboard']` registration. Setting this up once in `conftest.py` is safer than duplicating the import-patch sequence per module. This task adds the shared `flask_app` fixture, a per-test `db` fixture for worksheet isolation, and JWT/session helpers needed by cashier and admin tests.

The two non-obvious mechanics (documented in research):
1. **gspread must be patched before `admin_dashboard` is imported** — `db = get_sheets_client()` runs at module level; if the patch isn't active at import time, real credentials are required.
2. **`sys.modules['admin_dashboard']` must be registered** — `cashier_routes.py` does `from admin_dashboard import get_sheets_client` inline at request time (not import time). Without the short-name registration, Python loads a second unmocked copy of `admin_dashboard`, triggering the real `db = get_sheets_client()` call and crashing with a credentials error.

## Steps

1. **Set env vars + start gspread patches before import.** In the module-scoped `flask_app` fixture body, set `os.environ` for `FLASK_SECRET_KEY`, `GOOGLE_SHEETS_ID`, `WEB_CONCURRENCY=1`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FINANCE_USERNAME`, `FINANCE_PASSWORD`. Start `patch('google.oauth2.service_account.Credentials.from_service_account_file')` and `patch('gspread.authorize', return_value=MagicMock(open_by_key=...))` before the import.

2. **Import admin_dashboard with try/except (handles already-cached module).** Use the same pattern as `test_fraud_api.py`: `try: import backend.dashboard.admin_dashboard as adm; except: pass` then `import backend.dashboard.admin_dashboard as adm`. Stop patches after import. Set `adm.db = mock_spreadsheet`, `adm.get_sheets_client = lambda: mock_spreadsheet`, and critically `sys.modules['admin_dashboard'] = adm`.

3. **Yield `(adm.app, mock_spreadsheet)` and configure for testing.** Set `adm.app.config['TESTING'] = True` and `WTF_CSRF_ENABLED = False` before yield. The tuple yield lets individual tests destructure and reconfigure worksheets.

4. **Add function-scoped `db` fixture.** Creates a fresh `MagicMock()` spreadsheet each test, assigns it to `adm.db` and `adm.get_sheets_client`, and yields it. This prevents worksheet mock state from leaking between tests.

5. **Add helpers.** Add `_make_cashier_token(username, role)` module-level function (uses `jwt.encode` with default `JWT_SECRET='bangko-jwt-secret-2026'`). Add `admin_client(flask_app)` and `finance_client(flask_app)` fixtures that post to `/login` with env credentials. Add `_set_pending(client, items, total)` helper that seeds `pending_transaction` in the Flask session via `session_transaction()`.

## Must-Haves

- [ ] `flask_app` fixture is module-scoped and sets all required env vars before import
- [ ] `sys.modules['admin_dashboard'] = adm` is set inside the fixture
- [ ] gspread patches are started before import and stopped after
- [ ] `db` fixture is function-scoped and replaces `adm.db` and `adm.get_sheets_client` each test
- [ ] `_make_cashier_token` produces a valid JWT readable by cashier_routes' `@jwt_required`
- [ ] `admin_client` logs in via `/login` POST and returns an authenticated test client
- [ ] `_set_pending` correctly seeds `pending_transaction` in Flask session

## Verification

```bash
# Collect only — confirms fixtures are importable and discoverable
pytest tests/conftest.py tests/test_fraud_api.py --collect-only -q 2>&1 | head -20
# Confirm no SystemExit or import errors from admin_dashboard startup guards
python -c "
import os, sys
sys.path.insert(0, '.')
os.environ['FLASK_SECRET_KEY'] = 'test-s04'
os.environ['GOOGLE_SHEETS_ID'] = 'fake'
os.environ['WEB_CONCURRENCY'] = '1'
print('env ok')
"
```

No `SystemExit` or `ImportError` should appear during fixture collection.

## Inputs

- `tests/conftest.py` — existing file with `mock_google_sheets`, `sample_*` fixtures; add new fixtures without removing existing ones
- `tests/test_fraud_api.py` lines 225–291 — canonical `flask_app` fixture pattern to follow
- `backend/dashboard/cashier/cashier_routes.py` lines 37–44 — `JWT_SECRET` default value (`bangko-jwt-secret-2026`), `JWT_ALGORITHM = 'HS256'`
- `backend/dashboard/admin_dashboard.py` lines 59–78 — startup guards that call `sys.exit(1)` on missing key or `WEB_CONCURRENCY > 1`

## Expected Output

- `tests/conftest.py` — extended with `flask_app` (module-scoped), `db` (function-scoped), `admin_client`, `finance_client` fixtures, plus `_make_cashier_token` and `_set_pending` helpers

## Observability Impact

**Signals that change after this task:**
- `pytest tests/test_cashier_routes.py tests/test_admin_critical.py --collect-only` transitions from `ImportError` / `SystemExit` to clean collection — the primary readiness signal for downstream test tasks.
- `pytest tests/conftest.py tests/test_fraud_api.py --collect-only -q` must still pass without regressions (existing fraud tests continue collecting).

**How a future agent inspects this task:**
- Run `pytest tests/ --collect-only -q 2>&1 | grep -E "(flask_app|admin_client|finance_client|db)"` to verify fixtures are discovered.
- Run `pytest tests/conftest.py --collect-only -q 2>&1` — zero failures means the fixtures are syntactically valid and importable.
- Check `sys.modules.get('admin_dashboard')` inside a live test to confirm the short-name registration is active.

**Failure state visibility:**
- `SystemExit` during collection → `FLASK_SECRET_KEY` or `WEB_CONCURRENCY` env vars not set before import; check fixture env-var block.
- `ImportError: cannot import name 'get_sheets_client' from 'admin_dashboard'` → `sys.modules['admin_dashboard'] = adm` line missing or not reached.
- `AuthenticationError` / gspread credential crash → patches not started before import; check patch start/stop ordering.
- JWT decode error in cashier tests → `_make_cashier_token` uses wrong secret or algorithm; compare with `JWT_SECRET='bangko-jwt-secret-2026'` / `HS256` in cashier_routes.py.
