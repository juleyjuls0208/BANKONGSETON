---
id: T03
parent: S01
milestone: M007
provides:
  - Stitch-faithful LoginView restyle on shared theme/primitives with preserved async auth-submit, loading/disabled gating, and error visibility contracts
key_files:
  - .gsd/milestones/M007/slices/S01/tasks/T03-PLAN.md
  - mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift
  - tests/test_verify_m007_s01_shell_login_contract.py
  - .gsd/milestones/M007/slices/S01/S01-PLAN.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Keep `LoginViewModel` submit contract (`canSubmit`, async `login(...)`, loading/error state ownership) untouched and enforce it with source-contract assertions rather than UI-only styling checks
patterns_established:
  - Login source-contract checks now lock field semantics, async submit wiring, loading indicator visibility, and error rendering in `tests/test_verify_m007_s01_shell_login_contract.py`
  - Token-first login composition pattern: `AppTheme` + `StitchCard` + `stitchFieldStyle()` + `StitchPrimaryButtonStyle()`
observability_surfaces:
  - tests/test_verify_m007_s01_shell_login_contract.py (login assertions)
  - Runtime state surfaces in `LoginView`: `viewModel.isLoading`, `viewModel.errorMessage`, and `.disabled(!viewModel.canSubmit)`
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "login"`
duration: 0h 46m
verification_result: partial
completed_at: 2026-03-22T20:49:38+08:00
blocker_discovered: false
---

# T03: Restyle LoginView on shared primitives while preserving auth behavior

**Restyled `LoginView` with shared Stitch tokens/components while preserving `LoginViewModel` submit/loading/error behavior and adding login contract assertions that guard against wiring regressions.**

## What Happened

I validated the T03 task inputs and baseline files, then confirmed Qodo rules could not be loaded in this environment because `~/.qodo/config.json` is missing.

I refactored `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` to use shared primitives/tokens instead of ad hoc styling:
- `AppTheme` palette/spacing/typography tokens for all layout and visual styling,
- `StitchCard` for grouped login surface,
- `.stitchFieldStyle()` for Student ID and PIN fields,
- `.buttonStyle(StitchPrimaryButtonStyle())` for CTA.

I preserved authentication behavior semantics:
- Student ID/PIN bindings unchanged (`$viewModel.studentId`, `$viewModel.pin`),
- async submit wiring preserved: `Task { await viewModel.login(apiClient: apiClient, authManager: authManager) }`,
- disabled/loading gate preserved via `.disabled(!viewModel.canSubmit)` and loading text/spinner,
- explicit user-visible error rendering preserved with `if let error = viewModel.errorMessage` and `Text(error)`.

I extended `tests/test_verify_m007_s01_shell_login_contract.py` with login-specific assertions that now fail if tokenized primitives are removed, if field semantics are changed, or if submit/loading/error contract wiring is removed.

I also documented a non-obvious verifier gotcha in `.gsd/KNOWLEDGE.md`: running multiple pytest+coverage commands in parallel can race on `.coverage` SQLite state in this environment.

Finally, I marked T03 complete in `.gsd/milestones/M007/slices/S01/S01-PLAN.md`.

## Verification

I executed the task-level verification commands and slice-level checks:
- login-focused contract pytest passed,
- design-system contract pytest passed,
- full shell/login contract pytest passed after rerunning serially,
- iOS build command failed because `xcodebuild` is unavailable in this host environment,
- manual simulator smoke (login → tabs → forced session-expired route back to sign-in) could not be run without Xcode/simulator runtime.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "login"` | 0 | ✅ pass | 0.38s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py` | 0 | ✅ pass | 0.37s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py` | 0 | ✅ pass | 0.38s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (`xcodebuild` not installed on this host) | 0.02s |
| 5 | Manual smoke: login → tab shell transition, 4-tab switching, forced session-expired return-to-sign-in | N/A | ❌ not run (requires macOS simulator runtime) | N/A |

## Diagnostics

- Login contract regressions are now inspectable via:
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py -k "login"`
- Runtime state surfaces in `LoginView.swift`:
  - loading state: `if viewModel.isLoading` + `ProgressView()` + label swap,
  - disabled state: `.disabled(!viewModel.canSubmit)`,
  - error visibility: `if let error = viewModel.errorMessage` + `Text(error)`.
- Full slice contract checks:
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py`
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py`

## Deviations

- I did not modify `StitchFieldStyle.swift` or `StitchPrimaryButtonStyle.swift`; current primitives already satisfied the login restyle contract once consumed directly by `LoginView`.
- One intermediate parallel verification attempt produced a pytest-cov `.coverage` SQLite race; I reran the affected suite serially and recorded the valid passing result.

## Known Issues

- `xcodebuild` is unavailable in this execution environment, so iOS compile/manual simulator smoke proof remains pending on a macOS runner with Xcode installed.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — restyled login screen with shared `AppTheme` tokens and stitch primitives while preserving submit/loading/error semantics.
- `tests/test_verify_m007_s01_shell_login_contract.py` — added login-specific source-contract assertions for token usage, field semantics, async submit wiring, and loading/error visibility.
- `.gsd/KNOWLEDGE.md` — added pytest+coverage parallel-run race-condition rule for future verification runs.
- `.gsd/milestones/M007/slices/S01/S01-PLAN.md` — marked T03 as complete (`[x]`).
