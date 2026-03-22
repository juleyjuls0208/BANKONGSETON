---
estimated_steps: 5
estimated_files: 4
skills_used:
  - swiftui
  - frontend-design
  - make-interfaces-feel-better
  - accessibility
  - code-simplifier
---

# T02: Redesign Transactions UI with stitch search/filter controls and actionable state surfaces

**Slice:** S03 — Transactions Redesign + Search/Filter + State Fidelity
**Milestone:** M007

## Description

Implement the stitch-faithful Transactions surface that consumes the hardened view-model contract: working search/filter controls, clear state-specific cards (loading/empty/error/filtered-empty/populated), and load-more continuity with actionable recovery controls.

## Steps

1. Wire `.searchable` and explicit transaction-type filter controls in `TransactionsView` to the view-model query/filter properties from T01.
2. Render dedicated state surfaces for base loading, base empty, filtered empty/no-match, initial error, populated list, and pagination failure while preserving row navigation behavior.
3. Keep `Load More`, `Retry`, and `Clear Filter/Search` controls visibly actionable and non-decorative; ensure no state traps the user.
4. Apply stitch visual consistency (`AppTheme`, `StitchCard`, `StitchPrimaryButtonStyle`) across new controls/cards and ensure labels are descriptive/accessibility-safe.
5. Add `tests/test_verify_m007_s03_transactions_design_contract.py` asserting control presence/wiring markers, stitch primitive usage, and no-dead-control contracts.

## Must-Haves

- [ ] Search input and filter controls are present and wired to real result mutation.
- [ ] Transactions states include explicit filtered-empty and pagination-error presentations in addition to loading/empty/error/populated.
- [ ] Load-more and row navigation continuity remain intact in populated state.
- [ ] Every visible control in Transactions has meaningful behavior (retry/reset/load-more/filter/search).
- [ ] Design contract test enforces stitch primitive usage and state/control marker coverage.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_design_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: user-visible state cards map directly to underlying view-model channels, making failure mode diagnosis visible at runtime.
- How a future agent inspects this: inspect `TransactionsView.swift` state branches + control bindings and run `tests/test_verify_m007_s03_transactions_design_contract.py`.
- Failure state exposed: no-match and pagination-failure paths become explicit and recoverable instead of collapsing into a single generic empty/error overlay.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — baseline transactions UI shell.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — row rendering + nav affordance semantics.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — stitch token contracts for spacing/typography/colors.
- `tests/test_verify_m007_s03_transactions_behavior_contract.py` — T01 behavior invariants that UI must reflect.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — redesigned searchable/filterable transactions UI with explicit state surfaces.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — row-level tweaks needed for filtered-state/readability continuity.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — token adjustments if required for stitch parity in new controls/cards.
- `tests/test_verify_m007_s03_transactions_design_contract.py` — executable UI/design contract assertions for S03.
