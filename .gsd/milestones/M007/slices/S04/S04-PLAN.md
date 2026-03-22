# S04: Budget + Receipt + Lost-Card Redesign

**Goal:** Deliver stitch-faithful Budget, Receipt, and Lost-Card surfaces with explicit state behavior, no dead in-scope controls, and scope-clean receipt UX.
**Demo:** User can open Budget, save/retry budget updates from explicit state surfaces, open redesigned Receipt from Home or Transactions with stable item rendering and no utility-action clutter, and complete the Lost-Card flow from Settings with coherent success/error/session behavior.

## Must-Haves

- Directly satisfy **R055** by applying S01 visual contracts (`AppTheme`, `StitchCard`, `StitchPrimaryButtonStyle`) across Budget, Receipt, and Lost-Card screens.
- Directly satisfy **R056** by ensuring every visible in-scope S04 control is actionable (`save`, `retry`, `refresh`, `report lost card`, post-success next step) with no decorative dead CTAs.
- Directly satisfy **R061** by keeping non-scope receipt utility actions absent (no PDF/download/report-issue/report surfaces).
- Support **R059** by making Budget and Lost-Card loading/success/error states explicit and recoverable, while keeping Receipt item rendering resilient when backend item lists are empty or repetitive.
- Support **R063** by adding reusable S04 verifier artifacts (contract tests + one-command verifier + manual checklist) for downstream iOS demo closure.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- `rtk proxy bash scripts/verify-m007-s04.sh`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- Manual checklist in `.gsd/milestones/M007/slices/S04/S04-UAT.md` passes for budget save/error recovery, receipt entrypoint continuity/scope-clean rendering, and lost-card success/failure handling.

## Observability / Diagnostics

- Runtime signals: explicit Budget load/save failure channels, explicit Lost-Card flow phase state (`idle/loading/success/error`), and deterministic receipt fallback/item-render markers.
- Inspection surfaces: `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`, `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`, `scripts/verify-m007-s04.sh`, and accessibility identifiers/state cards in S04 SwiftUI views.
- Failure visibility: regressions surface as deterministic contract-test failures plus visible in-app recovery states (retry/refresh/report) instead of silent catch paths or ambiguous blank screens.
- Redaction constraints: verifier artifacts must not log PIN/JWT/auth-token/PII values; checks stay structural/copy-based only.

## Integration Closure

- Upstream surfaces consumed: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`, and existing S01/S02/S03 navigation routes.
- New wiring introduced in this slice: Budget and Lost-Card explicit state contracts bound to actionable UI surfaces, receipt stable line-item identity handling, and static/runtime verification hooks for S04-specific scope guards.
- What remains before the milestone is truly usable end-to-end: S05 settings persistence/scope cleanup, S06 motion/performance tuning, and S07 full integrated device-readiness closure.

## Tasks

- [ ] **T01: Harden Budget and Lost-Card behavior contracts with explicit recoverable state channels** `est:1h 35m`
  - Why: S04’s biggest functional risk is silent/ambiguous state handling; this must be fixed before polish so redesigned screens are not dead-ended under failures.
  - Files: `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`, `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`, `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
  - Do: Remove silent Budget load failure behavior in favor of explicit load/save status + retryable error channels, introduce a dedicated Lost-Card state model that handles unauthorized/card-lost paths coherently with auth/session boundaries, and lock these contracts with behavior-oriented source assertions.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Budget no longer hides load failures, Lost-Card flow exposes deterministic actionable states, and behavior-contract tests pass.
- [ ] **T02: Redesign Budget, Receipt, and Lost-Card views with stitch primitives, accessibility markers, and scope-clean controls** `est:1h 40m`
  - Why: Requirement closure depends on visible stitch parity and no-dead-control UX across all three S04 surfaces, not just internal state contracts.
  - Files: `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`, `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`, `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`, `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
  - Do: Apply `AppTheme` + `StitchCard` + `StitchPrimaryButtonStyle` patterns to Budget/Receipt/Lost-Card, add accessibility identifiers/labels/hints for key state and action controls, keep receipt utility actions absent, and ensure receipt item iteration uses stable identity (not name-only collisions) while preserving existing Home/Transactions/Settings entrypoint continuity.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: all S04 screens visibly use stitch primitives, receipt scope remains clean, accessibility markers exist for deterministic checks, and design-contract tests pass.
- [ ] **T03: Add one-command S04 verifier and manual acceptance checklist for demo closure** `est:1h`
  - Why: S04 must ship reusable proof artifacts for S06/S07; without an explicit verifier + checklist, regressions in scope/actionability are hard to catch quickly.
  - Files: `scripts/verify-m007-s04.sh`, `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`, `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`, `.gsd/milestones/M007/slices/S04/S04-UAT.md`
  - Do: Create an S04 verifier script that runs both pytest suites plus static literal checks for required S04 markers (state channels, action controls, receipt utility-action absence, navigation continuity), and add a concise manual UAT checklist covering budget success/failure recovery, receipt-from-home/transactions validation, and lost-card success/failure flows.
  - Verify: `rtk proxy bash scripts/verify-m007-s04.sh && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: S04 has deterministic automated closure commands and a runnable manual checklist that downstream slices can execute without re-discovering scope expectations.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- `scripts/verify-m007-s04.sh`
- `.gsd/milestones/M007/slices/S04/S04-UAT.md`
