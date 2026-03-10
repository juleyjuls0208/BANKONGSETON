---
phase: 31
plan: 05
subsystem: dashboard-backend
tags: [refactor, extraction, dashboard-core, web-app, admin-dashboard]
dependency_graph:
  requires: [31-01, 31-02, 31-03, 31-04]
  provides: [dashboard_core.py, slim-shims]
  affects: [web_app.py, admin_dashboard.py, wsgi.py, cashier_routes.py]
tech_stack:
  added: [dashboard_core.py]
  patterns: [register_routes factory, shim pattern, module-level re-export]
key_files:
  created:
    - backend/dashboard/dashboard_core.py
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/web_app.py
decisions:
  - "register_routes(app, socketio) factory: all shared routes defined as nested closures inside register_routes, both shims call it post-app-creation"
  - "db = get_sheets_client() at module level in both shims for cashier blueprint compatibility"
  - "Startup guards (FLASK_SECRET_KEY, JWT_SECRET, FINANCE_PASSWORD) stay in shims, not in core"
  - "web_app.py dashboard() route imports get_worksheet_with_retry from dashboard_core at call time (avoids top-level import cycle risk)"
metrics:
  duration: "~3 hours (multi-session)"
  completed: "2026-03-10T07:03:19Z"
  tasks_completed: 3
  files_modified: 3
  files_created: 1
---

# Phase 31 Plan 05: Dashboard Core Extraction Summary

**One-liner:** Extracted ~90% shared logic from two 2884–3320 line files into `dashboard_core.py`, leaving both `admin_dashboard.py` (~622 lines) and `web_app.py` (~230 lines) as thin deployment shims.

## What Was Built

### `dashboard_core.py` (~2940 lines)
The single source of truth for all shared dashboard logic:
- Google Sheets client (`get_sheets_client`, `get_worksheet_with_retry`, `_invalidate_cache`)
- Helper functions (`get_philippines_time`, `get_cors_origins`, `ensure_products_sheet`, `ensure_settings_sheet`)
- Auth decorators (`login_required`, `admin_only`, `desktop_features`)
- `register_routes(app, socketio)` factory — defines and registers ~60 shared routes as closures

### `admin_dashboard.py` (622 lines, was 3320)
Shim retains:
- Startup guards: `FLASK_SECRET_KEY`, `JWT_SECRET`, `FINANCE_PASSWORD`, `CASHIER_USERNAME/PASSWORD`
- `app = Flask(__name__)`, CORS, socketio, cashier blueprint
- `db = get_sheets_client()` module-level
- Shim-specific routes: `index`, `login` (with parent role path), `dashboard` (with hardware support), `students_page`, `products_page`, `transactions_page`, `finance_page`, `parents_page`
- Arduino hardware routes (`start_serial`, `disconnect_serial`, etc.)
- `__main__` block on port 5001

### `web_app.py` (230 lines, was 2884)
Shim retains:
- Startup guards: `FLASK_SECRET_KEY`, `JWT_SECRET`, `FINANCE_PASSWORD` (no cashier guard)
- `ARDUINO_API_KEY`, `UID_PATTERN`
- `app = Flask(__name__)`, CORS, socketio, cashier blueprint
- `db = get_sheets_client()` module-level
- Shim-specific routes: `index`, `login` (admin + finance only, no parent path), `dashboard` (`arduino_available=False`), `students_page`, `products_page`, `transactions_page`
- `arduino_card_read` WiFi endpoint
- `__main__` block on port 5003

## Decisions Made

1. **`register_routes` factory pattern** — all shared route functions are nested closures, registered onto the passed `app`. This avoids global state and circular imports.
2. **`db = get_sheets_client()` in both shims** — `cashier_routes.py` accesses `get_sheets_client` from the parent module namespace; re-exporting it plus initializing `db` at module level preserves this contract.
3. **Startup guards stay in shims** — `dashboard_core.py` is import-safe; it does not call `sys.exit`. Each shim enforces its own startup security requirements.
4. **`wsgi.py` untouched** — `from web_app import app as application` continues to work without any changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Added `_invalidate_cache` to `dashboard_core.py`**
- **Found during:** Task 2 (admin_dashboard.py shim writing)
- **Issue:** `admin_dashboard.py` shim imported `_invalidate_cache` but it was missing from initial `dashboard_core.py`
- **Fix:** Added `_invalidate_cache` function using `_sheets_cache` dict after `get_worksheet_with_retry`
- **Files modified:** `backend/dashboard/dashboard_core.py`
- **Commit:** 447abd8

**2. [Rule 2 - Missing] Added `ensure_products_sheet` to `dashboard_core.py`**
- **Found during:** Task 2 (route migration)
- **Issue:** Products routes in core called `ensure_products_sheet()` but it wasn't defined in core
- **Fix:** Added `ensure_products_sheet()` before `ensure_settings_sheet()`
- **Files modified:** `backend/dashboard/dashboard_core.py`
- **Commit:** 447abd8

**3. [Rule 2 - Missing] Added ~20 routes to `dashboard_core.py`**
- **Found during:** Task 1 audit
- **Issue:** Initial audit revealed products, analytics, exports, stats, and void routes were in `web_app.py` but not yet in `dashboard_core.py`
- **Fix:** Added all missing route sections before the health/status section in `register_routes`
- **Files modified:** `backend/dashboard/dashboard_core.py`
- **Commit:** 447abd8

## Smoke Test Results

```
SYNTAX OK: dashboard_core.py
SYNTAX OK: admin_dashboard.py
SYNTAX OK: web_app.py

OK: register_routes
OK: get_sheets_client
OK: get_cors_origins
OK: get_philippines_time
OK: _invalidate_cache
OK: get_worksheet_with_retry
```

Startup guards correctly abort without credentials (expected behavior — not a test failure).

## Self-Check: PASSED

- `backend/dashboard/dashboard_core.py` — created ✅
- `backend/dashboard/admin_dashboard.py` — modified ✅  
- `backend/dashboard/web_app.py` — modified ✅
- Commit `447abd8` (feat) — exists ✅
- Commit `9c8c534` (test) — exists ✅
