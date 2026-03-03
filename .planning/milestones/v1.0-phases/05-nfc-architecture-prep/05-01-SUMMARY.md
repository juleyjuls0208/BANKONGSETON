---
phase: 05-nfc-architecture-prep
plan: "01"
subsystem: nfc
tags: [nfc, google-sheets, uuid, secrets, virtualcard, gspread]

# Dependency graph
requires: []
provides:
  - NFCService class with register_virtual_card() and get_virtual_card_by_tokens()
  - ensure_virtual_cards_sheet(db) with 6-column VirtualCards schema
  - VIRTUAL_CARDS_SHEET_NAME and VIRTUAL_CARDS_HEADERS constants
  - Clean nfc_payments.py ready for Plan 02 endpoint imports
affects: [05-nfc-architecture-prep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ensure_*_sheet() pattern: get worksheet or create with headers on WorksheetNotFound"
    - "Stateless service class: all methods accept db parameter, no instance state"
    - "Token generation: uuid.uuid4() for VirtualCardToken, secrets.token_urlsafe(32) for DeviceToken"
    - "IsActive upsert: deactivate old rows (update_cell col 6 = FALSE) before appending new row"

key-files:
  created: []
  modified:
    - backend/nfc_payments.py

key-decisions:
  - "Clean rewrite (not patch) of nfc_payments.py — removed NFCPaymentManager, VirtualCard, PIN, biometric, expiry, multi-card, in-memory state"
  - "get_philippines_time() replicated locally (not imported from api_server.py) to avoid circular import risk given runtime sys.path.insert pattern"
  - "ensure_virtual_cards_sheet uses db.worksheet() (direct gspread call) instead of get_worksheet_with_retry to avoid importing that helper — matches plan intent"
  - "NFCService is stateless (no __init__ instance vars) — all methods receive db as parameter"

patterns-established:
  - "ensure_virtual_cards_sheet(db): mirrors ensure_products_sheet() from admin_dashboard.py"
  - "IsActive filtering: str(r.get('IsActive','')).upper() == 'TRUE' pattern for active row checks"

requirements-completed: [NFC-02]

# Metrics
duration: 5min
completed: 2026-02-28
---

# Phase 5 Plan 01: NFC Architecture Prep — NFCService Summary

**Sheets-backed NFCService with UUID v4 tokens, silent one-card-per-student replace, and IsActive filtering — replaces in-memory NFCPaymentManager**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-28T11:07:00Z
- **Completed:** 2026-02-28T11:12:58Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Replaced entire `nfc_payments.py` (402 lines) with clean 158-line `NFCService` implementation
- `ensure_virtual_cards_sheet(db)` creates VirtualCards sheet with 6-column schema on first call
- `register_virtual_card()` silently deactivates old active rows before appending new row (upsert pattern)
- `get_virtual_card_by_tokens()` returns only rows where IsActive == TRUE — deactivated rows are never matched
- All out-of-scope features removed: NFCPaymentManager, VirtualCard, PIN, biometric, expiry, token refresh, multi-card, in-memory dicts

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite nfc_payments.py with NFCService backed by Google Sheets** - `90257cc` (feat)

**Plan metadata:** _(pending docs commit)_

## Files Created/Modified
- `backend/nfc_payments.py` — Complete rewrite: NFCService class + ensure_virtual_cards_sheet() + module constants + get_philippines_time() helper

## Decisions Made
- **Clean rewrite, not patch**: The old NFCPaymentManager had PIN, biometric, token expiry, MAX_CARDS_PER_STUDENT, and in-memory storage — all out of scope for Phase 5. A clean rewrite avoids leaving dead code.
- **Replicated get_philippines_time() locally**: Importing from api_server.py would risk circular imports given the runtime `sys.path.insert` pattern used throughout the project.
- **Stateless NFCService**: No `__init__` with instance vars; all methods accept `db` parameter. Avoids module-level shared state that would be fragile in a multi-process Flask environment.
- **db.worksheet() direct call in ensure_virtual_cards_sheet**: Avoids importing `get_worksheet_with_retry` from api_server (circular import risk). The retry wrapper adds resilience but the ensure_ pattern works fine with direct worksheet() access.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The VirtualCards sheet is created automatically on first call to `ensure_virtual_cards_sheet(db)`.

## Next Phase Readiness
- `backend/nfc_payments.py` imports cleanly: `from nfc_payments import NFCService, VIRTUAL_CARDS_SHEET_NAME, VIRTUAL_CARDS_HEADERS` works with no errors
- `NFCService`, `ensure_virtual_cards_sheet`, `VIRTUAL_CARDS_SHEET_NAME`, `VIRTUAL_CARDS_HEADERS` all importable
- `NFCPaymentManager` is not present (confirmed by assertion in verification)
- Ready for Plan 02 to add Flask NFC endpoints that call `NFCService.register_virtual_card()` and `NFCService.get_virtual_card_by_tokens()`

## Self-Check: PASSED

- ✅ `backend/nfc_payments.py` exists on disk
- ✅ Commit `90257cc` exists in git log
- ✅ Import verification: `python -c "... from nfc_payments import NFCService ..."` → OK
- ✅ NFCPaymentManager not present (assertion confirmed)

---
*Phase: 05-nfc-architecture-prep*
*Completed: 2026-02-28*
