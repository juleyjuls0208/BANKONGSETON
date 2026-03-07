# Phase 20-02 Summary — Dark Mode & Currency Fix

## Status: COMPLETE ✅

## What Was Built

### Dark Mode — 3-Way Theme Selector
- **`values-night/colors.xml`** — re-maps `md_theme_light_*` names to `@color/md_theme_dark_*` references so `themes.xml` stays single-source and Android picks up dark values at night automatically
- **`values-night/themes.xml`** — identical to light theme except `android:windowLightStatusBar` = `false` (white status bar icons in dark mode)
- **`SecureStorage.kt`** — added `saveThemeMode(String)` / `getThemeMode(): String` (key `"theme_mode"`, default `"system"`); old boolean `saveDarkMode`/`isDarkMode` methods preserved for backward compatibility
- **`StudentApp.kt`** — new `Application` subclass; `applyTheme(mode)` companion method maps `"light"/"dark"/"system"` to `AppCompatDelegate` night modes; called in `onCreate()` on every app launch
- **`AndroidManifest.xml`** — `android:name=".StudentApp"` added to `<application>` tag
- **`activity_settings.xml`** — `SwitchMaterial` + "Dark Mode" row replaced with a `MaterialCardView` containing a `RadioGroup` with three `RadioButton`s (`themeSystem`, `themeLight`, `themeDark`)
- **`SettingsActivity.kt`** — fully rewritten theme section: reads stored mode → pre-selects correct radio button; `setOnCheckedChangeListener` saves mode, calls `StudentApp.applyTheme()`, then `recreate()` for instant apply
- **`strings.xml`** — added 4 new strings: `settings_theme`, `theme_system`, `theme_light`, `theme_dark`

### Currency Fix (฿ → ₱)
Replaced all Thai Baht symbols with Philippine Peso across:
- `res/layout/activity_home.xml` — placeholder text `฿0.00` → `₱0.00`
- `HomeActivity.kt` — 3 format strings
- `ReceiptActivity.kt` — 7 format strings (total, balanceBefore, balanceAfter, per-item unit price, qty, total × 2 code paths)
- `TransactionsAdapter.kt` — 2 format strings (amount, balance)

## Key Design Decisions
- **Night color strategy**: `values-night/colors.xml` re-maps names rather than duplicating hex values, keeping `themes.xml` as the single source of truth
- **`recreate()` on theme change**: Simplest correct approach — avoids manual view invalidation
- **Backward compat**: `saveDarkMode()`/`isDarkMode()` in `SecureStorage` left intact; no migration needed

## Build Verification
```
BUILD SUCCESSFUL in 7s
36 actionable tasks: 14 executed, 22 up-to-date
```
Warnings: pre-existing `startActivityForResult` deprecation in `HomeActivity.kt` — unrelated to this phase.
