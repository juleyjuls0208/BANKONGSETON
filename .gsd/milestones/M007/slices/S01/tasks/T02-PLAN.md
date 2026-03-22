---
estimated_steps: 4
estimated_files: 5
skills_used:
  - qodo-get-rules
  - swiftui
  - frontend-design
  - make-interfaces-feel-better
  - debug-like-expert
  - test
---

# T02: Recompose MainTabView into a stitch tab shell without breaking routing

**Slice:** S01 — Design System + Navigation Shell Rework
**Milestone:** M007

## Description

Replace default tab chrome with a reusable stitch-style shell while preserving the current destination routing and session-expired behavior.

## Steps

1. Build `StitchTabShell.swift` that defines shell-level layout, tab metadata, and active/inactive visual treatment using T01 theme tokens.
2. Refactor `MainTabView.swift` to render Home/History/Budget/Settings through the shell component and preserve existing tab order/icons.
3. Keep session-expired alert semantics unchanged (`authManager.showSessionExpiredAlert` + `authManager.clearAll()`), and adjust `ContentView.swift` only as needed to avoid shell/auth-gate regressions.
4. Add shell/session contract assertions in `tests/test_verify_m007_s01_shell_login_contract.py`, then run targeted pytest and iOS build.

## Must-Haves

- [ ] Four primary tabs still route to existing root views with no dead controls.
- [ ] Session-expired alert still appears from main shell path and clears auth state on action.
- [ ] Shell visuals use shared primitives/tokens rather than one-off literals.
- [ ] Contract test detects shell regression in tab labels/order/session wiring.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "tab_shell or session_alert"`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: shell exposes deterministic active-tab state and keeps `showSessionExpiredAlert` presentation path unchanged.
- How a future agent inspects this: run shell/login contract pytest and manually trigger session expiration in simulator to verify alert + sign-in recovery.
- Failure state exposed: regressions surface as missing tab controls, wrong tab routing, or absent auth-reset alert behavior.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — current stock tab implementation to replace.
- `mobile/ios/BankongSetonStudent/App/ContentView.swift` — current auth gate around login/tab root.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — session-expired alert state contract.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — token contract produced by T01.
- `tests/test_verify_m007_s01_design_system_contract.py` — baseline contract checks from T01.

## Expected Output

- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — reusable stitch tab shell container.
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — shell-based tab composition preserving destinations.
- `mobile/ios/BankongSetonStudent/App/ContentView.swift` — auth gate compatibility with new shell.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — project registration for new shell file.
- `tests/test_verify_m007_s01_shell_login_contract.py` — tab shell and session alert assertions.
