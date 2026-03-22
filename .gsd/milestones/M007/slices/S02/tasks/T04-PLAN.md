---
estimated_steps: 4
estimated_files: 5
skills_used:
  - test
  - lint
  - qodo-get-rules
  - requesting-code-review
  - review
---

# T04: Add slice closure harness and device-ready QR manual checklist

**Slice:** S02 — Home + QR Flow Redesign (QR-Only)
**Milestone:** M007

## Description

Package S02 proof into repeatable automation + manual checklist artifacts so later slices can verify Home/QR behavior quickly and diagnose regressions without rediscovering expected state contracts.

## Steps

1. Create `scripts/verify-m007-s02.sh` that runs S02 pytest suites and static assertions for QR-only UI strings, required QR state cases, and camera usage plist key.
2. Ensure the verifier is deterministic and fails fast with actionable exit messages when any contract check is missing.
3. Write `.gsd/milestones/M007/slices/S02/S02-UAT.md` with concise on-device pass/fail checklist for valid scan, invalid/expired token, insufficient balance, and camera-denied scenarios.
4. Run the verifier and fix invocation paths so future agents can execute one command before simulator/device checks.

## Must-Haves

- [ ] One-command verifier exists for S02 contract checks and fails on regressions.
- [ ] Verifier explicitly enforces QR-only invariant and full QR state coverage markers.
- [ ] Manual checklist captures camera permission and non-happy-path demo behavior, not just happy path.
- [ ] Artifacts are placed in stable paths referenced by slice-level verification.

## Verification

- `rtk proxy bash scripts/verify-m007-s02.sh`
- `rtk proxy test -s .gsd/milestones/M007/slices/S02/S02-UAT.md`

## Inputs

- `tests/test_verify_m007_s02_qr_behavior_contract.py` — scan ingestion and failure-path assertions from T01.
- `tests/test_verify_m007_s02_qr_design_contract.py` — QR state design/QR-only assertions from T02.
- `tests/test_verify_m007_s02_home_qr_design_contract.py` — Home QR entry assertions from T03.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — state-case markers to enforce in verifier checks.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — Home QR CTA identifier and QR-only copy checks.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — camera usage key presence check target.

## Expected Output

- `scripts/verify-m007-s02.sh` — deterministic slice verifier for automated closure checks.
- `.gsd/milestones/M007/slices/S02/S02-UAT.md` — manual iOS device pass/fail checklist for S02 QR flows.
- `tests/test_verify_m007_s02_qr_behavior_contract.py` — finalized assertions callable from verifier.
- `tests/test_verify_m007_s02_qr_design_contract.py` — finalized assertions callable from verifier.
- `tests/test_verify_m007_s02_home_qr_design_contract.py` — finalized assertions callable from verifier.

## Observability Impact

- Signals added/changed: unified S02 verification output identifying which contract class failed (behavior, design, Home wiring, or static scope guard).
- How a future agent inspects this: run `scripts/verify-m007-s02.sh` and follow failing subsection output; use `S02-UAT.md` for physical device diagnostics.
- Failure state exposed: broken QR-only invariant, missing state branch, or camera-key regressions surface as explicit failing check groups rather than ambiguous manual notes.
