---
estimated_steps: 4
estimated_files: 4
skills_used:
  - swiftui
  - frontend-design
  - make-interfaces-feel-better
  - accessibility
  - feature-dev
  - code-simplifier
---

# T03: Redesign Home QR entry surface and preserve post-payment refresh continuity

**Slice:** S02 — Home + QR Flow Redesign (QR-Only)
**Milestone:** M007

## Description

Polish Home’s QR entry section so the primary payment action is obvious, accessible, and still wired to refresh balance/recent transactions after successful QR payment dismissal.

## Steps

1. Refine Home layout hierarchy around balance card + QR CTA using `AppTheme` tokens and existing stitch primitives, avoiding decorative controls.
2. Keep `home-qr-pay-button` accessibility identifier and ensure tap always presents `QRPayView` through the existing sheet path.
3. Preserve and validate `QRPayView(onSuccess:)` callback behavior that reloads Home data after successful payment.
4. Add `tests/test_verify_m007_s02_home_qr_design_contract.py` to assert QR-only entry copy, CTA identifier/wiring, and callback-refresh linkage.

## Must-Haves

- [ ] Home exposes exactly one obvious payment entry path: QR Pay.
- [ ] `home-qr-pay-button` remains present and interactive for automation/UAT.
- [ ] Post-success QR dismissal still triggers Home data refresh callback.
- [ ] Home contract tests detect regressions in QR-only entry and callback wiring.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_home_qr_design_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: explicit Home QR CTA hierarchy and success-refresh callback continuity signal on dismiss.
- How a future agent inspects this: inspect `HomeView.swift` QR sheet callback and run `tests/test_verify_m007_s02_home_qr_design_contract.py` for structural assertions.
- Failure state exposed: broken callback wiring or missing CTA identifier is caught by deterministic source assertions before manual demo.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — current Home QR entry + refresh callback baseline.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — data reload contract used after QR success.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — sheet destination and success callback consumer.
- `tests/test_verify_m007_s01_design_system_contract.py` — prior primitive-usage assertion style to mirror.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — redesigned Home QR entry with preserved callback wiring.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — any refresh-path adjustments needed for deterministic post-QR reload.
- `tests/test_verify_m007_s02_home_qr_design_contract.py` — executable Home QR-only + callback continuity assertions.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — callback signature/usage updates if needed for refresh continuity.
