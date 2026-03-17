---
id: T01
parent: S04
milestone: M002
provides:
  - flask_app fixture (module-scoped) with mocked Sheets and sys.modules['admin_dashboard'] registration
  - db fixture (function-scoped) for per-test worksheet isolation
  - _make_cashier_token helper for JWT generation compatible with cashier_routes
  - admin_client and finance_client authenticated test-client fixtures
  - _set_pending session-seeding helper
key_files:
  - tests/conftest.py
key_decisions:
  - Followed test_fraud_api.py pattern (try/except import + post-import db replacement) verbatim to handle module caching
  - Used module-level _adm variable to share imported module reference between module-scoped flask_app and function-scoped db fixtures
  - _make_cashier_token reads JWT_SECRET from env (consistent with cashier_routes.py) so tests work with both default and .env-overridden secrets
patterns_established:
  - Patch gspread before import → replace adm.db after import → stop patches → register sys.modules['admin_dashboard']
  - Function-scoped db fixture restores a generic MagicMock after each test to prevent state leaks
observability_surfaces:
  - pytest --collect-only confirms fixture discovery without SystemExit or ImportError
  - sys.modules.get('admin_dashboard') inside any test confirms short-name registration is live
  - _make_cashier_token failure surfaces as jwt.InvalidSignatureError (secret mismatch) or decode error
duration: 20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Wire test infrastructure in conftest.py

**Extended `tests/conftest.py` with module-scoped `flask_app`, function-scoped `db`, `_make_cashier_token`, `admin_client`, `finance_client`, and `_set_pending` — all gspread patches active before import, `sys.modules['admin_dashboard']` registered.**

## What Happened

Added `import sys`, `import jwt`, and `patch` to the conftest imports (non-breaking additions). Then appended the S04 test infrastructure block:

1. **`_make_cashier_token(username, role)`** — module-level helper; reads `JWT_SECRET` from env (falls back to `bangko-jwt-secret-2026`), encodes with HS256. Matches cashier_routes.py exactly.

2. **`_set_pending(client, items, total)`** — seeds `pending_transaction` into Flask session via `session_transaction()`.

3. **`flask_app` (module-scoped)** — sets all seven env vars before import (`FLASK_SECRET_KEY`, `GOOGLE_SHEETS_ID`, `WEB_CONCURRENCY=1`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FINANCE_USERNAME`, `FINANCE_PASSWORD`). Starts `Credentials.from_service_account_file` and `gspread.authorize` patches. Imports `backend.dashboard.admin_dashboard` via the canonical try/except pattern. Stops patches. Sets `adm.db`, `adm.get_sheets_client`, and `sys.modules['admin_dashboard'] = adm`. Configures `TESTING=True`, `WTF_CSRF_ENABLED=False`. Yields `(adm.app, mock_spreadsheet)`.

4. **`db` (function-scoped)** — creates a fresh `MagicMock()` spreadsheet, assigns to `_adm.db` and `_adm.get_sheets_client`. Restores a generic mock on teardown.

5. **`admin_client` / `finance_client`** — POST to `/login` with env credentials and return authenticated test clients.

A module-level `_adm` variable bridges the module-scoped flask_app fixture with the function-scoped db fixture (pytest does not allow function-scoped fixtures to depend on module-scoped ones via nesting alone).

## Verification

```
python -m pytest tests/conftest.py tests/test_fraud_api.py --collect-only -q
# → 33 items collected, no errors

python -m pytest tests/ --collect-only -q
# → 223 tests collected in 0.62s, no SystemExit or ImportError

python -c "..."   # _make_cashier_token encode/decode round-trip with env-resolved secret
# → OK: {'username': 'cashier1', 'role': 'cashier'}
```

All must-haves confirmed:
- [x] flask_app is module-scoped and sets all required env vars before import
- [x] sys.modules['admin_dashboard'] = adm set inside the fixture
- [x] gspread patches started before import, stopped after
- [x] db fixture is function-scoped and replaces adm.db per test
- [x] _make_cashier_token produces a valid JWT readable by cashier_routes' @jwt_required
- [x] admin_client logs in via /login POST and returns authenticated client
- [x] _set_pending seeds pending_transaction in Flask session

## Diagnostics

- `pytest tests/ --collect-only -q` — zero errors means fixtures are importable
- `sys.modules.get('admin_dashboard')` inside any test — confirms short-name registration
- `SystemExit` on collect → FLASK_SECRET_KEY / WEB_CONCURRENCY env vars not set before import
- `InvalidSignatureError` on JWT decode → JWT_SECRET mismatch between encoder and decoder (check .env)
- `from admin_dashboard import get_sheets_client` fails → sys.modules['admin_dashboard'] registration missing

## Deviations

Module-level `_adm` variable used to share the imported module between module-scoped (`flask_app`) and function-scoped (`db`) fixtures. This is a minor implementation detail not explicit in the plan but required because pytest does not allow function-scoped fixtures to yield-depend on module-scoped ones at the fixture-argument level.

## Known Issues

None. Existing fixtures (`mock_google_sheets`, `sample_*`, etc.) are fully preserved.

## Files Created/Modified

- `tests/conftest.py` — added `import sys, jwt, patch`; appended `flask_app`, `db`, `admin_client`, `finance_client`, `_make_cashier_token`, `_set_pending`
- `.gsd/milestones/M002/slices/S04/tasks/T01-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
