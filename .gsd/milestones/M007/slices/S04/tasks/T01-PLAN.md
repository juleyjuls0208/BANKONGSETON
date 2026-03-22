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

# T01: Harden Budget and Lost-Card behavior contracts with explicit recoverable state channels

**Slice:** S04 — Budget + Receipt + Lost-Card Redesign
**Milestone:** M007

## Description

Stabilize S04 behavior before UI polish: remove silent Budget load failures, formalize actionable Budget/Lost-Card state channels, and encode the expected failure/session semantics in a dedicated behavior contract test.

## Steps

1. Load coding rules with `qodo-get-rules`, then inspect current Budget and Lost-Card logic for silent catches, ambiguous states, and session-boundary handling gaps.
2. Refactor `BudgetViewModel` to expose explicit load/save error channels (instead of bare catches) and recoverable retry semantics while preserving existing unauthorized/card-lost handling.
3. Introduce `LostCardViewModel` with explicit flow phases (`idle`, `loading`, `success`, `error`) and coherent handling for `APIError.unauthorized` / `APIError.cardLost` / generic failures.
4. Wire `LostCardView` to the new view-model contract so visible controls map to real actions in each phase (report/retry/post-success path) without dead controls.
5. Add `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` asserting required behavior markers for budget state channels, lost-card state machine, and auth/session coherence hooks.

## Must-Haves

- [ ] `BudgetViewModel` has explicit, non-silent failure state markers for load and save paths.
- [ ] Budget failure states expose retry-capable behavior rather than silently falling back to zeroed values.
- [ ] `LostCardViewModel` exists and centralizes idle/loading/success/error transitions.
- [ ] Lost-card flow handles unauthorized/card-lost outcomes coherently with `AuthManager` boundaries.
- [ ] Behavior contract test fails when any of these state markers regress.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: explicit Budget load/save error channels and explicit Lost-Card phase state.
- How a future agent inspects this: run `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` and inspect state properties in `BudgetViewModel.swift` / `LostCardViewModel.swift`.
- Failure state exposed: Budget and Lost-Card failures become visible/actionable in state instead of being silently swallowed.

## Inputs

- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — current budget load/save behavior with silent catch branches.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — current inline lost-card state handling baseline.
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — auth/session transition contract used by failure and card-lost paths.
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — `reportLostCard` and budget endpoint error semantics.

## Expected Output

- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — explicit budget state contract with non-silent failure handling.
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift` — dedicated lost-card flow state model.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — UI wired to explicit lost-card flow states and actionable controls.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — executable S04 behavior contract assertions.
