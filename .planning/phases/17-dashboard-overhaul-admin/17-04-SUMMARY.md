---
phase: 17-dashboard-overhaul-admin
plan: "04"
subsystem: ui
tags: [flask, jinja2, gspread, bootstrap, admin, topup, balance]

# Dependency graph
requires:
  - phase: 17-01
    provides: base.html template, @admin_only decorator, students.html skeleton
provides:
  - POST /api/admin/topup endpoint (admin-only, resolves student_id -> money card -> updates balance)
  - Admin-only top-up modal on students.html with per-row and page-level trigger buttons
affects: [17-dashboard-overhaul-admin, transactions, balance-management]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Admin-only route: @login_required + @admin_only decorators stacked"
    - "Student ID resolution pattern: Users sheet lookup -> money_card -> Money Accounts"
    - "Non-fatal transaction log: try/except around append_row, balance update is primary"
    - "Jinja2 IS_ADMIN JS injection: {{ 'true' if role == 'admin' else 'false' }} for client-side conditional rendering"

key-files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/templates/students.html

key-decisions:
  - "Replicated load_balance logic inline in admin_topup (not calling it) — load_balance reads request.json directly making it uncallable without an active request context"
  - "Transaction log failure is non-fatal — balance update succeeds even if Transactions Log append fails"
  - "IS_ADMIN Jinja2 variable injected into JS to conditionally render Actions column header and per-row buttons without duplicate template blocks"
  - "loadStudents() called after successful top-up to refresh the table with updated balances"

patterns-established:
  - "Admin-only endpoints: always stack @login_required then @admin_only"
  - "Student lookup: iterate Users sheet records, match on str(u.get('StudentID','')).strip()"

requirements-completed: [DASH-04]

# Metrics
duration: 5min
completed: 2026-03-05
---

# Phase 17 Plan 04: Admin Balance Top-Up Summary

**Admin-only POST /api/admin/topup endpoint + Bootstrap modal on students.html with per-row Top Up buttons that resolve student_id to money card and write a Load transaction to Google Sheets**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-05T00:00:00Z
- **Completed:** 2026-03-05T00:05:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- New `POST /api/admin/topup` route behind `@login_required` + `@admin_only`; accepts `{student_id, amount}`, validates both, resolves money card via Users sheet, updates Money Accounts balance + TotalLoaded + LastUpdated, writes a Load transaction row
- Admin-only "Top Up Balance" page header button + Bootstrap modal with inline feedback on `students.html`
- Per-row "Top Up" buttons in student table that pre-fill the modal with the student's ID; table auto-refreshes on success

## Task Commits

Each task was committed atomically:

1. **Task 1: Add /api/admin/topup endpoint** - `87b9229` (feat)
2. **Task 2: Add top-up modal to students.html** - `99c70ad` (feat)

**Plan metadata:** `(pending)` (docs: complete plan)

## Files Created/Modified

- `backend/dashboard/admin_dashboard.py` - Added `admin_topup()` route (112 lines) after `load_balance()`
- `backend/dashboard/templates/students.html` - Added admin top-up button, modal, JS fetch handler, per-row buttons

## Decisions Made

- Replicated `load_balance` logic inline rather than calling it — `load_balance` reads `request.json()` directly making internal calls impossible without an active request context
- Transaction log failure is non-fatal — the try/except around `append_row` ensures balance updates succeed even if Transactions Log is temporarily unavailable
- `IS_ADMIN` Jinja2 variable injected into JS (`{{ 'true' if role == 'admin' else 'false' }}`) to conditionally add the Actions column and per-row buttons without duplicating template blocks
- `loadStudents()` called post-success so the table immediately reflects the new balance

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DASH-04 complete — admin can manually top up student balances from the web dashboard
- Ready for 17-05 (next plan in phase)

---
*Phase: 17-dashboard-overhaul-admin*
*Completed: 2026-03-05*
