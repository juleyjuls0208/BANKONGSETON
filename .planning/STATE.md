# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app
**Current focus:** Phase 1 - Critical Fixes + Security

## Current Position

Phase: 1 of 6 (Critical Fixes + Security)
Plan: 3 of 3 completed in current phase
Status: Phase 1 plan 03 complete
Last activity: 2026-02-26 — Executed 01-03-PLAN.md: empty-credential guard, test secret cleanup, wsgi.py hardening

Progress: [##########] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 1-2min
- Total execution time: 0.05 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-critical-fixes-security | 3 | 5min | 2min |

**Recent Trend:**
- Last 5 plans: 01-01 (2min), 01-03 (1min)
- Trend: -

*Updated after each plan completion*
| Phase 01-critical-fixes-security P02 | 2min | 1 tasks | 2 files |
| Phase 01-critical-fixes-security P04 | 2min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Fix backend first — cashier POS is broken; security holes must be closed before adding features
- [Init]: Keep Google Sheets as database — no SQL migration
- [Init]: NFC: architect backend now, Android implementation is v2
- [Init]: Documentation as Markdown in /docs/ so system can be explained to peers
- [01-01]: Startup guard at module level (not __main__) so it fires on import too
- [01-01]: CORS dev-mode auto-allows localhost origins when FLASK_ENV=development or CORS_ORIGINS is empty
- [01-01]: Used plain print() for redacted startup messages since get_logger import can fail
- [01-03]: Field-specific 400 errors for empty username/password (not a single generic error)
- [01-03]: and admin_user truthy check appended to credential comparison (not separate block)
- [01-03]: Test credentials use obviously-fake strings not env vars (tests run against live server)
- [01-03]: wsgi.py retains only GOOGLE_SHEETS_ID/GOOGLE_CREDENTIALS_FILE as non-secret defaults
- [Phase 01-02]: Used /cashier/api/products (JWT-protected) instead of /api/products/list (admin session required) to avoid auth mismatch
- [Phase 01-02]: Added /cashier/api/logout route (missing from cashier_routes.py, called by template logout button)

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Phase 1: Cashier POS products bug root cause not yet confirmed~~ RESOLVED in 01-02: added /cashier/api/products and /cashier/api/logout routes
- ~~Phase 1: Empty credential login (admin_dashboard.py line 221) appears intentional; needs user decision on replacement strategy~~ RESOLVED in 01-03
- Phase 2: QUAL-05 (oauth2client -> google-auth) may require credential file format change — verify before executing
- Phase 4: Push notifications require FCM setup; check if Android app already has FCM dependency before planning

## Session Continuity

Last session: 2026-02-26
Stopped at: Completed 01-03-PLAN.md (empty-credential guard, test secrets cleanup, wsgi.py hardening).
Resume file: None
