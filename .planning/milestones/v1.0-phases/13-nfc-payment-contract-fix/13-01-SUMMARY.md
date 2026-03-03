---
phase: 13-nfc-payment-contract-fix
plan: 01
subsystem: nfc
tags: [android, kotlin, retrofit, nfc, virtual-card-token]

# Dependency graph
requires:
  - phase: 05-nfc-architecture-prep
    provides: NFC payment backend endpoints (nfc_payments.py with virtual_card_token response)
provides:
  - Android NfcRegistrationResponse data class with correct virtual_card_token field
  - NfcManager with KEY_VIRTUAL_CARD_TOKEN constant and correct field access
affects: [nfc-payments, android-nfc, hce-service]

# Tech tracking
tech-stack:
  added: []
  patterns: [field name consistency between Retrofit data class and backend JSON response]

key-files:
  created: []
  modified:
    - mobile/android/app/src/main/java/com/juls/bankongsetonandroid/ApiClient.kt
    - mobile/android/app/src/main/java/com/juls/bankongsetonandroid/NfcManager.kt

key-decisions:
  - "Renamed NfcRegistrationResponse.virtual_token → virtual_card_token to match Python backend contract"
  - "Renamed KEY_VIRTUAL_TOKEN constant → KEY_VIRTUAL_CARD_TOKEN (string value also updated); existing stored tokens invalidated — re-registration is correct recovery flow"

patterns-established:
  - "Android Retrofit data class field names must match Python backend JSON key names exactly (no @SerializedName mapping needed when names align)"

requirements-completed:
  - NFC-03

# Metrics
duration: 3min
completed: 2026-03-02
---

# Phase 13 Plan 01: NFC Payment Contract Fix Summary

**Fixed Android `NfcRegistrationResponse.virtual_token` field name mismatch — renamed to `virtual_card_token` to match Python backend `/api/nfc/register` response contract, and updated all NfcManager EncryptedSharedPreferences usages to use `KEY_VIRTUAL_CARD_TOKEN`**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-02T07:00:00Z
- **Completed:** 2026-03-02T07:03:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `NfcRegistrationResponse` data class now correctly maps `virtual_card_token` from the Python backend JSON response (was silently null before due to field name mismatch)
- `NfcManager` constant renamed `KEY_VIRTUAL_TOKEN` → `KEY_VIRTUAL_CARD_TOKEN` with string value `"virtual_card_token"`
- All 4 NfcManager usages updated: constant declaration, `isDeviceRegistered()` getString, `getVirtualToken()` getString, `registerDevice()` field access + prefs put
- Zero occurrences of old `virtual_token` or `KEY_VIRTUAL_TOKEN` in both files — NFC-03 requirement satisfied

## Task Commits

Each task was committed atomically:

1. **Task 1: Rename virtual_token → virtual_card_token in ApiClient.kt** - `748338d` (fix)
2. **Task 2: Update NfcManager.kt constant and field reference** - `e1e6e08` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `mobile/android/app/src/main/java/com/juls/bankongsetonandroid/ApiClient.kt` - `NfcRegistrationResponse` field renamed from `virtual_token` to `virtual_card_token`
- `mobile/android/app/src/main/java/com/juls/bankongsetonandroid/NfcManager.kt` - Constant and all usages renamed; field access updated

## Decisions Made
- Renamed the `KEY_VIRTUAL_TOKEN` constant string value from `"virtual_token"` to `"virtual_card_token"` — this intentionally invalidates any previously stored token in `EncryptedSharedPreferences`; re-registration is the correct recovery flow since previously stored tokens were null/wrong anyway
- The actual `NfcRegistrationResponse` in the file only had 2 fields (`virtual_token`, `expires_at`) — not 4 fields as shown in the plan's `<interfaces>` block. The fix was still the same rename; the backend contract difference was already correct, only the Android field name needed updating.

## Deviations from Plan

### Auto-fixed Issues

None — the field count difference between the plan's `<interfaces>` block (4 fields) and the actual file (2 fields: `virtual_token`, `expires_at`) did not require an auto-fix. The rename was applied to the field that existed. The plan's core objective was fully addressed.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** Plan executed exactly as written (minor interface description discrepancy in plan was immaterial to the fix).

## Issues Encountered
- None — both files were straightforward surgical renames with grep verification confirming zero old references remain

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NFC-03 fixed: Android model now matches Python backend contract end-to-end
- `virtual_card_token` flows correctly: Python returns it → Retrofit deserializes it → NfcManager stores it in EncryptedSharedPreferences → BankoHceService uses it for APDU responses
- Ready for Phase 13 Plan 02 (if any additional NFC fixes remain)

---
*Phase: 13-nfc-payment-contract-fix*
*Completed: 2026-03-02*
