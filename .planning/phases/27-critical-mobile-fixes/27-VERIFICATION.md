---
phase: 27-critical-mobile-fixes
verified: 2026-03-09T00:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 27: Critical Mobile Fixes — Verification Report

**Phase Goal:** Lost card state persists across app restarts on both platforms; iOS never crashes via `fatalError`; Android release build uses HTTPS only and NFC payment authorization is not publicly bypassable.  
**Verified:** 2026-03-09  
**Status:** ✅ PASSED  
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | After a card is reported lost and then replaced (status returns to active), the student can successfully log in on iOS and their card is no longer treated as lost | ✓ VERIFIED | `AuthManager.login()` L22: `if student.cardStatus == "active" { KeychainHelper.delete(forKey: "isCardLost") }` |
| 2 | Invalid URLs in APIClient never crash the app with a `fatalError` — they throw a recoverable error instead | ✓ VERIFIED | Zero `fatalError` calls in `APIClient.swift`; `case invalidURL` at L11; throws at L31, L75 |
| 3 | The `isCardLost` flag in Keychain is NOT deleted during `clearAll()`, so it persists correctly across logout | ✓ VERIFIED | `keysToDelete` array (L45–54) contains 8 keys — `"isCardLost"` is absent; only deleted in `login()` when card is active |
| 4 | After a card is reported lost and then reactivated, the student can log in on Android and their card is no longer treated as lost | ✓ VERIFIED | `LoginActivity.kt` L63–64: `if (loginResponse.student.status != "lost") { secureStorage.setCardLost(false) }` placed before navigation |
| 5 | The production Android app does NOT allow cleartext (HTTP) traffic — only HTTPS is permitted in release builds | ✓ VERIFIED | `usesCleartextTraffic` count in main `AndroidManifest.xml` = 0; attribute fully removed |
| 6 | Debug builds still allow cleartext to localhost and 10.0.2.2 (emulator) for development | ✓ VERIFIED | `app/src/debug/res/xml/network_security_config.xml` exists with `localhost` + `10.0.2.2` exceptions; `app/src/debug/AndroidManifest.xml` merges it via `tools:node="merge"` |
| 7 | NFC payment state (`isPaymentAuthorized`, `currentToken`) cannot be set arbitrarily by outside classes — access goes through controlled methods | ✓ VERIFIED | Both fields `private` in `BankoHceService` companion (L41, L45); `authorize()`, `deauthorize()`, `reauthorize()`, `isAuthorized()` public; zero direct writes in `NfcManager.kt` or `NfcPayOverlayActivity.kt` |

**Score:** 7/7 truths verified

---

## Required Artifacts

### Plan 27-01 Artifacts

| Artifact | Expected | Status | Evidence |
|----------|----------|--------|---------|
| `mobile/ios/BankongSetonStudent/Models/LoginModels.swift` | Student model with optional `cardStatus` field | ✓ VERIFIED | L20: `let cardStatus: String?` with CodingKey `"card_status"` at L25 |
| `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` | `APIError` enum with `invalidURL` case; zero `fatalError` calls | ✓ VERIFIED | `case invalidURL` at L11; `fatalError` count = 0; throws at L31, L75 |
| `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` | `clearAll()` without `isCardLost` deletion + `login()` with active-status clearance | ✓ VERIFIED | `isCardLost` absent from `keysToDelete`; deleted in `login()` at L23 when `cardStatus == "active"` |

### Plan 27-02 Artifacts

| Artifact | Expected | Status | Evidence |
|----------|----------|--------|---------|
| `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt` | Login success handler calls `setCardLost(false)` when card not lost | ✓ VERIFIED | L63–64: `if (loginResponse.student.status != "lost") { secureStorage.setCardLost(false) }` |
| `mobile/student_app_v2/app/src/main/AndroidManifest.xml` | Main manifest without `usesCleartextTraffic=true` | ✓ VERIFIED | Attribute fully absent; manifest confirmed clean |
| `mobile/student_app_v2/app/src/debug/res/xml/network_security_config.xml` | Debug network security config allowing localhost cleartext | ✓ VERIFIED | File exists; `localhost` + `10.0.2.2` with `cleartextTrafficPermitted="true"` |
| `mobile/student_app_v2/app/src/debug/AndroidManifest.xml` | Debug manifest referencing network security config | ✓ VERIFIED | File exists; references `@xml/network_security_config` with `tools:node="merge"` |
| `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` | NFC state fields private with `fun authorize(` accessor | ✓ VERIFIED | `private var currentToken` L41, `private var isPaymentAuthorized` L45, `@Volatile` on both; `authorize()` L51, `deauthorize()` L56, `reauthorize()` L61, `isAuthorized()` L68 |

---

## Key Link Verification

### Plan 27-01 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|---------|
| `AuthManager.login()` | `student.cardStatus` | login response model | ✓ WIRED | `if student.cardStatus == "active"` at L22 — field decoded from `"card_status"` JSON key |
| `AuthManager.clearAll()` | `keysToDelete` array | Keychain removal | ✓ WIRED (negative) | `"isCardLost"` is NOT in `keysToDelete` array (8 keys, none matching `isCardLost`) — correct behavior confirmed |

### Plan 27-02 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|---------|
| `LoginActivity.performLogin()` | `SecureStorage.setCardLost()` | login success callback | ✓ WIRED | L63–64: condition + `secureStorage.setCardLost(false)` inside `onResponse` success branch |
| `NfcManager.kt` | `BankoHceService.authorize()` | method calls replacing direct field writes | ✓ WIRED | L124: `loadToken(token)`, L175: `loadToken(getVirtualToken()!!)`, L190/207: `reauthorize()`; zero remaining direct writes |
| `NfcPayOverlayActivity.kt` | `BankoHceService.reauthorize()` | method call (no token available in overlay) | ✓ WIRED | L29: `BankoHceService.reauthorize()` for true case; L42: `BankoHceService.isAuthorized()` for read; L56, L66: `deauthorize()` for false cases |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| REQ-BUG-MOB-01 | 27-01 | Fix iOS `AuthManager` — `isCardLost` wiped by `clearAll()`, never persists | ✓ SATISFIED | `"isCardLost"` removed from `keysToDelete`; login re-clears when card is active |
| REQ-BUG-MOB-02 | 27-02 | Fix Android `handleCardLost()` — `isCardLost` deleted immediately after being set | ✓ SATISFIED | `LoginActivity` now calls `setCardLost(false)` on non-lost login response |
| REQ-BUG-MOB-03 | 27-01 | Remove `fatalError()` calls in iOS `APIClient.swift` | ✓ SATISFIED | Zero `fatalError` calls; replaced with `throw APIError.invalidURL` at two sites |
| REQ-SEC-02 | 27-02 | Prevent NFC payment authorization bypass — public writable static fields | ✓ SATISFIED | Both fields `private`; all write paths go through `authorize()` / `deauthorize()` / `reauthorize()` |
| REQ-SEC-03 | 27-02 | Remove `usesCleartextTraffic="true"` from Android release manifest | ✓ SATISFIED | Attribute absent from main manifest; debug-only exceptions via `src/debug/` source set |

**All 5 requirement IDs accounted for. No orphaned requirements.**

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| — | — | — | No TODOs, FIXMEs, placeholders, empty implementations, or console-only handlers found in any modified file |

---

## Human Verification Required

### 1. iOS Lost Card — End-to-End Flow

**Test:** Log in with a student whose card was previously marked lost (isCardLost = true in Keychain). Confirm the app loads the home screen normally without showing the "card lost" overlay.  
**Expected:** Home screen appears; lost-card UI is absent.  
**Why human:** Requires a live iOS Simulator + Keychain state setup with a seeded `isCardLost=true` value and a mocked login response with `cardStatus: "active"`.

### 2. Android HTTPS Enforcement in Release Build

**Test:** Build a release APK and perform a MITM proxy (e.g., Charles Proxy) intercept of API calls.  
**Expected:** All connections are HTTPS; cleartext HTTP is rejected/fails.  
**Why human:** Network policy enforcement is a runtime behavior that grep cannot validate — requires actual APK + proxy tooling.

### 3. NFC Payment Authorization Bypass Resistance

**Test:** Attempt to trigger a payment authorization without completing biometric/PIN by calling `reauthorize()` when no token is loaded.  
**Expected:** `reauthorize()` is a no-op when `currentToken == null`; payment is not authorized.  
**Why human:** Requires a device with NFC HCE support and an end-to-end payment terminal to confirm the safeguard holds at runtime.

---

## Gaps Summary

No gaps. All 7 observable truths verified, all 8 artifacts confirmed substantive and wired, all 5 requirement IDs satisfied.

**Notable design choice (no gap):** `BankoHceService` added a `loadToken()` method alongside `authorize()` to handle the two call sites (device registration, pre-biometric load) that load a token without immediately authorizing — this preserves the existing two-step flow (load → biometric/PIN → authorize) and is consistent with the requirement's intent of removing public write access.

---

_Verified: 2026-03-09_  
_Verifier: Claude (gsd-verifier)_
