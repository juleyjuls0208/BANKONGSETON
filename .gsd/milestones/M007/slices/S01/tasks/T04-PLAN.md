---
estimated_steps: 5
estimated_files: 5
skills_used:
  - qodo-get-rules
  - swiftui
  - frontend-design
  - make-interfaces-feel-better
  - test
  - lint
  - code-review
  - code-review-expert
---

# T04: Prove cross-screen primitive reuse on home + transactions surfaces

**Slice:** S01 — Design System + Navigation Shell Rework
**Milestone:** M007

## Description

Retire S01 visual-drift risk by applying shared primitives outside login/shell and locking that reuse with executable assertions.

## Steps

1. Refactor `HomeView.swift` balance card/QR CTA/section surfaces to use shared stitch card, button, spacing, and semantic color tokens.
2. Refactor `TransactionRowView.swift` and `TransactionsView.swift` list-row/list-container styling to consume shared tokens/components while preserving debit-credit semantics and navigation behavior.
3. Remove leftover screen-local style literals that duplicate T01 primitives where practical in these two destinations.
4. Expand `tests/test_verify_m007_s01_design_system_contract.py` to assert primitives are referenced by login + shell + at least one downstream destination (`HomeView` or transactions files).
5. Run full S01 verification suite (`pytest` files + `xcodebuild`) and fix any contract/build failures.

## Must-Haves

- [ ] Shared design primitives are now used in non-login destination screens.
- [ ] Transactions interaction behavior (navigable vs non-navigable rows) remains unchanged.
- [ ] Home QR entry control remains interactive and visible after restyle.
- [ ] Contract tests enforce multi-screen reuse so future slices cannot regress back to ad hoc styles.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py tests/test_verify_m007_s01_shell_login_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: home and transactions state UIs share consistent visual state indicators (loading/error/empty/success surfaces) through common primitives.
- How a future agent inspects this: run both S01 pytest contracts, then use simulator to exercise home refresh + transactions load-more/list navigation.
- Failure state exposed: regressions appear as failing primitive-reuse assertions or runtime breakage in home/transactions control interactions.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — destination screen requiring primitive adoption.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — row-level styling currently semi-custom.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — list container/state overlays.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — canonical token source from T01.
- `tests/test_verify_m007_s01_design_system_contract.py` — contract test baseline to extend.
- `tests/test_verify_m007_s01_shell_login_contract.py` — login/shell behavior guardrail to keep green while restyling.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — home screen restyled with shared primitives.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — transaction row restyled with shared tokens.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — transactions list container aligned to shell language.
- `tests/test_verify_m007_s01_design_system_contract.py` — assertions enforcing cross-screen primitive reuse.
- `tests/test_verify_m007_s01_shell_login_contract.py` — preserved shell/login behavior coverage after downstream styling updates.
