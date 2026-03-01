---
phase: 09-nfc-android-compat
plan: "02"
subsystem: api
tags: [nfc, android, retrofit, kotlin, flask, google-sheets]

# Dependency graph
requires:
  - phase: 05-nfc-architecture-prep
    provides: nfc_payments.py NFCService + VirtualCards sheet schema + nfc-integration-guide.md skeleton
provides:
  - GET /api/nfc/status endpoint returning is_registered/device_id/registered_at
  - POST /api/nfc/unregister endpoint setting IsActive=FALSE on active VirtualCard
  - StudentData.id correctly deserializes backend "id" JSON key in Android ApiClient.kt
  - nfc-integration-guide.md documents both new endpoints with full request/response tables
affects:
  - android NFC registration/unregistration flow
  - any client polling card status

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Session-token auth (active_sessions Bearer) for all student NFC endpoints — no JWT"
    - "ensure_virtual_cards_sheet() imported inside function body to avoid circular import risk"

key-files:
  created: []
  modified:
    - backend/api/api_server.py
    - mobile/android/app/src/main/java/com/juls/bankongsetonandroid/ApiClient.kt
    - docs/nfc-integration-guide.md

key-decisions:
  - "device_id body param in unregister accepted but not validated against sheet — student session is auth source of truth (per CONTEXT.md 'Backend behavior: Claude's discretion')"
  - "ensure_virtual_cards_sheet() imported inside function body (not top-level) — avoids circular import risk consistent with existing lazy-import pattern in codebase"

patterns-established:
  - "NFC student endpoints: session Bearer token auth, ensure_virtual_cards_sheet() call, get_all_records() scan pattern"

requirements-completed:
  - NFC-04
  - NFC-05

# Metrics
duration: 3min
completed: 2026-03-02
---

# Phase 09 Plan 02: NFC Status/Unregister Endpoints + Android SerializedName Fix Summary

**Added `GET /api/nfc/status` and `POST /api/nfc/unregister` to api_server.py with session-token auth, fixed Kotlin `StudentData.id` `@SerializedName("student_id")` → `"id"` bug, and documented both endpoints in nfc-integration-guide.md**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-02T00:00:00Z
- **Completed:** 2026-03-02T00:03:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `GET /api/nfc/status` returns `{ is_registered, device_id, registered_at }` for session-authed student — reads VirtualCards sheet and checks `IsActive == 'TRUE'`
- `POST /api/nfc/unregister` sets `IsActive = 'FALSE'` (column 6) on the student's active VirtualCard row; returns 404 if no active card found
- `StudentData.id` in `ApiClient.kt` now maps JSON key `"id"` (was `"student_id"` which matched nothing, causing empty student ID on all subsequent authenticated calls)
- `nfc-integration-guide.md` documents both new endpoints with full request/response tables before `## HCE Implementation`; "What is already built" list updated

## Task Commits

Each task was committed atomically:

1. **Task 1: Add GET /api/nfc/status and POST /api/nfc/unregister to api_server.py** - `91d2f05` (feat)
2. **Task 2: Fix StudentData.id SerializedName in ApiClient.kt + document new endpoints in nfc-integration-guide.md** - `ea5994f` (fix)

**Plan metadata:** *(see final docs commit)*

## Files Created/Modified

- `backend/api/api_server.py` — two new route handlers: `nfc_status()` and `nfc_unregister()`
- `mobile/android/app/src/main/java/com/juls/bankongsetonandroid/ApiClient.kt` — `@SerializedName("student_id")` → `@SerializedName("id")` on `StudentData.id`
- `docs/nfc-integration-guide.md` — added `## NFC Status` and `## NFC Unregister` sections; updated "What is already built" list

## Decisions Made

- `device_id` body param in `nfc_unregister` is accepted but not cross-validated against the sheet — the student session is the auth source of truth. Consistent with the existing `nfc_register` design where the student's session determines which card to operate on.
- `ensure_virtual_cards_sheet()` imported inside function body (not top-level module import) — avoids circular import risk consistent with the existing lazy-import `sys.path.insert` pattern throughout `api_server.py`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- NFC-04 (status endpoint) and NFC-05 (unregister endpoint) are closed
- Android `StudentData.id` bug is fixed — login now correctly stores the student ID enabling all subsequent authenticated calls
- Phase 09 plans complete: backend NFC API is fully implemented and documented

---
*Phase: 09-nfc-android-compat*
*Completed: 2026-03-02*
