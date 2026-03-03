---
phase: 04-student-app-notifications
plan: 03
subsystem: api
tags: [flask, gspread, google-sheets, settings, notifications]

# Dependency graph
requires:
  - phase: 04-student-app-notifications
    provides: admin_dashboard.py Flask app with gspread db global and @login_required decorator
provides:
  - GET /api/settings/threshold route returning low_balance_threshold from Settings sheet
  - POST /api/settings/threshold route upserting low_balance_threshold in Settings sheet
  - ensure_settings_sheet() auto-creates Settings sheet if absent
  - Admin UI card in dashboard.html for viewing and saving threshold value
affects: [04-student-app-notifications]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ensure_settings_sheet() mirrors ensure_products_sheet() pattern — auto-create sheet with headers on first access
    - Upsert pattern for Google Sheets rows (scan for existing row, update B-cell or append_row)
    - env fallback: float(os.getenv('LOW_BALANCE_THRESHOLD', 50)) used when sheet row absent

key-files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/templates/dashboard.html

key-decisions:
  - "Settings stored in Google Sheets 'Settings' sheet with Key/Value columns — no new DB table needed"
  - "Upsert approach: scan records for existing row (start=2 for header skip), update B-cell if found, append_row if not"
  - "Env fallback LOW_BALANCE_THRESHOLD=50 used for GET when sheet row not yet set"

patterns-established:
  - "ensure_settings_sheet(): create sheet with header row if not found — mirrors ensure_products_sheet()"
  - "Settings sheet Key/Value schema: Key column stores setting name, Value column stores value"

requirements-completed: [NOTF-02]

# Metrics
duration: ~30min
completed: 2026-02-26
---

# Phase 4 Plan 03: Admin-Configurable Low-Balance Threshold Summary

**GET/POST /api/settings/threshold routes backed by a Google Sheets Settings sheet, with admin UI card in dashboard.html for real-time threshold configuration**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-02-26
- **Completed:** 2026-02-26T14:20:32Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `ensure_settings_sheet()`, `get_threshold()`, `set_threshold()` to `admin_dashboard.py`
- GET `/api/settings/threshold` returns value from Settings sheet with env fallback (default 50)
- POST `/api/settings/threshold` upserts the threshold row (creates Settings sheet if absent)
- "Notification Settings" card added to `dashboard.html` with numeric input, Save button, and inline feedback
- JavaScript `loadThreshold()` / `saveThreshold()` auto-loads on page open and saves via fetch

## Task Commits

Each task was committed atomically:

1. **Task 1: Add GET/POST /api/settings/threshold routes** - `1674332` (feat)
2. **Task 2: Add threshold settings UI to dashboard.html** - `dd6d4b5` (feat)

## Files Created/Modified
- `backend/dashboard/admin_dashboard.py` - Added ensure_settings_sheet(), get_threshold(), set_threshold() before SOCKET.IO EVENTS section
- `backend/dashboard/templates/dashboard.html` - Added Notification Settings card (HTML + JS) before </body>

## Decisions Made
- Settings stored in Google Sheets "Settings" sheet with Key/Value columns — no new DB table needed, consistent with existing gspread approach
- Upsert logic: scan all records with `enumerate(records, start=2)` to skip header row, update B-cell if row found, `append_row` otherwise
- Env fallback `LOW_BALANCE_THRESHOLD=50` used for GET when sheet row not yet set — safe default

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- dashboard.html file must be opened with `encoding='utf-8'` on Windows due to Thai Baht symbol `฿` in label text (pre-existing file encoding). Handled by always using `encoding='utf-8'` in Python verification scripts.

## User Setup Required
None - no external service configuration required. The Settings sheet is auto-created on first use.

## Next Phase Readiness
- NOTF-02 complete: admin can now set the global low-balance threshold via the dashboard
- The threshold value is available via GET `/api/settings/threshold` for use by push notification logic in subsequent plans
- No blockers

---
*Phase: 04-student-app-notifications*
*Completed: 2026-02-26*
