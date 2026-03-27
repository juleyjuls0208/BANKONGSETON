---
id: T01
parent: S03
milestone: M008-l1ngya
provides: []
requires: []
affects: []
key_files: ["mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift", "tests/test_verify_m008_s03_ios_home_rollback_contract.py", ".gsd/milestones/M008-l1ngya/slices/S03/tasks/T01-SUMMARY.md"]
key_decisions: ["Preserved Home QR continuity seam exactly while simplifying only Home layout composition.", "Added explicit in-card Retry control in Home error state to keep failure recovery visible and local to the screen."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Passed S03 Home contract tests and the targeted M007 S07 continuity-node regression. Verified seam markers and observability log markers remain present in Home/HomeViewModel. Slice-level verifier command `scripts/verify-m008-s03.sh` currently fails with missing file (expected until T02 adds the verifier script)."
completed_at: 2026-03-27T11:36:30.033Z
blocker_discovered: false
---

# T01: Rolled HomeView back to a minimalist credit-card hero while preserving QR success continuity guard/tick refresh wiring.

> Rolled HomeView back to a minimalist credit-card hero while preserving QR success continuity guard/tick refresh wiring.

## What Happened
---
id: T01
parent: S03
milestone: M008-l1ngya
key_files:
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - tests/test_verify_m008_s03_ios_home_rollback_contract.py
  - .gsd/milestones/M008-l1ngya/slices/S03/tasks/T01-SUMMARY.md
key_decisions:
  - Preserved Home QR continuity seam exactly while simplifying only Home layout composition.
  - Added explicit in-card Retry control in Home error state to keep failure recovery visible and local to the screen.
duration: ""
verification_result: mixed
completed_at: 2026-03-27T11:36:30.034Z
blocker_discovered: false
---

# T01: Rolled HomeView back to a minimalist credit-card hero while preserving QR success continuity guard/tick refresh wiring.

**Rolled HomeView back to a minimalist credit-card hero while preserving QR success continuity guard/tick refresh wiring.**

## What Happened

Activated required skills, confirmed no Qodo config was available in this runner, and implemented a contract-first rollback. Added `tests/test_verify_m008_s03_ios_home_rollback_contract.py` to lock the intended Home rollback shape and seam requirements, then refactored `HomeView.swift` to a simpler credit-card hero composition with lightweight QR entry + recent transactions. Preserved `.sheet(isPresented: $showQrPay)` flow and continuity seam (`didConsumePresentedQRSuccess`, `qr_payment_success_continuity_tick`, one-shot guard log, tick increment, and `refreshAfterQRSuccess(...)`). Added explicit error-surface retry action while keeping pull-to-refresh path.

## Verification

Passed S03 Home contract tests and the targeted M007 S07 continuity-node regression. Verified seam markers and observability log markers remain present in Home/HomeViewModel. Slice-level verifier command `scripts/verify-m008-s03.sh` currently fails with missing file (expected until T02 adds the verifier script).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile tests/test_verify_m008_s03_ios_home_rollback_contract.py` | 0 | ✅ pass | 110ms |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m008_s03_ios_home_rollback_contract.py` | 0 | ✅ pass | 530ms |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py::test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path` | 0 | ✅ pass | 510ms |
| 4 | `rtk grep "qr_payment_success_continuity_tick\|didConsumePresentedQRSuccess\|handleQRPaySuccessCompletion" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` | 0 | ✅ pass | 90ms |
| 5 | `rtk grep "Ignoring duplicate QR success callback\|QR success continuity tick advanced\|Refreshing Home data after QR payment success dismiss\|Completed Home refresh after QR payment success dismiss" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` | 0 | ✅ pass | 80ms |
| 6 | `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s03.sh` | 127 | ❌ fail | 70ms |


## Deviations

Created initial S03 contract test file in T01 (planned in T02) to satisfy first-task test-first and negative-path coverage requirements.

## Known Issues

`scripts/verify-m008-s03.sh` is not present yet, so full slice one-command verification remains incomplete until T02. Swift LSP diagnostics are unavailable in this environment.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `.gsd/milestones/M008-l1ngya/slices/S03/tasks/T01-SUMMARY.md`


## Deviations
Created initial S03 contract test file in T01 (planned in T02) to satisfy first-task test-first and negative-path coverage requirements.

## Known Issues
`scripts/verify-m008-s03.sh` is not present yet, so full slice one-command verification remains incomplete until T02. Swift LSP diagnostics are unavailable in this environment.
