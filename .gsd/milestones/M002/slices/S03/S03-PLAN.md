# S03: FraudDetector Constraint & Health Standardization

**Goal:** Admin server hard-fails at startup when `WEB_CONCURRENCY > 1`; both `/api/health` endpoints return `{status, sheets_ok, latency_ms, queue_pending, timestamp}` and return 503 when Sheets is unreachable.
**Demo:** `scripts/verify-s03.sh` runs 18 checks and reports 18/18 pass; `python -m py_compile` exits 0 on all four changed files.

## Must-Haves

- `web_app.py` and `admin_dashboard.py` each exit with code 1 and a human-readable message when `WEB_CONCURRENCY > 1` or `GUNICORN_WORKERS > 1` (R016)
- Guard is at module level (not inside `if __name__ == '__main__':`) so gunicorn triggers it on WSGI import (R016)
- `dashboard_core.py` `/api/health` returns `{status, sheets_ok, latency_ms, queue_pending, timestamp}` and 503 when Sheets is unreachable (R018)
- `admin_dashboard.py` `/api/health` returns the same schema and 503 when Sheets is unreachable (R018)
- `api_server.py` `/api/health` returns the same schema and 503 when Sheets is unreachable (R018)
- All four files pass `python -m py_compile` with no errors

## Verification

```bash
bash scripts/verify-s03.sh
```

The script asserts:
- `python -m py_compile` exits 0 on `web_app.py`, `admin_dashboard.py`, `dashboard_core.py`, `api_server.py`
- `WEB_CONCURRENCY=2 python -c "import backend/dashboard/web_app"` exits non-zero (guard fires)
- `WEB_CONCURRENCY=2 python -c "import ..."` for `admin_dashboard.py` exits non-zero
- Health route in `dashboard_core.py` contains `sheets_ok`, `latency_ms`, `queue_pending`, `timestamp`
- Health route in `admin_dashboard.py` contains same four fields
- Health route in `api_server.py` contains same four fields
- All three health implementations return 503 on Sheets failure (grep for 503)
- WEB_CONCURRENCY guard message text is present in both web_app.py and admin_dashboard.py

## Observability / Diagnostics

- Runtime signals: `CRITICAL event=startup_aborted reason=multi_worker_forbidden` log line; `/api/health` JSON response with `sheets_ok: false` and 503 status
- Inspection surfaces: `scripts/verify-s03.sh`; `python -c "import sys; sys.exit(0)"` pattern for guard testing
- Failure visibility: `sheets_ok: false`, `latency_ms: 0` when Sheets client is None or raises; `queue_pending` int from live queue
- Redaction constraints: none (no secrets in health response)

## Integration Closure

- Upstream surfaces consumed: `get_queue_status()` from `resilience.py` (already imported in `dashboard_core.py`); `get_offline_queue()` from `offline_queue.py` (new import in `api_server.py`); module-level `db` in `dashboard_core.py` and `api_server.py`
- New wiring introduced: `offline_queue` import in `api_server.py`; real `db.worksheets()` ping inside both health handlers
- What remains before milestone is usable end-to-end: S04 (unit tests), S05 (runbook)

## Tasks

- [x] **T01: Add WEB_CONCURRENCY startup guard to web_app.py and admin_dashboard.py** `est:30m`
  - Why: R016 — FraudDetector module-level singleton is not safe across gunicorn workers; hard-fail prevents split-brain alert state silently.
  - Files: `backend/dashboard/web_app.py`, `backend/dashboard/admin_dashboard.py`
  - Do: In `web_app.py`, after the FINANCE_PASSWORD guard block (~line 80), add: read `WEB_CONCURRENCY` and `GUNICORN_WORKERS` from env, convert to int with try/except (default 1 on parse error), if either > 1 call `logger.critical(...)` + `sys.exit(1)` with message: `"FraudDetector requires single-worker mode. Set WEB_CONCURRENCY=1 in your gunicorn config."` — follow the exact pattern of the existing guards. In `admin_dashboard.py`, after the FLASK_SECRET_KEY guard block (~line 66), add the same guard using `print()` + `sys.exit(1)` to match the existing style in that file.
  - Verify: `python -m py_compile backend/dashboard/web_app.py && python -m py_compile backend/dashboard/admin_dashboard.py` — both exit 0. `WEB_CONCURRENCY=2 python -c "import sys; sys.path.insert(0,'backend/dashboard'); sys.path.insert(0,'backend'); import web_app" 2>&1` exits non-zero with the guard message.
  - Done when: Both files compile cleanly; `WEB_CONCURRENCY=2` causes non-zero exit on import; `WEB_CONCURRENCY=1` (default) does not.

- [x] **T02: Standardize /api/health in dashboard_core.py, admin_dashboard.py, and api_server.py; write verify-s03.sh** `est:1h`
  - Why: R018 — all three health endpoints currently return wrong shapes or unconditional 200; load balancers and monitoring cannot rely on them.
  - Files: `backend/dashboard/dashboard_core.py`, `backend/dashboard/admin_dashboard.py`, `backend/api/api_server.py`, `scripts/verify-s03.sh`
  - Do:
    1. `dashboard_core.py` — replace the `health_check()` function body inside `register_routes()` (~line 2951). New logic: record `t0 = time.time()`, then `if db is None: sheets_ok=False, latency_ms=0` else try `db.worksheets()` and set `sheets_ok=True, latency_ms=int((time.time()-t0)*1000)`, on exception set `sheets_ok=False`. Build response: `{status: "ok" if sheets_ok else "degraded", sheets_ok, latency_ms, queue_pending: get_queue_status().get("pending", 0), timestamp: datetime.now(PHILIPPINES_TZ).isoformat()}`. Return 200 if `sheets_ok`, 503 otherwise. Do NOT call `get_health_status()`.
    2. `admin_dashboard.py` — replace the `health_check()` function body at line ~440 with the same logic. Use the module-level `db` from `admin_dashboard.py` (~line 137). `get_queue_status()` is already imported from `resilience` (or the fallback stub). `PHILIPPINES_TZ` is already defined. `time` is already imported.
    3. `api_server.py` — at module level (after existing try/except imports, ~line 30), add: `try: from offline_queue import get_offline_queue as _get_offline_queue; _OFFLINE_QUEUE_AVAILABLE = True \nexcept ImportError: _OFFLINE_QUEUE_AVAILABLE = False`. Replace the `health_check()` at line 192 with real logic: `t0 = time.time()`, fresh `get_sheets_client()` call (not reusing stale `db`) wrapped in try/except, set `sheets_ok`/`latency_ms`, get `queue_pending` from `_get_offline_queue().get_status()['pending']` if `_OFFLINE_QUEUE_AVAILABLE` else 0, build same response dict, return 503 when `sheets_ok=False`. `time`, `pytz`, `datetime` already imported; `PHILIPPINES_TZ = pytz.timezone('Asia/Manila')` already defined in api_server.py.
    4. `scripts/verify-s03.sh` — 18-check script: py_compile on 4 files; guard message text present in both web_app.py and admin_dashboard.py; WEB_CONCURRENCY env var read present; `sheets_ok` / `latency_ms` / `queue_pending` / `timestamp` all present in each of the three health handlers; 503 returned on failure path in each; `get_offline_queue` import attempt present in api_server.py.
  - Verify: `bash scripts/verify-s03.sh` reports 18/18 pass.
  - Done when: Script reports 18/18; all four files compile; `api_server.py` health handler references `get_offline_queue`; each health handler returns 503 on Sheets failure.

## Files Likely Touched

- `backend/dashboard/web_app.py`
- `backend/dashboard/admin_dashboard.py`
- `backend/dashboard/dashboard_core.py`
- `backend/api/api_server.py`
- `scripts/verify-s03.sh`
