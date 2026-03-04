---
phase: 16-nfc-android-hce
plan: "04"
subsystem: android-nfc-ui
tags: [android, nfc, hce, ui, payment-flow]
dependency_graph:
  requires: [16-01]
  provides: [NfcPayOverlayActivity, HomeActivity-nfc-button]
  affects: [HomeActivity, NfcPayOverlayActivity, BankoHceService]
tech_stack:
  added: []
  patterns: [CountDownTimer, startActivityForResult, BiometricPrompt-PIN-fallback, AlertDialog-PIN]
key_files:
  created:
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt
    - mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml
  modified:
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
    - mobile/student_app_v2/app/src/main/res/layout/activity_home.xml
    - mobile/student_app_v2/app/src/main/AndroidManifest.xml
decisions:
  - "Used instance-based NfcManager.getInstance(this) calls — NfcManager is not a companion/static singleton"
  - "BankoHceService.isPaymentAuthorized (not NfcManager.isPaymentAuthorized) — payment auth flag lives on BankoHceService companion"
  - "PIN fallback via AlertDialog + NfcManager.verifyPin() — plan noted inline biometric code; used existing verifyPin() API instead"
  - "onResume polling pattern for HCE deactivation signal — avoids LocalBroadcastManager complexity; simple and correct"
  - "startActivityForResult kept (deprecated but functional) — existing codebase uses it; switching to ActivityResultLauncher is out of scope"
metrics:
  duration: "~10 min"
  completed_date: "2026-03-05"
  tasks_completed: 2
  files_changed: 5
---

# Phase 16 Plan 04: NFC Pay Overlay + HomeActivity Button Summary

Full NFC payment activation UI: "Activate NFC Pay" button on HomeActivity with biometric/PIN auth gate, and full-screen `NfcPayOverlayActivity` with 30-second countdown timer.

## What Was Built

### Task 1: NfcPayOverlayActivity + Layout (commit: 46ac70f)

**`activity_nfc_pay_overlay.xml`** — full-screen black overlay:
- NFC share icon (120dp, white tint)
- `instructionText`: "Hold phone to terminal" (22sp bold, white)
- `countdownText`: "30" (64sp bold, white) — live countdown
- "seconds remaining" label (14sp, #AAAAAA)
- `cancelButton`: OutlinedButton "Cancel" (white text)

**`NfcPayOverlayActivity.kt`** — payment-ready overlay controller:
- Sets `BankoHceService.isPaymentAuthorized = true` in `onCreate()`
- `CountDownTimer(30_000L, 1_000L)` — updates `countdownText` each second
- Timer expiry: clears auth flag, `setResult(RESULT_CANCELED)`, finish
- Cancel button: sets `userCancelled = true`, clears flag, `RESULT_CANCELED`
- `onResume()` polling: if `!userCancelled && !BankoHceService.isPaymentAuthorized` → `setResult(RESULT_OK)`, finish (catches HCE deactivation after terminal tap)
- `onDestroy()` cancels timer to prevent leaks

**`AndroidManifest.xml`** — registers `NfcPayOverlayActivity`:
- Theme: `Theme.AppCompat.NoActionBar`
- `screenOrientation="portrait"`, `exported="false"`

### Task 2: HomeActivity NFC Button (commit: 553dd5a)

**`activity_home.xml`** — added `activateNfcPayButton`:
- `MaterialButton`, `match_parent` width, `marginTop=12dp`
- `visibility="gone"` (shown only when NFC + registered)

**`HomeActivity.kt`** — NFC payment button wiring:
- `activateNfcPayButton: MaterialButton` field + `REQUEST_NFC_PAY = 1001` companion constant
- **`refreshNfcButton()`** helper: `isNfcAvailable() && isDeviceRegistered()` → `VISIBLE`, else `GONE`
- `onResume()` calls `refreshNfcButton()` on every resume
- **Click listener**: `NfcManager.getInstance(this).authenticateForPayment(...)` → on success launches `NfcPayOverlayActivity` via `startActivityForResult`
- **PIN fallback**: `onFailure("NEEDS_PIN")` → `showPinDialog()` with `AlertDialog` + number password input → `verifyPin()` → launch overlay
- **`onActivityResult`**: `REQUEST_NFC_PAY + RESULT_OK` → Toast "Payment successful" + `loadBalance()`

## Deviations from Plan

### Auto-corrected API calls

**[Rule 1 - Bug] Used instance-based NfcManager calls**
- **Found during:** Task 2 (reading NfcManager.kt before writing HomeActivity)
- **Issue:** Plan described `NfcManager.isNfcAvailable(this)` as static/companion calls, but `NfcManager` is a private-constructor singleton with `getInstance(context)` — no companion methods for these
- **Fix:** Used `NfcManager.getInstance(this).isNfcAvailable()` and `NfcManager.getInstance(this).isDeviceRegistered()`
- **Files modified:** HomeActivity.kt
- **Impact:** Zero — compile-correct

**[Rule 1 - Bug] Used BankoHceService.isPaymentAuthorized (not NfcManager.isPaymentAuthorized)**
- **Found during:** Task 1 (reading BankoHceService.kt)
- **Issue:** Plan referenced `NfcManager.isPaymentAuthorized` as a companion field — this field does not exist on NfcManager; it lives on `BankoHceService`
- **Fix:** Both `NfcPayOverlayActivity.kt` and `HomeActivity.kt` use `BankoHceService.isPaymentAuthorized`
- **Files modified:** NfcPayOverlayActivity.kt
- **Impact:** Zero — correct implementation

**[Rule 2 - Missing functionality] PIN fallback dialog added**
- **Found during:** Task 2 (reading NfcManager.authenticateForPayment signature)
- **Issue:** `authenticateForPayment()` signals `onFailure("NEEDS_PIN")` when no biometrics — plan mentioned inline biometric code but didn't provide PIN dialog implementation
- **Fix:** Added `showPinDialog()` with `AlertDialog` + masked number input → `NfcManager.verifyPin()` → launch overlay on success
- **Files modified:** HomeActivity.kt
- **Impact:** Devices without biometrics now fully supported

## Build Verification

```
BUILD SUCCESSFUL in 4s
17 actionable tasks: 11 executed, 6 up-to-date
```

Zero Kotlin errors. Four deprecation warnings (FLAG_FULLSCREEN, startActivityForResult x2, unused param) — all acceptable; these APIs are deprecated but functional across all target API levels.

Pattern verification:
```
activateNfcPayButton ✓  refreshNfcButton ✓  REQUEST_NFC_PAY ✓  NfcPayOverlayActivity ✓
```

## What Remains

**Task 3 (checkpoint:human-verify)** — physical device testing required:
- Install debug APK on NFC-capable Android device
- Verify end-to-end: login → Settings NFC setup → Home button visible → biometric/PIN auth → overlay countdown → cancel/expire/terminal tap

## Self-Check: PASSED

- `NfcPayOverlayActivity.kt` ✓ exists
- `activity_nfc_pay_overlay.xml` ✓ exists
- `HomeActivity.kt` ✓ updated (all 4 patterns present)
- `activity_home.xml` ✓ updated (activateNfcPayButton present)
- `AndroidManifest.xml` ✓ updated (NfcPayOverlayActivity declared)
- Task 1 commit: `46ac70f` ✓
- Task 2 commit: `553dd5a` ✓
