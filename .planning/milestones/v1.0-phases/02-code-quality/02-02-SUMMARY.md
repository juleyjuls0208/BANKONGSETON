---
phase: 02-code-quality
plan: 02
subsystem: logging
tags: [logging, python, dead-code, archiving, structured-logging, key-value]

# Dependency graph
requires:
  - phase: 01-critical-fixes-security
    provides: errors.py base module with BankoError, ErrorCode, get_logger
provides:
  - "Console-only key=value structured logging via setup_logging() in backend/errors.py"
  - "_archive/ directory at repo root with legacy dead code preserved"
affects: [03-logging-cleanup, 04-print-replacement]

# Tech tracking
tech-stack:
  added: []
  patterns: ["key=value structured log format: level=%(levelname)s logger=%(name)s %(message)s", "console-only logging with logger.propagate=False"]

key-files:
  created: ["_archive/web_app_complete.py", "_archive/mobile/BankongSetonApp/"]
  modified: ["backend/errors.py"]

key-decisions:
  - "Removed log_dir parameter entirely (no callers passed it — config_validator uses keyword log_level only)"
  - "Kept get_logger() unchanged (returns logging.getLogger(name) with default 'bangko') for downstream compatibility"
  - "Skipped unused import cleanup in admin_dashboard.py and wsgi.py (at-discretion deferred — complex interdependencies)"
  - "Vulture found no additional whole-file dead code beyond already-moved files at min-confidence 90"

patterns-established:
  - "Logging format: 'level=%(levelname)s logger=%(name)s %(message)s' — all log lines follow key=value structure"
  - "Dead code archive pattern: move to _archive/ (not delete) to preserve history while cleaning active codebase"

requirements-completed: [QUAL-01, QUAL-04]

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 2 Plan 02: Logging Infrastructure + Dead Code Archive Summary

**Console-only key=value structured logging in errors.py with FileHandler removed; legacy web_app_complete.py and mobile/BankongSetonApp archived to _archive/**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T10:12:28Z
- **Completed:** 2026-02-26T10:15:22Z
- **Tasks:** 2
- **Files modified:** 1 modified, 2 archived

## Accomplishments
- `setup_logging()` now emits `level=%(levelname)s logger=%(name)s %(message)s` format to stderr only — no file creation
- Removed `log_dir` parameter, `FileHandler`, `RotatingFileHandler`, and `os.makedirs('logs/')` from setup_logging()
- Added `logger.propagate = False` to prevent double-printing to root logger
- Removed unused `import os` from errors.py (no longer needed after FileHandler removal)
- Created `_archive/` at repo root with both legacy dead code items preserved
- Ran vulture at min-confidence 90 — confirmed no additional whole-file dead code

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite setup_logging() to console-only key=value format** - `4a9a61c` (fix)
2. **Task 2: Create _archive/ and move dead code files** - `a19b1f8` (chore)

**Plan metadata:** _(pending docs commit)_

## Files Created/Modified
- `backend/errors.py` - setup_logging() rewritten: FileHandler removed, StreamHandler-only, key=value format, propagate=False
- `_archive/web_app_complete.py` - Legacy duplicate of admin_dashboard moved here (22KB)
- `_archive/mobile/BankongSetonApp/` - Archived Android app folder (Kotlin/Gradle project)

## Decisions Made
- **Removed log_dir parameter entirely:** Only caller (`config_validator.py`) passes `log_level=` as keyword arg — no caller ever passed `log_dir`. Safe to remove outright.
- **Kept get_logger() unchanged:** Current implementation is `return logging.getLogger(name)` with default `'bangko'`. Plan explicitly required preservation for downstream compatibility; all callers work correctly with current behavior.
- **Deferred unused import cleanup in admin_dashboard.py/wsgi.py:** `get_cached`, `set_cached`, `with_retry`, `get_write_queue` in admin_dashboard are interdependent with resilience/cache modules — removing them risks breaking functionality. `wsgi.py` imports from `web_app` which doesn't exist — needs separate investigation. Both deferred as out-of-scope for this plan.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Logging infrastructure ready for Plan 04 (print() → logger replacement)
- Plan 03 (thread-safe global state) is independent and can proceed
- `_archive/` graveyard established for any future dead code discoveries
- Note: wsgi.py references non-existent `web_app.py` — pre-existing issue, not introduced by this plan

---
*Phase: 02-code-quality*
*Completed: 2026-02-26*
