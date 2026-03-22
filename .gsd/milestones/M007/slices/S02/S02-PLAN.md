# S02: Home + QR Flow Redesign (QR-Only)

**Goal:** Deliver stitch-faithful Home + QR payment surfaces where QR scan/confirm/error handling is robust in real demo conditions and QR remains the only exposed payment UX.
**Demo:** From redesigned Home, user taps **Pay with QR**, scans either a full `/api/qr/<token>` URL or bare token payload, sees loading/confirm/success/error states with actionable controls, completes payment, and returns to refreshed Home balance with no payment-method chooser surfaces.

## Must-Haves

- Directly satisfy **R056** by removing dead-end behavior in the visible Home + QR journey (scan ingestion, permission denied path, retry/cancel actions, and success return path all remain actionable).
- Directly satisfy **R057** by keeping QR as the only payment UX and ensuring no payment-method selector rows/labels/buttons appear in Home or QR flow states.
- Support **R055** by applying S01 `AppTheme` + `Stitch*` primitives across Home and all QR states for stitch-cohesive visual language.
- Support **R059** by preserving full QR state fidelity (`scanning`, `loading`, `confirming`, `success`, `error`) with explicit error/permission guidance.
- Support **R063** by producing executable slice verification + manual device checklist that future slices can reuse for on-device readiness evidence.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py tests/test_verify_m007_s02_home_qr_design_contract.py`
- `rtk proxy bash scripts/verify-m007-s02.sh`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy bash -lc "rtk grep -n \"permission denied|Camera access|scanner|expired QR|Retry|Cancel\" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift"` (inspectable failure-path messaging/state surface check)
- Manual device/UAT checklist in `.gsd/milestones/M007/slices/S02/S02-UAT.md` passes: Home QR CTA → scan valid token-only payload → confirm → success dismiss refresh; invalid/expired payload path; camera-denied path.

## Observability / Diagnostics

- Runtime signals: explicit `QRPayState` transitions, scanner-permission failure state messaging, and deterministic retry/cancel controls in non-happy paths.
- Inspection surfaces: source-contract pytest files for parsing/state/QR-only invariants, `scripts/verify-m007-s02.sh` for one-command closure checks, and UI-visible state messages for runtime diagnosis.
- Failure visibility: tests fail with missing symbol/state/QR-only assertions; runtime errors surface user-facing cause text (expired QR, unauthorized, insufficient balance, permission denied) rather than silent scanner stalls.
- Redaction constraints: verification artifacts must not include student PIN/JWT or raw credential values; only structural and state-message assertions.

## Integration Closure

- Upstream surfaces consumed: S01 design primitives in `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` and `mobile/ios/BankongSetonStudent/UI/Components/{StitchCard.swift,StitchPrimaryButtonStyle.swift}`; existing QR API contract in `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`.
- New wiring introduced in this slice: dual-format QR payload ingestion (URL + bare token), scanner permission/error propagation into QR state machine, stitch restyle across QR states, and Home→QR→Home refresh continuity hardening.
- What remains before the milestone is truly usable end-to-end: S03/S04/S05 must finish redesigned transactions/budget/receipt/settings scope, then S06 tunes motion and S07 performs final integrated on-device acceptance.

## Tasks

- [x] **T01: Harden QR scan ingestion and permission/error behavior contract** `est:1h 25m`
  - Why: R056 risk is currently highest in scan ingestion (URL-only parsing) and permission failure paths that can make the QR CTA appear dead during demo.
  - Files: `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift`, `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`, `tests/test_verify_m007_s02_qr_behavior_contract.py`
  - Do: Update QR payload extraction to accept both full QR URLs and bare token payloads, ignore duplicate scans when not in `.scanning`, propagate scanner permission/setup failures as actionable state transitions, and add pytest assertions for parser, scan-gating, and state-contract coverage.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Token-only scans can progress into loading/confirming, scanner-denied setup produces explicit actionable state (not silent fail), and behavior-contract tests pass.
- [ ] **T02: Restyle all QR states with stitch primitives while preserving QR-only actions** `est:1h 20m`
  - Why: R055/R059 require full-state stitch fidelity, and R057 requires explicit absence of payment-method UI in QR flow surfaces.
  - Files: `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`, `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `tests/test_verify_m007_s02_qr_design_contract.py`
  - Do: Refactor `scanning/loading/confirming/success/error` layouts to use `AppTheme`, `StitchCard`, and `StitchPrimaryButtonStyle`, ensure every visible state has meaningful primary/secondary action, preserve existing API-driven confirm behavior, and add assertions that QR state coverage and QR-only copy/controls remain intact.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: QR flow visually aligns with stitch primitives across all states, no payment-method chooser text/actions are present, and state-design tests pass.
- [ ] **T03: Redesign Home QR entry surface and preserve post-payment refresh continuity** `est:1h 05m`
  - Why: S02 demo starts on Home, so QR CTA prominence, accessibility, and callback wiring must stay reliable to satisfy R056 and support R055.
  - Files: `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`, `tests/test_verify_m007_s02_home_qr_design_contract.py`
  - Do: Polish Home QR entry hierarchy with stitch tokens/components, keep `home-qr-pay-button` stable and discoverable, preserve `QRPayView(onSuccess:)` refresh callback behavior for balance/recent transactions reload, and add assertions for QR-only Home entry contract.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s02_home_qr_design_contract.py && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: Home clearly exposes a single QR payment path, post-success dismissal still triggers Home refresh load, and Home contract tests pass.
- [ ] **T04: Add slice closure harness and device-ready QR manual checklist** `est:55m`
  - Why: S02 must leave executable proof for future slices (S06/S07) and manual camera/device validation that cannot be fully automated in CI.
  - Files: `scripts/verify-m007-s02.sh`, `.gsd/milestones/M007/slices/S02/S02-UAT.md`, `tests/test_verify_m007_s02_qr_behavior_contract.py`, `tests/test_verify_m007_s02_qr_design_contract.py`, `tests/test_verify_m007_s02_home_qr_design_contract.py`, `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
  - Do: Create one-command verifier that runs S02 pytest files plus static QR-only/state coverage checks and camera usage key presence, write a concise physical-device checklist for valid/invalid/permission-denied flows, and ensure verification references the existing iOS scheme/project paths.
  - Verify: `rtk proxy bash scripts/verify-m007-s02.sh && rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
  - Done when: S02 has reproducible automated verification and a manual pass/fail checklist that covers all QR non-happy paths required for demo readiness.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `tests/test_verify_m007_s02_qr_behavior_contract.py`
- `tests/test_verify_m007_s02_qr_design_contract.py`
- `tests/test_verify_m007_s02_home_qr_design_contract.py`
- `scripts/verify-m007-s02.sh`
- `.gsd/milestones/M007/slices/S02/S02-UAT.md`
