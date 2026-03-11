---
phase: 01-critical-fixes-security
plan: 03
subsystem: auth
tags: [flask, security, credentials, admin-login, wsgi]

# Dependency graph
requires:
  - phase: 01-critical-fixes-security
    provides: startup hardening (secret key guard, CORS restriction) from plan 01
provides:
  - Empty-credential guard on admin login route (BUG-04)
  - Admin login requires admin_user to be truthy (blank env var blocked)
  - Test files use obviously-fake placeholder credentials (SEC-05)
  - wsgi.py no longer sets any secrets in os.environ
affects: [01-critical-fixes-security, deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Empty-credential guard before credential comparison in login routes"
    - "wsgi.py sets only non-secret config defaults; all secrets via .env or hosting dashboard"

key-files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/wsgi.py
    - backend/test_phase1.py
    - backend/test_phase3.py

key-decisions:
  - "Show field-specific 400 errors for empty username vs empty password submissions"
  - "Use and admin_user truthy check in comparison to block blank env vars matching blank input"
  - "Use obviously-fake placeholder strings in tests (not env vars) since tests run against live server with requests library"
  - "wsgi.py keeps only GOOGLE_SHEETS_ID and GOOGLE_CREDENTIALS_FILE as non-secret defaults"

patterns-established:
  - "Empty-credential guard: if not username / if not password before any credential comparison"
  - "wsgi.py must never set secret values in os.environ"

requirements-completed: [BUG-04, SEC-05]

# Metrics
duration: 1min
completed: 2026-02-26
---

# Phase 01 Plan 03: Empty Credential Guard, Test Secret Cleanup, and wsgi.py Hardening Summary

**Admin login hardened with field-specific 400 errors for empty credentials and truthy check on admin_user; wsgi.py secrets removed; test files use obviously-fake placeholder credentials**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-26T08:53:25Z
- **Completed:** 2026-02-26T08:54:26Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added empty-credential guard to admin login: empty username or password returns 400 with specific field error
- Added `and admin_user` to admin credential comparison preventing blank env vars from granting login
- Replaced hardcoded `admin2025`/`admindashboard` credentials in test_phase3.py with `test-admin-do-not-use`/`test-password-do-not-use`
- Replaced `test-secret-key` JWT secret in test_phase1.py with `test-secret-key-do-not-use-in-production`
- Removed all hardcoded secrets from wsgi.py (SECRET_KEY, FLASK_SECRET_KEY, FINANCE_PASSWORD, ADMIN_PASSWORD, ARDUINO_API_KEY)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add empty-credential guard to admin login route** - `34550a7` (fix) *(prior commit)*
2. **Task 2: Replace hardcoded test secrets and fix wsgi.py** - `6b0db93` (fix)

**Plan metadata:** *(pending docs commit)*

## Files Created/Modified
- `backend/dashboard/admin_dashboard.py` - Empty-credential guard + `and admin_user` truthy check in login route
- `backend/dashboard/wsgi.py` - Removed all hardcoded secrets; kept only non-secret GOOGLE_SHEETS_ID and GOOGLE_CREDENTIALS_FILE
- `backend/test_phase1.py` - JWT_SECRET updated to `test-secret-key-do-not-use-in-production`
- `backend/test_phase3.py` - All admin/cashier credentials replaced with obviously-fake placeholders

## Decisions Made
- Field-specific error messages: "Username cannot be empty" vs "Password cannot be empty" — per user's locked decision in CONTEXT.md
- `and admin_user` appended to credential comparison (not `or` / separate block) — keeps login check atomic and self-documenting
- Obviously-fake strings chosen over env vars for test credentials — these tests use `requests` against a live server, so env vars would add setup complexity without meaningful security benefit for a test script
- wsgi.py retains GOOGLE_SHEETS_ID as a non-secret config default (sheet ID is not a credential)

## Deviations from Plan

### Auto-fixed Issues

**1. [Note] Task 1 was already committed prior to this execution run**
- The `admin_dashboard.py` changes (empty-credential guard + `and admin_user`) were already committed as `34550a7 fix(01-03): add empty-credential guard to admin login route` before this execution.
- Verification confirmed the changes were correct and complete.
- Task 2 (test secrets + wsgi.py) was the remaining work.

---

**Total deviations:** 0 auto-fixes needed. Task 1 was pre-committed; Task 2 executed cleanly.
**Impact on plan:** No scope changes. All plan requirements met.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BUG-04 (empty credential login) and SEC-05 (hardcoded test secrets) are both closed
- wsgi.py is clean for deployment — all secrets must now be configured via .env or PythonAnywhere dashboard
- Remaining plan 04+ requirements can proceed

---
*Phase: 01-critical-fixes-security*
*Completed: 2026-02-26*
