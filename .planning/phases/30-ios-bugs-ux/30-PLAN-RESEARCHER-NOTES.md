# Phase 30: iOS Bugs & UX — Implementation Plan

**Phase:** 30 — ios-bugs-ux  
**Planned:** 2026-03-09  
**Based on:** 30-RESEARCH.md, 30-CONTEXT.md  
**Mode:** yolo | Granularity: fine | Parallelization: true

---

## Goal

Fix 6 iOS-only issues:
- **REQ-BUG-MOB-04** — CARD_LOST shows wrong error message on login
- **REQ-BUG-MOB-05** — 401 token expiry leaves user stuck (no re-auth prompt)
- **REQ-UX-01** — Budget input overwritten by server load while typing
- **REQ-UX-02** — No empty state in transactions list
- **REQ-UX-03** — Balance shows ₱0.00 during initial load (should show cached)
- **REQ-UX-04** — PIN field shows password autofill suggestions
- **REQ-UX-05** — Sign In button hidden behind keyboard on iPhone SE

---

## Dependency Graph

```
Wave 1 (Infrastructure — must go first)
  T1: APIClient.swift     — add 401 → .unauthorized
  T2: AuthManager.swift   — add showSessionExpiredAlert, handleUnauthorized(), make clearAll() internal

Wave 2 (ViewModels — depends on Wave 1)
  T3: HomeViewModel.swift       — init() from Keychain (REQ-UX-03) + catch .unauthorized (REQ-BUG-MOB-05)
  T4: TransactionsViewModel.swift — catch .unauthorized (REQ-BUG-MOB-05)
  T5: BudgetViewModel.swift     — catch .unauthorized in load() and setBudget() (REQ-BUG-MOB-05)
  T6: LoginViewModel.swift      — catch .cardLost before .unauthorized (REQ-BUG-MOB-04)

Wave 3 (Views — independent of each other, depends on Wave 1+2)
  T7: MainTabView.swift         — add session-expired alert (REQ-BUG-MOB-05)
  T8: LoginView.swift           — PIN content type + keyboard avoidance (REQ-UX-04, REQ-UX-05)
  T9: BudgetView.swift          — hasEdited guard (REQ-UX-01)
  T10: TransactionsView.swift   — empty state overlay (REQ-UX-02)
```

T3–T6 can run in parallel after Wave 1 completes.  
T7–T10 can run in parallel after Wave 2 completes.

---

## Wave 1 — Infrastructure

### T1: APIClient.swift — Add 401 → `.unauthorized`

**File:** `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`  
**Requirement:** REQ-BUG-MOB-05  
**What:** Add a 401 status code arm to `perform()`, before the existing 403 block.

**Current code (403 block):**
```swift
if http.statusCode == 403 {
    if let body = try? JSONDecoder().decode([String: String].self, from: data),
       body["error"] == "CARD_LOST" {
        throw APIError.cardLost
    }
    throw APIError.unauthorized
}
```

**Change:** Insert immediately before the 403 block:
```swift
if http.statusCode == 401 {
    throw APIError.unauthorized
}
```

**Result:** Both 401 (session expired) and 403 non-CARD_LOST throw `.unauthorized`.  
**Risk:** None — `.unauthorized` was already used for 403; extending to 401 is additive.  
**Verify:** File compiles (swift build or Xcode). Search `statusCode == 401` appears once.

---

### T2: AuthManager.swift — Session Expiry Support

**File:** `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`  
**Requirement:** REQ-BUG-MOB-05  
**What:** Three changes:

1. **Add published flag** for session expired alert:
   ```swift
   @Published var showSessionExpiredAlert: Bool = false
   ```
   Place alongside existing `@Published` properties (e.g., `isLoggedIn`, `isCardLost`).

2. **Add `handleUnauthorized()` method:**
   ```swift
   func handleUnauthorized() {
       showSessionExpiredAlert = true
       // clearAll() is called from the View's alert button action, NOT here
       // This prevents the alert being torn down before the user reads it
   }
   ```

3. **Make `clearAll()` internal** (remove `private` keyword):
   ```swift
   // Before:
   private func clearAll() {
   // After:
   func clearAll() {
   ```
   This allows the View's alert button to call `authManager.clearAll()` directly.

**Risk:** Making `clearAll()` internal is safe — it is only called from `logout()` internally and will now also be callable from the new alert button. No existing callers are affected.  
**Verify:** `showSessionExpiredAlert` appears in file. `handleUnauthorized()` defined. `private func clearAll` no longer appears.

---

## Wave 2 — ViewModels

> All four tasks in Wave 2 can be done in parallel. They only depend on Wave 1 being complete.

### T3: HomeViewModel.swift — Cached Balance + Unauthorized Catch

**File:** `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`  
**Requirements:** REQ-UX-03, REQ-BUG-MOB-05

**Change A — Cached balance (REQ-UX-03):**  
Add `init()` after the `@Published` property declarations:
```swift
init() {
    if let cached = KeychainHelper.read(forKey: "last_balance"),
       let value = Double(cached) {
        balance = value
    }
}
```

**Change B — Unauthorized catch (REQ-BUG-MOB-05):**  
In `load()`, add a `catch APIError.unauthorized` branch:
```swift
} catch APIError.unauthorized {
    authManager.handleUnauthorized()
```
Place this before the generic `catch` block.

**Verify:** `init()` exists in file. `catch APIError.unauthorized` appears in `load()`. App shows cached balance (not ₱0.00) immediately on HomeView.

---

### T4: TransactionsViewModel.swift — Unauthorized Catch

**File:** `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`  
**Requirement:** REQ-BUG-MOB-05

**Change:** In `fetchPage()` (or whichever method calls `apiClient.perform()`), add:
```swift
} catch APIError.unauthorized {
    authManager.handleUnauthorized()
```
Before the generic `catch` block.

**Verify:** `catch APIError.unauthorized` appears in the fetch method.

---

### T5: BudgetViewModel.swift — Unauthorized Catch (Both Methods)

**File:** `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`  
**Requirement:** REQ-BUG-MOB-05

**Change:** In both `load()` and `setBudget()` (both call `apiClient.perform()`), add:
```swift
} catch APIError.unauthorized {
    authManager.handleUnauthorized()
```
Before each generic `catch` block.

**Note:** `BudgetViewModel` makes two separate API calls (read limit, write limit). Both need the unauthorized catch.  
**Verify:** `catch APIError.unauthorized` appears twice in the file (once per method).

---

### T6: LoginViewModel.swift — Card Lost Catch

**File:** `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift`  
**Requirement:** REQ-BUG-MOB-04

**Change:** In `login()`, add `.cardLost` catch BEFORE the existing `.unauthorized` catch:
```swift
} catch APIError.cardLost {
    errorMessage = "Your card has been reported lost. Please contact the canteen admin."
} catch APIError.unauthorized {
    errorMessage = "Invalid student ID or PIN. Please try again."
```

**Important:** `LoginViewModel` does NOT need `.unauthorized` handling for session expiry (401 on the login endpoint means wrong credentials, which is normal). Only `.cardLost` is added.  
**Verify:** `catch APIError.cardLost` appears before `catch APIError.unauthorized` in `login()`.

---

## Wave 3 — Views

> All four tasks in Wave 3 can be done in parallel. They depend on Wave 1+2 being complete.

### T7: MainTabView.swift — Session Expired Alert

**File:** `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`  
**Requirement:** REQ-BUG-MOB-05

**Change:** Add an `.alert` modifier on the root `TabView` (or outermost container in `MainTabView`):
```swift
.alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert) {
    Button("Sign In") {
        authManager.clearAll()
    }
} message: {
    Text("Your session has expired. Please sign in again.")
}
```

**Why MainTabView:** Single alert location. When user is in any tab and their session expires, this alert fires. After tapping "Sign In", `clearAll()` sets `isLoggedIn = false`, and `ContentView` routes back to `LoginView`.  
**Verify:** Alert modifier present in file. `authManager.clearAll()` called from button action (NOT from `handleUnauthorized()`).

---

### T8: LoginView.swift — PIN Content Type + Keyboard Avoidance

**File:** `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`  
**Requirements:** REQ-UX-04, REQ-UX-05

**Change A — PIN content type fix (REQ-UX-04):**  
Find the `SecureField` for PIN. Change its content type:
```swift
// Before:
.textContentType(.password)
// After:
.textContentType(.oneTimeCode)
```

**Change B — Keyboard avoidance (REQ-UX-05):**  
Wrap the inner `VStack` (the form content) in a `ScrollView`:
```swift
// Before:
NavigationStack {
    VStack(spacing: 24) {
        // ...logo, form, button...
    }
}

// After:
NavigationStack {
    ScrollView {
        VStack(spacing: 24) {
            // ...same content...
            Spacer(minLength: 20)
        }
    }
}
```

**Note:** Remove the trailing `Spacer()` (which was only needed for full-height layout) and replace with `Spacer(minLength: 20)` inside ScrollView to give some bottom breathing room.  
**Verify:** `.textContentType(.oneTimeCode)` in file. `ScrollView` wraps login form. On iPhone SE simulator, Sign In button visible when keyboard is up.

---

### T9: BudgetView.swift — `hasEdited` Guard

**File:** `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`  
**Requirement:** REQ-UX-01

**Change:** Add `hasEdited` state and guard. Three locations in the file:

1. **State declaration** (alongside existing `@State` vars):
   ```swift
   @State private var hasEdited = false
   ```

2. **`.task` modification** — guard the `limitInput` assignment:
   ```swift
   // Before (inside .task):
   limitInput = String(format: "%.2f", viewModel.limit)
   
   // After:
   if !hasEdited {
       limitInput = String(format: "%.2f", viewModel.limit)
   }
   ```

3. **TextField/SecureField** — add `onChange`:
   ```swift
   .onChange(of: limitInput) { _ in hasEdited = true }
   ```
   (iOS 16-compatible single-arg form — do NOT use `onChange(of:) { oldVal, newVal in }`)

4. **Outer container** — add `onDisappear`:
   ```swift
   .onDisappear { hasEdited = false }
   ```

**Verify:** `hasEdited` appears 3+ times. `onChange(of: limitInput)` uses `{ _ in }` closure.

---

### T10: TransactionsView.swift — Empty State Overlay

**File:** `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`  
**Requirement:** REQ-UX-02

**Change:** Add a new `.overlay` block alongside the existing loading/error overlays:
```swift
.overlay {
    if viewModel.transactions.isEmpty && !viewModel.isLoading && viewModel.errorMessage == nil {
        VStack(spacing: 8) {
            Text("No transactions yet")
                .font(.headline)
                .foregroundColor(.primary)
            Text("Your transaction history will appear here.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}
```

**Placement:** After the existing `.overlay { if viewModel.isLoading { ... } }` block.  
**Verify:** "No transactions yet" string appears in file. Condition checks `isEmpty && !isLoading && errorMessage == nil`.

---

## Execution Order Summary

```
Step 1: T1 (APIClient)            ← Must be first
Step 2: T2 (AuthManager)          ← Must be before ViewModels
Step 3: T3+T4+T5+T6 in parallel   ← All ViewModels (depend on T1+T2)
Step 4: T7+T8+T9+T10 in parallel  ← All Views (depend on T3–T6)
```

---

## Verification Checklist (Per Requirement)

| Req | File(s) Changed | Manual Test |
|-----|----------------|-------------|
| REQ-BUG-MOB-04 | LoginViewModel.swift | Log in with a CARD_LOST account → see "Your card has been reported lost. Please contact the canteen admin." in red |
| REQ-BUG-MOB-05 | APIClient, AuthManager, HomeViewModel, TransactionsViewModel, BudgetViewModel, MainTabView | Expire a JWT manually → navigate to any screen → see "Session Expired" alert → tap "Sign In" → land on LoginView |
| REQ-UX-01 | BudgetView.swift | Open Budget tab → start typing a number → switch to another tab → return → typed value discarded, server value shown |
| REQ-UX-02 | TransactionsView.swift | Log in with account with no transactions → see "No transactions yet" overlay |
| REQ-UX-03 | HomeViewModel.swift | Kill and reopen app → balance shows last-known value, not ₱0.00 |
| REQ-UX-04 | LoginView.swift | Tap PIN field → no password autofill suggestion bar appears |
| REQ-UX-05 | LoginView.swift | On iPhone SE simulator → tap PIN field → Sign In button visible above keyboard |

---

## File Change Summary

| File | Tasks | Diff Size |
|------|-------|-----------|
| `Core/Network/APIClient.swift` | T1 | +3 lines |
| `Core/Auth/AuthManager.swift` | T2 | +8 lines, 1 keyword change |
| `ViewModels/HomeViewModel.swift` | T3 | +8 lines |
| `ViewModels/TransactionsViewModel.swift` | T4 | +2 lines |
| `ViewModels/BudgetViewModel.swift` | T5 | +4 lines |
| `ViewModels/LoginViewModel.swift` | T6 | +2 lines |
| `Views/MainTabView.swift` | T7 | +7 lines |
| `Views/Auth/LoginView.swift` | T8 | +3 lines, 1 wrap |
| `Views/Budget/BudgetView.swift` | T9 | +5 lines |
| `Views/Transactions/TransactionsView.swift` | T10 | +12 lines |

**Total:** ~54 lines added/changed across 10 files. All changes are small, targeted, and isolated.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Alert dismissed before user sees it | Would happen if `clearAll()` called in `handleUnauthorized()` | PLAN explicitly places `clearAll()` in alert button action, not in `handleUnauthorized()` |
| `clearAll()` visibility blocks compilation | Medium — it's currently `private` | T2 explicitly removes `private` |
| `onChange` iOS 17 syntax breaks iOS 16 | Low — developer might copy wrong syntax | PLAN specifies `{ _ in }` form explicitly in T9 |
| LoginViewModel `.unauthorized` catch for 401 on login | Low — login 401 = wrong PIN, not session expiry | PLAN explicitly notes LoginViewModel does NOT get `.unauthorized` handling |
| `hasEdited` set from programmatic assignment | Low — if `onChange` on TextField is also triggered by `.task` | `.task` assigns to the `@State` var; `.onChange` on the TextField binding only fires on user input in SwiftUI |
