---
phase: 08-security-reliability-fixes
plan: 02
subsystem: api
tags: [gspread, flask, cashier, google-sheets, resilience]

# Dependency graph
requires:
  - phase: 07.1-web-deployable-dashboard
    provides: cashier_routes.py with _get_parent_app_module() helper
provides:
  - ensure_products_sheet() auto-creates Products sheet with canonical headers on first access
  - get_worksheet_with_retry() retry helper for cashier blueprint using _get_parent_app_module()
  - Cashier GET /cashier/api/products no longer returns 503 when Products sheet is absent
affects: [cashier-pos, products-sheet, reliability]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ensure_products_sheet pattern: check worksheet, create with canonical headers on WorksheetNotFound"
    - "Cashier-safe retry: use _get_parent_app_module().get_sheets_client() instead of global db"

key-files:
  created: []
  modified:
    - backend/dashboard/cashier/cashier_routes.py

key-decisions:
  - "No global db in cashier helpers — cashier_routes.py has no module-level db variable; use _get_parent_app_module().get_sheets_client() instead"
  - "import time as _time inside get_worksheet_with_retry body — consistent with lazy-load sys.path.insert pattern in this codebase"
  - "Used _db (not db) as local variable in helpers to avoid confusion with any outer scope db name"

patterns-established:
  - "ensure_products_sheet pattern: mirrors admin_dashboard.py but adapted for blueprint context without global db"

requirements-completed: [PROD-04, PROD-05]

# Metrics
duration: 1min
completed: 2026-03-01
---

# Phase 08 Plan 02: Cashier ensure_products_sheet Resilience Summary

**`ensure_products_sheet()` added to cashier_routes.py — auto-creates Products sheet on first access, eliminating 503 errors when sheet is absent**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-01T15:05:25Z
- **Completed:** 2026-03-01T15:06:17Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `get_worksheet_with_retry()` helper to cashier_routes.py using `_get_parent_app_module().get_sheets_client()` (no global db)
- Added `ensure_products_sheet()` that handles `gspread.exceptions.WorksheetNotFound` by auto-creating the sheet with canonical headers `['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']`
- Replaced 3-line `db.worksheet('Products')` block in `get_products()` with single `ensure_products_sheet()` call
- Closes PROD-04 (cashier POS no longer 503s when Products sheet absent) and PROD-05 (Products sheet auto-created with canonical headers)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add get_worksheet_with_retry() and ensure_products_sheet() to cashier_routes.py; replace line 176** - `21cd1c9` (fix)

**Plan metadata:** _(docs commit pending)_

## Files Created/Modified
- `backend/dashboard/cashier/cashier_routes.py` - Added two new helper functions after `_get_parent_app_module()`; replaced direct `db.worksheet('Products')` call with `ensure_products_sheet()`

## Decisions Made
- No `global db` used in cashier helpers — cashier_routes.py has no module-level `db` variable; all Sheets access goes through `_get_parent_app_module().get_sheets_client()`
- Used `_db` (not `db`) as local variable name in helpers to avoid confusion with outer scope
- `import time as _time` inside function body — consistent with lazy-load sys.path.insert pattern already in this codebase

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both PROD-04 and PROD-05 requirements closed
- Cashier POS `/api/products` endpoint is now resilient to missing Products sheet
- Phase 08 has 2 plans; 08-01 still has no SUMMARY — ready to execute 08-01

---
*Phase: 08-security-reliability-fixes*
*Completed: 2026-03-01*

## Self-Check: PASSED

- `backend/dashboard/cashier/cashier_routes.py` — FOUND on disk
- `08-02-SUMMARY.md` — FOUND on disk
- Commit `21cd1c9` — FOUND in git log
- All 6 verification checks PASS (syntax valid, helpers defined, no global db, direct call replaced, ensure_products_sheet called, canonical headers present)
