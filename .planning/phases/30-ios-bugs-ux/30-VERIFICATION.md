---
phase: 30-ios-bugs-ux
verified: 2026-03-10T00:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 30: iOS Bugs & UX Verification Report

**Phase Goal:** iOS correctly distinguishes lost card from unauthorized; handles token expiry gracefully; and closes five UX papercuts on the budget, transactions, and login screens.
**Verified:** 2026-03-10
**Status:** ✅ PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | A 401 response from the API throws `APIError.unauthorized` (not httpError) | ✓ VERIFIED | `APIClient.swift:52` — `if http.statusCode == 401 { throw APIError.unauthorized }` before the 403 block |
| 2  | `AuthManager` exposes `handleUnauthorized()` and `showSessionExpiredAlert` | ✓ VERIFIED | `AuthManager.swift:10` `@Published var showSessionExpiredAlert: Bool = false`; `AuthManager.swift:37` `func handleUnauthorized()` |
| 3  | All ViewModels that call the API catch `.unauthorized` and trigger `handleUnauthorized()` | ✓ VERIFIED | 5 matches across ViewModels: Home×1, Transactions×1, Budget×2, Login×1 (Login catch is for wrong creds, delegates to `handleUnauthorized` only on the non-login VMs) |
| 4  | `LoginViewModel` shows 'card reported lost' message when server returns `CARD_LOST` | ✓ VERIFIED | `LoginViewModel.swift:26-27` — `catch APIError.cardLost` with message "Your card has been reported lost. Please contact the canteen admin." — appears **before** `.unauthorized` catch |
| 5  | `HomeViewModel` reads `last_balance` from Keychain on `init()` so balance is not ₱0.00 at launch | ✓ VERIFIED | `HomeViewModel.swift:13-16` — `init()` reads `KeychainHelper.read(forKey: "last_balance")` and initialises `balance` |
| 6  | Session-expired alert appears when any ViewModel calls `handleUnauthorized()`; tapping 'Sign In' redirects to login | ✓ VERIFIED | `MainTabView.swift:31-36` — `.alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert)` with `Button("Sign In") { authManager.clearAll() }` |
| 7  | Typing in the budget field before server response arrives keeps the typed value | ✓ VERIFIED | `BudgetView.swift:8,77,115,124` — `hasEdited` guard (4 occurrences): declaration, `.onChange`, `.task` guard, `.onDisappear` reset |
| 8  | Transactions list shows 'No transactions yet' when empty and not loading | ✓ VERIFIED | `TransactionsView.swift:66-72` — three-condition overlay: `isEmpty && !isLoading && errorMessage == nil` |
| 9  | PIN field on LoginView does not trigger iOS password autofill suggestion bar | ✓ VERIFIED | `LoginView.swift:37` — `.textContentType(.oneTimeCode)` on the PIN `SecureField` |
| 10 | Sign In button is visible above keyboard on iPhone SE (no overlap) | ✓ VERIFIED | `LoginView.swift:10,76` — `ScrollView` wraps inner `VStack`; trailing `Spacer(minLength: 20)` |

**Score:** 10/10 truths verified

---

## Required Artifacts

### Plan 30-01 Artifacts

| Artifact | Provides | Status | Evidence |
|----------|----------|--------|----------|
| `Core/Network/APIClient.swift` | 401 → `.unauthorized` mapping | ✓ VERIFIED | Line 52: `statusCode == 401` arm before 403 block |
| `Core/Auth/AuthManager.swift` | `handleUnauthorized()`, `showSessionExpiredAlert`, public `clearAll()` | ✓ VERIFIED | Lines 10, 37, 54 — all three present; `handleUnauthorized` does NOT call `clearAll` (confirmed by reading function body) |
| `ViewModels/HomeViewModel.swift` | Cached balance init + `.unauthorized` catch | ✓ VERIFIED | Lines 13-16 (init), line 31 (catch) |
| `ViewModels/TransactionsViewModel.swift` | `.unauthorized` catch | ✓ VERIFIED | Line 40 |
| `ViewModels/BudgetViewModel.swift` | `.unauthorized` catch in `load()` AND `setBudget()` | ✓ VERIFIED | Lines 27 and 41 — count = 2 ✅ |
| `ViewModels/LoginViewModel.swift` | `.cardLost` catch with correct error message, before `.unauthorized` | ✓ VERIFIED | Lines 26-28; ordering confirmed: cardLost(26) < unauthorized(28) |

### Plan 30-02 Artifacts

| Artifact | Provides | Status | Evidence |
|----------|----------|--------|----------|
| `Views/MainTabView.swift` | Session expired `.alert` wired to `authManager.showSessionExpiredAlert` | ✓ VERIFIED | Lines 31-36; `@EnvironmentObject var authManager: AuthManager` at line 7 |
| `Views/Auth/LoginView.swift` | `oneTimeCode` content type + `ScrollView` keyboard avoidance | ✓ VERIFIED | Line 37 (oneTimeCode), line 10 (ScrollView), line 76 (Spacer minLength) |
| `Views/Budget/BudgetView.swift` | `hasEdited` guard preventing server overwrite | ✓ VERIFIED | 4 occurrences (declaration, onChange iOS-16-compatible, task guard, onDisappear reset) |
| `Views/Transactions/TransactionsView.swift` | Empty-state overlay with "No transactions yet" | ✓ VERIFIED | Lines 66-72; correct three-condition guard |

---

## Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `APIClient.swift` (401 throw) | `AuthManager.handleUnauthorized()` | ViewModels catching `APIError.unauthorized` | ✓ WIRED | Pattern `catch APIError.unauthorized` found in Home, Transactions, Budget (×2) = 4 non-login VM catches; each calls `authManager.handleUnauthorized()` |
| `HomeViewModel.init()` | `KeychainHelper.read(forKey: "last_balance")` | Direct call in `init()` | ✓ WIRED | `HomeViewModel.swift:14` — `KeychainHelper.read(forKey: "last_balance")` in init body |
| `AuthManager.showSessionExpiredAlert` | `MainTabView .alert` modifier | `$authManager.showSessionExpiredAlert` binding | ✓ WIRED | `MainTabView.swift:31` — `isPresented: $authManager.showSessionExpiredAlert` |
| `MainTabView` alert button | `authManager.clearAll()` | Button action (NOT in `handleUnauthorized`) | ✓ WIRED | `MainTabView.swift:33` — `authManager.clearAll()` inside `Button("Sign In")` action; confirmed NOT in `handleUnauthorized()` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| REQ-BUG-MOB-04 | 30-01 | Fix iOS CARD_LOST vs UNAUTHORIZED misclassification — blocked card shows "wrong PIN" instead of "card reported lost" | ✓ SATISFIED | `LoginViewModel.swift:26-27` — `catch APIError.cardLost` with correct message before `.unauthorized` catch |
| REQ-BUG-MOB-05 | 30-01, 30-02 | Handle 401 token expiry — user stuck in broken auth state with no re-auth prompt | ✓ SATISFIED | `APIClient.swift:52` maps 401→`.unauthorized`; `AuthManager` has `handleUnauthorized()`; `MainTabView` shows alert with "Sign In" → `clearAll()` |
| REQ-UX-01 | 30-02 | Fix budget input overwritten by server load | ✓ SATISFIED | `BudgetView.swift` — `hasEdited` guard (4 occurrences) prevents server value overwriting active user input |
| REQ-UX-02 | 30-02 | Add empty state to iOS transactions list | ✓ SATISFIED | `TransactionsView.swift:66-72` — "No transactions yet" overlay with three-condition guard |
| REQ-UX-03 | 30-01 | Show cached/last-known balance instead of ₱0.00 | ✓ SATISFIED | `HomeViewModel.swift:13-16` — `init()` reads `last_balance` from Keychain |
| REQ-UX-04 | 30-02 | Fix iOS login PIN field content type (autofill suppression) | ✓ SATISFIED | `LoginView.swift:37` — `.textContentType(.oneTimeCode)` |
| REQ-UX-05 | 30-02 | Fix iOS keyboard avoidance on login screen (iPhone SE) | ✓ SATISFIED | `LoginView.swift:10,76` — `ScrollView` wrapper + `Spacer(minLength: 20)` |

**All 7 requirement IDs from plan frontmatter accounted for. No orphaned requirements.**

---

## Anti-Patterns Found

Scanned all 10 modified files for: TODO/FIXME/XXX, placeholder comments, empty implementations, console.log-only bodies.

| File | Pattern | Result |
|------|---------|--------|
| All 10 files | TODO/FIXME/XXX/PLACEHOLDER | ✅ None found |
| `AuthManager.swift` | `clearAll()` called inside `handleUnauthorized()` (critical ordering bug) | ✅ NOT present — correctly deferred to View alert button |
| `BudgetView.swift` | iOS 17-only `onChange` two-arg form | ✅ iOS 16 single-arg form used: `{ _ in hasEdited = true }` |

**No anti-patterns detected.**

---

## Human Verification Required

The following items cannot be verified programmatically and require device/simulator testing:

### 1. Session Expired Alert Visual Presentation

**Test:** Force a 401 response from the API (use a proxy like Charles or expire the token manually). Observe the app.
**Expected:** An alert titled "Session Expired" with message "Your session has expired. Please sign in again." and a single "Sign In" button appears over the current tab screen. Tapping "Sign In" dismisses the alert and navigates to the login screen.
**Why human:** Alert presentation, animation, and navigation routing after `clearAll()` requires runtime SwiftUI state observation.

### 2. Budget Input Race Condition Prevention

**Test:** Navigate to Budget tab. Trigger a network request (pull-to-refresh or navigate away and back). Immediately start typing in the budget amount field. Observe whether your typed value is preserved.
**Expected:** The server response does NOT overwrite the value while you are typing. After navigating away and back, the server value reloads fresh.
**Why human:** Async race condition timing cannot be verified statically; requires real network interaction.

### 3. PIN Field Autofill Suppression

**Test:** On a real iOS device (not simulator) with saved passwords in iCloud Keychain, open the login screen and tap the PIN field.
**Expected:** No password autofill suggestion bar appears above the keyboard. A standard numeric keypad is shown.
**Why human:** Autofill suggestion bar behavior varies by device, iOS version, and Keychain state; cannot be tested statically.

### 4. iPhone SE Keyboard Avoidance

**Test:** Run on an iPhone SE (1st or 2nd gen) simulator or device. Tap the PIN field on the login screen to raise the keyboard.
**Expected:** The "Sign In" button remains fully visible above the keyboard — not obscured. Content scrolls if needed.
**Why human:** Layout geometry and keyboard overlap depend on actual viewport dimensions and SwiftUI layout engine at runtime.

---

## Commits Verified

| Hash | Plan | Description | Verified |
|------|------|-------------|----------|
| `2d862c3` | 30-01 | APIClient 401→.unauthorized + AuthManager session expiry infrastructure | ✅ Present in mobile/ios git log |
| `26fc7db` | 30-01 | ViewModels — unauthorized catch, cached balance, card lost message | ✅ Present in mobile/ios git log |
| `e85b4be` | 30-02 | MainTabView session expired alert wired to authManager | ✅ Present in mobile/ios git log |
| `7365bab` | 30-02 | UX fixes — oneTimeCode, ScrollView, hasEdited guard, empty state | ✅ Present in mobile/ios git log |

Note: All commits are in the `mobile/ios/` nested git repository (`main` branch), not the parent project git. This is the correct and expected setup per SUMMARY.md.

---

## Summary

**All 10 observable truths verified. All 7 requirements satisfied. No anti-patterns detected. 4 items flagged for human/runtime verification.**

Phase 30 goal is fully achieved at the code level:
- **REQ-BUG-MOB-04** (card lost misclassification): ✅ `LoginViewModel` now catches `.cardLost` before `.unauthorized` with the correct user-facing message.
- **REQ-BUG-MOB-05** (token expiry stuck state): ✅ Complete stack — `APIClient` maps 401→`.unauthorized`, `AuthManager.handleUnauthorized()` sets flag, `MainTabView` shows alert, "Sign In" calls `clearAll()` to route back.
- **REQ-UX-01** (budget overwrite): ✅ `hasEdited` guard in `BudgetView` with iOS 16-compatible `onChange`.
- **REQ-UX-02** (empty transactions): ✅ Three-condition overlay in `TransactionsView`.
- **REQ-UX-03** (₱0.00 at launch): ✅ `HomeViewModel.init()` pre-fills from Keychain.
- **REQ-UX-04** (PIN autofill): ✅ `.textContentType(.oneTimeCode)` on `SecureField`.
- **REQ-UX-05** (keyboard overlap SE): ✅ `ScrollView` + `Spacer(minLength:)` in `LoginView`.

The critical architectural constraint — `clearAll()` NOT being called inside `handleUnauthorized()` (alert teardown ordering) — is correctly implemented at both the `AuthManager` layer and the `MainTabView` binding layer.

---

_Verified: 2026-03-10_
_Verifier: Claude (gsd-verifier)_
