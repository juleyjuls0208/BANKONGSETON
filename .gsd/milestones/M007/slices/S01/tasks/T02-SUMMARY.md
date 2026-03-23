---
id: T02
parent: S01
milestone: M007
provides:
  - Stitch-style reusable tab shell wired into MainTabView with preserved auth/session-alert routing contracts and executable shell/login source assertions
key_files:
  - mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift
  - mobile/ios/BankongSetonStudent/Views/MainTabView.swift
  - mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj
  - tests/test_verify_m007_s01_shell_login_contract.py
  - .gsd/milestones/M007/slices/S01/S01-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - D075 — Implement shell chrome as custom UI around hidden native TabView to preserve routing/state while enabling stitch token styling
patterns_established:
  - `StitchTabShell` + `StitchTabItem` metadata pattern for deterministic tab order/labels/icons and active-tab feedback
  - Source-contract assertions for shell file existence, project wiring, tab mapping order, and session-expired alert semantics
observability_surfaces:
  - tests/test_verify_m007_s01_shell_login_contract.py
  - `MainTabView` alert path: `$authManager.showSessionExpiredAlert` + `authManager.clearAll()`
  - `StitchTabShell` accessibility state (`.accessibilityValue("selected"|"not selected")`) for active tab feedback
duration: 1h 02m
verification_result: partial
completed_at: 2026-03-22T20:45:26+08:00
blocker_discovered: false
---

# T02: Recompose MainTabView into a stitch tab shell without breaking routing

**Shipped a reusable token-driven `StitchTabShell`, migrated `MainTabView` onto it with unchanged session-expired auth reset behavior, and added shell/login contract tests with project wiring checks.**

## What Happened

I validated the T02 plan inputs, confirmed T01 design tokens/primitives were present, and verified Qodo rules could not be loaded in this environment because `~/.qodo/config.json` is missing.

I implemented `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` with:
- generic `StitchTabItem` metadata,
- `TabView(selection:)` content host (native tab bar hidden),
- custom bottom tab chrome using `AppTheme` palette/spacing/radius/typography,
- explicit active-tab accessibility feedback.

I refactored `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` to:
- declare canonical tab metadata/order (`home`, `history`, `budget`, `settings`),
- map each tab to existing root views (`HomeView`, `TransactionsView`, `BudgetView`, `SettingsView`),
- keep session-expired alert semantics unchanged (`$authManager.showSessionExpiredAlert` and `authManager.clearAll()` on action).

I registered the new shell file in `project.pbxproj` (file reference, build file, Shell group, sources phase), then added `tests/test_verify_m007_s01_shell_login_contract.py` to assert:
- shell file/project registration,
- token-based shell contract symbols,
- tab metadata/order/icon/view mapping in `MainTabView`,
- unchanged session-expired alert wiring,
- unchanged `ContentView` auth gate.

I also marked T02 done in `.gsd/milestones/M007/slices/S01/S01-PLAN.md` and appended decision D075 to `.gsd/DECISIONS.md`.

## Verification

I ran the task-level shell/session command and slice-level verification commands relevant at this stage:
- shell/session targeted pytest passed,
- design-system contract pytest passed,
- full shell/login contract pytest passed,
- iOS build command failed in this environment because `xcodebuild` is unavailable.

The must-haves covered by automated verification are satisfied except simulator build proof (environment limitation):
- four-tab mapping preserved with existing destination roots,
- session-expired alert path/wiring preserved,
- shell visuals consume shared tokens,
- source-contract test detects shell regression points.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "tab_shell or session_alert"` | 0 | ✅ pass | 0.98s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py` | 0 | ✅ pass | 0.98s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py` | 0 | ✅ pass | 0.94s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (`xcodebuild` not installed in this host) | 0.02s |

## Diagnostics

- Shell contract inspection: `tests/test_verify_m007_s01_shell_login_contract.py`.
- Active-tab feedback inspection: `StitchTabShell.swift` accessibility value toggles selected/not selected per tab.
- Session-expired recovery path inspection: `MainTabView.swift` alert still binds `authManager.showSessionExpiredAlert` and calls `authManager.clearAll()`.
- Build viability on macOS can be re-checked with the same `xcodebuild` command from slice verification.

## Deviations

- Could not load Qodo rules because local Qodo config is missing (`~/.qodo/config.json` not present).
- Could not execute iOS build proof on this machine because `xcodebuild` is not installed.

## Known Issues

- Simulator/runtime manual smoke (login → tab shell transition + forced session-expired recovery) remains pending on a macOS/Xcode environment.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — added reusable stitch tab shell and tab item metadata using shared `AppTheme` tokens.
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — replaced stock `.tabItem` composition with `StitchTabShell` while preserving tab routing and session-expired alert behavior.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — registered `StitchTabShell.swift` in file refs, UI/Shell group, and source build phase.
- `tests/test_verify_m007_s01_shell_login_contract.py` — added shell/session/auth-gate source-contract assertions.
- `.gsd/milestones/M007/slices/S01/S01-PLAN.md` — marked T02 complete (`[x]`).
- `.gsd/DECISIONS.md` — appended D075 documenting tab-shell architecture choice.
