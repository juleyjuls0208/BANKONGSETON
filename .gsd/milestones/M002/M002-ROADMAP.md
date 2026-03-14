# M002: Production Readiness & Deployment Stability

**Vision:** Close five concrete production gaps before real school use — resolve a malformed requirements file, wire the existing cache layer to prevent Sheets quota exhaustion, constrain FraudDetector to single-worker, unit-test money-moving code paths, and standardize health checks with a deployment runbook.

## Success Criteria

- `pip install -r backend/dashboard/requirements.txt` and `pip install -r backend/api/requirements_api.txt` both succeed on a fresh virtualenv with no errors
- Repeated requests to hot endpoints (product list, student list, transaction recent) are served from cache; Sheets is not called on cache hits
- Mutations (complete_sale, load_balance, void_transaction) invalidate the correct cache keys; subsequent reads fetch fresh data
- Starting the admin server with `WEB_CONCURRENCY=2` (or `--workers 2`) fails at startup with a human-readable error
- `GET /api/health` on both apps returns `{status, sheets_ok, latency_ms, queue_pending, timestamp}`; both return 503 when Sheets is unreachable
- `pytest tests/test_cashier_routes.py tests/test_admin_critical.py` passes in under 10 seconds with zero live Sheets calls
- `docs/DEPLOY.md` exists and covers env vars, service account setup, first-run migration, health check sequence, single-worker constraint, E.164 phone format, and offline queue behavior on fresh deploy

## Key Risks / Unknowns

- **requirements.txt merge conflict** — file is malformed today; pip would choke on it; must be the first thing fixed
- **Cache invalidation correctness** — cache reads are mechanical; clearing the right keys after mutations is where stale-data bugs live
- **Test fixture import patching** — cashier_routes.py and admin_dashboard.py import Sheets clients at module level; getting the mock patch target right is the risky part
- **api_server.py Sheets ping in health check** — API server creates Sheets client per-request; health check needs a real connectivity probe without creating a persistent connection

## Proof Strategy

- Requirements merge conflict risk → retire in S01 by running `pip install -r` on a fresh venv and confirming both apps start
- Cache invalidation correctness risk → retire in S02 by verifying that a mutation + subsequent read returns fresh data (not stale cache)
- Test fixture patching risk → retire in S04 by confirming all tests pass with no network calls (mock assertions)
- api health check risk → retire in S03 by testing the endpoint with a mocked Sheets failure and confirming 503 response

## Verification Classes

- Contract verification: `pip install -r` success; `pytest` green with no live Sheets calls; health endpoint JSON structure assertions
- Integration verification: cache hit confirmed via `GET /api/cache/stats` before/after; mutation invalidation verified by sequential read→mutate→read
- Operational verification: `WEB_CONCURRENCY=2` startup hard-fail; PythonAnywhere deploy following runbook reaches passing `/api/health`
- UAT / human verification: none — all verification is automated or script-driven

## Milestone Definition of Done

This milestone is complete only when all are true:

- `pip install -r` succeeds for both apps on a clean venv — no errors, no missing packages
- Merge conflict in `backend/dashboard/requirements.txt` is resolved and file is valid
- Hot Sheets-reading endpoints serve from cache on repeated requests; cache stats show hits
- Mutations clear the relevant cache keys; stale reads do not occur after complete_sale, load_balance, void_transaction
- Admin server exits with a human-readable error when `WEB_CONCURRENCY > 1`
- `GET /api/health` on both apps returns structured JSON with Sheets connectivity status; returns 503 when Sheets is down
- `pytest` critical-path suite passes green with zero live Sheets calls in under 10 seconds
- `docs/DEPLOY.md` exists and is accurate for a fresh PythonAnywhere deployment

## Requirement Coverage

- Covers: R014, R015, R016, R017, R018, R019
- Partially covers: none
- Leaves for later: none
- Orphan risks: none

## Slices

- [x] **S01: Requirements & Git Hygiene** `risk:high` `depends:[]`
  > After this: `pip install -r` succeeds for both Flask apps on a fresh virtualenv — merge conflict resolved, all missing packages added to api requirements.

- [x] **S02: Cache Layer Wiring** `risk:medium` `depends:[S01]`
  > After this: Hot endpoints serve from cache; mutations invalidate correctly; `GET /api/cache/stats` shows hits during a simulated lunch-rush sequence.

- [x] **S03: FraudDetector Constraint & Health Standardization** `risk:low` `depends:[S01]`
  > After this: Admin server refuses to start with `WEB_CONCURRENCY=2`; both `/api/health` endpoints return structured JSON with real Sheets connectivity status and return 503 when Sheets is unreachable.

- [x] **S04: Critical Path Unit Tests** `risk:medium` `depends:[S01]`
  > After this: `pytest` runs ~35 tests on complete_sale, load_balance, void_transaction, and cashier auth — green, zero live Sheets calls, under 10 seconds.

- [ ] **S05: Deployment Runbook** `risk:low` `depends:[S01,S03,S04]`
  > After this: `docs/DEPLOY.md` exists with env vars, service account setup, first-run migration steps, health check sequence, and all known operational constraints documented.

## Boundary Map

### S01 → S02, S03, S04, S05

Produces:
- `backend/dashboard/requirements.txt` — merge conflict resolved; bcrypt>=4.0.0 and twilio>=9.0.0 present; valid pip-installable file
- `backend/api/requirements_api.txt` — complete: gspread>=5.12.0, firebase-admin, twilio>=9.0.0, bcrypt>=4.0.0, psutil>=5.9.0, python-dotenv, pytz added alongside existing entries
- Verified: `pip install -r` succeeds for both apps on a fresh venv (documented as S01 verification)

Consumes:
- nothing (first slice)

### S02 → S05

Produces:
- `get_cached` / `set_cached` / `invalidate_pattern` from `cache.py` wired to hot endpoints in `admin_dashboard.py`: product list (`/api/products/list`), student list (`/students` data), money accounts, transaction recent, analytics summary
- Same cache pattern applied to hot endpoints in `api_server.py`: student profile, balance lookup, product list
- `complete_sale()`, `load_balance()`, `void_transaction()` each call `invalidate_pattern()` after successful Sheets write
- `GET /api/cache/stats` returns `{hits, misses, size, hit_rate}` — already routed at `/api/cache/stats` in admin_dashboard.py, wired to real `cache.py` stats
- Cache TTL: 30s for read-heavy data (products, students), 10s for transaction data

Consumes from S01:
- Clean requirements files (cache.py imports confirmed available on fresh venv)

### S03 → S05

Produces:
- Startup guard in `admin_dashboard.py`: reads `WEB_CONCURRENCY` env var (gunicorn sets this) and `GUNICORN_WORKERS`; if either > 1, logs CRITICAL and calls `sys.exit(1)` with message: "FraudDetector requires single-worker mode. Set WEB_CONCURRENCY=1 in your gunicorn config."
- `api_server.py` `GET /api/health` returns `{status, sheets_ok, latency_ms, queue_pending, timestamp}` — does a real Sheets ping (list worksheets with timeout); returns 503 when Sheets unreachable
- `admin_dashboard.py` `GET /api/health` updated to return 503 (not 200) when `get_health_status()` reports Sheets down; returns same structured fields for consistency

Consumes from S01:
- Clean requirements (no new deps added in S03)

### S04 → S05

Produces:
- `tests/conftest.py` updated: `mock_sheets_client` fixture patching `gspread.service_account` and `gspread.Client`; returns a `MagicMock` with configurable worksheet data
- `tests/test_cashier_routes.py` — ~18 tests:
  - `test_complete_sale_success` — valid card, sufficient balance, Sheets write succeeds
  - `test_complete_sale_suspended_card` — card in suspended list → 403
  - `test_complete_sale_insufficient_balance` — balance < total → 402
  - `test_complete_sale_offline_fallback` — Sheets raises APIError → offline queue enqueued, returns 200 with `{"offline": true}`
  - `test_complete_sale_sms_failure_nonfatal` — Twilio raises → sale still succeeds
  - `test_cashier_api_login_sheets_auth` — username/bcrypt hash in Cashier Accounts sheet → 200 with token
  - `test_cashier_api_login_legacy_fallback` — no Cashier Accounts sheet → legacy cashier/cashier123 → 200
  - `test_cashier_api_login_bad_credentials` → 401
  - `test_cashier_api_login_inactive_account` — Status=Inactive → 403
  - Additional edge cases to reach ~18
- `tests/test_admin_critical.py` — ~17 tests:
  - `test_load_balance_success` — Sheets write succeeds, balance updated, SMS attempted
  - `test_load_balance_sms_failure_nonfatal` — Twilio raises → load still succeeds
  - `test_load_balance_invalid_amount` — negative or zero amount → 400
  - `test_void_transaction_success` — balance restored, void record appended
  - `test_void_transaction_double_void_rejected` — transaction type already Void → 400
  - `test_void_transaction_not_found` → 404
  - `test_void_transaction_balance_restoration` — asserts restored balance = original balance + void amount
  - Additional edge cases to reach ~17

Consumes from S01:
- Clean requirements (pytest, all mocked imports available)

### S05 → (milestone end)

Produces:
- `docs/DEPLOY.md` — sections: Prerequisites, Environment Variables (complete list with descriptions), Google Sheets Service Account Setup, PythonAnywhere WSGI Config, First-Run Migration (run migrate_transactions.py, verify Sheets worksheets auto-created), Health Check Sequence (expected responses from both /api/health endpoints), Known Operational Constraints (single-worker only, E.164 phone format for SMS, offline queue db created empty on fresh deploy, ParentPhone column must exist in Users sheet)

Consumes from S01:
- Final requirements files (env vars documented from what's actually needed)
Consumes from S03:
- Single-worker constraint and health check response shapes (document what's actually implemented)
Consumes from S04:
- Test run instructions (runbook includes how to run the test suite before deploying)
