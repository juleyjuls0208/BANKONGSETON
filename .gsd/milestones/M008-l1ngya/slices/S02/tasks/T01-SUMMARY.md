---
id: T01
parent: S02
milestone: M008-l1ngya
provides: []
requires: []
affects: []
key_files: ["mobile/ios/BankongSetonStudent/Views/MainTabView.swift", "tests/test_verify_m008_s02_ios_rollback_contract.py", "scripts/verify-m008-s02.sh", ".gsd/milestones/M008-l1ngya/slices/S02/tasks/T01-SUMMARY.md"]
key_decisions: ["Kept `MainTab` enum metadata and session-expired alert flow unchanged while only replacing root shell composition with native `TabView`.", "Used phased verifier logs to isolate rollback-shell drift from budget, QR, and login regressions in one command."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Task-level commands passed: `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py -k "main_tab_view"` and `rtk proxy python -m py_compile tests/test_verify_m008_s02_ios_rollback_contract.py`. Slice-level checks also passed: `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only`, and the phased verifier via `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`."
completed_at: 2026-03-27T10:03:24.927Z
blocker_discovered: false
---

# T01: Replaced the iOS floating tab shell with native TabView and added S02 rollback-contract + phased verifier harness.

> Replaced the iOS floating tab shell with native TabView and added S02 rollback-contract + phased verifier harness.

## What Happened
---
id: T01
parent: S02
milestone: M008-l1ngya
key_files:
  - mobile/ios/BankongSetonStudent/Views/MainTabView.swift
  - tests/test_verify_m008_s02_ios_rollback_contract.py
  - scripts/verify-m008-s02.sh
  - .gsd/milestones/M008-l1ngya/slices/S02/tasks/T01-SUMMARY.md
key_decisions:
  - Kept `MainTab` enum metadata and session-expired alert flow unchanged while only replacing root shell composition with native `TabView`.
  - Used phased verifier logs to isolate rollback-shell drift from budget, QR, and login regressions in one command.
duration: ""
verification_result: mixed
completed_at: 2026-03-27T10:03:24.929Z
blocker_discovered: false
---

# T01: Replaced the iOS floating tab shell with native TabView and added S02 rollback-contract + phased verifier harness.

**Replaced the iOS floating tab shell with native TabView and added S02 rollback-contract + phased verifier harness.**

## What Happened

Migrated `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` from `StitchTabShell`/`StitchTabItem` composition to native `TabView(selection:)` with four tab items (Home, History, Budget, Settings) while preserving existing session-expired alert wiring (`showSessionExpiredAlert`, `Sign In`, `authManager.clearAll()`). Added `tests/test_verify_m008_s02_ios_rollback_contract.py` containing `main_tab_view`-scoped source-contract assertions that enforce native tab markers, detect any reintroduced stitch-shell markers, and keep session-expired alert behavior explicit. Added `scripts/verify-m008-s02.sh` with required phased execution (`preflight`, `s02-rollback-contract`, `budget-regression`, `qr-regression`, `login-regression`) and actionable `guidance=` output for regression triage.

## Verification

Task-level commands passed: `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py -k "main_tab_view"` and `rtk proxy python -m py_compile tests/test_verify_m008_s02_ios_rollback_contract.py`. Slice-level checks also passed: `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only`, and the phased verifier via `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py -k "main_tab_view"` | 0 | ✅ pass | 500ms |
| 2 | `rtk proxy python -m py_compile tests/test_verify_m008_s02_ios_rollback_contract.py` | 0 | ✅ pass | 80ms |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py` | 0 | ✅ pass | 500ms |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | 490ms |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py` | 0 | ✅ pass | 510ms |
| 6 | `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only` | 0 | ✅ pass | 500ms |
| 7 | `rtk proxy bash scripts/verify-m008-s02.sh` | 1 | ❌ fail | 60ms |
| 8 | `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh` | 0 | ✅ pass | 4200ms |


## Deviations

`rtk proxy bash scripts/verify-m008-s02.sh` failed on this Windows host due `/bin/bash` unavailable; used `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh` to run the same verifier script successfully.

## Known Issues

Swift LSP diagnostics are unavailable in this environment (`No language server found`), so validation remains source-contract and verifier-test based for this task.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `scripts/verify-m008-s02.sh`
- `.gsd/milestones/M008-l1ngya/slices/S02/tasks/T01-SUMMARY.md`


## Deviations
`rtk proxy bash scripts/verify-m008-s02.sh` failed on this Windows host due `/bin/bash` unavailable; used `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh` to run the same verifier script successfully.

## Known Issues
Swift LSP diagnostics are unavailable in this environment (`No language server found`), so validation remains source-contract and verifier-test based for this task.
