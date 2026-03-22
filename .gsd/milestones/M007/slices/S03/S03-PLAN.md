# S03: Transactions Redesign + Search/Filter + State Fidelity

**Goal:** Deliver a stitch-faithful Transactions experience with working search/filter interactions, robust pagination continuity, and explicit non-happy-path state handling that does not dead-end the user.
**Demo:** User opens History/Transactions with real data, narrows results using search + type filter, reaches a no-match state with clear recovery controls, loads additional pages when available, and still sees actionable messaging for initial-load and pagination failures without losing already-loaded transactions.

## Must-Haves

- Directly satisfy **R058** by implementing functional Transactions search + filter on top of existing pagination/load-more behavior.
- Directly satisfy **R059** by separating and rendering transaction state fidelity: initial loading, initial error, base empty, filtered empty (no matches), populated, and pagination error with recovery action.
- Support **R055** by keeping Transactions visuals aligned to S01 `AppTheme` + `Stitch*` primitives.
- Support **R056** by ensuring every visible Transactions control is meaningful (`search`, `filter`, `clear`, `retry`, `load more`) with no decorative dead controls.
- Support **R063** by producing executable S03 verifier artifacts and a concise manual Transactions acceptance checklist for downstream on-device demo closure.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_behavior_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_design_contract.py`
- `rtk proxy bash scripts/verify-m007-s03.sh`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- Manual checklist in `.gsd/milestones/M007/slices/S03/S03-UAT.md` passes: search narrowing, filter switching, no-match recovery, load-more continuity, and non-blocking pagination error handling.

## Observability / Diagnostics

- Runtime signals: explicit state channels for initial-load vs pagination failure, plus derived-list state (`base empty` vs `filtered empty`) in `TransactionsViewModel`.
- Inspection surfaces: `tests/test_verify_m007_s03_transactions_behavior_contract.py`, `tests/test_verify_m007_s03_transactions_design_contract.py`, `scripts/verify-m007-s03.sh`, and visible Transactions UI state cards/messages.
- Failure visibility: regressions surface as deterministic contract-test failures; runtime failures remain inspectable through distinct on-screen recovery affordances instead of generic blocking overlays.
- Redaction constraints: verification artifacts must avoid PIN/JWT/PII exposure; only structural/state markers and non-sensitive copy assertions are allowed.

## Integration Closure

- Upstream surfaces consumed: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, and `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift#getTransactions`.
- New wiring introduced in this slice: local search/filter derivation layered over paginated source data, separated failure channels for initial vs pagination fetches, and Transactions UI controls bound to those state channels.
- What remains before the milestone is truly usable end-to-end: S04/S05 must complete redesign scope, S06 tunes motion/perf, and S07 validates integrated iOS 17+ demo journey.

## Tasks

- [x] **T01: Harden Transactions view-model state contract for local search/filter + pagination fidelity** `est:1h 35m`
  - Why: R058/R059 risk sits in state modeling first; without explicit source-vs-derived data and split error channels, UI polish can still produce dead-end behavior.
  - Files: `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`, `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`, `tests/test_verify_m007_s03_transactions_behavior_contract.py`
  - Do: Introduce a clear source list (`allTransactions`) plus derived display list from query/filter state, add normalized transaction-type filter semantics, split initial-load error from pagination error, and preserve load-more continuity with a defensive `hasMore` fallback when backend omits `has_more`.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_behavior_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: View-model state can distinguish base empty vs filtered empty, pagination errors no longer mask already-loaded rows, and behavior-contract tests pass.
- [x] **T02: Redesign Transactions UI with stitch search/filter controls and actionable state surfaces** `est:1h 30m`
  - Why: R055/R056 depend on visible UI wiring; controls must be both stitch-cohesive and behaviorally live across all transaction states.
  - Files: `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`, `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `tests/test_verify_m007_s03_transactions_design_contract.py`
  - Do: Add native search + explicit type-filter control surface, wire clear/reset/retry behaviors, render dedicated cards for initial loading/error/base empty/filtered empty/pagination error/populated states, and keep navigable receipt rows + load-more action continuity.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_design_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Search/filter controls visibly mutate results, every visible CTA is functional, and design-contract tests confirm stitch primitive usage plus no-dead-control invariants.
- [ ] **T03: Add S03 verifier harness and manual Transactions acceptance checklist** `est:55m`
  - Why: Slice closure needs reusable proof artifacts for S07; without a one-command verifier + manual script, regressions can slip between slices.
  - Files: `scripts/verify-m007-s03.sh`, `tests/test_verify_m007_s03_transactions_behavior_contract.py`, `tests/test_verify_m007_s03_transactions_design_contract.py`, `.gsd/milestones/M007/slices/S03/S03-UAT.md`
  - Do: Build an S03 verifier script that runs both pytest contracts plus static assertions for search/filter/load-more/error-state markers, and write a concise manual checklist for populated/empty/error/no-match/load-more flows.
  - Verify: `rtk proxy bash scripts/verify-m007-s03.sh && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: S03 has deterministic automated closure checks and a runnable manual checklist usable by downstream integration slices.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `tests/test_verify_m007_s03_transactions_behavior_contract.py`
- `tests/test_verify_m007_s03_transactions_design_contract.py`
- `scripts/verify-m007-s03.sh`
- `.gsd/milestones/M007/slices/S03/S03-UAT.md`
