---
estimated_steps: 5
estimated_files: 5
skills_used:
  - qodo-get-rules
  - swiftui
  - build-iphone-apps
  - test
---

# T02: Roll back Home/Transactions/Settings to baseline seams while preserving QR and budget continuity

**Slice:** S02 — Full UX Rollback Baseline + Native Tab Bar
**Milestone:** M008-l1ngya

## Description

Complete the R068 structural rollback using commit `558d8bc` as interaction reference for Home/Transactions/Settings, while preserving contract-critical QR continuity and confirming no S01 budget or M007 login regressions.

## Steps

1. Refactor `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` to baseline-style native layout scaffolding (simpler hierarchy, reduced decorative shell) while keeping QR entry flow, `qr_payment_success_continuity_tick`, and post-success refresh wiring.
2. Refactor `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` to baseline list/overlay interaction seams, explicitly remove `.searchable(...)`, and preserve continuity tick refresh behavior.
3. Refactor `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` to baseline-oriented form sections (Appearance + Account actions) while keeping logout + lost-card wiring compatible with `SettingsViewModel.logout` callback API.
4. Expand `tests/test_verify_m008_s02_ios_rollback_contract.py` to assert Home/Transactions/Settings rollback markers, no-search contract, and QR continuity markers.
5. Finalize and run `scripts/verify-m008-s02.sh` until S02 rollback checks and all regression phases pass.

## Must-Haves

- [ ] Home/Transactions/Settings are structurally aligned with pre-M007 baseline interaction seams.
- [ ] Transactions has no `.searchable(...)` declaration after rollback.
- [ ] QR continuity markers remain present and asserted (`qr_payment_success_continuity_tick`, refresh hooks).
- [ ] `tests/test_verify_m008_s01_ios_budget_contract.py` and M007 QR/login guard tests still pass.
- [ ] `scripts/verify-m008-s02.sh` provides single-command slice closure proof.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py`
- `rtk proxy bash scripts/verify-m008-s02.sh`

## Observability Impact

- Signals added/changed: verifier phases now include per-surface rollback assertions and regression boundaries.
- How a future agent inspects this: run `rtk proxy bash scripts/verify-m008-s02.sh` and inspect failing phase guidance.
- Failure state exposed: baseline-surface drift vs QR/budget/login regressions are separated by phase.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — current Home surface to roll back structurally.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — current Transactions surface with search bar to remove.
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — current Settings surface to simplify to baseline form seams.
- `tests/test_verify_m008_s02_ios_rollback_contract.py` — T01 contract harness to expand.
- `scripts/verify-m008-s02.sh` — T01 verifier scaffold to finalize.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — baseline-oriented Home structure with QR continuity preserved.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — baseline-oriented Transactions structure with no search bar.
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` — baseline-oriented Settings form structure.
- `tests/test_verify_m008_s02_ios_rollback_contract.py` — completed rollback contract assertions for all S02-owned surfaces.
- `scripts/verify-m008-s02.sh` — finalized slice verifier including regression phases.
