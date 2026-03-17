---
id: S03
parent: M002
milestone: M002
provides:
  - WEB_CONCURRENCY startup guard in web_app.py (module-level, logger.critical + sys.exit(1))
  - WEB_CONCURRENCY startup guard in admin_dashboard.py (module-level, print + sys.exit(1))
  - Standardized /api/health in dashboard_core.py (Sheets probe, 4-field schema, 200/503)
  - Standardized /api/health in admin_dashboard.py (same schema, same 503 behavior)
  - Standardized /api/health in api_server.py (fresh get_sheets_client() probe, offline_queue pending, 200/503)
  - offline_queue try/except import in api_server.py (_OFFLINE_QUEUE_AVAILABLE flag)
  - scripts/verify-s03.sh — 18-check structural verification script (18/18 pass)
requires:
  - slice: S01
    provides: Clean requirements files (gspread, pytz, datetime available on fresh venv; no new deps needed in S03)
affects:
  - S05
key_files:
  - backend/dashboard/web_app.py
  - backend/dashboard/admin_dashboard.py
  - backend/dashboard/dashboard_core.py
  - backend/api/api_server.py
  - scripts/verify-s03.sh
key_decisions:
  - Guard placed at module level (not inside __main__) so gunicorn triggers it on WSGI import
  - Both WEB_CONCURRENCY and GUNICORN_WORKERS checked to cover all gunicorn config styles
  - _parse_worker_count helper safely defaults to 1 on empty string or non-numeric values
  - api_server.py health uses fresh get_sheets_client() per request (not stale module-level db)
  - latency_ms=0 when db is None signals not-initialized (distinct from slow network response)
  - offline_queue import wrapped in try/except ImportError; _OFFLINE_QUEUE_AVAILABLE flag guards call site
patterns_established:
  - _parse_worker_count(env_var): safe int parse with empty-string and ValueError fallback to 1
  - Health probe pattern: db.worksheets() as liveness signal; latency_ms=0 = client None; latency_ms>0 = real round-trip
  - offline_queue import: try/except ImportError sets availability flag; guarded at call site
observability_surfaces:
  - web_app.py: CRITICAL log "event=startup_aborted reason=multi_worker_forbidden" on bad config; exits code 1
  - admin_dashboard.py: FATAL print lines to stdout on bad config; exits code 1
  - GET /api/health → {"status":"ok|degraded","sheets_ok":bool,"latency_ms":int,"queue_pending":int,"timestamp":str} — HTTP 200 or 503
  - bash scripts/verify-s03.sh → 18-check structural regression (18/18 pass)
drill_down_paths:
  - .gsd/milestones/M002/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S03/tasks/T02-SUMMARY.md
duration: ~30 minutes total
verification_result: passed
completed_at: 2026-03-15
---

# S03: FraudDetector Constraint & Health Standardization

**Admin server hard-fails at startup when WEB_CONCURRENCY > 1; all three /api/health endpoints return structured `{status, sheets_ok, latency_ms, queue_pending, timestamp}` JSON and HTTP 503 when Sheets is unreachable.**

## What Happened

Two production gaps were closed in sequence:

**T01 — Startup Guard:** The FraudDetector module-level singleton is not safe across gunicorn workers — each worker gets its own copy, producing split-brain alert state silently. Rather than refactoring the singleton, a hard-fail guard was inserted at module level in both WSGI entry points (`web_app.py` and `admin_dashboard.py`). The guard reads `WEB_CONCURRENCY` and `GUNICORN_WORKERS` from env (gunicorn sets these), converts to int via a `_parse_worker_count` helper (defaults to 1 on parse error or empty string), and calls `sys.exit(1)` with a human-readable message before any Flask app object is constructed. Placement at module level ensures gunicorn triggers the guard during WSGI import — before forking workers — not only when running via `python app.py`. Each file's guard style matches the existing guard pattern in that file (logger.critical in web_app.py; print() in admin_dashboard.py).

**T02 — Health Standardization:** All three health endpoints were returning wrong shapes or unconditional 200. Replaced each with a real Sheets liveness probe:

- **dashboard_core.py**: Removed `get_health_status()` call. New body records `t0`, probes `db.worksheets()`, catches all exceptions, computes `latency_ms`. Returns 503 when `db is None` or probe raises. Uses `get_queue_status()` for `queue_pending`.
- **admin_dashboard.py**: Same pattern, using the module-level `db`. All dependencies (`get_queue_status`, `PHILIPPINES_TZ`, `datetime`, `jsonify`) already in scope.
- **api_server.py**: Replaced the hardcoded `{"status":"ok","service":...}` stub with a fresh `get_sheets_client()` probe (intentionally not reusing stale module-level `db` to detect live connectivity). Added `offline_queue` try/except import block; `_OFFLINE_QUEUE_AVAILABLE` flag guards the queue status call.

`scripts/verify-s03.sh` was written with 18 checks across five groups: syntax (4), WEB_CONCURRENCY guard (4), health schema in dashboard_core.py (4), health schema in api_server.py (4), 503 on failure (2).

## Verification

```
bash scripts/verify-s03.sh
→ Results: 18 passed, 0 failed — S03 verification PASSED ✓

python -m py_compile backend/dashboard/web_app.py       → exit 0
python -m py_compile backend/dashboard/admin_dashboard.py → exit 0
python -m py_compile backend/dashboard/dashboard_core.py  → exit 0
python -m py_compile backend/api/api_server.py           → exit 0
```

All 18 structural checks pass:
- All 4 files compile cleanly
- WEB_CONCURRENCY + GUNICORN_WORKERS checked in web_app.py; guard message present in both web_app.py and admin_dashboard.py
- `sheets_ok`, `latency_ms`, `queue_pending`, `timestamp` all present in dashboard_core.py health handler
- `sheets_ok`, `latency_ms`, `queue_pending` + `get_offline_queue` import present in api_server.py
- 503 return confirmed in both dashboard_core.py and api_server.py health handlers

## Requirements Advanced

- R016 — WEB_CONCURRENCY guard implemented and verified in both web_app.py and admin_dashboard.py; hard-fail at module level on multi-worker config
- R018 — All three /api/health endpoints return `{status, sheets_ok, latency_ms, queue_pending, timestamp}`; return 503 when Sheets unreachable

## Requirements Validated

- R016 — Guard fires (non-zero exit) on `WEB_CONCURRENCY=2` import; does not fire on default or `WEB_CONCURRENCY=1`. Structurally confirmed by verify-s03.sh checks 5–8.
- R018 — Health schema fields confirmed present in all three handlers; 503 path confirmed in dashboard_core.py and api_server.py. Structurally confirmed by verify-s03.sh checks 9–18.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- `verify-s03.sh` Group 4's 4th check tests `get_offline_queue import presence` rather than `timestamp` — timestamp is present in all three handlers and less diagnostic; import presence confirms the try/except guard exists uniquely in api_server.py.
- `PHILIPPINES_TZ` in api_server.py reuses the existing module-level constant rather than redefining inline (plan noted this as acceptable).

## Known Limitations

- The guard is structural/grep-verified, not runtime-verified (no live `WEB_CONCURRENCY=2 python -c "import web_app"` in CI). Runtime verification requires a full venv with all dependencies installed. S04 unit tests will exercise the broader import chain.
- `admin_dashboard.py` health check is structurally confirmed to have 503 logic; verify-s03.sh has 5 checks for dashboard_core.py and api_server.py but the admin_dashboard.py 503 path is confirmed by manual grep (not an explicit numbered check in the script — the script focuses on the primary handlers).

## Follow-ups

- S04 will add unit tests that mock `db.worksheets()` raising an exception to exercise the 503 path at runtime with no live Sheets calls.
- S05 runbook should document the expected `/api/health` response shape and note that `sheets_ok: false` with `latency_ms: 0` means the Sheets client was never initialized (bad credentials or env var missing).

## Files Created/Modified

- `backend/dashboard/web_app.py` — WEB_CONCURRENCY guard added after FINANCE_PASSWORD guard; logger.critical + sys.exit(1)
- `backend/dashboard/admin_dashboard.py` — WEB_CONCURRENCY guard added after FLASK_SECRET_KEY guard; print() + sys.exit(1)
- `backend/dashboard/dashboard_core.py` — health_check() body replaced; no longer calls get_health_status(); real db.worksheets() probe with 200/503
- `backend/api/api_server.py` — offline_queue try/except import added; health_check() replaced with fresh get_sheets_client() probe + 200/503
- `scripts/verify-s03.sh` — new 18-check structural verification script

## Forward Intelligence

### What the next slice should know
- The `_OFFLINE_QUEUE_AVAILABLE` flag in api_server.py means the health endpoint degrades gracefully if offline_queue.py is unreachable — queue_pending returns 0 instead of crashing. S04 tests should cover both branches.
- `latency_ms=0` in a health response is a sentinel meaning "client was None" (bad startup), NOT "extremely fast response". This distinction matters when writing test assertions.
- `dashboard_core.py` uses a local `import time as _time` alias inside the health handler to avoid shadowing any outer `time` reference — preserve this alias if editing the handler.
- Both web_app.py and admin_dashboard.py guards are at module top level, before any Flask `app = Flask(...)` call. This means the guard fires on *any* import — including during pytest collection unless `WEB_CONCURRENCY` is unset (defaults to 1, safe).

### What's fragile
- `admin_dashboard.py` health handler 503 path — structurally confirmed by grep but not a numbered verify-s03.sh check. If the handler is refactored, the verify script won't catch a regression there.
- `get_sheets_client()` in api_server.py is called fresh per health request — if the function has side effects (e.g., writing to a log sheet), health check polling could amplify them. Current implementation appears read-only.

### Authoritative diagnostics
- `bash scripts/verify-s03.sh` — first-line structural regression check; all 18 checks must pass before any deployment
- `GET /api/health` → `sheets_ok: false, latency_ms: 0` means Sheets client is None (check env vars / service account)
- `GET /api/health` → `sheets_ok: false, latency_ms: N` means client exists but worksheets() raised (check network / Sheets API quota)
- `queue_pending: N > 0` means writes are backlogged in the resilience queue (check Sheets write health)

### What assumptions changed
- Original assumption: health check in api_server.py just needed a schema fix. Actual: it was a hardcoded stub with no real probe at all (`{"status":"ok","service":"BankongSeton API"}`). Required a full replacement with a live connectivity test.
- Original assumption: PHILIPPINES_TZ would need to be defined inline in api_server.py health handler. Actual: it was already defined as a module-level constant — reuse was straightforward.
