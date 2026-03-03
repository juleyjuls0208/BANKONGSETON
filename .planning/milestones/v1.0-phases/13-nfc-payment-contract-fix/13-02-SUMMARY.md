---
phase: 13-nfc-payment-contract-fix
plan: "02"
subsystem: payments
tags: [nfc, android, hce, api, payments]

requires:
  - phase: 13-nfc-payment-contract-fix
    provides: "Context and plan for NFC-04 contract fix"

provides:
  - "NFCService.get_virtual_card_by_token() — single-token lookup method"
  - "/api/nfc/pay handler that accepts virtual_card_token only (no X-Device-Token)"
  - "CORS allow_headers without X-Device-Token"

affects: [android-hce, nfc-pay, api-server]

tech-stack:
  added: []
  patterns:
    - "Single-token VirtualCard lookup: match on VirtualCardToken + IsActive only"
    - "Backward-compatible method addition: keep old two-token method alongside new"

key-files:
  created: []
  modified:
    - backend/nfc_payments.py
    - backend/api/api_server.py

key-decisions:
  - "Add get_virtual_card_by_token() as new method rather than replacing get_virtual_card_by_tokens() — backward compatible"
  - "Renumber steps in nfc_pay() (Step 1 body validation, Step 2 lookup) after removing X-Device-Token block"
  - "Update error message from 'Invalid virtual card token or device token' to 'Invalid or inactive virtual card token' for clarity"

patterns-established:
  - "NFC pay flow: virtual_card_token alone is sufficient; server resolves device_token internally via VirtualCards sheet"

requirements-completed:
  - NFC-04

duration: 3min
completed: "2026-03-02"
---

# Phase 13 Plan 02: NFC Payment Contract Fix Summary

**Removed X-Device-Token requirement from `/api/nfc/pay` by adding `NFCService.get_virtual_card_by_token()` single-token lookup, enabling Android HCE service to complete NFC payments with card token alone**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-02T06:20:00Z
- **Completed:** 2026-03-02T06:23:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `NFCService.get_virtual_card_by_token(virtual_card_token, db)` that looks up VirtualCard by token alone (no device_token), while keeping the existing `get_virtual_card_by_tokens()` for backward compatibility
- Removed X-Device-Token header extraction and 401 guard from `nfc_pay()` handler
- Switched `nfc_pay()` to use single-token lookup; updated error message and docstring
- Removed `X-Device-Token` from CORS `allow_headers` list since it is no longer sent by the client

## Task Commits

Each task was committed atomically:

1. **Task 1: Add get_virtual_card_by_token() to NFCService** - `62ed1cc` (feat)
2. **Task 2: Update nfc_pay() to remove X-Device-Token requirement** - `dc788bd` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/nfc_payments.py` — Added `get_virtual_card_by_token()` method after existing `get_virtual_card_by_tokens()`
- `backend/api/api_server.py` — Removed X-Device-Token block, switched to single-token lookup, updated CORS headers

## Decisions Made

- Kept `get_virtual_card_by_tokens()` (two-token version) intact for backward compatibility — only added the new single-token variant alongside it
- Renumbered nfc_pay() steps after removing Step 1 (X-Device-Token block): body validation becomes Step 1, VirtualCard lookup becomes Step 2
- Updated CORS `allow_headers` to remove `"X-Device-Token"` since Android HCE no longer sends it

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- NFC-04 requirement satisfied: Android HCE service (`BankoHceService`) can now complete NFC payments using only the `virtual_card_token` from the APDU response
- `/api/nfc/pay` accepts requests with `{ virtual_card_token, items, total }` body and JWT — no X-Device-Token header needed
- Ready for Phase 13 completion / transition to next phase

---
*Phase: 13-nfc-payment-contract-fix*
*Completed: 2026-03-02*
