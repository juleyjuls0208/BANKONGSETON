# 23-05 SUMMARY — Settings + Report Lost Card

**Phase:** 23-iphone-app-version  
**Plan:** 05  
**Wave:** 2  
**Status:** COMPLETE

---

## What Was Built

Three new Swift files created, one updated.

### Files Written / Modified

| File | Action | Purpose |
|------|--------|---------|
| `ViewModels/SettingsViewModel.swift` | Created | Theme management (persisted to Keychain), logout orchestration |
| `Views/Settings/SettingsView.swift` | Created | Settings screen: theme picker + logout + lost card NavigationLink |
| `Views/LostCard/LostCardView.swift` | Created | Report Lost Card confirmation screen; POST to API on tap |
| `Views/MainTabView.swift` | Updated | Removed `SettingsView` stub and scaffold comment; file now contains only `MainTabView` |

---

## Key Behaviours

- **Theme toggle**: `Picker` with `.segmented` style; three options ("System" / "Light" / "Dark"). Selection triggers `didSet` which writes to Keychain key `"theme_mode"`. `.preferredColorScheme(viewModel.colorScheme)` applied to root view — takes effect immediately.
- **Theme persistence**: `SettingsViewModel.init()` reads `"theme_mode"` from Keychain on startup; defaults to `"system"` if absent.
- **Logout**: Calls `authManager.logout(apiClient:)` async — clears all 9 Keychain keys and sets `isLoggedIn = false`, causing `ContentView` to switch to `LoginView`.
- **No NFC section** — iOS cannot use HCE; Android's NFC settings section is intentionally absent.
- **LostCardView**: sends `POST /student/lost-card` via `apiClient.reportLostCard()`. On success saves `"true"` to Keychain key `"isCardLost"` and shows green confirmation text. Report button disabled after success.
- **CARD_LOST error**: `LostCardView` catches `APIError.cardLost` and calls `authManager.handleCardLost()`.
- **No `₱`** anywhere — `฿` only (no currency symbol in Settings or LostCard — not needed there).
- **No `NavigationView`** — `NavigationStack` used in `SettingsView`.

---

## Artifacts Delivered

- `SettingsViewModel` — `@MainActor`, `selectedTheme` with `didSet` Keychain write, `colorScheme` computed property returning `ColorScheme?`, `logout(apiClient:authManager:)` async
- `SettingsView` — `Form` with "Appearance" section (segmented picker) and "Account" section (NavigationLink to LostCardView + destructive Logout button with inline ProgressView)
- `LostCardView` — warning icon, description text, red "Report Lost Card" button, success confirmation, error display, CARD_LOST handler
- `MainTabView.swift` — fully clean; no stubs; references `HomeView`, `TransactionsView`, `BudgetView`, `SettingsView` from their real files

---

## All Wave 2 Plans Complete

| Plan | Screen(s) | Status |
|------|-----------|--------|
| 23-02 | Login | ✅ |
| 23-03 | Home / Transactions / Receipt | ✅ |
| 23-04 | Budget Tracker | ✅ |
| 23-05 | Settings + Report Lost Card | ✅ |

---

## What Remains (Plan 06)

- **Plan 06 (Wave 3):** Final build verification, update `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, write `23-06-SUMMARY.md`.
