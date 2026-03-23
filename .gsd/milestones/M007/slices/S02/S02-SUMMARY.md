---
id: S02
parent: M007
milestone: M007
provides:
  - QR-only Home→QR payment closure with token/URL scan compatibility, explicit non-happy-path controls, and post-success Home refresh continuity.
  - Deterministic S02 proof surfaces (contracts + verifier + UAT result artifact) for downstream integration closure.
requires:
  - S01
affects:
  - R055
  - R056
  - R057
  - R059
  - R063
key_files:
  - mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - scripts/verify-m007-s02.sh
  - .gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md
key_decisions:
  - D077: Keep QR scan ingestion compatible with full URL and bare token payloads while enforcing no-dead-control QR entry.
  - D078: Preserve post-success continuity by refreshing Home state immediately after QR completion.
  - D079: Use deterministic source-contract literal checks in verifier scripts (`rtk proxy python` substring checks) for cross-shell stability.
patterns_established:
  - Drive QR flow through explicit `QRPayState` transitions with actionable retry/cancel controls in non-happy paths.
  - Keep Home payment UX strictly QR-only; do not add payment-method chooser surfaces.
observability_surfaces:
  - scripts/verify-m007-s02.sh (`phase=behavior-contract|design-contracts|static-scope`)
  - tests/test_verify_m007_s02_qr_behavior_contract.py
  - tests/test_verify_m007_s02_qr_design_contract.py
  - tests/test_verify_m007_s02_home_qr_design_contract.py
  - .gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md
drill_down_paths:
  - .gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M007/slices/S02/tasks/T03-SUMMARY.md
  - .gsd/milestones/M007/slices/S02/tasks/T04-SUMMARY.md
duration: 4h 35m
verification_result: partial
completed_at: 2026-03-22T15:39:00+00:00
---

# S02: Home + QR Flow Redesign (QR-Only)

**Delivered the QR-only Home→QR journey with robust scan compatibility, explicit failure recovery controls, and artifact-backed pass evidence.**

## What Happened

S02 replaced the fragile QR journey with a deterministic flow that remains actionable across happy and failure paths.

- Hardened scan ingestion and state gating so QR processing accepts both full `/api/qr/<token>` URLs and bare token payloads (D077).
- Strengthened scanner permission/error behavior so denied/setup failures surface explicit user guidance instead of silent stalls.
- Preserved Home continuity after QR success via callback-driven refresh wiring (D078).
- Locked QR-only product scope and state-contract markers with deterministic source checks and verifier automation (D079).

All slice claims in this summary are reconciled against `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` and the S02 verifier/UAT artifacts.

## Verification

Evidence captured for S02:

- `rtk proxy sh scripts/verify-m007-s02.sh` → PASS (`behavior-contract`, `design-contracts`, `static-scope`).
- `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md` → `uatType: artifact-driven`, `verdict: PASS`.

Environment constraint carried in evidence: macOS simulator build proof (`xcodebuild`) is unavailable on this Windows executor; artifact-driven closure is passing while live simulator/device confirmation stays part of final milestone readiness.

## Requirements Advanced

- **R056** — removed dead-end behavior in the visible Home+QR path by enforcing actionable scan, confirm, retry, cancel, and close controls.
- **R057** — preserved a single QR payment entry path with no payment-method chooser surfaces.
- **R055/R059** — applied stitch primitives across QR states while maintaining explicit state-fidelity behavior.
- **R063** — produced executable verifier + UAT evidence surfaces reusable by downstream integration gates.

## Requirements Validated

- **R057** — validated at artifact level through S02 verifier contract phases and UAT PASS evidence.
- **R059** — validated at artifact level through explicit QR state/error-path contract checks and UAT PASS evidence.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- Host-level shell/tooling constraints required verifier execution via host-compatible shell paths in UAT evidence; no product-scope deviation from S02 plan.

## Known Limitations

- Physical-device/simulator runtime confirmation is not present in this host and remains required for final milestone device-readiness closure.

## Follow-ups

- Re-run the planned S02 `xcodebuild` and manual camera-flow checks in a macOS/iOS-capable environment during final gate execution.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — QR payload parsing, state gating, and explicit error mapping.
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` — camera permission handling and scanner setup failure propagation.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — stitch-aligned QR states and actionable retry/cancel/close controls.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — QR-only Home entry and post-success refresh continuity wiring.
- `scripts/verify-m007-s02.sh` — one-command phased S02 contract verifier.
- `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md` — authoritative artifact-driven UAT verdict.

## Forward Intelligence

### What the next slice should know
- The S02 closure contract depends on QR state markers and Home continuity wiring; preserve both when touching QR or Home flows.

### What's fragile
- Scanner permission and token parsing edges remain high-regression points; changes here can silently break demo-critical non-happy paths.

### Authoritative diagnostics
- `scripts/verify-m007-s02.sh` plus `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md` are the fastest trust surfaces for S02 behavior/design/scope regressions.

### What assumptions changed
- Assumption: QR scanner receives only full API URL payloads.
- Actual: production scans can deliver bare token payloads, so both formats must remain first-class inputs.
