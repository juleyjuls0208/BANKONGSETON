---
id: T04
parent: S01
milestone: M007
provides:
  - Home + Transactions now reuse shared Stitch design primitives/tokens with preserved navigation/auth interactions and regression-proof cross-screen source-contract assertions
key_files:
  - .gsd/milestones/M007/slices/S01/tasks/T04-PLAN.md
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - tests/test_verify_m007_s01_design_system_contract.py
  - .gsd/DECISIONS.md
  - .gsd/milestones/M007/slices/S01/S01-PLAN.md
key_decisions:
  - D076 — enforce downstream primitive reuse by applying `AppTheme` + `StitchCard`/`StitchPrimaryButtonStyle` in Home/Transactions and locking it with source-contract checks across login/shell/destinations
patterns_established:
  - Destination-screen reuse pattern: balance/state/list surfaces consume shared Stitch primitives (`StitchCard`, `StitchPrimaryButtonStyle`) plus semantic `AppTheme` tokens instead of local literals
  - Cross-screen contract pattern: design-system test asserts primitive references in login + shell + downstream destinations (home/transactions) to prevent visual drift regressions
observability_surfaces:
  - Runtime state visibility in `HomeView` and `TransactionsView` via tokenized loading/error/empty surfaces and preserved transaction navigability wiring
  - Source-contract coverage in `tests/test_verify_m007_s01_design_system_contract.py` and `tests/test_verify_m007_s01_shell_login_contract.py`
  - Verification commands: `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py tests/test_verify_m007_s01_shell_login_contract.py`, slice-level pytest checks, and `rtk proxy xcodebuild ... build`
duration: 0h 58m
verification_result: partial
completed_at: 2026-03-22T20:55:28+08:00
blocker_discovered: false
---

# T04: Prove cross-screen reuse by applying primitives to home + transactions surfaces

**Applied shared Stitch primitives to Home/Transactions and locked cross-screen primitive reuse with executable design-contract assertions.**

## What Happened

I validated the T04 inputs and baseline code, then confirmed Qodo rules could not be loaded in this environment because `~/.qodo/config.json` is missing.

I refactored `HomeView` to remove ad hoc styling and use shared primitives/tokens while preserving behavior:
- balance surface now uses tokenized gradient/chrome on `StitchCard`,
- QR CTA now uses `StitchPrimaryButtonStyle()` and remains interactive (`showQrPay` + sheet flow unchanged),
- loading/error/empty recent-transactions states now render through tokenized shared surfaces,
- transaction navigation behavior in recent items remains unchanged (`transaction.isNavigable` still gates `NavigationLink`).

I refactored `TransactionRowView` and `TransactionsView` so transactions surfaces reuse the shared design language:
- row chrome now uses `StitchCard` with semantic `AppTheme` colors/typography,
- debit/credit semantics are preserved (`isDebit` logic retained; sign + semantic color still convey money flow),
- navigable vs non-navigable rows are unchanged in `TransactionsView`,
- list/loading-more/error/empty states now use tokenized spacing/background/buttons/surfaces.

I expanded `tests/test_verify_m007_s01_design_system_contract.py` to enforce multi-screen primitive reuse:
- login + shell references are asserted,
- home + transactions destination references are asserted,
- foundational token/component and project-wiring checks remain intact.

I also appended decision D076 in `.gsd/DECISIONS.md` and marked T04 complete in `.gsd/milestones/M007/slices/S01/S01-PLAN.md`.

## Verification

I ran the task-level and slice-level verification commands. Source-contract suites pass after the refactor. `xcodebuild` cannot run in this host because Xcode tooling is unavailable, so iOS compile/manual simulator smoke remains pending on a macOS runner.

A transient verification failure occurred when I ran two pytest commands in parallel, which raced on `.coverage` SQLite state. I then changed one variable (sequential execution + coverage file cleanup) and reran successfully.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py tests/test_verify_m007_s01_shell_login_contract.py` | 0 | ✅ pass | 0.38s |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py` | 0 | ✅ pass | 0.43s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py` | 0 | ✅ pass | 0.34s |
| 4 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (`xcodebuild` not installed on this host) | 0.02s |
| 5 | Manual smoke: login → tab shell transition, tab switching across all 4 tabs, forced session-expired alert return to sign-in | N/A | ❌ not run (requires macOS simulator runtime) | N/A |

## Diagnostics

- Cross-screen design-system contract checks:
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py`
- Shell/login behavior guardrails:
  - `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py`
- Runtime inspection points for this task:
  - `HomeView`: QR CTA visibility/interactivity (`home-qr-pay-button`), recent-transactions loading/error/empty state surfaces.
  - `TransactionsView`: list row tapability remains gated by `transaction.isNavigable`, load-more state, and loading/error/empty overlays.

## Deviations

- I did not modify `tests/test_verify_m007_s01_shell_login_contract.py`; existing shell/login assertions stayed valid while downstream reuse guarantees were added in the design-system contract test.
- Intermediate parallel pytest execution caused a coverage DB race (`coverage_schema`), so I reran affected checks serially and recorded stable results.

## Known Issues

- `xcodebuild` is unavailable in this environment, so compile-level verification and simulator manual smoke must be executed on a macOS/Xcode-capable runner.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — restyled home balance/QR/recent-transactions surfaces with `AppTheme` + shared primitives while preserving load/refresh/navigation behavior.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — moved row styling to tokenized shared surfaces and preserved debit/credit semantics.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — aligned list container + state overlays/load-more control to shared primitives/tokens while keeping navigable/non-navigable behavior.
- `tests/test_verify_m007_s01_design_system_contract.py` — added multi-screen primitive-reuse assertions spanning login, shell, home, and transactions destinations.
- `.gsd/DECISIONS.md` — appended D076 for downstream primitive-reuse enforcement pattern.
- `.gsd/milestones/M007/slices/S01/S01-PLAN.md` — marked T04 as complete (`[x]`).
