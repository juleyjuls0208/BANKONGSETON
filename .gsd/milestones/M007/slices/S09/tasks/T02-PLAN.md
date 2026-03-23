---
estimated_steps: 4
estimated_files: 6
skills_used:
  - qodo-get-rules
  - build-iphone-apps
  - swiftui
  - test
  - debug-like-expert
---

# T02: Execute Apple-host simulator/runtime checks and publish S09 runtime proof

**Slice:** S09 — macOS Runtime + Physical Device Acceptance Closure
**Milestone:** M007

## Description

Run the S09 verifier in an Apple-capable environment and capture real runtime evidence. This task converts S09 from static readiness to executed simulator/runtime proof with explicit phase-level pass/fail results.

## Steps

1. Run S09 on a macOS host with Xcode CLI tools installed; start by executing S07 baseline gates (contracts + `verify-m007-s07.sh`) via the S09 verifier preflight/baseline phases.
2. Execute Apple-tooling phases through `scripts/verify-m007-s09.sh`: tool discovery (`xcodebuild`, `xcrun`), simulator build for `BankongSetonStudent`, and `xcrun xctrace list templates` capture.
3. Persist `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` and `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` from the collected phase outcomes, ensuring each phase includes command, status, and timestamp.
4. If any phase fails, keep artifacts but ensure verifier exits non-zero with localized guidance so downstream UAT/validation steps consume a clear blocker list.

## Must-Haves

- [ ] Apple host/tooling readiness is explicitly proven (or explicitly blocked) in S09 runtime proof.
- [ ] Simulator build for `BankongSetonStudent` is executed and captured as a first-class phase result.
- [ ] Runtime proof artifacts are non-empty and schema-consistent with T01 evidence contracts.

## Verification

- `rtk proxy sh scripts/verify-m007-s09.sh`
- `rtk proxy python -c "import json; from pathlib import Path; data=json.loads(Path('.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json').read_text(encoding='utf-8')); required=['generated_at','host','overall_verdict','phases']; missing=[k for k in required if k not in data]; assert not missing, missing; phases={phase['id']: phase for phase in data['phases']}; expected=['s07_baseline','apple_tooling','simulator_build','xctrace_templates','artifact_completeness']; absent=[p for p in expected if p not in phases]; assert not absent, absent; assert all('status' in phases[p] for p in expected), 'missing phase status'"`

## Observability Impact

- Signals added/changed: concrete command-level runtime telemetry from Apple tooling and simulator build execution.
- How a future agent inspects this: read `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` first, then `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` for narrative context.
- Failure state exposed: phase-specific blocker localization (tool missing, build failure, xctrace failure, artifact-write failure) with guidance lines.

## Inputs

- `scripts/verify-m007-s09.sh` — S09 runtime orchestrator from T01.
- `scripts/verify-m007-s09-runtime.py` — proof serializer from T01.
- `tests/test_verify_m007_s09_runtime_contract.py` — runtime verifier contract guard.
- `scripts/verify-m007-s07.sh` — upstream baseline closure gate.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — simulator build target definition.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/xcshareddata/xcschemes/BankongSetonStudent.xcscheme` — scheme resolved by xcodebuild phase.

## Expected Output

- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json` — machine-readable phase verdicts and runtime command evidence.
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md` — human-readable runtime proof summary linked to phase outcomes.
- `scripts/verify-m007-s09.sh` — verifier updates (if needed) after Apple-host execution hardening.
- `scripts/verify-m007-s09-runtime.py` — serializer updates (if needed) after real runtime output validation.
