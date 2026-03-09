# Phase 30 Context: iOS Bugs & UX

## Phase Overview

Fix 6 iOS-only issues across two categories: error handling bugs (REQ-BUG-MOB-04, REQ-BUG-MOB-05) and UX polish (REQ-UX-01 through REQ-UX-05). No backend changes, no Android changes.

**Depends on:** Phase 27 (critical mobile fixes) — complete.

---

## Decisions

### Gray Area 1 — 401 session expiry flow (REQ-BUG-MOB-05)

**Decision:** Alert → redirect to login. No silent logout.

- Add `APIError.unauthorized` case to `APIClient.swift` (mirrors existing `APIError.cardLost` pattern)
- Add `handleUnauthorized()` method to `AuthManager.swift` — calls `clearAll()` and sets an observable flag/publishes an event
- All ViewModels that call the API catch `.unauthorized` and trigger the alert flow
- Alert message: "Your session has expired. Please sign in again."
- Single "Sign In" button on the alert — dismisses alert and redirects to login screen
- After re-login, user lands on Home tab fresh. No deep-link back to where they were.

### Gray Area 2 — Card lost error messaging (REQ-BUG-MOB-04)

**Decision:** Inline red error text on login screen only.

- Detection: parse error response body for the string `CARD_LOST` (not by HTTP status code)
- Surface: login screen only, as inline red error text (consistent with existing error display in `LoginView`)
- Message: "Your card has been reported lost. Please contact the canteen admin."
- Mid-session card-lost is already handled by the existing `handleCardLost()` flow from Phase 27 — no changes needed there

### Gray Area 3 — Budget input protection (REQ-UX-01)

**Decision:** `hasEdited` flag, resets on navigate-away.

- Add `@State var hasEdited = false` to `BudgetView`
- Set `hasEdited = true` in `onChange` of `limitInput`
- In `.task`, only assign `limitInput = String(format: "%.2f", viewModel.limit)` if `!hasEdited`
- Reset `hasEdited = false` in `.onDisappear` so server value reloads fresh on next visit
- Unsaved typed input is discarded when the user navigates away (this is intentional)

### Gray Area 4 — Loading & empty states (REQ-UX-02 + REQ-UX-03)

**REQ-UX-02 — Empty transactions list:**
- Show an empty state overlay when `viewModel.transactions.isEmpty` and not loading
- Message: "No transactions yet"
- Subtext: "Your transaction history will appear here."
- No icon required

**REQ-UX-03 — Balance shows ₱0.00 during loading:**
- `HomeViewModel` already saves to Keychain key `last_balance` after each load
- On `HomeViewModel` init, read `last_balance` from Keychain and set as the initial `balance` value
- When fresh data arrives, update `balance` normally
- Result: user sees last known balance immediately instead of ₱0.00

---

## Out of Scope

- REQ-UX-04 (PIN autofill) and REQ-UX-05 (keyboard hiding Sign In on SE) — these are straightforward fixes with no gray areas; implementation details left to the planner
- No backend changes
- No Android changes
- No new screens or navigation restructuring

---

## Key Files

| File | Change |
|------|--------|
| `Core/Network/APIClient.swift` | Add `APIError.unauthorized` case |
| `Core/Auth/AuthManager.swift` | Add `handleUnauthorized()` method |
| `ViewModels/HomeViewModel.swift` | Read `last_balance` from Keychain on init |
| `ViewModels/BudgetViewModel.swift` | No changes needed (fix is in the View) |
| `Views/Auth/LoginView.swift` | Card lost inline error; PIN field content type fix; keyboard avoidance for SE |
| `Views/Budget/BudgetView.swift` | `hasEdited` flag to protect input from server overwrite |
| `Views/Home/HomeView.swift` | Pass cached balance through; 401 alert |
| `Views/Transactions/TransactionsView.swift` | Empty state overlay |
| All ViewModels that call API | Handle `.unauthorized` → trigger alert flow |
