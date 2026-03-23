---
id: S09
parent: M007
milestone: M007
provides:
  - Override remediation landed in iOS runtime surfaces: dark-mode default startup, PIN-free login, and transactions filter taxonomy `QR Pay` / `Card Pay` / `Load`.
  - Deterministic S09 phased verifier + runtime-proof artifacts (`S09-RUNTIME-PROOF.json/.md`) with explicit phase/guidance diagnostics.
  - Post-override acceptance evidence package (`S09-UAT-RESULT.md`, `M007-VALIDATION.md`) that truthfully records current PASS/FAIL state.
requires:
  - S07
affects:
  - R055
  - R056
  - R057
  - R058
  - R059
  - R062
  - R063
key_files:
  - scripts/verify-m007-s09.sh
  - scripts/verify-m007-s09-runtime.py
  - tests/test_verify_m007_s09_runtime_contract.py
  - tests/test_verify_m007_s09_evidence_contract.py
  - tests/test_verify_m007_s09_override_contract.py
  - mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift
  - mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift
  - mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
  - mobile/ios/BankongSetonStudent/Models/LoginModels.swift
  - mobile/ios/BankongSetonStudent/Models/TransactionModels.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md
  - .gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md
  - .gsd/milestones/M007/M007-VALIDATION.md
key_decisions:
  - D088: S09 closure evidence uses phased verifier telemetry plus machine/human runtime proof artifacts.
  - D090: iOS login remains student-ID-only (no PIN) to match backend auth contract.
  - D091: When Apple runtime/device execution is unavailable, publish explicit FAIL evidence instead of fabricated PASS claims.
patterns_established:
  - Use `run_phase` + `fail_with_guidance` to localize runtime failures (`phase=...`, `guidance=...`) for fast remediation.
  - Keep override regressions locked by marker contracts (`dark_mode_default`, `login_pin_present`, `legacy_filter_label`, `tx_filter_taxonomy`).
  - Clear stale runtime-proof artifacts before rerunning phased verifier so evidence reflects one execution window.
observability_surfaces:
  - `scripts/verify-m007-s09.sh`
  - `scripts/verify-m007-s09-runtime.py`
  - `tests/test_verify_m007_s09_override_contract.py`
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`
  - `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`
drill_down_paths:
  - .gsd/milestones/M007/slices/S09/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S09/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S09/tasks/T03-SUMMARY.md
duration: 2h 57m
verification_result: partial
completed_at: 2026-03-23T17:44:00+08:00
---

# S09: macOS Runtime + Physical Device Acceptance Closure

S09 completed override remediation and closure instrumentation, then produced truthful post-override evidence showing what passed and what is still externally blocked.

## What This Slice Actually Delivered

### 1) Override remediation is implemented and contract-locked

- **Dark-mode default startup** enforced at app bootstrap (`.preferredColorScheme(.dark)`).
- **PIN removed from iOS login** across UI + state + request payload:
  - no PIN field in `LoginView.swift`
  - no PIN state/validation in `LoginViewModel.swift`
  - `APIClient.login(studentId:)` and `LoginRequest(studentId:)` only.
- **Transactions taxonomy replaced** with `QR Pay` / `Card Pay` / `Load`:
  - view labels updated in `TransactionsView.swift`
  - model mapping normalized in `TransactionModels.swift`
  - legacy `Debit` / `Credit Card` markers treated as regressions.

### 2) Runtime verifier/evidence surfaces are operational

- S09 phased verifier exists and runs with actionable telemetry:
  - phases: `s07_baseline`, `apple_tooling`, `simulator_build`, `xctrace_templates`, `artifact_completeness`.
- Runtime-proof serializer writes:
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`.
- Contract tests enforce shape, phase coverage, and UAT marker completeness.

### 3) Post-override closure evidence is published

- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` includes explicit override checkpoint verdicts and S07-01..S07-11 rows.
- `.gsd/milestones/M007/M007-VALIDATION.md` now references S09 post-override artifacts and states current verdict.
- Evidence is intentionally **non-fabricated**: runtime/UAT remain FAIL until Apple host + physical iOS 17+ execution is performed.

## Verification (Slice-Plan Checks)

| # | Command | Exit | Result | Notes |
|---|---|---:|---|---|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py tests/test_verify_m007_s09_override_contract.py` | 0 | ✅ PASS | 12 tests passed |
| 2 | `rtk proxy sh scripts/verify-m007-s09.sh` | 1 | ❌ FAIL | blocked at `phase=apple_tooling` (`xcodebuild`/`xcrun` not found on this host) |
| 3 | `rtk proxy python -c "... PIN not in LoginView + required filters in TransactionsView ..."` | 0 | ✅ PASS | override source checks pass |
| 4 | `rtk proxy python -c "... '.dark' marker in BankongSetonStudentApp.swift ..."` | 0 | ✅ PASS | dark startup marker present |
| 5 | `rtk proxy python -c "... required markers in S09-UAT-RESULT.md ..."` | 0 | ✅ PASS | UAT evidence markers complete |

## Requirement Impact

- **R055 / R058:** override remediation is implemented and contract-verified at source level.
- **R056 / R057 / R059 / R062:** no regression surfaced by S09 contracts; prior slice behavior remains in place.
- **R063:** still open for full validation because Apple runtime and physical-device sign-off were not executable in this Windows executor.

## Observability / Diagnostics Status

Confirmed operational:
- `scripts/verify-m007-s09.sh` emits localized `phase=` and `guidance=` diagnostics.
- Runtime proof artifacts update with phase-level records and verdict computation.
- Override contracts localize failures to explicit regression tags (`dark_mode_default`, `login_pin_present`, `legacy_filter_label`, `tx_filter_taxonomy`).

## Blockers and What Next

Current hard blocker:
- No Apple toolchain in this environment (`xcodebuild`, `xcrun` unavailable), therefore runtime phases beyond `s07_baseline` cannot be completed here.

Next operator actions (Apple-capable runner):
1. Run `rtk proxy sh scripts/verify-m007-s09.sh` until all required phases pass.
2. Execute physical iOS 17+ UAT (`S07-01`..`S07-11`) with explicit override checks.
3. Update `S09-UAT-RESULT.md` verdict/sign-off and refresh `M007-VALIDATION.md` to final closure verdict.

## Forward Guidance for Reassess-Roadmap

- S09 delivered all code-level override fixes and closure instrumentation.
- Remaining risk is **environmental execution**, not missing implementation.
- Milestone closure decision should hinge on whether an Apple-host/device acceptance run can be scheduled immediately; no additional feature development is required before that run.