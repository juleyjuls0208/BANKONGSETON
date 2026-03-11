# Phase 27-02 Summary — Android Critical Fixes

**Completed:** 2026-03-09  
**Requirements:** REQ-BUG-MOB-02, REQ-SEC-02, REQ-SEC-03

## What Was Done

### Task 1: Android isCardLost fix in LoginActivity
- Added `if (loginResponse.student.status != "lost") { secureStorage.setCardLost(false) }` in the success callback of `performLogin()`, before navigation to HomeActivity
- Students whose cards have been reactivated will have the lost-card flag cleared on next login

### Task 2: Cleartext HTTP moved to debug-only source set
- Removed `android:usesCleartextTraffic="true"` from `app/src/main/AndroidManifest.xml` — production builds now enforce HTTPS-only
- Created `app/src/debug/res/xml/network_security_config.xml` allowing cleartext to `localhost` and `10.0.2.2` (emulator) only
- Created `app/src/debug/AndroidManifest.xml` that references the security config and uses `tools:node="merge"` — AGP automatically merges this into debug builds only

### Task 3: NFC payment state encapsulation
**BankoHceService (companion object):**
- Made `isPaymentAuthorized` and `currentToken` `private` (retaining `@Volatile`)
- Added public methods: `loadToken(token)`, `authorize(token)`, `deauthorize()`, `reauthorize()`, `isAuthorized()`
- `onDeactivated()` now calls `deauthorize()` instead of writing the field directly

**NfcManager.kt (6 write sites migrated):**
- Device registration: `BankoHceService.currentToken = token` → `BankoHceService.loadToken(token)`
- Unregister: `currentToken = null` + `isPaymentAuthorized = false` → `BankoHceService.deauthorize()`
- authenticateForPayment: `currentToken = getVirtualToken()` → `BankoHceService.loadToken(getVirtualToken()!!)`
- verifyPin success: `isPaymentAuthorized = true` → `BankoHceService.reauthorize()`
- onAuthenticationSucceeded: `isPaymentAuthorized = true` → `BankoHceService.reauthorize()`

**NfcPayOverlayActivity.kt (4 sites migrated):**
- onCreate: `isPaymentAuthorized = true` → `BankoHceService.reauthorize()`
- onResume read: `!BankoHceService.isPaymentAuthorized` → `!BankoHceService.isAuthorized()`
- onFinish (timer): `isPaymentAuthorized = false` → `BankoHceService.deauthorize()`
- cancelPayment: `isPaymentAuthorized = false` → `BankoHceService.deauthorize()`

## Files Modified
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt`
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt`

## Files Created
- `mobile/student_app_v2/app/src/debug/res/xml/network_security_config.xml`
- `mobile/student_app_v2/app/src/debug/AndroidManifest.xml`

## Verification
- `usesCleartextTraffic` absent from main AndroidManifest.xml ✅
- Zero direct writes to `BankoHceService.isPaymentAuthorized` or `BankoHceService.currentToken` in NfcManager.kt or NfcPayOverlayActivity.kt ✅
- Both fields private with `@Volatile` in BankoHceService companion object ✅
- Debug network security files created ✅
- `setCardLost(false)` called in LoginActivity on non-lost status ✅

## Notes
- `NfcManager.companion` has its own `currentToken` field (line 38) — this is a separate, unrelated field in NfcManager itself (not BankoHceService), appears unused. Left untouched.
- `loadToken()` was added alongside `authorize()` because two call sites needed to load a token without immediately authorizing payment (device registration and pre-biometric load). This preserves the existing authorization flow where auth happens separately (biometric/PIN step) from token loading.
