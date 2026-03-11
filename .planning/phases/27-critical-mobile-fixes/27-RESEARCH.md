# Phase 27: Critical Mobile Fixes - Research

**Researched:** 2026-03-09
**Domain:** iOS Swift / Android Kotlin mobile bug fixes and security hardening
**Confidence:** HIGH (all findings from direct codebase inspection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

1. **Lost card flag lifecycle (REQ-BUG-MOB-01, REQ-BUG-MOB-02)**
   - **iOS fix:** Remove `"isCardLost"` from the `keysToDelete` array inside `AuthManager.clearAll()`. Flag survives app kills/restarts. Cleared on explicit logout (correct) or backend-driven on next successful login if card is active.
   - **Android fix:** Scope is `student_app_v2` only. Legacy `mobile/android` is out of scope.
   - **Clearance strategy:** Backend-driven — if login response confirms card is active, app clears local flag. No separate API call.

2. **iOS fatalError replacement (REQ-BUG-MOB-03)**
   - Replace both `fatalError()` calls in `APIClient.swift` with thrown errors using `APIError.invalidURL` (or create that case).
   - Lines: ~27 in `authenticatedRequest()`, ~70 in `login()`
   - Method already `throws`; error propagates up like any other network error.

3. **Android HTTPS-only (REQ-SEC-03)**
   - Remove `android:usesCleartextTraffic="true"` from main `AndroidManifest.xml`.
   - Add `network_security_config.xml` under `src/debug/res/xml/` permitting cleartext to `localhost` and `10.0.2.2`.
   - Reference from debug manifest via `android:networkSecurityConfig`.

4. **NFC authorization encapsulation (REQ-SEC-02)**
   - Make `isPaymentAuthorized` and `currentToken` private in `BankoHceService` companion.
   - Expose `authorize(token: String)` and `deauthorize()` methods.
   - All external callers must be updated.

### Claude's Discretion

(None specified in CONTEXT.md beyond the locked decisions above.)

### Deferred Ideas (OUT OF SCOPE)

- Legacy `mobile/android` app — not fixed in this phase
- Card replacement flow UI — flag clearance on next login is sufficient
- Any changes to the Flask backend
- NFC auth changes on iOS
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-BUG-MOB-01 | Fix iOS `AuthManager.handleCardLost()` — saves `isCardLost` then immediately clears it via `clearAll()`; lost card state never persists | **Confirmed bug:** `clearAll()` deletes `"isCardLost"` from Keychain at line 48. Fix = remove that key from the `keysToDelete` array. Need to add login-side clearance logic since `LoginResponse` has no card status field today. |
| REQ-BUG-MOB-02 | Fix Android `handleCardLost()` — same `isCardLost` flag deleted immediately after being set; never persists | **Confirmed bug:** `SecureStorage.clearAuth()` only removes `KEY_AUTH_TOKEN` + `KEY_STUDENT_ID` — `isCardLost` is NOT wiped by `clearAuth()`. The bug is different from iOS: `SettingsActivity.reportLostCard()` correctly calls `setCardLost(true)` and `clearAuth()` never removes it. See Research Q1 below for full analysis. |
| REQ-BUG-MOB-03 | Remove `fatalError()` calls in iOS `APIClient.swift` | **Confirmed:** Two `fatalError()` calls found. `APIError` enum does NOT have `invalidURL` case — must be added. |
| REQ-SEC-02 | Prevent NFC payment authorization bypass — `isPaymentAuthorized` and `currentToken` are public writable static fields | **Confirmed:** Both fields are `@Volatile var` with default Kotlin visibility (public). Three write-sites enumerated: `NfcManager.kt` (5 writes), `NfcPayOverlayActivity.kt` (4 writes), `BankoHceService.kt` (1 internal write in `processCommandApdu`). |
| REQ-SEC-03 | Remove `usesCleartextTraffic="true"` from Android release manifest | **Confirmed:** `android:usesCleartextTraffic="true"` present in `app/src/main/AndroidManifest.xml` line 17. No debug source set exists yet. |
</phase_requirements>

---

## Summary

Phase 27 addresses four production bugs and two security issues across the iOS and Android `student_app_v2` apps. All five targeted requirements have been verified by direct codebase inspection with HIGH confidence.

**Key finding — Android bug (REQ-BUG-MOB-02) is different from iOS:** The iOS bug is that `clearAll()` deletes `isCardLost` (confirmed). The Android bug, however, is subtler: `SecureStorage.clearAuth()` does NOT delete `isCardLost` — the real Android problem is that `LoginActivity` doesn't clear the flag on successful login when the backend confirms an active card. The `SettingsActivity.reportLostCard()` flow correctly sets the flag and `clearAuth()` preserves it, so the Android persistence fix is primarily about the login-side clearance strategy, not a duplicate-delete problem.

**Key finding — APIError.invalidURL does not exist:** The Swift `APIError` enum has 5 cases (`cardLost`, `unauthorized`, `httpError(Int)`, `decodingError(Error)`, `networkError(Error)`) and `invalidURL` is not among them. It must be added.

**Key finding — debug source set does not exist:** Only `app/src/main/` exists; no `app/src/debug/` directory. Both the debug manifest and `network_security_config.xml` need to be created from scratch.

**Primary recommendation:** Execute as four independent tasks in one plan — each fix is self-contained with no cross-dependencies.

---

## Research Q&A (from CONTEXT.md "Research Needed")

### Q1: Android `isCardLost` — Does `clearAuth()` preserve it?

**CONFIRMED: `clearAuth()` ALREADY PRESERVES `isCardLost`.**

`SecureStorage.clearAuth()` (lines 68-72):
```kotlin
fun clearAuth() {
    sharedPreferences.edit()
        .remove(KEY_AUTH_TOKEN)
        .remove(KEY_STUDENT_ID)
        .apply()
}
```
It removes only `KEY_AUTH_TOKEN` and `KEY_STUDENT_ID`. `KEY_IS_CARD_LOST` is not removed.

**`SettingsActivity` flow order:**
1. `reportLostCard()` calls `ApiClient.apiService.reportLostCard(...)` 
2. On success: `secureStorage.setCardLost(true)` — flag is SET
3. `completeLogout()` later calls `secureStorage.clearAuth()` — flag is **PRESERVED** because `clearAuth()` doesn't touch it
4. So Android already persists the flag correctly across app restarts from `SettingsActivity`

**Implication for REQ-BUG-MOB-02:** The Android "fix" per the locked decision is the **login-side clearance** — the `LoginActivity` needs to check `loginResponse.student.status` after a successful login and call `secureStorage.setCardLost(false)` if the card is active. The `Student` model already has a `status: String` field from the API.

**The bug Android actually has:** After reporting lost and then successfully logging in with a replacement/reactivated card, the `isCardLost` flag is never cleared because `LoginActivity` ignores `student.status`. So the user is stuck seeing "card reported lost" permanently.

### Q2: iOS login response — Does it include a card status field?

**CONFIRMED: `LoginResponse` does NOT include a card status field.**

iOS `LoginResponse` (from `LoginModels.swift`):
```swift
struct LoginResponse: Codable {
    let token: String
    let student: Student
}

struct Student: Codable {
    let studentId: String
    let name: String
    // No status field
}
```

**Implication:** To implement "clear `isCardLost` on successful login if card is active," the iOS `LoginViewModel.login()` must add a post-login check. Options:
1. **Option A (minimal):** After successful login, unconditionally clear `isCardLost` from Keychain (reasoning: a successful login itself implies the card is active enough for authentication). This is safe because the backend will return 403 + CARD_LOST on subsequent API calls if the card is still blocked.
2. **Option B (strict):** Add `cardStatus: String?` to iOS `Student` model and clear the flag only when `status == "active"`.

The Android `Student` model already has `status: String` from the API response, confirming the backend sends it. Option B is more correct but requires a model change. Option A is a 1-line fix. **The locked decision says "if the backend returns an active/non-lost card status" — Option B aligns with this.**

### Q3: `APIError` enum in Swift — Does `invalidURL` exist?

**CONFIRMED: `invalidURL` does NOT exist. Must be added.**

Current `APIError` enum cases (from `APIClient.swift` lines 1-10):
```swift
enum APIError: Error {
    case cardLost          // 403 + body["error"] == "CARD_LOST"
    case unauthorized      // 403 (any other body)
    case httpError(Int)    // non-2xx other than 403
    case decodingError(Error)
    case networkError(Error)
}
```

The fix must add `case invalidURL` as a sixth case, then replace both `fatalError()` calls:
- Line ~27: `fatalError("Invalid URL for path: \(path)")` → `throw APIError.invalidURL`
- Line ~70: `fatalError("Invalid login URL")` → `throw APIError.invalidURL`

No callers need to be updated since `APIError` conforms to `Error` and callers already catch `APIError.*` exhaustively using `catch error` fallbacks.

### Q4: `student_app_v2` debug source set — Does it already exist?

**CONFIRMED: No debug source set exists. Must be created.**

Directory listing of `app/src/`:
```
app/src/
└── main/          ← only source set
```

No `app/src/debug/` directory exists. The Android Gradle build system automatically merges a `src/debug/` source set when building debug variants — it does not need to be declared in `build.gradle.kts` because `debug` is a built-in build type.

**What must be created:**
1. `app/src/debug/` directory (will be auto-recognized by AGP 8.3.2)
2. `app/src/debug/res/xml/network_security_config.xml` — cleartext exceptions for localhost/emulator
3. `app/src/debug/AndroidManifest.xml` — references the security config

The existing `build.gradle.kts` uses AGP 8.3.2 with a `release` build type defined. The implicit `debug` build type requires no `build.gradle.kts` changes.

### Q5: All write sites for `BankoHceService.isPaymentAuthorized` and `currentToken`

**CONFIRMED: Full enumeration from grep.**

#### `BankoHceService.currentToken` write sites:
| File | Line | Operation | Context |
|------|------|-----------|---------|
| `NfcManager.kt` | 124 | `= token` | After successful device registration — store token in HCE |
| `NfcManager.kt` | 156 | `= null` | `unregisterDevice()` cleanup |
| `NfcManager.kt` | 176 | `= getVirtualToken()` | `authenticateForPayment()` — loads token before auth prompt |
| `BankoHceService.kt` | 51 | `= NfcManager.getInstance(...).getVirtualToken()` | `processCommandApdu()` — self-restore after process kill (internal only) |

#### `BankoHceService.isPaymentAuthorized` write sites:
| File | Line | Operation | Context |
|------|------|-----------|---------|
| `NfcManager.kt` | 157 | `= false` | `unregisterDevice()` cleanup |
| `NfcManager.kt` | 191 | `= true` | `showBiometricPrompt()` — biometric success callback |
| `NfcManager.kt` | 208 | `= true` | `verifyPin()` — PIN success |
| `NfcPayOverlayActivity.kt` | 29 | `= true` | `onCreate()` — direct authorization at overlay launch |
| `NfcPayOverlayActivity.kt` | 56 | `= false` | `startCountdown()` `onFinish()` — timer expiry |
| `NfcPayOverlayActivity.kt` | 66 | `= false` | `cancelPayment()` — user cancel |
| `BankoHceService.kt` | 77 | `= false` | `onDeactivated()` — reset after each NFC tap (internal, stays internal) |

**Summary of callers that need migration:**
- `NfcManager.kt`: 4 writes to `currentToken`, 3 writes to `isPaymentAuthorized` → migrate to `authorize(token)` / `deauthorize()`
- `NfcPayOverlayActivity.kt`: 3 writes to `isPaymentAuthorized` → migrate to `authorize()` / `deauthorize()`
- `BankoHceService.kt` internal writes in `processCommandApdu()` and `onDeactivated()` can remain direct since they're within the class itself

---

## Architecture Patterns

### iOS: Keychain-based Persistent State

**Pattern:** All auth state stored in Keychain via `KeychainHelper` (not UserDefaults). Keys are string constants.

**Current `clearAll()` pattern:**
```swift
private func clearAll() {
    let keysToDelete = [
        "auth_token",
        "student_id",
        "student_name",
        "last_balance",
        "theme_mode",
        "isCardLost",        // ← BUG: this line must be removed
        "budget_alert_month",
        "budgetAlerted80",
        "budgetAlerted100"
    ]
    keysToDelete.forEach { KeychainHelper.delete(forKey: $0) }
    isLoggedIn = false
    studentName = ""
}
```

**Fix pattern (REQ-BUG-MOB-01):** Remove `"isCardLost"` from the array. That's the entire iOS persistence fix.

**For login-side clearance:** Add to `AuthManager.login()`:
```swift
func login(token: String, student: Student) {
    KeychainHelper.save(token, forKey: "auth_token")
    // ... existing saves ...
    if student.cardStatus == "active" {          // if Option B chosen
        KeychainHelper.delete(forKey: "isCardLost")
    }
    isLoggedIn = true
}
```

### Android: EncryptedSharedPreferences for Persistent State

**Pattern:** `SecureStorage` wraps `EncryptedSharedPreferences` with typed helpers. `clearAuth()` is narrow by design (removes only auth credentials).

**Fix pattern (REQ-BUG-MOB-02):** Add login-side clearance in `LoginActivity.performLogin()`:
```kotlin
// After successful login, clear lost card flag if student status is active
if (loginResponse.student.status != "lost") {
    secureStorage.setCardLost(false)
}
```
The `Student` data class already has `val status: String` — no model change needed on Android.

### Android: Network Security Config pattern

**Standard pattern for debug-only cleartext:**
```xml
<!-- app/src/debug/res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">localhost</domain>
        <domain includeSubdomains="false">10.0.2.2</domain>
    </domain-config>
</network-security-config>
```

```xml
<!-- app/src/debug/AndroidManifest.xml -->
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:networkSecurityConfig="@xml/network_security_config" />
</manifest>
```

The debug manifest is a **partial manifest** — it only needs to override the `application` attributes that differ from the main manifest. AGP merges them at build time.

### Android: BankoHceService Encapsulation Pattern

**Current (vulnerable):**
```kotlin
companion object {
    @Volatile var currentToken: String? = null
    @Volatile var isPaymentAuthorized: Boolean = false
}
```

**Target pattern:**
```kotlin
companion object {
    @Volatile private var currentToken: String? = null
    @Volatile private var isPaymentAuthorized: Boolean = false

    fun authorize(token: String) {
        currentToken = token
        isPaymentAuthorized = true
    }

    fun deauthorize() {
        currentToken = null
        isPaymentAuthorized = false
    }
}
```

**Internal reads** in `processCommandApdu()` and `handleSelectCommand()` access `currentToken` and `isPaymentAuthorized` directly — these stay as-is since they're inside `BankoHceService` itself and private fields are accessible within the same class.

**The `processCommandApdu()` self-restore pattern** (`currentToken = NfcManager.getInstance(...).getVirtualToken()`) is a direct field write — after making the field private, this line is inside `BankoHceService` itself, so it still compiles. No change needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Android debug/release config split | Conditional logic in code | AGP source sets (`src/debug/`) | Standard Android mechanism; zero runtime overhead |
| Cleartext exception scoping | Manual environment checks | `network_security_config.xml` | System-enforced; can't be bypassed by app code |
| iOS error propagation from URL construction | Silent nil returns | `throw APIError.invalidURL` | Method already `throws`; callers already handle errors |

---

## Common Pitfalls

### Pitfall 1: Removing the wrong Keychain key on iOS
**What goes wrong:** Removing `"isCardLost"` from `keysToDelete` removes it from the explicit logout path too — but that's the correct behavior per the lifecycle spec (the flag IS cleared on explicit logout, which calls `clearAll()`). The fix is intentionally removing it from the array so it survives *implicit* clears (app kill).
**Prevention:** Verify that `logout()` calls `clearAll()` (confirmed at line 23 of `AuthManager.swift`) — this means explicit logout still clears the flag correctly even after the fix.

### Pitfall 2: Android `deauthorize()` also nulls `currentToken`
**What goes wrong:** The locked design `deauthorize()` sets `currentToken = null` — but `onDeactivated()` in `BankoHceService` currently only resets `isPaymentAuthorized`, not `currentToken`. After encapsulation, callers that previously did `BankoHceService.isPaymentAuthorized = false` only would now call `deauthorize()` which also nulls the token.
**Impact:** `NfcPayOverlayActivity.startCountdown().onFinish()` and `cancelPayment()` currently only clear `isPaymentAuthorized`. After migration to `deauthorize()`, the token is also cleared. This is **more secure** (correct behavior) but may cause the next payment attempt to require re-auth. This is intentional per the security fix.
**Warning sign:** If `NfcPayOverlayActivity` calls `deauthorize()` and the token is gone, the user must re-authenticate before the next NFC tap. Verify this is acceptable UX.

### Pitfall 3: Debug manifest `<application>` merge conflict
**What goes wrong:** If the debug manifest includes attributes already in the main manifest without `tools:replace`, the Gradle merge may fail or produce unexpected results.
**Prevention:** Debug manifest should only specify the `android:networkSecurityConfig` attribute — nothing else. The `tools:` namespace is not needed for pure-additive attribute additions.

### Pitfall 4: iOS `LoginResponse` model change scope
**What goes wrong:** If adding `cardStatus` to iOS `LoginResponse.Student`, the field must be `Optional` (`String?`) so existing API responses without the field don't cause decoding failures.
**Prevention:** Declare as `let cardStatus: String?` with `CodingKeys` mapping to `"status"` or whatever the backend field name is. Check the Android `Student` model — it uses `val status: String` (non-optional), which means the backend always sends it.

### Pitfall 5: `@Volatile` retention after encapsulation
**What goes wrong:** After making fields `private`, forgetting to keep `@Volatile` annotation. Both fields are written from multiple threads (UI thread in `NfcPayOverlayActivity`, IO coroutine in `NfcManager`, HCE service thread in `BankoHceService`).
**Prevention:** Keep `@Volatile` on both `private var` declarations in the companion object.

---

## Code Examples

### iOS Fix 1: Remove `isCardLost` from `clearAll()` (REQ-BUG-MOB-01)

```swift
// File: mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift
// Change: Remove "isCardLost" from keysToDelete

private func clearAll() {
    let keysToDelete = [
        "auth_token",
        "student_id",
        "student_name",
        "last_balance",
        "theme_mode",
        // "isCardLost",   ← REMOVE THIS LINE
        "budget_alert_month",
        "budgetAlerted80",
        "budgetAlerted100"
    ]
    keysToDelete.forEach { KeychainHelper.delete(forKey: $0) }
    isLoggedIn = false
    studentName = ""
}
```

### iOS Fix 2: Login-side clearance (REQ-BUG-MOB-01)

Two sub-options:

**Option A — unconditional clear on login (simplest):**
```swift
// In LoginViewModel.login(), after authManager.login(token:student:):
KeychainHelper.delete(forKey: "isCardLost")
```

**Option B — model-based clear (more correct, matches locked decision):**
```swift
// In LoginModels.swift — add cardStatus to Student:
struct Student: Codable {
    let studentId: String
    let name: String
    let cardStatus: String?   // ← ADD
    enum CodingKeys: String, CodingKey {
        case studentId = "student_id"
        case name
        case cardStatus = "status"   // ← ADD
    }
}

// In AuthManager.login():
func login(token: String, student: Student) {
    KeychainHelper.save(token, forKey: "auth_token")
    KeychainHelper.save(student.studentId, forKey: "student_id")
    KeychainHelper.save(student.name, forKey: "student_name")
    if student.cardStatus == "active" {
        KeychainHelper.delete(forKey: "isCardLost")
    }
    studentName = student.name
    isLoggedIn = true
}
```

### iOS Fix 3: Replace `fatalError()` with thrown error (REQ-BUG-MOB-03)

```swift
// In APIClient.swift — add case to APIError enum:
enum APIError: Error {
    case invalidURL           // ← ADD THIS
    case cardLost
    case unauthorized
    case httpError(Int)
    case decodingError(Error)
    case networkError(Error)
}

// Replace authenticatedRequest() guard (line ~27):
guard let url = URL(string: APIEndpoints.baseURL + path) else {
    throw APIError.invalidURL    // was: fatalError("Invalid URL for path: \(path)")
}

// Replace login() guard (line ~70):
guard let url = URL(string: APIEndpoints.baseURL + APIEndpoints.login) else {
    throw APIError.invalidURL    // was: fatalError("Invalid login URL")
}
```

### Android Fix 1: Login-side `isCardLost` clearance (REQ-BUG-MOB-02)

```kotlin
// In LoginActivity.kt — inside performLogin() onResponse callback:
if (response.isSuccessful) {
    response.body()?.let { loginResponse ->
        secureStorage.saveAuthToken(loginResponse.token)
        secureStorage.saveStudentId(loginResponse.student.id)
        
        // Clear lost card flag if backend confirms card is active
        if (loginResponse.student.status != "lost") {
            secureStorage.setCardLost(false)
        }
        
        // ... rest of existing code ...
    }
}
```

### Android Fix 2: HTTPS-only (REQ-SEC-03)

```xml
<!-- Remove from app/src/main/AndroidManifest.xml: -->
<!-- android:usesCleartextTraffic="true" -->

<!-- New file: app/src/debug/res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">localhost</domain>
        <domain includeSubdomains="false">10.0.2.2</domain>
    </domain-config>
</network-security-config>

<!-- New file: app/src/debug/AndroidManifest.xml -->
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:networkSecurityConfig="@xml/network_security_config" />
</manifest>
```

### Android Fix 3: NFC field encapsulation (REQ-SEC-02)

```kotlin
// In BankoHceService.kt companion object:
companion object {
    private const val TAG = "BankoHceService"
    // ... AID/SW constants unchanged ...

    @Volatile
    private var currentToken: String? = null   // was: var (public)

    @Volatile
    private var isPaymentAuthorized: Boolean = false  // was: var (public)

    fun authorize(token: String) {
        currentToken = token
        isPaymentAuthorized = true
    }

    fun deauthorize() {
        currentToken = null
        isPaymentAuthorized = false
    }
}

// In NfcManager.kt — migrate all write sites:
// Line 124: BankoHceService.currentToken = token  →  BankoHceService.authorize(token)
// Line 156-157: BankoHceService.currentToken = null + isPaymentAuthorized = false  →  BankoHceService.deauthorize()
// Line 176: BankoHceService.currentToken = getVirtualToken()  →  getVirtualToken()?.let { BankoHceService.authorize(it) }
// Line 191: BankoHceService.isPaymentAuthorized = true  →  (already handled by showBiometricPrompt calling onSuccess which was previously setting authorized — needs BankoHceService.authorize with existing token)
// Line 208: BankoHceService.isPaymentAuthorized = true  →  (verifyPin success — use BankoHceService.authorize with stored token)

// In NfcPayOverlayActivity.kt — migrate all write sites:
// Line 29: BankoHceService.isPaymentAuthorized = true  →  BankoHceService.currentToken is now private; overlay can't set token; this becomes just a call to a new authorizeExisting() or the overlay must get token from NfcManager
// Line 56, 66: BankoHceService.isPaymentAuthorized = false  →  BankoHceService.deauthorize()
```

**⚠️ Important note on `NfcPayOverlayActivity` line 29:** The overlay currently sets `isPaymentAuthorized = true` directly. After encapsulation, since `currentToken` is now private, the overlay cannot call `authorize(token)` without a token. Two approaches:
1. Pass the token as an Intent extra to `NfcPayOverlayActivity` (cleanest)
2. Add a `reauthorize()` method that sets `isPaymentAuthorized = true` only if `currentToken` is already non-null (simpler, preserves existing flow where `NfcManager.authenticateForPayment()` already loaded the token via line 176)

**Recommendation:** Use approach 2 — add `fun reauthorize()` that guards on non-null token.

---

## Files Affected Summary

| File | Change | Requirement |
|------|--------|-------------|
| `mobile/ios/.../Core/Auth/AuthManager.swift` | Remove `"isCardLost"` from `keysToDelete`; add clearance in `login()` | REQ-BUG-MOB-01 |
| `mobile/ios/.../Models/LoginModels.swift` | Add `cardStatus: String?` to `Student` (if Option B) | REQ-BUG-MOB-01 |
| `mobile/ios/.../Core/Network/APIClient.swift` | Add `case invalidURL`; replace 2× `fatalError()` | REQ-BUG-MOB-03 |
| `mobile/student_app_v2/app/src/main/java/.../LoginActivity.kt` | Add `setCardLost(false)` after successful login | REQ-BUG-MOB-02 |
| `mobile/student_app_v2/app/src/main/AndroidManifest.xml` | Remove `usesCleartextTraffic="true"` | REQ-SEC-03 |
| `mobile/student_app_v2/app/src/debug/res/xml/network_security_config.xml` | **NEW** — localhost/emulator cleartext exception | REQ-SEC-03 |
| `mobile/student_app_v2/app/src/debug/AndroidManifest.xml` | **NEW** — reference security config | REQ-SEC-03 |
| `mobile/student_app_v2/app/src/main/java/.../BankoHceService.kt` | Make fields private; add `authorize()`/`deauthorize()`/`reauthorize()` | REQ-SEC-02 |
| `mobile/student_app_v2/app/src/main/java/.../NfcManager.kt` | Migrate 4 write sites to `authorize()`/`deauthorize()` | REQ-SEC-02 |
| `mobile/student_app_v2/app/src/main/java/.../NfcPayOverlayActivity.kt` | Migrate 3 write sites to `reauthorize()`/`deauthorize()` | REQ-SEC-02 |

---

## Open Questions

1. **iOS `isCardLost` clearance — Option A vs Option B**
   - What we know: Android `Student` model has `status: String` (backend always sends it). iOS `Student` does not.
   - What's unclear: Locked decision says "if the backend returns an active/non-lost card status" — this implies Option B. But it requires adding a field to the iOS model.
   - **Recommendation:** Option B — add `cardStatus: String?` to iOS `Student`, map to `"status"`. This matches the locked decision and is consistent with Android.

2. **`NfcPayOverlayActivity` line 29 authorization approach**
   - What we know: The overlay sets `isPaymentAuthorized = true` in `onCreate()`. After encapsulation, `currentToken` is private.
   - What's unclear: Is the token always already loaded by `NfcManager.authenticateForPayment()` (line 176) before the overlay launches?
   - **Recommendation:** Yes — looking at the flow, `NfcManager.authenticateForPayment()` calls `BankoHceService.currentToken = getVirtualToken()` (line 176) before showing biometric/PIN. By the time the overlay is launched, the token is already set. Add `fun reauthorize()` that asserts `currentToken != null` and sets `isPaymentAuthorized = true` — this is safe.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection — all files read and verified:
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt`
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SettingsActivity.kt`
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt`
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt`
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt`
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt`
  - `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt`
  - `mobile/student_app_v2/app/src/main/AndroidManifest.xml`
  - `mobile/student_app_v2/app/build.gradle.kts`
  - `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
  - `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
  - `mobile/ios/BankongSetonStudent/Models/LoginModels.swift`
  - `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift`

## Metadata

**Confidence breakdown:**
- Bug root causes: HIGH — verified by reading exact source lines
- Security field enumeration: HIGH — full grep of codebase
- Fix patterns: HIGH — straightforward iOS/Android idioms
- iOS login-side Option A vs B: MEDIUM — requires a planner decision on model scope

**Research date:** 2026-03-09
**Valid until:** Stable codebase — no external dependencies changing; valid until files are modified
