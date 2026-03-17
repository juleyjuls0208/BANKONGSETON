# S03: FraudDetector Constraint & Health Standardization — Research

**Date:** 2026-03-15

## Summary

S03 owns R016 (FraudDetector Worker Safety) and R018 (Health Check Standardization). Both are low-complexity changes to existing files — no new logic, no new dependencies. The health check update is the meatier task; the WEB_CONCURRENCY guard is ~5 lines.

**Critical finding:** The production WSGI entry point is `web_app.py` (via `backend/dashboard/wsgi.py`), not `admin_dashboard.py`. The S03 plan says "startup guard in `admin_dashboard.py`" but the guard that will actually fire for a gunicorn multi-worker deployment is the one in `web_app.py`. Both files need the guard. The health endpoint used in production is in `dashboard_core.py` (registered via `register_routes()`), not directly in `admin_dashboard.py`. **All four files require edits.**

The health check standardization requires replacing the current placeholder/HealthMonitor-based responses with a real Sheets ping that measures latency and returns the agreed schema `{status, sheets_ok, latency_ms, queue_pending, timestamp}` — 503 when unreachable.

## Recommendation

Make all changes surgically to the four files identified. Do NOT touch health.py or HealthMonitor — it's unnecessary for S03 and is already used for `/api/status` (detailed diagnostics). The S03 health endpoints return a simpler, standardized contract intended for load balancer / monitoring checks.

For the Sheets ping in `dashboard_core.py`: use the module-level `db` variable, but guard against `db is None` (it can be None if Sheets init fails at import time). Call `db.worksheets()` — a lightweight API call that verifies the spreadsheet is reachable. For `api_server.py`: same approach using the module-level `db`.

For `queue_pending` in `dashboard_core.py` / `admin_dashboard.py`: call `get_queue_status()['pending']` from `resilience.py` (already imported). For `api_server.py`: import `get_offline_queue` from `offline_queue.py` (not currently imported there, add a try/except import).

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Sheets ping | `db.worksheets()` | Minimal API call on the already-open spreadsheet object; no new auth needed |
| Queue pending count (admin) | `get_queue_status()` from resilience.py | Already imported in dashboard_core.py and admin_dashboard.py |
| Queue pending count (api) | `get_offline_queue().get_status()` from offline_queue.py | SQLiteWriteQueue.get_status() returns `{pending, failed, synced}` |
| Startup pattern | Existing guards in web_app.py (lines 53–80) | `logger.critical(…)` + `sys.exit(1)` is already the established pattern for startup aborts |

## Existing Code and Patterns

### Entry Points
- `backend/dashboard/wsgi.py` — PythonAnywhere WSGI config imports `from web_app import app as application`. Gunicorn uses this. **`web_app.py` is the real production entry point.**
- `backend/dashboard/web_app.py` — Deployed WSGI shim. Has three existing startup guards (FLASK_SECRET_KEY, JWT_SECRET, FINANCE_PASSWORD) at lines 53–80, each following the pattern `logger.critical(…); sys.exit(1)`. **WEB_CONCURRENCY guard goes here.**
- `backend/dashboard/admin_dashboard.py` — Local dev entry point. Has its own FLASK_SECRET_KEY guard at lines 59–66 using `print()` + `sys.exit(1)`. **WEB_CONCURRENCY guard goes here too.**

### Health Endpoints (current state)
- `backend/dashboard/dashboard_core.py:2951` — `register_routes()` defines `/api/health`. Currently calls `get_health_status()` and returns the full HealthMonitor dict, always 200. Does NOT do a live Sheets ping. **This is the admin health endpoint that matters for production.**
- `backend/dashboard/admin_dashboard.py:439` — Its own `/api/health` route. Same pattern as dashboard_core.py. Dead for production (web_app.py uses dashboard_core.py's health route). Should still be updated for consistency/local dev.
- `backend/api/api_server.py:192` — `/api/health` returns `{'status': 'ok', 'service': '…', 'version': '1.0.0'}` unconditionally. No Sheets ping, always 200. **Must be replaced with real check.**

### Sheets Clients
- `dashboard_core.py:131–157` — `get_sheets_client()` at module level; `db = get_sheets_client()` in a try/except that silently passes on failure, leaving `db = None`. Health check ping must guard `if db is None`.
- `api_server.py:76–92` — Same pattern: `get_sheets_client()` called at module level as `db = get_sheets_client()` (no try/except — can raise at startup). Health check should call `get_sheets_client()` directly to get a fresh client, not rely on the module-level `db` (since `db` might be stale or the client could have an expired token).
- `admin_dashboard.py:120–137` — Same `get_sheets_client()` pattern, `db = get_sheets_client()` at module level.

### Queue Status
- `backend/resilience.py:295` — `get_queue_status()` returns `{'pending': int, 'failed': int, 'processing': bool}` from an in-memory `queue.Queue`. Imported by both `dashboard_core.py` and `admin_dashboard.py`.
- `backend/offline_queue.py:107` — `SQLiteWriteQueue.get_status()` returns `{'pending': int, 'failed': int, 'synced': int, 'last_sync_at': …}`. Used by cashier_routes.py for offline queue management. **api_server.py does not currently import this.**
- `backend/offline_queue.py:22` — `_DEFAULT_DB_PATH` is `os.path.join(os.path.dirname(__file__), 'offline_queue.db')` — lives in `backend/`. api_server.py's sys.path already includes `backend/` via `sys.path.insert(0, …)` at line 27.

### FraudDetector State
- `backend/fraud_detection.py:726` — `get_fraud_detector()` returns module-level singleton `_fraud_detector`. Lives in `backend/`, not in the WSGI-deployed `web_app.py`. 
- `backend/dashboard/admin_dashboard.py:2324` — `_fraud_sheets_initialized` module-level bool; `_get_fraud_detector_with_sheets()` loads Sheets state lazily. This is the split-brain state.
- **Key insight:** `web_app.py` / `dashboard_core.py` do NOT import FraudDetector or define fraud routes. The split-brain risk is real but only affects `admin_dashboard.py` (local dev). The WEB_CONCURRENCY guard in `web_app.py` is still valuable as a forward-safe constraint if fraud routes are ever added to core.

### Startup Guard Pattern (web_app.py)
```python
# Established pattern from web_app.py lines 53–60:
if not _secret_key or _secret_key == _INSECURE_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_secret_key message=\"...\""
    )
    sys.exit(1)
```
The WEB_CONCURRENCY guard should follow this exact pattern.

## Constraints

- **No new dependencies** — all required modules are already in requirements. `offline_queue.py` is already in `backend/` and importable.
- **sys.path already set** — `api_server.py` does `sys.path.insert(0, …)` pointing to `backend/` at line 27; `offline_queue` is importable.
- **`db.worksheets()` does an API call** — expect 200–1500ms latency on PythonAnywhere; this is acceptable for a health check but should NOT be called on every request, only in the health endpoint.
- **gunicorn `WEB_CONCURRENCY` env var** — set automatically by gunicorn before forking workers. Reading it at module import time (not inside `if __name__ == '__main__':`) is the correct placement; the guard fires when gunicorn imports the WSGI module.
- **`GUNICORN_WORKERS`** — not set by gunicorn automatically (it's a custom convention). Include it per the S03 plan for explicit configuration support.
- **dashboard_core.py `db` can be None** — the module-level `db` init is wrapped in `try/except: pass`. Health ping must handle `if db is None` → sheets_ok=False, latency_ms=0.
- **timestamp format** — use `datetime.now(PHILIPPINES_TZ).isoformat()` to stay consistent with the rest of the codebase.

## Common Pitfalls

- **Wrong entry point** — adding the guard only to `admin_dashboard.py` and not `web_app.py` means it never fires for a real gunicorn deployment. Both must be updated.
- **Health check inside `if __name__ == '__main__':`** — the WEB_CONCURRENCY guard must be at module level (outside `__main__`), otherwise gunicorn won't trigger it.
- **HealthMonitor is NOT the right tool for S03 health** — `get_health_status()` returns a nested dict for `/api/status`-style deep diagnostics. The S03 `/api/health` contract is simpler and flatter. Calling `get_health_status()` in the new implementation would give the wrong shape.
- **Using `db.worksheets()` after stale client** — the `db` module-level client can have an expired auth token. If the health check uses the stale `db`, it may get auth errors that look like Sheets being down. For `api_server.py`, calling `get_sheets_client()` fresh in the health endpoint avoids this. For `dashboard_core.py`, using the existing `db` is fine since other endpoints use the same pattern.
- **503 vs 500** — return 503 (Service Unavailable) when Sheets is unreachable, NOT 500. 503 signals a transient infra issue; 500 implies a bug.
- **Importing offline_queue in api_server.py** — wrap in try/except import at module level (like nfc_payments is already wrapped), so a missing sqlite3 (unlikely) doesn't crash the server.
- **Int conversion for WEB_CONCURRENCY** — `os.environ.get('WEB_CONCURRENCY', '1')` returns a string; must convert to int before comparing. An empty string or non-numeric value should default to 1 (use try/except around `int()`).

## Open Risks

- **`db.worksheets()` timeout** — gspread doesn't expose a network timeout by default; a hung Sheets connection could make the health endpoint block for 30+ seconds. Mitigation: the health check will still eventually resolve (or the process will restart). Not worth adding threading/signal timeout complexity for S03.
- **admin_dashboard.py health route is redundant** — since `web_app.py` uses `dashboard_core.py`'s health route, the health route in `admin_dashboard.py` (line 439) is only reachable in local dev. Still update it to match the standardized shape so local dev behavior is consistent with production.
- **WEB_CONCURRENCY=1 on PythonAnywhere** — PythonAnywhere always uses single-worker per WSGI app in practice; the guard will never actually fire in production. Its value is as a defensive constraint against accidental misconfig.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Flask (health endpoints) | No specific skill needed | installed (fullstack-developer covers it) |
| gspread | No skill needed | n/a |

## Sources

- Entry point architecture (source: `backend/dashboard/wsgi.py` + `web_app.py` — wsgi.py imports from web_app, not admin_dashboard)
- Startup guard pattern (source: `web_app.py` lines 53–80 — logger.critical + sys.exit(1))
- HealthMonitor response shape (source: `backend/health.py:44–63` — nested structure, wrong shape for S03 contract)
- Queue status APIs (source: `backend/resilience.py:228–234`, `backend/offline_queue.py:107–129`)
- Dashboard core health route (source: `backend/dashboard/dashboard_core.py:2951–2958` — this is what web_app.py actually serves)
- Sheets client pattern (source: `dashboard_core.py:131–157`, `api_server.py:76–92`)
