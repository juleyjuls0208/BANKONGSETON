---
phase: 01-critical-fixes-security
plan: 02
subsystem: ui
tags: [flask, jinja2, javascript, websocket, socket.io, rfid, pos]

# Dependency graph
requires: []
provides:
  - Cashier POS template as a single valid HTML document
  - /cashier/api/products JWT-authenticated endpoint
  - /cashier/api/logout endpoint
affects:
  - cashier POS functionality
  - product grid loading
  - checkout flow

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cashier blueprint uses JWT auth for all API routes including product fetching"
    - "Products fetched from same-server dashboard (port 5003), not cross-origin mobile API (port 5001)"

key-files:
  created: []
  modified:
    - backend/dashboard/cashier/cashier_routes.py
    - backend/dashboard/cashier/templates/cashier_index.html

key-decisions:
  - "Used /cashier/api/products (JWT-protected cashier route) instead of /api/products/list (admin session required) - avoids auth mismatch between cashier JWT and admin Flask session"
  - "Added /cashier/api/logout route (was missing but called by template) to clear JWT cookie"

patterns-established:
  - "Cashier blueprint self-contains all its API routes with JWT auth"

requirements-completed:
  - BUG-01

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 1 Plan 02: Cashier POS Template Fix Summary

**Added missing /cashier/api/products and /cashier/api/logout routes so the cashier POS template can load products and log out correctly**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T08:54:12Z
- **Completed:** 2026-02-26T08:56:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Verified cashier_index.html was already a single clean HTML document (template corruption described in research had already been fixed)
- Added JWT-authenticated `/cashier/api/products` route to cashier blueprint - fetches from Google Sheets, returns id/name/category/price/active fields
- Added `/cashier/api/logout` route that deletes the JWT cookie
- All 5 verification checks pass: single HTML doc, correct endpoint, socket.io before initWebSocket, one loadProducts function, one renderProducts function

## Task Commits

Each task was committed atomically:

1. **Task 1: Add missing cashier API routes and verify clean template** - `4118597` (fix)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `backend/dashboard/cashier/cashier_routes.py` - Added get_products() and api_logout() routes
- `backend/dashboard/cashier/templates/cashier_index.html` - Staged as-is (already clean)

## Decisions Made
- Used `/cashier/api/products` rather than `/api/products/list`: the plan allows either (per must_haves: `/api/products/list or /cashier/api/products`). `/api/products/list` uses `@login_required` which checks for `admin_logged_in` in the Flask session — cashier users authenticate with JWT tokens, not admin sessions. Calling `/api/products/list` from the cashier would redirect to the admin login page. Creating a dedicated cashier route with JWT auth is the correct architectural choice.
- Added `/cashier/api/logout` (Rule 2 - Missing Critical): the template calls this endpoint but it was missing from cashier_routes.py. Without it, the Logout button silently fails.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added /cashier/api/logout route**
- **Found during:** Task 1 (reviewing all template API calls)
- **Issue:** Template calls `/cashier/api/logout` via `fetch('/cashier/api/logout', {method: 'POST'})` but the route did not exist in cashier_routes.py — logout button would silently fail
- **Fix:** Added `api_logout()` route that deletes the `jwt_token` cookie
- **Files modified:** backend/dashboard/cashier/cashier_routes.py
- **Verification:** Route present in `grep cashier_bp.route` output
- **Committed in:** 4118597 (Task 1 commit)

**2. [Rule 1 - Architectural Note] Endpoint changed from /api/products/list to /cashier/api/products**
- **Found during:** Task 1 (auth analysis)
- **Issue:** Plan specified `/api/products/list` but that route uses `@login_required` (admin Flask session), incompatible with cashier JWT auth
- **Fix:** Created `/cashier/api/products` with `@jwt_required` matching the cashier's auth scheme; the plan's must_haves explicitly permits `/cashier/api/products`
- **Files modified:** backend/dashboard/cashier/cashier_routes.py
- **Verification:** Python syntax check OK; route present in grep output
- **Committed in:** 4118597 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 auth-driven route choice)
**Impact on plan:** Both fixes necessary for correct operation. No scope creep.

## Issues Encountered
- The template corruption described in the research (HTML tags inside JS function bodies) had already been fixed before this plan executed. The current file was already a clean single HTML document. The primary work shifted to adding the missing backend routes that the template required.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BUG-01 (cashier POS blank screen) resolved: template is clean, products endpoint exists with JWT auth
- Remaining Phase 1 requirements: BUG-02 (null card UID), BUG-03 (Sheets graceful errors), BUG-05 (transaction atomicity), SEC-04 (card UID validation), SEC-05 (test file secrets)
- Plans 03+ address remaining requirements

## Self-Check

### Files Exist
- `backend/dashboard/cashier/cashier_routes.py` - FOUND (verified by git status + grep)
- `backend/dashboard/cashier/templates/cashier_index.html` - FOUND (verified by python open())

### Commits Exist
- `4118597` - FOUND (fix(01-02): add missing cashier API routes and verify clean template)

## Self-Check: PASSED

---
*Phase: 01-critical-fixes-security*
*Completed: 2026-02-26*
