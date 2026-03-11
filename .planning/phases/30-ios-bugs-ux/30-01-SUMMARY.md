---
phase: 30-ios-bugs-ux
plan: "01"
subsystem: ios-app
tags: [ios, swift, auth, error-handling, ux, viewmodels]
dependency_graph:
  requires: []
  provides:
    - 401-unauthorized-handling
    - session-expiry-infrastructure
    - card-lost-login-message
    - cached-balance-on-launch
  affects:
    - 30-02 (UI wiring of handleUnauthorized alert)
tech_stack:
  added: []
  patterns:
    - catch-specific-before-generic
    - keychain-cache-on-init
    - alert-teardown-ordering
key_files:
  created: []
  modified:
    - mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
    - mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift
    - mobile/ios/BankongSetonStudent/Models/LoginModels.swift
    - mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift
    - mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift
    - mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift
    - mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift
decisions:
  - "catch APIError.unauthorized placed BEFORE generic catch in all three non-login ViewModels"
  - "handleUnauthorized() intentionally does NOT call clearAll() — clearAll is deferred to View's alert button action to prevent alert being torn down before user sees it"
  - "LoginViewModel catches .cardLost before .unauthorized — a 401 on login = wrong credentials, not session expiry"
  - "HomeViewModel.init() reads Keychain last_balance so balance shows immediately on launch, not ₱0.00"
  - "mobile/ios/ is a separate nested git repo — commits are in mobile/ios git, not parent project git"
metrics:
  duration: 8min
  completed_date: "2026-03-10"
  tasks_completed: 2
  files_modified: 7
requirements_covered:
  - REQ-BUG-MOB-04
  - REQ-BUG-MOB-05
  - REQ-UX-03
---

# Phase 30 Plan 01: iOS Session Expiry, Card Lost & Cached Balance Summary

**One-liner:** 401→.unauthorized mapping + AuthManager session expiry infrastructure + card-lost login message + Keychain-cached balance init across all iOS ViewModels.

## What Was Built

### Task 1 — APIClient + AuthManager infrastructure (commit `2d862c3`)

**APIClient.swift:**
- Added `statusCode == 401 → throw APIError.unauthorized` immediately before the existing 403 block
- Replaced `fatalError()` in `authenticatedRequest()` and `login()` with `throw APIError.invalidURL`
- Added `invalidURL` case to the `APIError` enum

**AuthManager.swift:**
- Added `@Published var showSessionExpiredAlert: Bool = false`
- Added `handleUnauthorized()` method — sets `showSessionExpiredAlert = true`, does NOT call `clearAll()` (critical ordering: alert must be visible before view is torn down)
- Changed `private func clearAll()` → `func clearAll()` so Views can call it from alert button actions

**LoginModels.swift (bonus fix — Rule 2):**
- Added `cardStatus: String?` optional field to `Student` model with `card_status` CodingKey
- `AuthManager.login()` clears `isCardLost` Keychain key when card status is "active"

### Task 2 — ViewModels (commit `26fc7db`)

**HomeViewModel.swift:**
- Added `init()` that reads `last_balance` from Keychain and initialises `balance` — balance shows immediately on launch instead of ₱0.00
- Added `catch APIError.unauthorized { authManager.handleUnauthorized() }` in `load()` before generic catch

**TransactionsViewModel.swift:**
- Added `catch APIError.unauthorized { authManager.handleUnauthorized() }` in `fetchPage()` before generic catch

**BudgetViewModel.swift:**
- Added `catch APIError.unauthorized` in both `load()` AND `setBudget()` (2 occurrences) before generic catch

**LoginViewModel.swift:**
- Added `catch APIError.cardLost` BEFORE the existing `catch APIError.unauthorized`
- Error message: "Your card has been reported lost. Please contact the canteen admin."

## Verification Results

| Check | Expected | Result |
|-------|----------|--------|
| `statusCode == 401` in APIClient | 1 match | ✅ line 52 |
| `clearAll()` not private | no `private` | ✅ confirmed |
| `.unauthorized` catches across ViewModels | 5 total (Home×1, Transactions×1, Budget×2, Login×1) | ✅ 5 matches |
| BudgetViewModel `.unauthorized` count | 2 | ✅ 2 |
| `KeychainHelper.read.*last_balance` in HomeViewModel | 1 match | ✅ line 14 |
| `.cardLost` catch in LoginViewModel | correct message | ✅ confirmed |

## Deviations from Plan

### Pre-existing work (infrastructure already done)

**Found during:** Task 1 file reads

**Issue:** APIClient.swift already had `statusCode == 401` block; AuthManager.swift already had `showSessionExpiredAlert`, `handleUnauthorized()`, and public `clearAll()`.

**Explanation:** These changes were introduced in a prior session (Phase 30 context/research phase). The plan was written before execution — the infrastructure was pre-built.

**Action:** Verified all pre-existing code matched plan spec exactly. Proceeded directly to Task 2 ViewModel changes.

### Auto-fix — LoginModels.swift cardStatus field [Rule 2 - Missing critical functionality]

**Found during:** Task 1 review

**Issue:** `AuthManager.login()` referenced `student.cardStatus` to conditionally clear the `isCardLost` Keychain key, but `Student` model had no `cardStatus` field — this would be a compile error.

**Fix:** Added `cardStatus: String?` to `Student` with `card_status` CodingKey. Committed with Task 1 files.

**Files modified:** `mobile/ios/BankongSetonStudent/Models/LoginModels.swift`

### Separate nested git repository

**Found during:** Commit phase

**Issue:** `mobile/ios/` contains its own `.git` directory — it is a standalone git repository, not tracked by the parent project's git.

**Action:** All commits made inside `mobile/ios/` repository (on `main` branch). Parent project git shows `mobile/ios/` as untracked directory — this is expected and correct.

## Self-Check

```
[x] mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift — modified
[x] mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift — modified
[x] mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift — modified
[x] mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift — modified
[x] mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift — modified
[x] mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift — modified
[x] Commit 2d862c3 — Task 1 (APIClient + AuthManager + LoginModels)
[x] Commit 26fc7db — Task 2 (ViewModels)
```

## Self-Check: PASSED
