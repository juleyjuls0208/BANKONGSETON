---
phase: 04-student-app-notifications
plan: 02
subsystem: api
tags: [firebase, fcm, push-notifications, python, flask]

# Dependency graph
requires:
  - phase: 04-student-app-notifications
    provides: "04-01 fixed FCM auth mismatch and added register_fcm_token endpoint"
provides:
  - "fcm_sender.py with Firebase Admin SDK init and send_low_balance_push() helper"
  - "Low-balance push notification wired into cashier transaction flow"
  - "Settings sheet threshold config with env var fallback"
affects: [student-app-android]

# Tech tracking
tech-stack:
  added: [firebase-admin>=6.0.0]
  patterns:
    - "Fire-and-forget notification after transaction commit — failure never blocks response"
    - "Settings sheet Key/Value lookup with env var fallback for admin-configurable thresholds"
    - "Double-init guard for Firebase Admin SDK (firebase_admin._apps check)"

key-files:
  created:
    - backend/api/fcm_sender.py
  modified:
    - backend/api/api_server.py
    - backend/api/requirements_api.txt

key-decisions:
  - "firebase-admin imported lazily inside functions (not at module level) — prevents import crash when credentials file is absent in non-notification environments"
  - "Threshold read from Settings sheet on every transaction (not cached) — allows admin to change threshold without restart"
  - "Settings sheet read wrapped in inner try/except — Settings sheet unavailable falls back to env var silently"

patterns-established:
  - "Post-commit notification pattern: all side effects after append_row, all wrapped in outer try/except"

requirements-completed: [NOTF-01]

# Metrics
duration: 1min
completed: 2026-02-26
---

# Phase 4 Plan 02: FCM Low-Balance Notification Summary

**Firebase Admin SDK helper (fcm_sender.py) + cashier transaction flow wired to send FCM push when student balance drops below admin-configured threshold**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-26T14:23:55Z
- **Completed:** 2026-02-26T14:25:15Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created `fcm_sender.py` with `send_low_balance_push()` using Firebase Admin SDK, double-init guard, and graceful failure handling
- Wired low-balance notification into `process_cashier_transaction()` — fires after `append_row`, reads threshold from Settings sheet (Key=`low_balance_threshold`) with `LOW_BALANCE_THRESHOLD` env var as fallback
- Added `firebase-admin>=6.0.0` to `requirements_api.txt`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create fcm_sender.py with Firebase Admin SDK** - `dda3fd6` (feat)
2. **Task 2: Wire low-balance check into process_cashier_transaction** - `8674201` (feat)

**Plan metadata:** (docs: complete plan)

## Files Created/Modified
- `backend/api/fcm_sender.py` - Firebase Admin SDK init + `send_low_balance_push()` helper; never raises
- `backend/api/api_server.py` - Low-balance notification block inserted after `trans_sheet.append_row()`, before email receipt block
- `backend/api/requirements_api.txt` - Added `firebase-admin>=6.0.0`

## Decisions Made
- **Lazy firebase_admin import** inside functions rather than at module top-level — prevents crash when `config/firebase-credentials.json` is absent (e.g. dev without Firebase setup)
- **Per-transaction Settings sheet read** (not cached) so admin can change the threshold without restarting the API server
- **Inner try/except for Settings sheet** — if the Settings sheet doesn't exist or is unavailable, silently falls back to env var and logs a warning, never failing the transaction

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
**External services require manual configuration.** See below for Firebase setup:

- Download Firebase service account JSON from: Firebase Console → Project Settings → Service accounts → Generate new private key → Save as `config/firebase-credentials.json`
- Set `LOW_BALANCE_THRESHOLD` in `.env` (float, e.g. `50`). Default is `50` if not set.
- Add a `Settings` sheet to the Google Spreadsheet with columns `Key` and `Value`; add a row with `Key=low_balance_threshold` and `Value=50` (or desired threshold) to override the env var at runtime.

## Next Phase Readiness
- FCM notification infrastructure complete; Android app can now receive low-balance alerts after cashier transactions
- Ready for 04-03 (next plan in phase 4)

---
*Phase: 04-student-app-notifications*
*Completed: 2026-02-26*
