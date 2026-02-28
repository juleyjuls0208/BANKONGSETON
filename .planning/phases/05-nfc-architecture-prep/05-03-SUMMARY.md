---
phase: 05-nfc-architecture-prep
plan: "03"
subsystem: docs
tags: [nfc, hce, android, kotlin, flask, api-docs]

# Dependency graph
requires:
  - phase: 05-nfc-architecture-prep
    provides: POST /api/nfc/register and POST /api/nfc/pay endpoints with actual request/response shapes (api_server.py)
  - phase: 05-nfc-architecture-prep
    provides: NFCService with VIRTUAL_CARDS_HEADERS and register_virtual_card/get_virtual_card_by_tokens (nfc_payments.py)
provides:
  - docs/nfc-integration-guide.md — complete self-contained NFC HCE integration guide for v2 Android developer
  - BankoHceService.kt copy-paste Kotlin with HostApduService and AID F049494F4E41
  - Registration Kotlin with EncryptedSharedPreferences storage
  - Full error code table for both endpoints
  - VirtualCards sheet schema with all 6 column headers
affects:
  - android-nfc-client
  - v2-android-developer

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "NFC payload is pipe-delimited string 'virtual_card_token|device_token' — no JSON envelope"
    - "BankoHceService responds to SELECT AID F049494F4E41 with UTF-8 payload + 0x9000"

key-files:
  created:
    - docs/nfc-integration-guide.md
  modified: []

key-decisions:
  - "Guide written from actual api_server.py + nfc_payments.py source — not from plan descriptions"
  - "Section 4 documents Android implementation including BankoHceService, registration, and cashier-side payment flow"
  - "Important Notes section explicitly calls out superseded NFC_IMPLEMENTATION.md to prevent confusion"

patterns-established:
  - "NFC integration guide pattern: sequence diagram + per-endpoint error tables + copy-paste Kotlin + sheet schema"

requirements-completed:
  - NFC-05

# Metrics
duration: 2min
completed: 2026-02-28
---

# Phase 5 Plan 03: NFC Integration Guide Summary

**373-line self-contained NFC HCE guide covering both endpoints with error tables, BankoHceService Kotlin, AID F049494F4E41, and VirtualCards sheet schema — written from actual api_server.py implementation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-28T11:25:04Z
- **Completed:** 2026-02-28T11:27:48Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Wrote `docs/nfc-integration-guide.md` (373 lines) covering full NFC HCE flow for v2 Android developer
- All request/response shapes extracted directly from working `api_server.py` + `nfc_payments.py` implementation
- BankoHceService Kotlin and registration Kotlin are copy-paste ready with EncryptedSharedPreferences
- Both endpoints fully documented with all 4xx error codes, causes, and resolutions
- VirtualCards sheet schema documented with all 6 column headers (from `VIRTUAL_CARDS_HEADERS` constant)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write docs/nfc-integration-guide.md from implemented endpoints** - `8783ffd` (docs)

**Plan metadata:** *(pending — docs commit)*

## Files Created/Modified

- `docs/nfc-integration-guide.md` — Complete NFC HCE integration guide: overview, sequence diagram, API reference (POST /api/nfc/register + POST /api/nfc/pay), Android manifest, BankoHceService.kt, registration Kotlin, VirtualCards schema, important notes

## Decisions Made

- Guide written strictly from source code (`api_server.py` lines 497–651, `nfc_payments.py` VIRTUAL_CARDS_HEADERS) — no reliance on plan descriptions for request/response shapes
- Explicitly warned v2 developer not to use `docs/NFC_IMPLEMENTATION.md` (superseded design with PIN/biometrics)
- Included cashier-side payment flow in Section 4.4 even though Android app doesn't call `/api/nfc/pay` — provides complete picture for developer orientation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. This plan creates only a documentation file.

## Next Phase Readiness

- NFC-05 requirement fully satisfied: guide is self-contained, future developer can implement v2 without asking the original author
- All Phase 5 NFC Architecture Prep plans complete: NFC-01, NFC-03, NFC-04, NFC-05 requirements closed
- Phase 5 is complete — ready for transition to next phase (or milestone completion)

---
*Phase: 05-nfc-architecture-prep*
*Completed: 2026-02-28*
