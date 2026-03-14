# M002: Production Readiness & Deployment Stability — Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

## Project Description

Bangko ng Seton is an RFID-based school canteen payment system deployed on PythonAnywhere. Two Flask apps (admin dashboard on port 5000, mobile API on port 5001) share Google Sheets as the database. M001 completed all 13 feature requirements. M002 closes the stabilization gaps surfaced during M001 implementation before the system sees real school use.

## Why This Milestone

M001 left five concrete production gaps: a malformed requirements file (unresolved merge conflict), a cache layer that exists but is almost entirely unwired, a FraudDetector that silently splits-brain under multi-worker gunicorn, zero unit tests on money-moving code paths, and a hardcoded health check on the API server. These are not theoretical risks — the requirements.txt merge conflict makes the file invalid today.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run `pip install -r backend/dashboard/requirements.txt` and `pip install -r backend/api/requirements_api.txt` on a fresh virtualenv and have both apps start without errors
- Hit hot endpoints (products, students, transaction list) repeatedly during lunch rush without exhausting the 60 req/min Sheets quota
- Start the admin server with a clear error if accidentally configured for multiple gunicorn workers
- Run `pytest` on the critical path suite and get a green result in under 10 seconds, with no live Sheets calls
- Follow `docs/DEPLOY.md` from scratch to a working PythonAnywhere deployment

### Entry point / environment

- Entry point: `python backend/dashboard/admin_dashboard.py` / `python backend/api/api_server.py` / `gunicorn` via PythonAnywhere WSGI
- Environment: PythonAnywhere production; local dev for test verification
- Live dependencies: Google Sheets API (primary), Twilio (optional, gated), Firebase FCM (optional, gated)

## Completion Class

- Contract complete means: `pip install -r` passes, `pytest` critical-path suite green, all health endpoints return structured JSON
- Integration complete means: cache invalidation works correctly after mutations; startup guard fires under multi-worker config
- Operational complete means: `docs/DEPLOY.md` followed on PythonAnywhere reaches passing `/api/health`

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `pip install -r` on a fresh venv for both apps succeeds with no errors
- A repeated product-list request hits cache (second call returns faster / cache stats show hit)
- Starting admin app with `WEB_CONCURRENCY=2` fails at startup with a human-readable message
- `pytest tests/test_cashier_routes.py tests/test_admin_critical.py` passes in <10s with no network calls
- `GET /api/health` on api_server returns `{status, sheets_ok, latency_ms}` and returns 503 when Sheets unreachable

## Risks and Unknowns

- **Merge conflict resolution**: The `<<<< ==== >>>>` markers in `requirements.txt` must be resolved correctly — both the bcrypt entry (in HEAD) and any S02-branch additions need to be preserved. Git history will show what each side added.
- **Cache invalidation correctness**: Wiring cache reads is easy; invalidating the right keys after mutations is where stale-data bugs hide. Must verify that complete_sale, load_balance, and void_transaction each clear the correct keys.
- **api_server.py Sheets connectivity**: The API server doesn't have a Sheets client at module level — it creates one per request via `get_sheets_client()`. Health check needs to do a real ping without creating a persistent connection.
- **Test fixture complexity**: cashier_routes.py and admin_dashboard.py both import Sheets client at module level. Getting mock fixtures right (patching at the right import level) is the risky part of S04.

## Existing Codebase / Prior Art

- `backend/cache.py` — 254-line cache implementation with `get_cached`, `set_cached`, `invalidate_pattern`, `get_cache_stats`. Already imported in admin_dashboard.py but used by only 2 of ~100 Sheets calls.
- `backend/dashboard/admin_dashboard.py` — main Flask app (~2500 lines); has `get_cached_sheet_data()` helper (lines ~153–186) that wraps a 30s TTL cache — but only 2 endpoints use it. Has `_sheets_cache` module-level dict as a parallel simpler cache. Should consolidate to `cache.py`.
- `backend/health.py` — `HealthMonitor` class with full structured health output (Sheets status, cache stats, uptime, system). Already used by admin_dashboard.py health endpoint. api_server.py does not use it.
- `backend/dashboard/requirements.txt` — has unresolved merge conflict at lines 19–24 (`<<<< HEAD`, `====`, `>>>> gsd/M001/S02`). bcrypt is in the HEAD section. The conflict must be resolved before any pip install.
- `backend/api/requirements_api.txt` — sparse: flask, flask-cors, gunicorn, pyjwt, cryptography only. Missing: gspread>=5.12.0, firebase-admin, twilio>=9.0.0, bcrypt>=4.0.0, psutil>=5.9.0, python-dotenv, pytz.
- `backend/fraud_detection.py` — `get_fraud_detector()` returns a module-level singleton. `_fraud_sheets_initialized` in admin_dashboard.py is also module-level. Each gunicorn worker process gets its own copy of both.
- `tests/conftest.py` — existing fixtures; needs `mock_sheets_client` fixture for proper unit test isolation.
- `tests/test_fraud_api.py` — 33 tests, properly mocked — the canonical pattern to follow for new test files.
- `backend/dashboard/wsgi.py` — PythonAnywhere WSGI config; hardcodes project path `/home/bankoseton/BANKONGSETON/backend/dashboard/`.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions.

## Relevant Requirements

- R014 — Requirements file completeness (S01)
- R015 — Cache layer coverage (S02)
- R016 — FraudDetector worker safety (S03)
- R017 — Critical path unit tests (S04)
- R018 — Health check standardization (S03)
- R019 — Deployment runbook (S05)

## Scope

### In Scope

- Resolve merge conflict in requirements.txt; audit and complete both requirements files
- Wire existing cache.py to hot Sheets-reading endpoints; add mutation invalidation
- FraudDetector startup hard-fail on workers > 1
- Standardize health endpoints across both apps (structured JSON, real Sheets ping, 503 on failure)
- ~35 unit tests on money-moving critical paths with mocked Sheets client
- `docs/DEPLOY.md` deployment runbook for PythonAnywhere

### Out of Scope / Non-Goals

- Making FraudDetector truly multi-worker safe (poll-on-request model) — hard-fail is the chosen approach
- Broad test coverage (60%+) — critical paths only
- CI pipeline / GitHub Actions — no CI infrastructure in scope
- New features of any kind
- Migrating off Google Sheets to a real database
- iOS app, GCash/Maya integration (already out-of-scope from M001)

## Technical Constraints

- PythonAnywhere free/paid tier: single WSGI worker per app, 60 req/min Sheets quota per service account
- Google Sheets: `get_all_records()` is expensive — each call counts against quota; cache TTL of 30s is the established pattern
- FraudDetector is in-memory per-process: single-worker constraint must be documented and enforced
- Both Flask apps use Google Sheets as the only database — no Redis, no Postgres, no shared state except Sheets
- `ParentPhone` must be in E.164 format (+639XXXXXXXXX) — SMS silently drops malformed numbers; must be documented in runbook

## Integration Points

- Google Sheets API — rate-limited at 60 req/min; cache layer is the mitigation
- PythonAnywhere WSGI — single worker per app; gunicorn config is set via the PythonAnywhere dashboard
- Twilio SMS — optional, gated on TWILIO_* env vars; must be in both requirements files
- Firebase FCM — optional, gated on GOOGLE_APPLICATION_CREDENTIALS; must be in api requirements

## Open Questions

- None — all decision points resolved in discussion
