---
estimated_steps: 5
estimated_files: 4
skills_used:
  - swiftui
  - frontend-design
  - make-interfaces-feel-better
  - accessibility
  - best-practices
  - feature-dev
---

# T02: Restyle all QR states with stitch primitives while preserving QR-only actions

**Slice:** S02 — Home + QR Flow Redesign (QR-Only)
**Milestone:** M007

## Description

Apply stitch-faithful visual language to every QR state (`scanning`, `loading`, `confirming`, `success`, `error`) while ensuring every visible action remains meaningful and payment-method UI does not reappear.

## Steps

1. Map each QR state to target stitch structure using existing `AppTheme`, `StitchCard`, and `StitchPrimaryButtonStyle` primitives.
2. Refactor `QRPayView` layouts for scanning guidance, loading feedback, cart confirmation details, success acknowledgement, and error recovery actions with consistent spacing/typography.
3. Keep CTA semantics actionable per state (confirm/retry/cancel/done) and preserve existing API-driven confirm flow from `QRPayViewModel`.
4. Ensure QR-only invariant by removing/avoiding any payment-method chooser labels/actions in QR surfaces.
5. Add `tests/test_verify_m007_s02_qr_design_contract.py` to assert state-case coverage, stitch primitive usage, and absence of payment-method UI strings.

## Must-Haves

- [ ] All five QR states render with stitch token/component usage instead of default ad hoc styling.
- [ ] Every state exposes meaningful user action(s); no visible CTA is decorative or dead.
- [ ] QR confirm UI remains QR-only with no payment-method selector copy/actions.
- [ ] Source-contract tests enforce state coverage and QR-only visual constraints.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: state-specific guidance/error copy and deterministic state-to-action mapping visible in QR UI.
- How a future agent inspects this: run `tests/test_verify_m007_s02_qr_design_contract.py` and inspect per-state SwiftUI switch branches in `QRPayView.swift`.
- Failure state exposed: missing/non-actionable state surfaces become explicit test failures; runtime non-happy paths remain visible via dedicated UI state content.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — baseline state UI to restyle.
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — state machine contract that the view must render faithfully.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — stitch tokens to reuse.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — standardized surface component for card sections.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — CTA style contract.
- `tests/test_verify_m007_s02_qr_behavior_contract.py` — behavior constraints from T01 that visual refactor must preserve.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — stitch-styled, state-complete QR flow with actionable controls.
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — minor state/copy adjustments required to support redesigned state UX.
- `tests/test_verify_m007_s02_qr_design_contract.py` — executable assertions for QR state fidelity, primitive usage, and QR-only invariant.
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — token tweaks only if required for QR-state parity.
