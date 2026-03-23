---
id: S06
parent: M007
milestone: M007
provides:
  - Centralized motion policy seam (`AppTheme.Motion`) consumed across shared primitives and high-impact stateful screens.
  - Reduce Motion-aware transitions for QR, Transactions, Budget, Lost-Card, and Home flows without loss of in-scope actionability.
  - Deterministic S06 proof surfaces (contracts + phased verifier + UAT-result artifact) for motion-quality closure.
requires:
  - S01
  - S02
  - S03
  - S04
  - S05
affects:
  - R055
  - R056
  - R059
  - R062
  - R063
key_files:
  - mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift
  - mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift
  - mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift
  - mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - scripts/verify-m007-s06.sh
  - .gsd/milestones/M007/slices/S06/S06-UAT.md
  - .gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md
key_decisions:
  - D084: Motion behavior is governed by a shared primitive policy seam with explicit Reduce Motion override and tokenized intent durations/curves.
patterns_established:
  - Drive motion from shared policy intents (`primaryButtonPress`, `tabSelection`, `cardSurface`) instead of per-view ad hoc animation literals.
  - Keep reduced-motion behavior explicit and state-key driven (opacity/low-displacement fallbacks) while preserving actionability markers.
observability_surfaces:
  - scripts/verify-m007-s06.sh (`phase=preflight|behavior-contract|design-contract|static-contract`)
  - tests/test_verify_m007_s06_motion_behavior_contract.py
  - tests/test_verify_m007_s06_motion_design_contract.py
  - .gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md
drill_down_paths:
  - .gsd/milestones/M007/slices/S06/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S06/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S06/tasks/T03-SUMMARY.md
duration: 3h 44m
verification_result: partial
completed_at: 2026-03-23T10:20:00+08:00
---

# S06: Motion and Performance Tuning (iOS 17+)

**Delivered a shared, accessibility-aware motion policy with restrained transitions across demo-critical stateful flows and deterministic closure evidence.**

## What Happened

S06 replaced scattered transition behavior with one inspectable motion seam and then applied it to shared primitives plus high-impact state screens.

- Added `AppTheme.Motion` policy tokens and helper APIs for primitive intents and Reduce Motion-aware fallback behavior.
- Wired shared primitives (`StitchPrimaryButtonStyle`, `StitchTabShell`, `StitchCard`) to consume motion policy via explicit `accessibilityReduceMotion` branches.
- Tuned QR/Transactions/Budget/Lost-Card/Home state transitions with keyed, restrained policy-driven animation paths and reduced-motion fallbacks.
- Expanded motion behavior/design contract tests and added fail-fast S06 verifier + UAT artifacts to make closure deterministic and diagnosable.

All claims in this summary are reconciled against `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` plus S06 verifier/UAT artifacts.

## Verification

Evidence captured for S06:

- `rtk proxy sh scripts/verify-m007-s06.sh` → PASS (`preflight`, `behavior-contract`, `design-contract`, `static-contract`).
- `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md` → `uatType: artifact-driven`, `verdict: PASS`.

Environment constraints retained in evidence:
- `rtk proxy bash scripts/verify-m007-s06.sh` is not usable on this Windows host (`/bin/bash` unavailable).
- `xcodebuild` and `xcrun` are unavailable on this host; simulator/profile captures remain deferred to milestone-final Apple-capable runtime gate.

## Requirements Advanced

- **R062** — centralized and applied restrained motion policy with explicit accessibility reduce-motion handling across shared primitives and key stateful flows.
- **R059** — ensured stateful screens use explicit transition channels instead of abrupt cuts or uncontrolled loops.
- **R055/R056** — kept stitch consistency and actionability intact while adding motion tuning; no in-scope control became hidden/dead.
- **R063** — delivered deterministic contract/verifier/UAT evidence surfaces for auditable motion-quality closure.

## Requirements Validated

- **R062** — validated at artifact level via motion behavior/design contracts, phased verifier PASS, and S06 UAT-result PASS evidence.
- **R059** — validated at artifact level via explicit state-transition marker checks and reduced-motion fallback checks in verifier/contracts.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- No product-scope deviation from S06 plan; host-compatible fallback execution paths were used for artifact closure.

## Known Limitations

- Apple-only profiling/runtime evidence (`xcodebuild`, `xcrun xctrace`) is unavailable in this environment and remains required in final milestone device-readiness validation.

## Follow-ups

- Execute S06 simulator/device motion validation and Animation Hitches capture in a macOS/iOS-capable environment during final milestone closure.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — shared motion token/policy APIs and Reduce Motion-aware animation helper seam.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — policy-driven primary-button press feedback with Reduce Motion handling.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — policy-driven tab-selection transitions with Reduce Motion handling.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — policy-driven card-surface transition support.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — keyed state transitions for QR flow with reduced-motion fallback.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — keyed state/pagination transitions with reduced-motion fallback.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — policy-driven load/save state transition handling.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — phase-key transitions and reduced-motion secondary action behavior.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — policy-driven transitions for error/recent-transaction state surfaces.
- `tests/test_verify_m007_s06_motion_behavior_contract.py` — behavior contract guardrails for policy, Reduce Motion, and actionability continuity.
- `tests/test_verify_m007_s06_motion_design_contract.py` — design contract guardrails for transition markers and no-infinite-loop restraint.
- `scripts/verify-m007-s06.sh` — one-command phased S06 verifier.
- `.gsd/milestones/M007/slices/S06/S06-UAT.md` — manual motion/perf checklist.
- `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md` — authoritative artifact-driven UAT verdict.

## Forward Intelligence

### What the next slice should know
- Motion behavior now depends on `AppTheme.Motion` intent tokens and per-screen transition keys; edits should extend this seam instead of introducing local animation constants.

### What's fragile
- Reduced-motion branches and no-loop constraints are easy to regress during UI polish passes; ad hoc animation additions can silently violate S06 closure guarantees.

### Authoritative diagnostics
- `scripts/verify-m007-s06.sh` plus `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md` are the canonical trust surfaces for S06 motion-policy and state-transition closure.

### What assumptions changed
- Assumption: motion quality could be tuned per-screen without a shared policy seam.
- Actual: centralized policy + reduced-motion contracts are required to keep quality and accessibility behavior consistent and regression-detectable across screens.