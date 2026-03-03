---
phase: 08-security-reliability-fixes
plan: 01
subsystem: security
tags: [jwt, websocket, flask, python, exception-handling, startup-guard]

# Dependency graph
requires:
  - phase: 01-critical-fixes-security
    provides: FLASK_SECRET_KEY startup guard pattern in admin_dashboard.py
provides:
  - JWT_SECRET startup guard in api_server.py (sys.exit(1) on missing/empty secret)
  - Sanitized WebSocket card_error emissions (generic message, not raw exception text)
  - Full traceback logging server-side for all 4 card error handlers
affects:
  - 08-security-reliability-fixes
  - any future backend deployment (JWT_SECRET must be set in .env)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Startup guard: check env var with .strip(), sys.exit(1) on empty/missing (matches admin_dashboard.py FLASK_SECRET_KEY pattern)"
    - "Exception sanitization: log full traceback with exc_info=True server-side, emit only generic message to WebSocket clients"

key-files:
  created: []
  modified:
    - backend/api/api_server.py
    - backend/dashboard/admin_dashboard.py

key-decisions:
  - "JWT_SECRET guard blocks empty/missing only (no insecure-default check) — CONTEXT.md locked decision"
  - "random fallback (secrets.token_urlsafe) removed — silently bypassed guard and broke JWT verification across restarts"
  - "em dash (—) used in generic card_error message per CONTEXT.md decision (not double-hyphen)"
  - "exc_info=True added only to card_read_error (the one location that was missing it); other 3 already had it"

patterns-established:
  - "Startup guard pattern: os.getenv('KEY', '').strip() → if not KEY: logger.critical(...) → sys.exit(1)"
  - "WebSocket exception sanitization: emit generic message to client, log full traceback with exc_info=True server-side"

requirements-completed: [SEC-02, QUAL-01]

# Metrics
duration: 1min
completed: 2026-03-01
---

# Phase 8 Plan 01: Security Fixes — JWT Guard and WebSocket Exception Sanitization Summary

**JWT_SECRET startup guard added to api_server.py (sys.exit(1) on empty/missing) and all 4 WebSocket card_error handlers sanitized to emit generic messages with full tracebacks logged server-side**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-01T15:05:22Z
- **Completed:** 2026-03-01T15:07:11Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `api_server.py` now refuses to start if `JWT_SECRET` is unset or empty (mirrors FLASK_SECRET_KEY guard in admin_dashboard.py — closes SEC-02)
- Removed `secrets.token_urlsafe(32)` random fallback that silently bypassed the guard and would break JWT verification across restarts
- All 4 `socketio.emit('card_error', {'message': str(e)})` calls replaced with generic `'Card scan failed — please try again'` (closes QUAL-01)
- Added missing `exc_info=True` to the `card_read_error` logger call (the only one of the 4 that was missing it)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add JWT_SECRET startup guard to api_server.py** - `97ed7ac` (fix)
2. **Task 2: Fix 4 WebSocket exception text leaks in admin_dashboard.py** - `01dde78` (fix)

**Plan metadata:** *(docs commit to follow)*

## Files Created/Modified

- `backend/api/api_server.py` — JWT_SECRET startup guard replaces random-fallback assignment; server hard-fails with `event=startup_aborted reason=missing_jwt_secret` if secret is absent
- `backend/dashboard/admin_dashboard.py` — 4 card_error WebSocket emits sanitized; `exc_info=True` added to card_read_error logger call

## Decisions Made

- `JWT_SECRET` guard checks empty/missing only (not insecure-default) — per locked CONTEXT.md decision "Block empty/missing only"
- Removed `secrets.token_urlsafe(32)` fallback — this silently bypassed the guard on every restart, making JWT tokens non-reproducible between server restarts
- Used em dash (—) not double-hyphen (--) in the generic client message — per CONTEXT.md decision
- Only added `exc_info=True` to the one card_read_error handler that was missing it; the other 3 already had it

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unicode escape written as literal string in Edit tool**
- **Found during:** Task 2 (fixing card_error emits)
- **Issue:** Edit tool wrote `\u2014` as literal 6-char string instead of actual em dash character (—)
- **Fix:** Re-applied edits using the actual em dash character (—) via replaceAll
- **Files modified:** backend/dashboard/admin_dashboard.py
- **Verification:** `python -c "...src.count('Card scan failed \u2014 please try again')..."` returned 4
- **Committed in:** `01dde78` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — unicode escape encoding issue)  
**Impact on plan:** Minimal; only the em dash encoding required a re-edit. No scope creep.

## Issues Encountered

None — both tasks completed without any blocking issues.

## User Setup Required

None — no external service configuration required. However, `JWT_SECRET` must now be set in `.env` for `api_server.py` to start. Existing deployments that relied on the random fallback will fail to start until `JWT_SECRET` is explicitly configured.

## Next Phase Readiness

- SEC-02 and QUAL-01 closed
- Ready for 08-02 (next plan in phase 08-security-reliability-fixes)
- Note: `JWT_SECRET` must be populated in `.env` before running api_server.py

---
*Phase: 08-security-reliability-fixes*  
*Completed: 2026-03-01*
