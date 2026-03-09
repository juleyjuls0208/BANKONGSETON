---
phase: 30-ios-bugs-ux
plan: "02"
subsystem: ios-views
tags: [session-alert, ux, ios, swiftui, keyboard-avoidance, empty-state]
dependency_graph:
  requires: [30-01]
  provides: [session-expired-ui, login-ux, budget-ux, transactions-ux]
  affects: [MainTabView, LoginView, BudgetView, TransactionsView]
tech_stack:
  added: []
  patterns: [EnvironmentObject-alert-binding, hasEdited-guard-pattern, SwiftUI-overlay-empty-state]
key_files:
  created: []
  modified:
    - mobile/ios/BankongSetonStudent/Views/MainTabView.swift
    - mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift
    - mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift
    - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
decisions:
  - clearAll() placed in alert button action (not handleUnauthorized) so alert renders before MainTabView tears down
  - iOS 16 single-arg onChange form used: .onChange(of: limitInput) { _ in } to avoid iOS 17-only two-arg form
  - ScrollView wraps LoginView VStack (not NavigationStack) — only inner content scrolls, not nav chrome
metrics:
  duration: ~10 minutes
  completed: 2026-03-10
  tasks_completed: 2
  files_modified: 4
requirements_covered:
  - REQ-BUG-MOB-05
  - REQ-UX-01
  - REQ-UX-02
  - REQ-UX-04
  - REQ-UX-05
---

# Phase 30 Plan 02: iOS View UX Fixes Summary

**One-liner:** Session expired alert wired to `showSessionExpiredAlert`, plus four SwiftUI UX fixes for PIN autofill, keyboard avoidance, budget input guard, and empty-state overlay.

## What Was Built

Four View files updated to surface the data-layer work from Plan 30-01 and fix standalone UX issues:

### Task 1 — MainTabView: session expired alert (`e85b4be`)

- Added `@EnvironmentObject var authManager: AuthManager` to `MainTabView`
- Added `.alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert)` on the root `TabView`
- Alert message: "Your session has expired. Please sign in again."
- Single "Sign In" button calls `authManager.clearAll()` — deferred to button action so the alert renders before `isLoggedIn = false` tears down the view hierarchy

### Task 2 — Three-file UX fixes (`7365bab`)

**LoginView (REQ-UX-04 + REQ-UX-05):**
- PIN `SecureField` changed from `.textContentType(.password)` → `.textContentType(.oneTimeCode)` — suppresses iOS password autofill suggestion bar for numeric PIN fields
- Inner `VStack` wrapped in `ScrollView` so content scrolls above keyboard on iPhone SE; trailing `Spacer()` replaced with `Spacer(minLength: 20)`

**BudgetView (REQ-UX-01):**
- `@State private var hasEdited = false` added
- `.task` block guards `limitInput = …` assignment with `if !hasEdited { … }` — prevents async server response from overwriting text the user is actively typing
- `.onChange(of: limitInput) { _ in hasEdited = true }` uses iOS 16 single-arg form
- `.onDisappear { hasEdited = false }` resets flag on navigation away so server value reloads fresh next visit

**TransactionsView (REQ-UX-02):**
- New `.overlay` block after the error overlay with "No transactions yet" headline and "Your transaction history will appear here." subtext
- Three-condition guard: `isEmpty && !isLoading && errorMessage == nil` ensures overlay only appears when list is genuinely empty

## Commits (mobile/ios repo — branch main)

| Hash | Task | Description |
|------|------|-------------|
| `e85b4be` | Task 1 | MainTabView session expired alert wired to authManager |
| `7365bab` | Task 2 | UX fixes — oneTimeCode, ScrollView, hasEdited guard, empty state |

## Deviations from Plan

None — plan executed exactly as written.

The only discovery worth noting: `MainTabView` had no `@EnvironmentObject` for `authManager` yet (it was simply a dumb container). Adding the property declaration was the expected setup step before attaching the `.alert` binding — not a deviation.

## Self-Check: PASSED

- `e85b4be` present in `git log` ✅
- `7365bab` present in `git log` ✅
- `showSessionExpiredAlert` in MainTabView: 1 match ✅
- `authManager.clearAll()` in MainTabView: 1 match (button action only) ✅
- `oneTimeCode` in LoginView: 1 match ✅
- `hasEdited` count in BudgetView: 4 matches ✅
- `No transactions yet` in TransactionsView: 1 match ✅
