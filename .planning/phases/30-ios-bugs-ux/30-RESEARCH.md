# Phase 30: iOS Bugs & UX — Research

**Researched:** 2026-03-09
**Domain:** SwiftUI iOS app — error handling, Keychain persistence, view state management, keyboard avoidance
**Confidence:** HIGH (all findings are from direct source-code audit of the existing codebase)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Gray Area 1 — 401 session expiry flow (REQ-BUG-MOB-05)**
- Add `APIError.unauthorized` case to `APIClient.swift` (mirrors existing `APIError.cardLost` pattern)
- Add `handleUnauthorized()` method to `AuthManager.swift` — calls `clearAll()` and sets an observable flag/publishes an event
- All ViewModels that call the API catch `.unauthorized` and trigger the alert flow
- Alert message: "Your session has expired. Please sign in again."
- Single "Sign In" button on the alert — dismisses alert and redirects to login screen
- After re-login, user lands on Home tab fresh. No deep-link back to where they were.

**Gray Area 2 — Card lost error messaging (REQ-BUG-MOB-04)**
- Detection: parse error response body for the string `CARD_LOST` (not by HTTP status code)
- Surface: login screen only, as inline red error text (consistent with existing error display in `LoginView`)
- Message: "Your card has been reported lost. Please contact the canteen admin."
- Mid-session card-lost is already handled by the existing `handleCardLost()` flow from Phase 27 — no changes needed there

**Gray Area 3 — Budget input protection (REQ-UX-01)**
- Add `@State var hasEdited = false` to `BudgetView`
- Set `hasEdited = true` in `onChange` of `limitInput`
- In `.task`, only assign `limitInput = String(format: "%.2f", viewModel.limit)` if `!hasEdited`
- Reset `hasEdited = false` in `.onDisappear` so server value reloads fresh on next visit
- Unsaved typed input is discarded when the user navigates away (this is intentional)

**Gray Area 4 — Loading & empty states (REQ-UX-02 + REQ-UX-03)**
- REQ-UX-02: Show empty state overlay when `viewModel.transactions.isEmpty` and not loading. Message: "No transactions yet". Subtext: "Your transaction history will appear here." No icon required.
- REQ-UX-03: `HomeViewModel` already saves to Keychain key `last_balance` after each load. On `HomeViewModel` init, read `last_balance` from Keychain and set as the initial `balance` value. When fresh data arrives, update `balance` normally.

### Claude's Discretion

- REQ-UX-04 (PIN autofill) and REQ-UX-05 (keyboard hiding Sign In on SE) — straightforward fixes with no gray areas; implementation details left to the planner.

### Deferred Ideas (OUT OF SCOPE)

- No backend changes
- No Android changes
- No new screens or navigation restructuring
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-BUG-MOB-04 | Fix iOS CARD_LOST vs UNAUTHORIZED misclassification — blocked card shows "wrong PIN" instead of "card reported lost" | APIClient.swift already has `APIError.cardLost` (403+CARD_LOST) vs `APIError.unauthorized` (403 other). LoginViewModel catches `.unauthorized` but NOT `.cardLost` — add that catch branch to show correct message. |
| REQ-BUG-MOB-05 | Handle 401 token expiry in iOS — user stuck in broken authenticated state with no re-auth prompt | `APIClient.perform()` maps 403 to errors but 401 falls through to `httpError(401)`. Need a new `APIError.sessionExpired` (or reuse `unauthorized`) for 401, `AuthManager.handleUnauthorized()` method, and alert wiring in all ViewModels. |
| REQ-UX-01 | Fix iOS budget input overwritten by server load | `BudgetView.task` assigns `limitInput` AFTER `viewModel.load()` completes, but `load()` is async and concurrent typing can still race. Add `hasEdited` guard as decided. |
| REQ-UX-02 | Add empty state to iOS transactions list | `TransactionsView` has error overlay but no empty-state overlay. When `viewModel.transactions.isEmpty && !viewModel.isLoading && viewModel.errorMessage == nil`, show "No transactions yet" + subtext. |
| REQ-UX-03 | Show cached/last-known balance on iOS while loading instead of ₱0.00 | `HomeViewModel` init sets `balance = 0`. Keychain key `last_balance` already saved as `"%.2f"` string on every successful load. Read and parse it in `init()`. |
| REQ-UX-04 | Fix iOS login PIN field content type | `LoginView` `SecureField` has `.textContentType(.password)` — change to `.textContentType(.oneTimeCode)` (best practice for numeric PINs; suppresses password autofill, no suggestion bar). |
| REQ-UX-05 | Fix iOS keyboard avoidance on login screen — Sign In button hidden behind keyboard on iPhone SE | `LoginView` uses plain `VStack` inside `NavigationStack`. Wrap form content in `ScrollView` (or use `.ignoresSafeArea(.keyboard, edges: .bottom)` on the scroll container) so the Sign In button scrolls above the keyboard. |
</phase_requirements>

---

## Summary

Phase 30 is a pure iOS Swift/SwiftUI change set — no backend, no Android. There are seven fixes across five files, grouped into two error-handling bugs and five UX polish items.

**Error bugs:** The two error-handling bugs (REQ-BUG-MOB-04 and REQ-BUG-MOB-05) both live at the intersection of `APIClient.swift`, `AuthManager.swift`, and the ViewModels. For REQ-BUG-MOB-04, the CARD_LOST error case is already correctly parsed in `APIClient.perform()`, but `LoginViewModel.login()` has no `catch APIError.cardLost` branch — it falls through to the generic "Network error" path. For REQ-BUG-MOB-05, HTTP 401 is not currently distinguished from other non-2xx status codes in `APIClient.perform()` — it raises `httpError(401)`, which ViewModels silently swallow or show as a generic error. The fix requires adding a 401 arm to `perform()`, a `handleUnauthorized()` on `AuthManager`, and alert wiring in the four ViewModels that touch the API (`HomeViewModel`, `TransactionsViewModel`, `BudgetViewModel`, `LoginViewModel`).

**UX fixes:** All five UX fixes are self-contained and touch a single file each. REQ-UX-01 adds a two-line guard in `BudgetView`. REQ-UX-02 adds an overlay branch in `TransactionsView`. REQ-UX-03 initializes `balance` from Keychain in `HomeViewModel.init()`. REQ-UX-04 is a one-word attribute change in `LoginView`. REQ-UX-05 wraps the login form in a `ScrollView` or applies keyboard avoidance modifier in `LoginView`.

**Primary recommendation:** Implement changes as one wave: infrastructure (APIClient + AuthManager) first, then ViewModels, then Views — each step is a small targeted edit with no merge conflicts.

---

## Standard Stack

### Core (already in project — no new dependencies)

| Component | Current Usage | Notes |
|-----------|--------------|-------|
| SwiftUI | All Views | iOS 16+ only (NavigationStack confirmed in use) |
| Swift Concurrency (async/await) | All ViewModels | `@MainActor` pattern already established |
| Keychain (KeychainHelper) | Auth tokens, last_balance, isCardLost | Custom wrapper around `Security` framework |
| `@Published` + `ObservableObject` | All ViewModels | Standard MVVM pattern used throughout |
| `@EnvironmentObject` | `APIClient`, `AuthManager` | Injected from `BankongSetonStudentApp` |
| `@State`, `.task`, `.onDisappear` | Views | Standard SwiftUI lifecycle |

### No New Libraries Required
All fixes use SwiftUI primitives and existing project infrastructure. No new packages needed.

---

## Architecture Patterns

### Recommended Project Structure (unchanged)
```
Core/
├── Auth/AuthManager.swift        # add handleUnauthorized()
├── Keychain/KeychainHelper.swift # unchanged
└── Network/APIClient.swift       # add 401 → APIError case

ViewModels/
├── HomeViewModel.swift           # init from Keychain + .unauthorized catch
├── TransactionsViewModel.swift   # .unauthorized catch
├── BudgetViewModel.swift         # .unauthorized catch
└── LoginViewModel.swift          # .cardLost catch

Views/
├── Auth/LoginView.swift          # PIN content type + keyboard avoidance
├── Budget/BudgetView.swift       # hasEdited guard
└── Transactions/TransactionsView.swift  # empty state overlay
```

### Pattern 1: Unauthorized Alert via AuthManager Published Flag

**What:** `AuthManager` publishes a `showSessionExpiredAlert: Bool` flag. Any ViewModel that catches `.unauthorized` calls `authManager.handleUnauthorized()`. The root `ContentView` (or `MainTabView`) watches `authManager.showSessionExpiredAlert` and presents an `.alert` that calls `authManager.clearAll()` — which sets `isLoggedIn = false`, triggering navigation back to `LoginView`.

**Why this pattern:** ViewModels cannot present SwiftUI alerts directly. The `AuthManager` is already an `@EnvironmentObject` shared across all Views. The same pattern is used for `handleCardLost()` (sets flag → clears auth → navigation change).

**Example — AuthManager addition:**
```swift
// In AuthManager.swift
@Published var showSessionExpiredAlert: Bool = false

func handleUnauthorized() {
    showSessionExpiredAlert = true  // View reads this to show alert
    clearAll()                      // clears Keychain + sets isLoggedIn = false
}
```

**Example — ViewModel catch:**
```swift
// In HomeViewModel, TransactionsViewModel, BudgetViewModel
} catch APIError.unauthorized {
    authManager.handleUnauthorized()
```

**Example — Alert in a View (e.g. HomeView):**
```swift
.alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert) {
    Button("Sign In") { authManager.showSessionExpiredAlert = false }
} message: {
    Text("Your session has expired. Please sign in again.")
}
```

> **Note on alert placement:** The alert can be placed on `MainTabView` (single point) or on each individual view. Since `authManager.isLoggedIn` becoming `false` already triggers navigation to `LoginView` via `ContentView`, the alert only needs to appear while `isLoggedIn` is still `true` (i.e., before `clearAll()` fires). Placing the alert in each ViewModel-owning View or in `MainTabView` both work. `MainTabView` is cleaner (one `.alert` modifier).

> **Alternative pattern:** Since `clearAll()` sets `isLoggedIn = false` immediately, the alert may dismiss before the user reads it. A safer approach: `clearAll()` inside the "Sign In" button action on the alert, not inside `handleUnauthorized()`. This way the alert fires first, user taps "Sign In", then `clearAll()` is called, transitioning to login.

### Pattern 2: REQ-BUG-MOB-04 — Login CARD_LOST Catch

**What:** `LoginViewModel.login()` currently catches `.unauthorized` (wrong PIN). Add a `.cardLost` catch before it.

**Current code:**
```swift
} catch APIError.unauthorized {
    errorMessage = "Invalid student ID or PIN. Please try again."
```

**Fix:**
```swift
} catch APIError.cardLost {
    errorMessage = "Your card has been reported lost. Please contact the canteen admin."
} catch APIError.unauthorized {
    errorMessage = "Invalid student ID or PIN. Please try again."
```

**Why no other changes:** `APIClient.perform()` already correctly detects `CARD_LOST` in the 403 response body (Phase 27 did this). The only gap is that `LoginViewModel` never had a `cardLost` catch.

### Pattern 3: REQ-UX-03 — Cached Balance Init

**What:** `HomeViewModel.init()` reads `last_balance` from Keychain.

```swift
init() {
    if let cached = KeychainHelper.read(forKey: "last_balance"),
       let value = Double(cached) {
        balance = value
    }
}
```

**Why safe:** `last_balance` is already written as `String(format: "%.2f", bal.balance)` in `HomeViewModel.load()`. `Double()` init from a `"%.2f"` string is always safe.

### Pattern 4: REQ-UX-01 — Budget hasEdited Guard

**What:** Add `@State var hasEdited = false` to `BudgetView`. Set in `onChange(of: limitInput)`. Guard in `.task`. Reset in `.onDisappear`.

```swift
@State private var hasEdited = false

// In .task:
await viewModel.load(apiClient: apiClient, authManager: authManager)
if !hasEdited {
    limitInput = String(format: "%.2f", viewModel.limit)
}

// On the TextField:
.onChange(of: limitInput) { _ in hasEdited = true }

// On the outer VStack or NavigationStack:
.onDisappear { hasEdited = false }
```

**SwiftUI `onChange` syntax note:** iOS 17+ uses `onChange(of:) { newValue in }` (two-arg closure). iOS 16 uses `onChange(of:) { _ in }` (old API). Since the project targets iOS 16+ (uses `NavigationStack`), use the iOS 16-compatible single-arg form: `.onChange(of: limitInput) { _ in hasEdited = true }`.

### Pattern 5: REQ-UX-02 — Empty State Overlay

**What:** `TransactionsView` already uses `.overlay` blocks for loading and errors. Add a third:

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

### Pattern 6: REQ-UX-04 — PIN Content Type Fix

**What:** Change `.textContentType(.password)` to `.textContentType(.oneTimeCode)` on the PIN `SecureField` in `LoginView`.

**Why `.oneTimeCode`:** This suppresses iOS password autofill suggestions, shows no credential suggestion bar, but still allows numeric keyboard. For a PIN field (not a reusable password), this is the correct semantic content type. Alternatively, `.textContentType(.none)` removes all content type handling entirely — either works. `.oneTimeCode` is preferred as it still benefits from iOS smart behavior (e.g., autofill from SMS OTP, but not from Passwords app).

### Pattern 7: REQ-UX-05 — Keyboard Avoidance on Login Screen

**Current structure:**
```swift
NavigationStack {
    VStack(spacing: 24) {   // logo + form + button
        ...
        Spacer()            // pushes button up in full-height layout
    }
}
```

**Problem:** On iPhone SE (4" screen), the keyboard covers the "Sign In" button. `VStack` + `Spacer()` at the bottom means the button is near the bottom of the viewport.

**Fix — wrap in ScrollView:**
```swift
NavigationStack {
    ScrollView {
        VStack(spacing: 24) {
            // ... same content ...
            Spacer(minLength: 20)
        }
    }
}
```

**Why ScrollView works:** When the keyboard appears, SwiftUI's `ScrollView` adjusts its content inset, so the user can scroll the Sign In button into view above the keyboard. This is a standard iOS pattern for short-form login screens.

**Alternative — `.ignoresSafeArea(.keyboard, edges: .bottom)`:** Explicitly tells the view NOT to adjust for the keyboard. The opposite of what we want. Do not use this.

**Alternative — `KeyboardAdaptive` / `.padding(.bottom, keyboardHeight)`:** Custom keyboard height tracking. Over-engineered for this case. The `ScrollView` approach is simpler and equally correct.

### Anti-Patterns to Avoid

- **Alert in ViewModel:** ViewModels cannot show SwiftUI alerts. The flag must be published on `AuthManager` (or use a Combine PassthroughSubject). Do not try to present an alert directly from a ViewModel.
- **`clearAll()` before alert shows:** If `clearAll()` is called first, `isLoggedIn` becomes `false`, `ContentView` switches to `LoginView`, and the alert is dismissed before the user sees it. Call `clearAll()` from the alert button action, not from `handleUnauthorized()`.
- **Detecting 401 by HTTP status in `LoginViewModel`:** 401 on login means the server rejected the credentials (wrong PIN) — which is normal. The 401 unauthorized detection for session expiry only applies to authenticated endpoints (getBalance, getTransactions, etc.). `LoginViewModel` should NOT have `.unauthorized` handling for token expiry.
- **Overwriting `hasEdited` on `viewModel.limit` change:** The `hasEdited` flag should ONLY be set from user typing, not from programmatic changes to `limitInput`. Make sure `onChange` is placed on the TextField binding, not triggered by the `.task` assignment.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Keyboard height tracking | Custom `NotificationCenter` observer for `keyboardWillShow` | `ScrollView` with default keyboard avoidance | SwiftUI `ScrollView` handles keyboard inset automatically since iOS 14 |
| Session expiry state machine | Complex state machine with timer | `@Published var showSessionExpiredAlert` on `AuthManager` | One flag, mirrors existing `isCardLost` pattern already in the codebase |
| PIN field numeric-only enforcement | Custom `UIViewRepresentable` UITextField | `.keyboardType(.numberPad)` + `.textContentType(.oneTimeCode)` | Already correct (keyboardType is already set via `SecureField` keyboard type) |

---

## Common Pitfalls

### Pitfall 1: Alert Dismissed Before User Reads It
**What goes wrong:** `handleUnauthorized()` calls `clearAll()` → `isLoggedIn = false` → `ContentView` swaps to `LoginView` → alert is torn down.
**Why it happens:** SwiftUI navigation and alert presentation are driven by the same state change.
**How to avoid:** Set `showSessionExpiredAlert = true` first (without calling `clearAll()`). Call `clearAll()` from the alert button action. This ensures the alert persists until the user taps "Sign In".
**Correct flow:**
```swift
func handleUnauthorized() {
    showSessionExpiredAlert = true
    // clearAll() called from the alert button tap, NOT here
}
// In the View:
.alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert) {
    Button("Sign In") { authManager.clearAll() }
} message: { Text("Your session has expired. Please sign in again.") }
```
Note: `clearAll()` is currently `private`. It must be made `internal` (or a new method `confirmLogout()`) to be callable from the View.

### Pitfall 2: `APIError.unauthorized` vs 401 vs `httpError(401)`
**What goes wrong:** Current `APIClient.perform()` maps 403 to `.cardLost` or `.unauthorized`, but 401 falls into `httpError(401)`. ViewModels catch `APIError.cardLost` and `APIError.unauthorized` but not `httpError(401)`.
**How to avoid:** Add a 401 arm to `perform()`:
```swift
if http.statusCode == 401 {
    throw APIError.unauthorized
}
```
Place this BEFORE the existing 403 block. Now `.unauthorized` covers both "session expired (401)" and "generic 403" cases. Rename the intent in the decision: `APIError.unauthorized` = session expired (401), NOT the wrong-PIN 403. The two `unauthorized` meanings are now different contexts: 401 on authenticated calls = session expired; 403 on login = wrong PIN.

> **Decision alignment note:** The CONTEXT.md says "Add `APIError.unauthorized` case to `APIClient.swift`" but this case ALREADY EXISTS in the current code as a 403-only path. The actual change needed is to also throw it for 401. The planner must reconcile this: the existing `.unauthorized` case is being repurposed/extended to cover 401 token expiry.

### Pitfall 3: `onChange` iOS Version Compatibility
**What goes wrong:** `onChange(of:perform:)` was deprecated in iOS 17. Using the new two-argument closure syntax breaks on iOS 16.
**How to avoid:** Use the iOS 16-compatible form: `.onChange(of: limitInput) { _ in hasEdited = true }`.

### Pitfall 4: `clearAll()` is Private
**What goes wrong:** The View needs to call `authManager.clearAll()` from the alert button, but `clearAll()` is `private`.
**How to avoid:** Either make `clearAll()` internal (remove `private`), or add a thin public wrapper method (e.g., `confirmSessionExpiredLogout()`).

### Pitfall 5: LoginViewModel CARD_LOST catch needs `.cardLost` (not string)
**What goes wrong:** Developer might try to check `errorMessage` contains "CARD_LOST" rather than catching the typed enum case.
**How to avoid:** `APIError.cardLost` is a proper enum case. Use typed catch: `} catch APIError.cardLost {`.

---

## Code Examples

Verified patterns from direct source-code audit:

### Current APIClient.perform() — 403 handling (already correct)
```swift
// Source: mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
if http.statusCode == 403 {
    if let body = try? JSONDecoder().decode([String: String].self, from: data),
       body["error"] == "CARD_LOST" {
        throw APIError.cardLost
    }
    throw APIError.unauthorized
}
```

### 401 extension needed:
```swift
if http.statusCode == 401 {
    throw APIError.unauthorized
}
if http.statusCode == 403 {
    if let body = try? JSONDecoder().decode([String: String].self, from: data),
       body["error"] == "CARD_LOST" {
        throw APIError.cardLost
    }
    throw APIError.unauthorized
}
```

### AuthManager clearAll() visibility fix:
```swift
// Change from private to internal:
func clearAll() {   // was: private func clearAll()
```

### HomeViewModel init with cached balance:
```swift
init() {
    if let cached = KeychainHelper.read(forKey: "last_balance"),
       let value = Double(cached) {
        balance = value
    }
}
```

### TransactionsView empty state (inside existing .overlay blocks):
```swift
.overlay {
    if viewModel.transactions.isEmpty && !viewModel.isLoading && viewModel.errorMessage == nil {
        VStack(spacing: 8) {
            Text("No transactions yet")
                .font(.headline)
            Text("Your transaction history will appear here.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}
```

---

## Files to Change — Complete Map

| File | Changes Required |
|------|-----------------|
| `Core/Network/APIClient.swift` | Add 401 → throw `APIError.unauthorized` arm (before existing 403 block) |
| `Core/Auth/AuthManager.swift` | (1) Add `@Published var showSessionExpiredAlert = false`, (2) Add `handleUnauthorized()` method, (3) Change `clearAll()` from `private` to internal |
| `ViewModels/HomeViewModel.swift` | (1) Add `init()` reading `last_balance` from Keychain, (2) Add `catch APIError.unauthorized` in `load()` |
| `ViewModels/TransactionsViewModel.swift` | Add `catch APIError.unauthorized` in `fetchPage()` |
| `ViewModels/BudgetViewModel.swift` | Add `catch APIError.unauthorized` in `load()` and `setBudget()` |
| `ViewModels/LoginViewModel.swift` | Add `catch APIError.cardLost` before `catch APIError.unauthorized` |
| `Views/Auth/LoginView.swift` | (1) Change `.textContentType(.password)` → `.textContentType(.oneTimeCode)`, (2) Wrap body in `ScrollView` for keyboard avoidance, (3) Add `.alert` for session expiry (or place in MainTabView) |
| `Views/Budget/BudgetView.swift` | Add `hasEdited` state + `onChange` + `onDisappear` + guard in `.task` |
| `Views/Transactions/TransactionsView.swift` | Add empty state `.overlay` block |

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `NavigationView` | `NavigationStack` (iOS 16+) | Already using NavigationStack — correct |
| `onChange(of:perform:)` | `.onChange(of:) { _ in }` | iOS 16 compat form |
| Manual keyboard avoidance | `ScrollView` auto-adjusts | Standard SwiftUI pattern |
| `textContentType(.password)` for PINs | `textContentType(.oneTimeCode)` | Suppresses password autofill |

---

## Open Questions

1. **Alert placement — per-View vs MainTabView**
   - What we know: `MainTabView` hosts all four tabs; all authenticated ViewModels can fire `handleUnauthorized()`
   - What's unclear: The planner must pick one placement. `MainTabView` = one alert modifier, simpler. Per-View = each view handles its own alert.
   - Recommendation: Place on `MainTabView` — single alert, mirrors how the existing `isLoggedIn` flip already routes back to `LoginView` via `ContentView`. Less repetition.

2. **`APIError.unauthorized` dual meaning**
   - What we know: Currently `.unauthorized` = 403 non-CARD_LOST. With the 401 change, it also means "session expired."
   - What's unclear: This overloading is intentional per CONTEXT.md ("mirrors existing `APIError.cardLost` pattern") but the semantic is slightly muddled.
   - Recommendation: Proceed with overloading as decided. The behavior in both cases (401 or 403 non-CARD_LOST on authenticated endpoints) should trigger `handleUnauthorized()`. The distinction doesn't matter for user experience.

---

## Sources

### Primary (HIGH confidence)
- Direct source audit: `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- Direct source audit: `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- Direct source audit: `mobile/ios/BankongSetonStudent/ViewModels/*.swift` (all four VMs)
- Direct source audit: `mobile/ios/BankongSetonStudent/Views/**/*.swift` (all relevant views)
- `.planning/phases/30-ios-bugs-ux/30-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- SwiftUI `onChange` iOS 16 compatibility: well-established pattern; `.onChange(of:) { _ in }` is the correct form for iOS 16 targets

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — project uses SwiftUI with async/await; no new dependencies needed
- Architecture: HIGH — all patterns derived from existing code in the repo
- Pitfalls: HIGH — identified from direct code inspection (401 fallthrough, clearAll visibility, onChange compatibility)

**Research date:** 2026-03-09
**Valid until:** N/A — findings are from static source code, not external APIs
