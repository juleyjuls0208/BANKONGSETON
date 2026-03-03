---
phase: 02-code-quality
plan: 01
subsystem: api
tags: [threading, utils, card-reader, uid-normalization, thread-safety]

# Dependency graph
requires: []
provides:
  - "normalize_card_uid() — canonical UID normalisation (None-safe, strips whitespace, leading zeros, uppercase)"
  - "CardReaderState — threading.Lock-protected class wrapping arduino, arduino_bridge, card_reading_active, pending_student_id"
  - "card_reader_state — module-level singleton"
affects: [02-05, admin_dashboard, api_server, cashier_routes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "threading.Lock for all shared mutable state (get/set/update API)"
    - "Centralised UID normalisation — single source of truth, no per-module variants"

key-files:
  created:
    - backend/utils.py
    - tests/test_utils.py
  modified: []

key-decisions:
  - "threading.Lock (not RLock) — re-entrant locking not needed since get/set/update do not call each other"
  - "No imports from errors.py in utils.py — avoids circular import risk given runtime sys.path.insert pattern"
  - "python-dotenv installed system-wide (not venv) to unblock conftest.py; no venv present in project"
  - "from backend.utils import used in tests (namespace package, no __init__.py) — consistent with project root test invocation"

patterns-established:
  - "Thread-safe state pattern: all mutable shared state through CardReaderState.get/set/update"
  - "Canonical normalisation: single backend/utils.py function replaces per-module divergent copies"

requirements-completed: [QUAL-02, QUAL-03]

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 2 Plan 01: Shared Utils (normalize_card_uid + CardReaderState) Summary

**Canonical `normalize_card_uid()` function (None-safe, strip/lstrip-zeros/upper) and `CardReaderState` thread-safe singleton using `threading.Lock`, replacing divergent per-module implementations**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T10:12:59Z
- **Completed:** 2026-02-26T10:15:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `backend/utils.py` created with `normalize_card_uid()`, `CardReaderState` class, and `card_reader_state` singleton
- `tests/test_utils.py` created with 19 tests: 8 uid normalisation, 9 CardReaderState basic, 2 concurrency (50-thread)
- All 19 pytest tests pass including concurrent 50-thread set/get and mixed operations tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create backend/utils.py** - `0f9fb6f` (feat)
2. **Task 2: Write unit and concurrency tests** - `e830a66` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/utils.py` — `normalize_card_uid()`, `CardReaderState`, `card_reader_state` singleton
- `tests/test_utils.py` — 19 unit + concurrency tests for both utilities

## Decisions Made

- Used `threading.Lock` (not `RLock`) — re-entrant locking is unnecessary since the three public methods (`get`, `set`, `update`) do not call each other
- No imports from `errors.py` in `utils.py` to avoid circular import risk (admin_dashboard and api_server use runtime `sys.path.insert`)
- `python-dotenv` installed at the system level (no venv in this project) to unblock conftest.py import
- Tests use `from backend.utils import ...` style (consistent with running pytest from project root; backend/ is a namespace package)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed pytest and python-dotenv**
- **Found during:** Task 2 (running test suite)
- **Issue:** pytest not installed (only `pip` and `vulture` present); conftest.py required `python-dotenv`
- **Fix:** `pip install pytest pytest-cov` then `pip install python-dotenv`
- **Files modified:** None (system packages)
- **Verification:** `python -m pytest tests/test_utils.py` runs and all 19 tests pass
- **Committed in:** part of task 2 commit (e830a66)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Purely an environment bootstrap issue; no code changes required.

## Issues Encountered

None — tests passed on first run after environment was bootstrapped.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `backend/utils.py` is ready for downstream plans (02-05) to import `from backend.utils import normalize_card_uid, card_reader_state`
- No blockers

---
*Phase: 02-code-quality*
*Completed: 2026-02-26*
