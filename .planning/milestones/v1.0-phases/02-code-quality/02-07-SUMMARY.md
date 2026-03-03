---
phase: 02-code-quality
plan: 07
subsystem: api
tags: [python, utils, normalize_card_uid, type-annotation, pytest]

# Dependency graph
requires:
  - phase: 02-code-quality
    provides: normalize_card_uid in backend/utils.py (plan 02-05)
provides:
  - normalize_card_uid(None) returns None (QUAL-02 compliant)
  - Return type annotation updated to str | None
  - All 19 unit tests passing with corrected assertion
affects: [api_server.py, cashier_routes.py, admin_dashboard.py — all callers of normalize_card_uid]

# Tech tracking
tech-stack:
  added: []
  patterns: [None-pass-through for sentinel values rather than converting to empty string]

key-files:
  created: []
  modified:
    - backend/utils.py
    - tests/test_utils.py

key-decisions:
  - "normalize_card_uid(None) returns None (sentinel pass-through), not '' — aligns with QUAL-02 spec"
  - "Empty string input ('') continues to return '' — whitespace/empty path unchanged"

patterns-established:
  - "Sentinel pass-through: None inputs return None, not a coerced default value"

requirements-completed: [QUAL-02]

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 2 Plan 7: normalize_card_uid None Fix Summary

**normalize_card_uid(None) now returns None instead of empty string, closing QUAL-02 gap and making UAT Test 3 print `ABC None ABC`**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T11:23:29Z
- **Completed:** 2026-02-26T11:25:16Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Fixed `normalize_card_uid(None)` to return `None` instead of `""` (QUAL-02 compliance)
- Updated return type annotation from `str` to `str | None`
- Updated docstring to accurately describe None vs empty-string behaviour
- Updated test assertion from `== ""` to `is None`
- All 19 unit tests still pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix normalize_card_uid to return None for None input** - `328b2d6` (fix)
2. **Task 2: Update test assertion and run full test suite** - `8be8b5c` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `backend/utils.py` - Guard clause `return None`, type annotation `str | None`, docstrings updated
- `tests/test_utils.py` - test_normalize_none docstring + assertion updated to `is None`

## Decisions Made
- `normalize_card_uid(None)` returns `None` as sentinel pass-through — None in, None out. This is the QUAL-02 specified behaviour and avoids masking None values with empty strings in callers.
- The empty-string path (`normalize_card_uid("")` → `""`) is unchanged; only the None guard is affected.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 6 QUAL requirements addressed across plans 02-01 through 02-07 (QUAL-02 now fully closed)
- Phase 2 complete; ready for Phase 3 planning

---
*Phase: 02-code-quality*
*Completed: 2026-02-26*
