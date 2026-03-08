---
phase: 21
plan: "01"
subsystem: mobile-android, backend-dashboard
tags: [bugfix, hce, fcm, nfc, parent-login, google-services]
dependency_graph:
  requires: []
  provides: [V11-NFCA-01, V11-PAR-01-06]
  affects: [FCMService, BankoHceService, admin_dashboard]
tech_stack:
  added: []
  patterns: [coroutine-call-execute, null-check-restore, typed-except]
key_files:
  created: []
  modified:
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/FCMService.kt
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt
    - backend/dashboard/admin_dashboard.py
  deleted:
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/google-services.json (untracked, disk-only)
decisions:
  - HCE token restored via NfcManager.getInstance().getVirtualToken() (its own EncryptedSharedPreferences), not SecureStorage — SecureStorage holds auth token only
  - google-services.json at app/src/main/java/.../google-services.json was untracked so no git rm needed, just deleted from disk
metrics:
  duration: "~25 min"
  completed: "2026-03-08"
  tasks_completed: 4
  tasks_total: 4
  files_modified: 3
  files_deleted: 1
---

# Phase 21 Plan 01: v1.1 Regression Fixes Summary

Four confirmed v1.1 regressions fixed — FCM token rotation, HCE token persistence, parent login error transparency, and stray google-services.json cleanup.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | FCMService sends token to backend on rotation | `4897a91` | `FCMService.kt` |
| 2 | Restore HCE virtual card token after process kill | `e383db3` | `BankoHceService.kt` |
| 3 | Parent login surfaces Sheets errors (not silent 401) | `62cac7e` | `admin_dashboard.py` |
| 4 | Delete misplaced google-services.json from java source tree | _(untracked file removed from disk)_ | _(no commit needed)_ |

## What Was Built

- **Task 1 — FCM token rotation:** `FCMService.onNewToken()` now calls `ApiClient.apiService.registerFCMToken(...).execute()` inside a coroutine when the user is already logged in. Previously the token was saved to SharedPreferences but never pushed to the backend on rotation, so push notifications silently stopped working after a token refresh.

- **Task 2 — HCE token persistence:** `BankoHceService.processCommandApdu()` now begins with a null-check that restores `currentToken` from `NfcManager.getInstance(applicationContext).getVirtualToken()` if it is null (lost after Android kills the process). Recovery is logged to logcat at DEBUG level.

- **Task 3 — Parent login error transparency:** The `except Exception: pass` in the parent login handler was replaced with typed handlers: `ConnectionError`/`TimeoutError` → 503 + `logger.error`, generic `Exception` → 500 + `logger.error`. Parents now see a real error instead of a silent 401 when Google Sheets is unavailable.

- **Task 4 — google-services.json cleanup:** `app/src/main/java/com/bankongseton/student/google-services.json` was never committed to git (untracked). Deleted from disk. The correct copy at `app/src/google-services.json` is untouched.

## Deviations from Plan

### Discoveries (no code impact)

**1. Plan method name wrong** — Plan referred to `processApdu()` but the actual method is `processCommandApdu()`. Fixed inline.

**2. SecureStorage does not hold NFC token** — Plan suggested `SecureStorage.getToken(applicationContext)`. Inspection of `SecureStorage.kt` confirmed it only holds auth token, student ID, and UI prefs. The virtual card token is stored in `NfcManager`'s own `EncryptedSharedPreferences` (`banko_nfc_secure`). Fixed to use `NfcManager.getInstance(applicationContext).getVirtualToken()`.

**3. One misplaced file already absent** — `app/google-services.json` did not exist (already removed previously). Only one file needed deletion.

**4. Misplaced file was untracked** — `git rm` failed because the file was never committed. Deleted directly from disk; no git commit required.

**5. LSP errors in admin_dashboard.py** — 157 pre-existing type and import errors throughout the file. None caused by Task 3 changes. Logged as out-of-scope.

## Self-Check

### Files exist
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/FCMService.kt` ✅
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` ✅
- `backend/dashboard/admin_dashboard.py` ✅
- `mobile/student_app_v2/app/src/google-services.json` (correct location) ✅
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/google-services.json` (deleted) ✅

### Commits exist
- `4897a91` fix(21-01): FCMService sends token to backend on rotation ✅
- `e383db3` fix(21-01): restore HCE virtual card token from storage after process kill ✅
- `62cac7e` fix(21-01): parent login surfaces Sheets errors instead of silently swallowing ✅

## Self-Check: PASSED
