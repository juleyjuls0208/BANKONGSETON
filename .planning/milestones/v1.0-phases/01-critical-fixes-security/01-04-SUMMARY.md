---
phase: 01-critical-fixes-security
plan: "04"
subsystem: api
tags: [rfid, validation, security, card-uid, regex]

# Dependency graph
requires:
  - phase: 01-critical-fixes-security
    provides: "startup guard, CORS restriction, credential redaction from plans 01-01 through 01-03"
provides:
  - "UID_PATTERN regex ('^[0-9A-Fa-f]{8}$') and validate_card_uid() in admin_dashboard.py"
  - "UID_PATTERN and validate_card_uid() in api_server.py with validation in process_cashier_transaction()"
  - "UID_PATTERN in cashier_routes.py with format validation in complete_sale()"
  - "read_card_thread() rejects empty and non-hex UIDs before any Sheets query"
affects: [02-quality-reliability, cashier-pos, api-routes, rfid-card-handling]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Input boundary validation: validate UID format with regex before normalization or Sheets access"
    - "requires_ack flag on card_error WebSocket events for cashier-facing errors"

key-files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/api/api_server.py
    - backend/dashboard/cashier/cashier_routes.py

key-decisions:
  - "UID_PATTERN defined independently in each module (not shared util) to avoid cross-module import complexity"
  - "validate_card_uid() only defined where needed (admin_dashboard.py and api_server.py); cashier_routes.py uses inline UID_PATTERN.match() since it imports admin_dashboard functions at runtime"
  - "requires_ack: True flag on card_error events matches locked decision that cashier errors need explicit acknowledgment"

patterns-established:
  - "Validate UID at entry boundary before normalization: validate_card_uid(uid) returns (bool, str)"
  - "Reject invalid UIDs with HTTP 400 and descriptive message; never pass to normalize_card_uid() or Sheets"

requirements-completed:
  - BUG-02
  - SEC-04

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 1 Plan 4: Card UID Input Validation Summary

**Regex-based card UID validation ('^[0-9A-Fa-f]{8}$') at all three entry points — Arduino reader, API server, and cashier POS — blocking empty and malformed UIDs before any Google Sheets query**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T08:54:10Z
- **Completed:** 2026-02-26T08:56:20Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `admin_dashboard.py`: Added `UID_PATTERN`, `validate_card_uid()`, and guards in `read_card_thread()` that emit `card_error` with `requires_ack: True` and log warnings for empty or non-hex UIDs from the Arduino reader
- `api_server.py`: Added `UID_PATTERN`, `validate_card_uid()`, and validation call in `process_cashier_transaction()` before `normalize_card_uid()` — invalid UIDs return HTTP 400
- `cashier_routes.py`: Added `UID_PATTERN` at module level and format validation guard in `complete_sale()` before `normalize_card_uid()` — invalid UIDs return HTTP 400 with descriptive message

## Task Commits

Each task was committed atomically:

1. **Task 1: UID validation in admin_dashboard.py** - `ff0f884` (feat)
2. **Task 2: UID validation in api_server.py and cashier_routes.py** - `6c90aff` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `backend/dashboard/admin_dashboard.py` — Added `import re`, `UID_PATTERN`, `validate_card_uid()`, and guards in `read_card_thread()` for empty and malformed UIDs
- `backend/api/api_server.py` — Added `import re`, `UID_PATTERN`, `validate_card_uid()`, and validation before `normalize_card_uid()` in `process_cashier_transaction()`
- `backend/dashboard/cashier/cashier_routes.py` — Added `import re`, `UID_PATTERN`, and format check in `complete_sale()` before `normalize_card_uid()`

## Decisions Made
- `UID_PATTERN` defined independently in each module (not in a shared util) to avoid runtime import issues given the non-standard module loading pattern (cashier_routes.py does `sys.path.insert` inside functions to load admin_dashboard at runtime)
- `validate_card_uid()` as a named function in admin_dashboard.py and api_server.py; cashier_routes.py uses inline `UID_PATTERN.match()` since it already imports admin_dashboard functions at call time
- Left the existing `if len(uid) == 8:` check in `read_card_thread()` intact (harmless — always True after regex passes); restructuring the block was unnecessary risk

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three UID entry points now validated; no empty or non-hex UID can reach `normalize_card_uid()` or any Google Sheets query
- Phase 1 plan 4 closes BUG-02 (empty card UID silent match) and SEC-04 (malformed UID bypass)
- Ready to proceed to next plan in Phase 1

---
*Phase: 01-critical-fixes-security*
*Completed: 2026-02-26*
