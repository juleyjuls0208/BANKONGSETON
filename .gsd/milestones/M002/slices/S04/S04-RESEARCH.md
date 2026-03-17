# S04: Critical Path Unit Tests — Research

**Date:** 2026-03-15

## Summary

S04 requires ~35 unit tests across two new test files (`tests/test_cashier_routes.py` and `tests/test_admin_critical.py`) covering `complete_sale`, `load_balance`, `void_transaction`, and cashier login auth. The primary risks are **not** the business logic itself — it's the module import mechanics. Both `admin_dashboard.py` and `cashier_routes.py` have patterns that make naïve mocking fail silently.

The canonical pattern for handling the module-level startup hazards already exists in `tests/test_fraud_api.py`. S04 follows the same fixture skeleton but adds one critical extra step: registering `sys.modules['admin_dashboard'] = adm` after import so that the **inline `from admin_dashboard import get_sheets_client` calls inside `complete_sale()` and `api_login()`** hit the mocked module rather than spawning a fresh real import.

For `load_balance` and `void_transaction`, the admin_dashboard `flask_app` fixture from `test_fraud_api.py` can be reused almost verbatim — the main delta is simpler worksheet mock setup (no FraudDetector helper patches needed). For cashier routes, JWT auth requires either a real token in a cookie or a decorator patch; generating a real JWT token at fixture time is cleaner and avoids coupling to implementation internals.

## Recommendation

Follow `test_fraud_api.py`'s `flask_app` fixture as the authoritative pattern. Extend `conftest.py` with a shared `flask_app` fixture that:
1. Sets required env vars (`FLASK_SECRET_KEY`, `GOOGLE_SHEETS_ID`, `WEB_CONCURRENCY=1`) via `monkeypatch` or `os.environ`
2. Patches `google.oauth2.service_account.Credentials.from_service_account_file` + `gspread.authorize`
3. Imports `backend.dashboard.admin_dashboard as adm`
4. **Critically**: sets `sys.modules['admin_dashboard'] = adm` so cashier inline imports get the mocked module
5. Replaces `adm.db` and `adm.get_sheets_client` with the configured mock

Session setup for admin routes: call `client.post('/login', json={...})` with env-var credentials. JWT setup for cashier routes: call `client.post('/cashier/api/login', json={...})` after mocking the Cashier Accounts worksheet — or generate the JWT directly and set the cookie.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Flask test client | `adm.app.test_client()` from imported module | Already wired with all blueprints and auth |
| Module-level Sheets mock | `creds_patch` + `gspread_patch` pattern from `test_fraud_api.py` | Proven to handle `db = get_sheets_client()` at import time |
| Session pre-population | `with client.session_transaction() as sess: sess[...] = ...` | Flask's built-in test session context manager |
| JWT cookie | `jwt.encode(payload, JWT_SECRET, algorithm='HS256')` then `client.set_cookie(...)` | Uses the same JWT_SECRET the decorator reads |

## Existing Code and Patterns

- `tests/test_fraud_api.py` — **canonical pattern to follow**; `flask_app` fixture (lines 225–278) shows the exact import/patch sequence; `admin_session` fixture (lines 287–291) shows session-based login; `_patch_detector` shows per-test module-level object replacement
- `tests/conftest.py` — existing fixtures (`mock_google_sheets`, `sample_student_data`, `sample_money_account_data`, `sample_transaction_data`); needs new `mock_sheets_client` fixture as described in S04 boundary; existing fixtures do NOT set up the Flask app — that's done per test-module in test_fraud_api.py
- `backend/dashboard/admin_dashboard.py:132–149` — `get_sheets_client()` + `db = get_sheets_client()` runs at import; both `FLASK_SECRET_KEY` guard (lines 59–66) and `WEB_CONCURRENCY` guard (lines 75–78) call `sys.exit(1)` at import time
- `backend/dashboard/cashier/cashier_routes.py:75–131` — `api_login()` does `sys.path.insert(...); from admin_dashboard import get_sheets_client` **inline at request time** (not at import time); same for `complete_sale()` lines 284–287
- `backend/dashboard/cashier/cashier_routes.py:37–44` — `JWT_SECRET` is `os.getenv('JWT_SECRET', 'bangko-jwt-secret-2026')` — has a non-empty default, so JWT test tokens work without setting the env var
- `backend/dashboard/admin_dashboard.py:256–292` — `login()` route sets `session['admin_logged_in'] = True`, `session['role'] = 'admin'`; `admin_only` decorator checks `session.get('role') == 'admin'`
- `backend/offline_queue.py:204` — `get_offline_queue()` returns `SQLiteWriteQueue` singleton; needs to be mocked in offline-fallback test

## Constraints

- **Two startup guards call `sys.exit(1)` at import time**: `FLASK_SECRET_KEY` (must be non-empty, non-default) and `WEB_CONCURRENCY` (must be ≤ 1). Env vars must be set **before** `import backend.dashboard.admin_dashboard`.
- **Module already cached from test_fraud_api.py**: If S04 tests run in the same pytest session as `test_fraud_api.py`, `backend.dashboard.admin_dashboard` is already in `sys.modules`. The fixture must handle both cases (cached and fresh import) — same try/except pattern as in test_fraud_api.py.
- **`sys.modules['admin_dashboard']` must be registered**: `cashier_routes.py` does `from admin_dashboard import get_sheets_client` inline in `api_login()` and `complete_sale()`. Without `sys.modules['admin_dashboard'] = adm`, Python loads a second unmocked copy of admin_dashboard, triggering `db = get_sheets_client()` with real credentials (and failing). **Verified**: after setting `sys.modules['admin_dashboard'] = adm`, the inline import correctly gets the mocked module.
- **`load_balance` uses `money_sheet.find('Balance').col`**: The MagicMock for `money_sheet` auto-creates `.find()` → `.col` via MagicMock attribute chaining, returning a MagicMock. `update_cell(row_index, mock_col, new_balance)` will succeed silently. No special mock setup needed.
- **`complete_sale` reads `flask_session['pending_transaction']`**: Must be pre-populated before the test request using `with client.session_transaction() as sess: sess['pending_transaction'] = {'items': [...], 'total': 50.0}`.
- **JWT `@jwt_required` reads cookie**: `request.cookies.get('jwt_token')` — the test client must have a valid JWT cookie set. Generate with `jwt.encode(...)` using `JWT_SECRET = 'bangko-jwt-secret-2026'` (the default) or env var value.
- **`load_balance` is `@login_required` only** (no `@admin_only`): finance role can call it. `void_transaction` requires both `@login_required` and `@admin_only` (`session['role'] == 'admin'`).
- **`PHASE3_AVAILABLE` flag**: SMS and FCM are gated on `PHASE3_AVAILABLE`. In test env, `PHASE3_AVAILABLE` will be `True` if all phase3 modules import. Twilio and FCM calls must be patched to prevent real network calls. Mock `backend.dashboard.admin_dashboard.get_sms_notifier` and `backend.dashboard.cashier.cashier_routes` imports of `get_sms_notifier`/`notifications`.
- **Windows encoding**: `admin_dashboard.py` line 113 prints `"✅ Cashier blueprint registered"` — causes `UnicodeEncodeError` in a bare `python -c` on Windows. Pytest sets UTF-8 encoding so tests run fine. Do not test via bare `python -c` on Windows without `io.TextIOWrapper`.

## Common Pitfalls

- **Not registering `sys.modules['admin_dashboard']`** — The inline `from admin_dashboard import get_sheets_client` in `api_login()` and `complete_sale()` will spawn a second fresh import of `admin_dashboard.py` with no mocks, hitting the real `db = get_sheets_client()` call. This causes either a credentials error (crashing the test) or a silent second module with unmocked Sheets. Fix: `sys.modules['admin_dashboard'] = adm` in the fixture.
- **Forgetting `FLASK_SECRET_KEY` before import** — `admin_dashboard.py` calls `sys.exit(1)` at import if this is missing/insecure. Must set in `os.environ` before the import inside the fixture (before `creds_patch.start()`).
- **`WEB_CONCURRENCY` default is `"1"` (safe), but `_parse_worker_count` reads `os.environ.get(..., "1")`** — safe by default; just don't set it to `"2"` in test env.
- **`pending_transaction` missing** — `complete_sale()` returns 400 if `flask_session.get('pending_transaction')` is None. Must use `session_transaction()` to seed it before calling the endpoint.
- **Status code discrepancy for inactive cashier account** — Roadmap says `Status=Inactive → 403`, but actual code (`cashier_routes.py:86`) returns **401**. Tests should match the actual code (401), not the roadmap spec.
- **`get_sms_notifier` leaks** — Both `complete_sale` (in cashier_routes) and `load_balance` (in admin_dashboard) call `get_sms_notifier()` and then `sms.send_*()`. If not patched, this imports Twilio and may fail. Patch `backend.notifications.get_sms_notifier` to return a MagicMock.
- **`void_transaction` uses `session.get('username', 'admin')` not `session.get('admin_username')`** — This is a pre-existing minor bug (login sets `'admin_username'`, not `'username'`), so `admin_user` in void records will always be `'admin'` in tests. Don't assert on the specific admin name in void records.
- **`gspread.exceptions.APIError` constructor** — `APIError` takes a `requests.Response`-like object. For offline-fallback tests, use `gspread.exceptions.APIError(MagicMock(status_code=429))` or just `Exception` raised from the mock. Check whether the offline path catches `gspread.exceptions.APIError` specifically (it does, line 371).

## Open Risks

- **`PHASE3_AVAILABLE=True` in test env**: If all backend modules (analytics, exports, notifications, fraud_detection, scheduler) import cleanly, `PHASE3_AVAILABLE` will be `True` and `load_balance` will attempt SMS/FCM. This is likely — the venv already has all deps. Tests must mock `get_sms_notifier` to avoid Twilio env var checks.
- **Offline queue SQLite creates a file**: `get_offline_queue()` creates `offline_queue.db` in the current directory. For the offline-fallback test, mock `get_offline_queue` entirely rather than letting it create a real SQLite DB. Alternatively, use `tmp_path` fixture and patch `_DEFAULT_DB_PATH`.
- **`gspread.exceptions.APIError` needs a Response object**: The offline fallback test must raise it correctly. Use `MagicMock(status_code=429, headers={})` as the mock response to avoid AttributeError in gspread's error handler.
- **Module re-import isolation between test files**: If `test_fraud_api.py` runs first and sets `adm.db = old_mock`, S04's `flask_app` fixture must overwrite `adm.db` with its own mock. The `scope='module'` or `scope='function'` decision matters — use `scope='module'` within each test file to avoid fixture overhead, but ensure the mock is reconfigured per test class.
- **Cashier blueprint path in sys.modules**: `cashier_routes` is imported as `backend.dashboard.cashier.cashier_routes` via the package path. Its inline imports use short names. This only matters for the `from admin_dashboard import ...` calls. No other inline import in cashier_routes causes issues.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| pytest | n/a — built-in knowledge | n/a |
| Flask test client | n/a — built-in knowledge | n/a |
| unittest.mock | n/a — built-in knowledge | n/a |

No additional skills needed. The technology stack is standard Python testing (pytest + unittest.mock).

## Key Implementation Notes for S04

### conftest.py additions
Add `mock_sheets_client` fixture:
```python
@pytest.fixture
def mock_sheets_client():
    """Configurable worksheet MagicMock for unit tests."""
    mock_spreadsheet = MagicMock()
    def worksheet_factory(name):
        ws = MagicMock()
        ws.title = name
        return ws
    mock_spreadsheet.worksheet.side_effect = worksheet_factory
    return mock_spreadsheet
```

### flask_app fixture (shared or per-module)
```python
# In each test module OR in conftest.py
@pytest.fixture(scope='module')
def flask_app():
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-for-s04'
    os.environ['GOOGLE_SHEETS_ID'] = 'fake-sheet-id'
    os.environ['WEB_CONCURRENCY'] = '1'
    os.environ['ADMIN_USERNAME'] = 'admin'
    os.environ['ADMIN_PASSWORD'] = 'adminpass'
    os.environ['FINANCE_USERNAME'] = 'finance'
    os.environ['FINANCE_PASSWORD'] = 'financepass'

    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheets.return_value = []
    mock_spreadsheet.worksheet.return_value = MagicMock()
    mock_spreadsheet.add_worksheet.return_value = MagicMock()

    creds_patch = patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=MagicMock())
    gspread_patch = patch('gspread.authorize', return_value=MagicMock(open_by_key=MagicMock(return_value=mock_spreadsheet)))
    creds_patch.start()
    gspread_patch.start()

    try:
        import backend.dashboard.admin_dashboard as adm
    except Exception:
        pass
    import backend.dashboard.admin_dashboard as adm

    adm.db = mock_spreadsheet
    adm.get_sheets_client = lambda: mock_spreadsheet
    # CRITICAL: register under short name for inline imports in cashier_routes
    sys.modules['admin_dashboard'] = adm

    creds_patch.stop()
    gspread_patch.stop()

    adm.app.config['TESTING'] = True
    adm.app.config['WTF_CSRF_ENABLED'] = False
    yield adm.app, mock_spreadsheet  # yield both for per-test reconfiguration
```

### JWT token helper for cashier tests
```python
import jwt as _jwt
JWT_SECRET = os.getenv('JWT_SECRET', 'bangko-jwt-secret-2026')

def _make_cashier_token(username='cashier', role='cashier'):
    from datetime import datetime, timedelta
    payload = {
        'user_id': f'{username}_id',
        'username': username,
        'display_name': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=8),
        'iat': datetime.utcnow(),
    }
    return _jwt.encode(payload, JWT_SECRET, algorithm='HS256')
```

### Session setup for admin tests
```python
@pytest.fixture
def admin_client(flask_app):
    client = flask_app[0].test_client()
    client.post('/login', json={'username': 'admin', 'password': 'adminpass'})
    return client
```

### Pending transaction setup for complete_sale tests
```python
def _set_pending(client, items, total):
    with client.session_transaction() as sess:
        sess['pending_transaction'] = {'items': items, 'total': total, 'cashier_id': 'cashier_id'}
```

## Sources

- Inline code analysis: `tests/test_fraud_api.py` (canonical mock pattern, flask_app fixture, admin_session fixture)
- Inline code analysis: `backend/dashboard/cashier/cashier_routes.py` (JWT auth, inline import pattern, complete_sale logic, offline fallback, status code for inactive account = 401)
- Inline code analysis: `backend/dashboard/admin_dashboard.py` (startup guards, load_balance, void_transaction, session keys, PHASE3_AVAILABLE gating)
- Verification experiment: confirmed `sys.modules['admin_dashboard']` is not set after package import; confirmed fix works (see research commands)
- Inline code analysis: `backend/offline_queue.py` (SQLite queue, enqueue method, `get_offline_queue()` factory)
