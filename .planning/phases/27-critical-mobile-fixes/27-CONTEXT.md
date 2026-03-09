# Phase 27 Context: Critical Mobile Fixes

## Phase Goal

Fix four production bugs and two security issues across iOS and Android mobile apps:
- Lost card state not persisting across app restarts (iOS + Android)
- iOS crashes via `fatalError()` on bad URLs
- Android release build allows HTTP cleartext traffic
- NFC payment authorization fields are publicly writable

Requirements: REQ-BUG-MOB-01, REQ-BUG-MOB-02, REQ-BUG-MOB-03, REQ-SEC-02, REQ-SEC-03

---

## Locked Decisions

### 1. Lost card flag lifecycle (REQ-BUG-MOB-01, REQ-BUG-MOB-02)

**iOS fix:** Remove `"isCardLost"` from the `keysToDelete` array inside `AuthManager.clearAll()`. The flag must survive app kills and restarts. It is intentionally cleared on explicit logout (when user taps "Log out" — `clearAll()` is called at that point, which is correct behavior).

**Android fix:** Scope is `student_app_v2` only. The legacy `mobile/android` app is out of scope for Phase 27.

**Clearance strategy:** The `isCardLost` flag is cleared backend-driven on next successful login. If the backend returns an active/non-lost card status after login, the app clears the local flag. No separate API call or manual step required.

**Flag lifecycle summary:**
- Set: when user reports card lost
- Survives: app kill, app restart
- Cleared: on explicit logout OR on next successful login if backend confirms card is active

### 2. iOS fatalError replacement (REQ-BUG-MOB-03)

Replace both `fatalError()` calls in `APIClient.swift` with thrown errors. Use `APIError.invalidURL` (or create that case if it doesn't exist). The method already `throws`, so callers already handle errors. No silent swallowing — the error propagates up and the UI handles it like any other network error.

Files affected:
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — line ~27 in `authenticatedRequest()`, line ~70 in `login()`

### 3. Android HTTPS-only (REQ-SEC-03)

Scope is `student_app_v2` only. The legacy `mobile/android` app is out of scope.

**Fix:** Remove `android:usesCleartextTraffic="true"` from the main `AndroidManifest.xml`.

**Dev workaround:** Add a `network_security_config.xml` under `src/debug/res/xml/` (or a debug-flavor manifest override) that permits cleartext traffic to `localhost` and `10.0.2.2` (Android emulator host). Reference it from the debug manifest via `android:networkSecurityConfig`. This keeps the release build HTTPS-only while allowing local Flask HTTP dev.

Files affected:
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — remove `usesCleartextTraffic`
- `mobile/student_app_v2/app/src/debug/res/xml/network_security_config.xml` — new file (localhost exception)
- `mobile/student_app_v2/app/src/debug/AndroidManifest.xml` — new or updated (reference security config)

### 4. NFC authorization encapsulation (REQ-SEC-02)

Scope is `student_app_v2` only.

**Fix:** Make `isPaymentAuthorized` and `currentToken` private in `BankoHceService` companion object. Expose a controlled API:

```kotlin
// in BankoHceService companion object
fun authorize(token: String) { currentToken = token; isPaymentAuthorized = true }
fun deauthorize() { currentToken = null; isPaymentAuthorized = false }
```

All external callers (`NfcManager`, `NfcPayOverlayActivity`, and any other class currently setting these fields directly) must be updated to call `authorize()`/`deauthorize()` instead.

Files affected:
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt`
- Any other file in `student_app_v2` that writes to `BankoHceService.isPaymentAuthorized` or `BankoHceService.currentToken` directly

---

## Carried-Forward Decisions

From Phase 16 context:
- `BankoHceService` is the HCE service; companion object holds auth state. Coroutine pattern used in `NfcManager`.

From Phase 23 context:
- iOS app targets minimum iOS 16, uses SwiftUI, Keychain for auth token storage.
- `AuthManager` is the single source of truth for auth state on iOS.

---

## Out of Scope

- Legacy `mobile/android` app — not fixed in this phase
- Card replacement flow UI (how the student activates a replacement card) — the flag clearance on next login is sufficient for Phase 27
- Any changes to the Flask backend
- NFC auth changes on iOS (no equivalent issue found)

---

## Research Needed (for planner)

1. **Android `isCardLost` in `student_app_v2`**: Confirm whether `clearAuth()` in `SecureStorage.kt` already preserves `isCardLost` or also wipes it. The `SettingsActivity` flow appears to call `setCardLost(true)` before `clearAuth()` — verify order and whether `clearAuth()` deletes the flag.

2. **iOS login response shape**: Confirm whether the login API response currently includes a card status field that could drive the "clear isCardLost on active card" behavior, or if that check needs to be added to the login flow.

3. **APIError enum in Swift**: Confirm current cases in `APIError` to know whether `invalidURL` exists or needs to be added.

4. **`student_app_v2` debug flavor**: Confirm whether a `debug` source set / flavor already exists in `build.gradle` or if it needs to be created for the network security config.

5. **Callers of `BankoHceService` auth fields**: Do a full grep for `isPaymentAuthorized` and `currentToken` in `student_app_v2` to enumerate all write sites before encapsulation.
