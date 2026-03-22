---
estimated_steps: 5
estimated_files: 4
skills_used:
  - qodo-get-rules
  - swiftui
  - debug-like-expert
  - test
  - best-practices
---

# T01: Harden Transactions view-model state contract for local search/filter + pagination fidelity

**Slice:** S03 — Transactions Redesign + Search/Filter + State Fidelity
**Milestone:** M007

## Description

Stabilize the transactions data/state contract before UI polish: maintain one canonical paginated source list, derive displayed rows from local query/filter state, and split initial-load failures from pagination failures so loaded history never disappears behind a global error overlay.

## Steps

1. Load coding rules with `qodo-get-rules`, then review existing `TransactionsViewModel` fetch/pagination/error behavior and identify where R058/R059 gaps currently occur.
2. Refactor the view model to keep canonical paginated data separate from derived display data, adding query/filter properties and deterministic recompute hooks.
3. Add normalized transaction filter semantics in models/view model (e.g., all/debit/credit) that tolerate backend type-string variation.
4. Split failure channels (`initial` vs `pagination`) and ensure `hasMore` continuity remains safe even when backend omits `has_more`.
5. Create `tests/test_verify_m007_s03_transactions_behavior_contract.py` with source-contract assertions for derived-list behavior, filter semantics, and non-blocking pagination-failure handling markers.

## Must-Haves

- [ ] View model has a canonical source list plus derived displayed-list state driven by search + filter inputs.
- [ ] Transaction-type filter semantics are centralized and resilient to known backend type-string variants.
- [ ] Initial-load error handling is distinct from pagination error handling.
- [ ] `hasMore` continuity has a defensive fallback for responses that omit `has_more`.
- [ ] Behavior contract test fails when these state-safety markers regress.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s03_transactions_behavior_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: distinct view-model signals for initial load status, pagination status, and derived filter/search state.
- How a future agent inspects this: run `tests/test_verify_m007_s03_transactions_behavior_contract.py` and inspect state-channel properties/guards in `TransactionsViewModel.swift`.
- Failure state exposed: pagination failures remain visible as recoverable status without masking already-fetched transaction rows.

## Inputs

- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift` — current single-list/single-error implementation baseline.
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift` — transaction model helpers and type normalization seam.
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — `getTransactions(limit:offset:)` contract constraints.
- `.gsd/milestones/M007/slices/S03/S03-RESEARCH.md` — backend/search/filter constraints and state-fidelity risks.

## Expected Output

- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift` — canonical+derived state model with split error channels.
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift` — normalized filter classification helpers for transaction types.
- `tests/test_verify_m007_s03_transactions_behavior_contract.py` — executable behavior/state contract assertions for S03.
