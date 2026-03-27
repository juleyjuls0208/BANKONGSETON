# S03: Home Rollback + Credit-Card Hero + QR Continuity

**Goal:** Roll back `HomeView` to a minimalist pre-M007-style surface centered on a credit-card balance hero while preserving the QR entry + post-success continuity seam and chaining S02 regression guards.
**Demo:** After this: Home shows minimalist credit-card balance hero with preserved QR entry/continuity checks passing.

## Tasks
- [x] **T01: Rolled HomeView back to a minimalist credit-card hero while preserving QR success continuity guard/tick refresh wiring.** — Deliver the Home rollback implementation for R070 without breaking R076 continuity. Keep Home surface simple and native while retaining the exact QR success callback/tick/refresh seam used by QR and Transactions continuity guards.
Failure Modes (Q5): dependencies are `HomeViewModel.load(...)` API fetch and `QRPayView` success callback path; on API errors keep explicit error banner/retry visibility, on callback duplication preserve `didConsumePresentedQRSuccess` guard and one-shot tick increment.
Load Profile (Q6): shared resources are Home load/refresh path + transaction list rendering; per operation cost is one post-success refresh plus normal initial load; 10x risk is duplicate callback churn if dedupe guard is removed.
Negative Tests (Q7): empty display name and empty transaction list rendering, API refresh failure after QR success, repeated success callback in one presentation should increment continuity tick once.
  - Estimate: 1h 30m
  - Files: mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift, mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift, mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift, tests/test_verify_m007_s07_integration_behavior_contract.py
  - Verify: rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py::test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path
- [x] **T02: Added phased S03 verifier chaining S02 guards and tightened Home rollback contract diagnostics with file-path marker context.** — Lock S03 closure to executable proof for R070/R076 and prevent rollback regressions from leaking into established S02 boundaries.
Failure Modes (Q5): dependencies are `tests/test_verify_m008_s03_ios_home_rollback_contract.py` and chained `scripts/verify-m008-s02.sh`; on downstream failure bubble phase-specific guidance and stop closure.
Load Profile (Q6): shared resources are pytest process + serial phase runner; per operation cost is one S03 suite + one continuity node check + one S02 chain run; 10x impact is runtime growth, not semantic drift, because phases are serial.
Negative Tests (Q7): preflight missing files fail with guidance, removed continuity marker fails home-qr-continuity phase, and script must fail if S02 chain fails even when S03 local tests pass.
  - Estimate: 1h 10m
  - Files: tests/test_verify_m008_s03_ios_home_rollback_contract.py, scripts/verify-m008-s03.sh, scripts/verify-m008-s02.sh, tests/test_verify_m007_s07_integration_behavior_contract.py, mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - Verify: rtk proxy python -m py_compile tests/test_verify_m008_s03_ios_home_rollback_contract.py && rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s03.sh
