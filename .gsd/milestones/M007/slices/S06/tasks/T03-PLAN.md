---
estimated_steps: 5
estimated_files: 4
skills_used:
  - qodo-get-rules
  - test
  - review
  - best-practices
  - debug-like-expert
---

# T03: Add S06 contract tests, phased verifier, and iOS 17+ UAT/perf checklist

**Slice:** S06 — Motion and Performance Tuning (iOS 17+)
**Milestone:** M007

## Description

Create deterministic closure artifacts for S06 so motion/performance quality is validated mechanically before subjective demo review. This task adds behavior/design contracts, a one-command verifier with phase diagnostics, and a manual UAT/profiling checklist for iOS 17+ runtime validation.

## Steps

1. Create `test_verify_m007_s06_motion_behavior_contract.py` to assert centralized motion policy presence, Reduce Motion usage in shared primitives, and preserved in-scope control actionability markers.
2. Create `test_verify_m007_s06_motion_design_contract.py` to assert tuned motion markers in QR/Transactions/Budget/LostCard/Home surfaces and restrained-motion constraints (no decorative infinite loops in core paths).
3. Implement `scripts/verify-m007-s06.sh` with fail-fast phases: `preflight`, `behavior-contract`, `design-contract`, `static-contract`.
4. Write `.gsd/milestones/M007/slices/S06/S06-UAT.md` with default-motion and Reduce Motion manual checks plus iOS 17+ profiling steps (`xctrace` Animation Hitches) and shell fallback notes.
5. Execute the contract tests and verifier commands (`sh` and canonical `bash`) and ensure missing markers/forbidden markers fail with clear phase guidance.

## Must-Haves

- [ ] Two S06 pytest contract files exist and assert both behavior and design constraints for motion tuning.
- [ ] `scripts/verify-m007-s06.sh` enforces all four phases with deterministic required/forbidden marker checks.
- [ ] `S06-UAT.md` contains explicit iOS 17+ default-motion path, Reduce Motion path, and profiling checklist steps.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py`
- `rtk proxy sh scripts/verify-m007-s06.sh`
- `rtk proxy bash scripts/verify-m007-s06.sh`
- `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"`

## Observability Impact

- Signals added/changed: verifier phase telemetry and contract assertion messages provide deterministic localization of motion/perf regressions.
- How a future agent inspects this: run `scripts/verify-m007-s06.sh`, inspect failing phase output, then use the two pytest files to pinpoint missing/forbidden markers.
- Failure state exposed: missing motion-policy/reduce-motion wiring or over-animated/decorative loops surface as explicit phase/test failures instead of subjective UI feedback.

## Inputs

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — motion policy contract surface to validate.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — shared primitive motion behavior to validate.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — shared shell transition behavior to validate.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — QR state transition contract target.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — transactions state transition contract target.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — budget transition contract target.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — lost-card transition contract target.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — home interaction continuity contract target.
- `tests/test_verify_m007_s05_settings_behavior_contract.py` — prior-slice behavior contract style baseline.
- `tests/test_verify_m007_s05_settings_design_contract.py` — prior-slice design contract style baseline.
- `scripts/verify-m007-s05.sh` — prior-slice phased verifier baseline.
- `.gsd/milestones/M007/slices/S06/S06-RESEARCH.md` — S06 risk/constraint baseline for checklist completeness.

## Expected Output

- `tests/test_verify_m007_s06_motion_behavior_contract.py` — S06 behavior contract assertions for motion/reduce-motion/actionability.
- `tests/test_verify_m007_s06_motion_design_contract.py` — S06 design contract assertions for state-screen tuning/restraint.
- `scripts/verify-m007-s06.sh` — one-command phased verifier for S06.
- `.gsd/milestones/M007/slices/S06/S06-UAT.md` — manual iOS 17+ motion/perf acceptance checklist.
