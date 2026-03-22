---
estimated_steps: 4
estimated_files: 4
skills_used:
  - qodo-get-rules
  - swiftui
  - frontend-design
  - make-interfaces-feel-better
  - accessibility
  - test
---

# T03: Restyle LoginView on shared primitives while preserving auth behavior

**Slice:** S01 — Design System + Navigation Shell Rework
**Milestone:** M007

## Description

Make login stitch-faithful using the shared design system while preserving existing sign-in semantics (loading, disabled state, error display, async submit path).

## Steps

1. Refactor `LoginView.swift` layout (branding, form grouping, CTA surface/background) to consume `AppTheme` + stitch component primitives from T01.
2. Keep Student ID/PIN input semantics and `Task { await viewModel.login(...) }` wiring unchanged so auth behavior remains intact.
3. Ensure disabled/loading/error visual states remain explicit and accessible (contrast + readable error text + non-dead sign-in CTA state transitions).
4. Extend `tests/test_verify_m007_s01_shell_login_contract.py` with login-specific assertions and run pytest + iOS build.

## Must-Haves

- [ ] Login screen visibly uses shared tokens/components instead of local ad hoc styles.
- [ ] Sign-in button preserves loading and disabled state logic from `LoginViewModel`.
- [ ] Error message presentation remains wired and user-visible.
- [ ] Login contract assertions fail if submit wiring or field semantics are removed.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "login"`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: login UI state transitions (idle/loading/error/disabled) become visually standardized via shared primitives.
- How a future agent inspects this: run login-focused pytest assertions and manual login attempts with valid/invalid credentials in simulator.
- Failure state exposed: broken submit wiring, stale disabled logic, or missing error-state rendering becomes immediately visible.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — baseline login implementation.
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift` — canonical submit/loading/error contract.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — shared token definitions from T01.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift` — reusable input style primitive.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — reusable CTA style primitive.
- `tests/test_verify_m007_s01_shell_login_contract.py` — shell/login contract test scaffold from T02.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — stitch-style login view with preserved auth behavior.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift` — finalized form style API used by login.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — finalized CTA style API used by login.
- `tests/test_verify_m007_s01_shell_login_contract.py` — expanded login behavior assertions.
