---
estimated_steps: 5
estimated_files: 7
skills_used:
  - qodo-get-rules
  - swiftui
  - debug-like-expert
  - code-simplifier
  - best-practices
  - test
---

# T02: Wire final QR-success continuity across Home and Transactions without state regressions

**Slice:** S07 — Final Integration + Device Demo Readiness Gate
**Milestone:** M007

## Description

Apply final runtime wiring fixes so a successful QR payment always lands in coherent post-payment state across Home and Transactions, while preserving all previously delivered search/filter/pagination and error-state behavior.

## Steps

1. Harden QR success completion path in `QRPayView` / `QRPayViewModel` so success side effects are one-shot (no duplicate refresh/dismiss callbacks from auto-dismiss + manual actions).
2. Wire post-QR refresh continuity into `HomeView` / `HomeViewModel` so balance and recent transactions are deterministically refreshed after successful payment completion.
3. Wire `TransactionsView` / `TransactionsViewModel` to consume the same continuity signal and refresh history without breaking current search/filter or pagination-failure semantics.
4. Preserve current in-scope actionability markers (retry/load-more/confirm/save/report/logout controls) and keep out-of-scope surfaces absent.
5. Update S07 integration behavior contracts if any marker names/identifiers shift while preserving requirement intent.

## Must-Haves

- [ ] QR success path triggers refresh continuity exactly once per completed payment flow.
- [ ] Home and Transactions reflect post-payment continuity without erasing existing search/filter/load-more behavior.
- [ ] No dead controls or out-of-scope surfaces are introduced while wiring final integration.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- `rtk proxy sh scripts/verify-m007-s07.sh`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: QR-success continuity and refresh transitions should remain log-visible (`QRPayState`, Home refresh, Transactions refresh markers).
- How a future agent inspects this: run `scripts/verify-m007-s07.sh` and inspect `phase=integration-contract` output plus relevant view-model logs.
- Failure state exposed: duplicate QR-success side effects, stale post-payment lists, or lost actionability fail S07 contracts with explicit phase guidance.

## Inputs

- `tests/test_verify_m007_s07_integration_behavior_contract.py` — continuity contract expectations from T01.
- `tests/test_verify_m007_s07_scope_guard_contract.py` — final scope guard expectations from T01.
- `scripts/verify-m007-s07.sh` — phased closure verifier from T01.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — QR success state UI + completion callbacks.
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — QR flow state transitions.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — post-QR sheet completion and refresh hook.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — refresh-after-success seam.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — transactions screen continuity wiring surface.
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift` — canonical/derived state + pagination continuity.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — one-shot success completion wiring and stable actionability.
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — integration-safe QR state transitions.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — deterministic post-QR refresh handoff.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — observable refresh continuity markers.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — post-QR continuity consumption without UI regression.
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift` — continuity-aware refresh that preserves search/filter/pagination semantics.
- `tests/test_verify_m007_s07_integration_behavior_contract.py` — updated markers if wiring names changed.
