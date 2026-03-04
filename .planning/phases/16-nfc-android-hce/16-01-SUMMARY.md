---
phase: "16-nfc-android-hce"
plan: "16-01"
subsystem: "mobile/student_app_v2 NFC/HCE"
tags: ["nfc", "hce", "android", "biometric", "kotlin", "retrofit"]
dependency_graph:
  requires: []
  provides: ["BankoHceService", "NfcManager", "NFC API endpoints"]
  affects: ["mobile/student_app_v2/app"]
tech_stack:
  added: ["androidx.biometric:biometric:1.1.0"]
  patterns: ["HostApduService", "EncryptedSharedPreferences", "BiometricPrompt", "coroutines for network calls"]
key_files:
  created:
    - "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt"
    - "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt"
  modified:
    - "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt"
    - "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt"
    - "mobile/student_app_v2/app/build.gradle.kts"
    - "mobile/student_app_v2/app/src/main/AndroidManifest.xml"
decisions:
  - "Used existing hce_service.xml (AID F042414E4B4F4E475345544F4E) instead of creating apdu_service.xml — AID matches cashier reader"
  - "NfcManager uses coroutines (CoroutineScope + suspend fun) instead of Retrofit .enqueue() callbacks to match student_app_v2 ApiClient pattern"
  - "authToken parameter added to registerDevice/unregisterDevice (not in legacy) to pass JWT Bearer token to NFC endpoints"
metrics:
  duration: "~4 minutes"
  completed: "2026-03-05"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 4
---

# Phase 16 Plan 01: Android HCE Infrastructure Port Summary

**One-liner:** Ported Android HCE NFC payment infrastructure (BankoHceService + NfcManager) into student_app_v2 with coroutine-based API calls and biometric/PIN authentication.

## What Was Built

Ported the NFC Host Card Emulation (HCE) infrastructure from the legacy `mobile/android` app into `mobile/student_app_v2`, establishing the foundational files for NFC payments:

1. **`Models.kt`** — Added three new data classes: `NfcDeviceRequest`, `NfcRegistrationResponse`, `NfcUnregisterRequest`
2. **`ApiClient.kt`** — Added `registerNfcDevice` and `unregisterNfcDevice` suspend endpoints to `BangkoApiService`
3. **`build.gradle.kts`** — Added `androidx.biometric:biometric:1.1.0` dependency
4. **`BankoHceService.kt`** — Full HCE service implementation extending `HostApduService`; responds to SELECT APDU with virtual card token; resets `isPaymentAuthorized` on each deactivation
5. **`NfcManager.kt`** — Device registration/unregistration via coroutines; biometric prompt (with PIN fallback via `NEEDS_PIN` callback signal); encrypted token storage using `EncryptedSharedPreferences`
6. **`AndroidManifest.xml`** — Added `NFC`, `USE_BIOMETRIC` permissions, `android.hardware.nfc.hce` feature (`required=false`), and `BankoHceService` service declaration referencing `@xml/hce_service`

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Models, ApiClient NFC endpoints, biometric dependency | `c3ef71b` |
| 2 | BankoHceService, NfcManager, AndroidManifest NFC declarations | `a6d87c6` |

## Verification

- `compileDebugKotlin` — BUILD SUCCESSFUL (zero errors)
- `assembleDebug` — BUILD SUCCESSFUL (36 tasks)
- `grep "BankoHceService" AndroidManifest.xml` — returns service declaration ✓
- `grep "registerNfcDevice\|unregisterNfcDevice" ApiClient.kt` — returns 2 lines ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used existing `hce_service.xml` instead of creating `apdu_service.xml`**
- **Found during:** Task 2
- **Issue:** Plan said to create `apdu_service.xml` with AID `F0394148148100`, but `hce_service.xml` already existed in the project with the correct AID `F042414E4B4F4E475345544F4E` ("BANKONGSETON" in hex). The plan itself noted "Use the same AID as in the legacy app to match the cashier reader configuration" — the existing file already satisfies this.
- **Fix:** AndroidManifest `meta-data` references `@xml/hce_service` (existing) instead of `@xml/apdu_service`. No new XML file created.
- **Files modified:** `AndroidManifest.xml`
- **Commit:** `a6d87c6`

**2. [Rule 1 - Bug] Rewrote NfcManager to use coroutines instead of Retrofit `.enqueue()`**
- **Found during:** Task 2
- **Issue:** Legacy `NfcManager.kt` used `ApiClient.getInstance(context)` with callback-based `.enqueue()`. The student_app_v2 `ApiClient` is a singleton (`ApiClient.apiService`) and the new NFC endpoints are `suspend fun`.
- **Fix:** `NfcManager.registerDevice` and `unregisterDevice` use `CoroutineScope(Dispatchers.IO).launch` with `withContext(Dispatchers.Main)` for UI callbacks.
- **Files modified:** `NfcManager.kt`
- **Commit:** `a6d87c6`

**3. [Rule 2 - Missing functionality] Added `authToken` parameter to `registerDevice`/`unregisterDevice`**
- **Found during:** Task 2
- **Issue:** Legacy NfcManager did not pass an auth token (server-side auth may have been different). student_app_v2 uses JWT Bearer tokens for all API calls.
- **Fix:** Both methods accept `authToken: String` and pass `"Bearer $authToken"` in the Authorization header.
- **Files modified:** `NfcManager.kt`
- **Commit:** `a6d87c6`

## Self-Check: PASSED
- `BankoHceService.kt` exists ✓
- `NfcManager.kt` exists ✓
- `AndroidManifest.xml` updated ✓
- Commit `c3ef71b` exists ✓
- Commit `a6d87c6` exists ✓
- `assembleDebug` BUILD SUCCESSFUL ✓
