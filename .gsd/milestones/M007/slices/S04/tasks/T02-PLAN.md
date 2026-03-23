---
estimated_steps: 5
estimated_files: 4
skills_used:
  - qodo-get-rules
  - swiftui
  - accessibility
  - make-interfaces-feel-better
  - frontend-design
---

# T02: Redesign Budget, Receipt, and Lost-Card views with stitch primitives, accessibility markers, and scope-clean controls

**Slice:** S04 — Budget + Receipt + Lost-Card Redesign
**Milestone:** M007

## Description

Implement the visible S04 redesign: migrate Budget/Receipt/Lost-Card screens to stitch primitives, keep all in-scope controls actionable, harden receipt rendering stability, and preserve existing receipt/lost-card navigation continuity from Home/Transactions/Settings.

## Steps

1. Re-read the state contracts produced in T01 and align Budget/Lost-Card UI composition around those explicit states.
2. Redesign `BudgetView` with `AppTheme`, `StitchCard`, and `StitchPrimaryButtonStyle`, including clear loading/error/success messaging and actionable save/retry/refresh controls.
3. Redesign `ReceiptView` to stitch style while keeping scope-clean behavior (no PDF/report utilities), and replace name-only line-item identity iteration with stable identity rendering for duplicate item names.
4. Redesign `LostCardView` to stitch style and accessibility standards, ensuring every visible CTA maps to real phase transitions from `LostCardViewModel`.
5. Add `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` to assert stitch primitive usage, accessibility identifiers/hints, receipt scope guards, stable line-item iteration markers, and navigation continuity anchors.

## Must-Haves

- [ ] Budget/Receipt/Lost-Card screens use shared stitch primitives and `AppTheme` tokens.
- [ ] Receipt keeps non-scope utility controls absent (no PDF/download/report-issue surfaces).
- [ ] Receipt item rendering no longer depends on `id: \.name` collisions.
- [ ] Accessibility identifiers/labels/hints are present for key state cards and action controls across S04 screens.
- [ ] Design contract test enforces stitch usage, scope-clean markers, and navigation continuity hooks.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: explicit S04 UI state cards and accessibility identifiers for loading/error/success/action controls.
- How a future agent inspects this: run `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` and inspect S04 SwiftUI view files for required identifiers and stitch primitive markers.
- Failure state exposed: regressions show as missing state surfaces/identifiers or dead CTA paths rather than ambiguous UI output.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — current non-stitch budget UI baseline.
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` — current list-based receipt implementation with name-only item identity.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — current pre-stitch lost-card UI shell.
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — budget state contract from T01.
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift` — lost-card state contract from T01.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — stitch theme tokens and spacing/typography palette.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — stitch-faithful budget UI with actionable state surfaces.
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` — stitch receipt UI with stable line-item rendering and scope-clean controls.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — stitch lost-card UI wired to explicit phase states.
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py` — executable design/scope/accessibility contract assertions.
