---
id: S01
parent: M007
milestone: M007
provides:
  - Shared SwiftUI design system contract (tokens + primitives) and stitch-style navigation/login shell reused beyond auth entry.
  - Cross-screen primitive adoption in Home and Transactions with source-level regression checks.
requires: []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift
  - mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift
  - mobile/ios/BankongSetonStudent/Views/MainTabView.swift
  - mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
  - tests/test_verify_m007_s01_design_system_contract.py
  - tests/test_verify_m007_s01_shell_login_contract.py
key_decisions:
  - Use a semantic AppTheme namespace plus shared UI primitives as the single source of stitch styling truth.
  - Implement custom tab chrome around a hidden native TabView host to preserve existing routing/state semantics while enabling stitch shell visuals.
  - Lock shell/login/cross-screen reuse with source-contract pytest checks to catch visual-contract regressions early.
patterns_established:
  - Token-first composition (`AppTheme` + reusable components/modifiers) instead of per-screen hardcoded styling.
  - Contract-test guardrails for UI structure/wiring and cross-screen primitive reuse.
observability_surfaces:
  - rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py
  - rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py
  - MainTabView session-expired alert path (`$authManager.showSessionExpiredAlert` + `authManager.clearAll()`).
  - LoginView runtime state surfaces (`viewModel.isLoading`, `viewModel.errorMessage`, `.disabled(!viewModel.canSubmit)`).
drill_down_paths:
  - .gsd/milestones/M007/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S01/tasks/T03-SUMMARY.md
  - .gsd/milestones/M007/slices/S01/tasks/T04-SUMMARY.md
duration: 3h 58m
verification_result: partial
completed_at: 2026-03-22T20:55:28+08:00
---

# S01: Design System + Navigation Shell Rework

**Shipped a reusable stitch-faithful SwiftUI foundation (theme, primitives, custom tab shell, and login restyle) and proved cross-screen reuse on Home/Transactions with executable source-contract checks.**

## What Happened

S01 established the base visual contract for M007 instead of restyling screens in isolation.

- **T01** created shared theme/primitives (`AppTheme`, `Color+Hex`, `StitchCard`, field/button styles), registered them in the Xcode project, and added initial design-system contract tests.
- **T02** introduced `StitchTabShell` and migrated `MainTabView` to a custom stitch shell while preserving existing tab destinations and session-expired auth-reset semantics.
- **T03** restyled `LoginView` onto shared primitives/tokens while preserving `LoginViewModel` submit/loading/error behavior.
- **T04** applied the shared primitives to Home and Transactions surfaces (cards, states, row styling) and expanded tests to assert cross-screen adoption so downstream slices can rely on one visual language.

The slice retired the main S01 risk (visual-contract fragmentation) by proving shared primitives are used in multiple destinations, not only login/shell.

## Verification

Executed verification from slice/task evidence:

- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py` ✅
- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py` ✅
- Targeted subsets for shell/session/login assertions (`-k "tab_shell or session_alert"`, `-k "login"`) ✅
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` ❌ on this host (`xcodebuild` unavailable)
- Manual simulator smoke (login → tab shell, 4-tab switching, forced session-expired return-to-sign-in) not run in this environment

Result: source-level contract verification passed; compile/runtime simulator proof remains environment-blocked.

## Requirements Advanced

- **R055** — Delivered the shared stitch visual system and applied it across login, tab shell, home, and transactions.
- **R056** — Preserved in-scope interaction continuity in restyled surfaces (login submit states, tab switching, session-expired recovery wiring).

## Requirements Validated

- none yet — full simulator/device runtime proof for this slice requires a macOS/Xcode environment.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- Qodo rules could not be loaded in this environment because `~/.qodo/config.json` was missing.
- Planned `xcodebuild` and simulator smoke checks could not run on this host due missing Xcode tooling.
- Parallel pytest runs briefly triggered a `.coverage` SQLite race; checks were rerun serially for stable evidence.

## Known Limitations

- iOS compile-level proof and simulator/manual smoke remain pending on a macOS runner with Xcode installed.
- `S01-UAT.md` is still a doctor recovery placeholder and should be replaced with a real human-check script before relying on slice-level UAT evidence.

## Follow-ups

- Run the planned `xcodebuild` command on macOS and capture pass/fail evidence for this slice.
- Replace `.gsd/milestones/M007/slices/S01/S01-UAT.md` placeholder with concrete human verification steps aligned to the redesigned shell/login/base destinations.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — centralized semantic color/spacing/type/shadow tokens.
- `mobile/ios/BankongSetonStudent/UI/Theme/Color+Hex.swift` — shared color hex utility extracted from feature-local scope.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — reusable surface/card primitive.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift` — reusable input styling modifier.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — reusable primary CTA style.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — custom tokenized tab shell preserving existing tab destination model.
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — shell migration with preserved session-expired alert handling.
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — tokenized login restyle with preserved async auth wiring.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — shared primitive adoption for balance/QR/recent-transaction surfaces.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` and `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — shared token/primitive adoption while preserving debit/credit + navigability semantics.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — project registration for newly introduced Swift files.
- `tests/test_verify_m007_s01_design_system_contract.py` — design-system and cross-screen reuse contract checks.
- `tests/test_verify_m007_s01_shell_login_contract.py` — shell/session/login source-contract checks.

## Forward Intelligence

### What the next slice should know
- The styling contract is now centralized; downstream slices should consume `AppTheme` and shared primitives rather than introducing new local literals.

### What's fragile
- Environment-dependent verification — source-contract tests pass cross-platform, but compile/runtime proof depends on macOS/Xcode availability.

### Authoritative diagnostics
- `tests/test_verify_m007_s01_design_system_contract.py` — best guardrail for theme/primitives/cross-screen reuse regressions.
- `tests/test_verify_m007_s01_shell_login_contract.py` — best guardrail for tab shell mapping, auth gate, and login behavior wiring.

### What assumptions changed
- Assumption: visual restyle could be verified primarily by compile/runtime checks in this environment.
- Actual: in this host, source-contract tests are the reliable verification surface; simulator/device checks must be delegated to macOS/Xcode runtime.