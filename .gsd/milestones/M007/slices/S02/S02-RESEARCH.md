# S02 Research — Home + QR Flow Redesign (QR-Only)

**Date:** 2026-03-22  
**Status:** Ready for planning

## Requirement Targeting (Active)

S02 directly owns/supports:

- **Owns:**
  - **R056** — No dead controls in visible in-scope UI
  - **R057** — QR-only payment UX (no payment-method chooser surfaces)
- **Supports:**
  - **R055** — Stitch-faithful redesign (home + QR states)
  - **R059** — QR loading/error/success state fidelity
  - **R063** — On-device demo readiness

## Summary

This slice is **targeted research** (known stack, moderate integration risk). The codebase already has working QR flow primitives from M005 (Home button → QR scanner → cart confirm → success/error), but visual parity is incomplete and there are fragility points that can produce dead/failed demo behavior.

### Current baseline in code

- `HomeView.swift` is already partially stitch-themed and has always-visible **Pay with QR** CTA.
- QR flow exists (`QRPayView.swift`, `QRPayViewModel.swift`, `QRScannerView.swift`) but UI is still mostly default SwiftUI styling and not aligned with current stitch tokens/components (`AppTheme`, `StitchCard`, `StitchPrimaryButtonStyle`).
- `APIClient` already exposes `getQrCart(token:)` and `confirmQrPayment(token:)` using JWT auth.
- Camera usage description exists in `project.pbxproj` (`INFOPLIST_KEY_NSCameraUsageDescription` set for Debug + Release).

### High-risk mismatch discovered

`QRPayViewModel.handleScannedURL` currently accepts **full URL only** (`urlString.contains("/api/qr/")`).

But backend/cashier/Arduino path now emits **token-only QR payloads** via `qr_value` (8-char token) for OLED readability:
- `backend/dashboard/cashier/cashier_routes.py` stores `qr_value: token`
- `arduino/bankongseton_r4/bankongseton_r4.ino` parser prefers `"qr_value"` over full URL

So iOS can fail to progress from scan → loading for real OLED scans unless token-only parsing is supported. This is a direct **R056 risk** (visible CTA appears dead during live demo).

## Recommendation

Plan S02 around **behavior hardening first, restyle second**:

1. **Stabilize scan ingestion + no-dead-control behavior**
   - accept both full URL and bare token payloads
   - gate duplicate scans while loading
   - provide explicit camera-permission-denied UX (not silent black preview)
2. **Redesign Home + all QR states with stitch tokens/components**
   - keep existing API contracts and state machine
   - migrate visuals to `AppTheme` + `Stitch*` primitives
3. **Add slice-level verification script + manual device pass checklist**
   - static contract checks + runtime/physical checks for demo readiness

## Implementation Landscape

### Key files and current role

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
  - Home surface, QR CTA sheet trigger, home refresh callback after QR success
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
  - balance + recent tx fetch; refreshes on QR success callback
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
  - state-driven UI shell (`scanning/loading/confirming/success/error`)
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
  - token extraction + QR API calls + state transitions
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift`
  - AVFoundation scanner bridge; currently no explicit permission-state UX
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
  - stitch design tokens (palette, typography, spacing, radius, shadows)
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
  - existing reusable primitives that QR flow should adopt

### Natural seams for planner tasking

1. **Behavior seam (risk retirement first)**
   - `QRPayViewModel.swift` token parsing + scan gating
   - `QRScannerView.swift` permission/error surface contract
2. **QR visual seam**
   - `QRPayView.swift` restyle all 5 states using AppTheme/Stitch components
3. **Home visual seam**
   - `HomeView.swift` stitch parity and CTA hierarchy polish while preserving existing callback wiring
4. **Verification seam**
   - add `scripts/verify-m007-s02.sh` (or equivalent) + explicit manual test matrix

## Critical Constraints / Fragility

- **Token format drift:** iOS currently assumes URL payload; hardware path prefers token payload.
- **Permission UX gap:** denied camera permission currently yields non-actionable scanner failure.
- **Duplicate scan race:** scanner delegate can emit repeated frames; current viewmodel has no early guard for non-scanning state.
- **Do not alter backend contracts in this slice:** API shapes are already live and consumed by Android/iOS.
- **Keep QR-only invariant:** no payment-method chooser or alternate payment controls should be introduced.

## Don’t Hand-Roll

Use existing, already-proven components/patterns:

- `AppTheme` tokens (`Palette`, `Spacing`, `Typography`, `Radius`)
- `StitchCard`, `StitchPrimaryButtonStyle` for consistent visual language
- existing `QRPayState` state machine and `APIClient` QR methods
- AVFoundation stack already in `QRScannerView` (no new scanning dependency)

## Verification Strategy (for S02 execution)

### Static/contract checks

- Home QR entry still wired:
  - `rtk grep "home-qr-pay-button" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- QR state machine still complete:
  - `rtk grep "case \.scanning|case \.loading|case \.confirming|case \.success|case \.error" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- QR-only surface (no method selector text in Home/QR):
  - `rtk grep "Payment Method|Select Method|NFC Pay" mobile/ios/BankongSetonStudent/Views/Home mobile/ios/BankongSetonStudent/Views/QR -g "*.swift"`
- Stitch primitives applied in QR/Home:
  - `rtk grep "AppTheme\.|StitchCard|StitchPrimaryButtonStyle" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- Camera usage key present in project:
  - `rtk grep "INFOPLIST_KEY_NSCameraUsageDescription" mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`

### Runtime checks (macOS/Xcode host)

- Build:
  - `xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- Manual flow:
  1. Login → Home renders redesigned shell
  2. Tap Pay with QR → scanner opens
  3. Scan valid token/URL payload → loading → confirm
  4. Confirm payment → success state + dismiss
  5. Home balance refresh callback fires
  6. Scan expired/invalid token path shows non-dead error state
  7. Camera denied path shows actionable guidance

### Environment note

`xcodebuild` is not available in this scout environment (`program not found`), so compile/runtime proof must be produced on macOS executor/device stage.

## Skill-Guided Implementation Notes

Applied from activated skills:

- **swiftui**: “Prove, don’t promise” and verify each change with build/runtime evidence.
- **make-interfaces-feel-better**: preserve tactile press states, avoid heavy transitions, maintain minimum hit areas.
- **accessibility**: ensure clear labels/messages for scanner and error states; avoid color-only error signaling.
- **debug-like-expert** mindset: verify actual QR payload shape from backend/Arduino path, don’t assume URL-only input.

## Skill Discovery (suggest)

Core technologies for this slice:
- SwiftUI (installed skill: `swiftui`)
- AVFoundation QR scanning (no dedicated installed skill)

Attempted discovery command for missing niche skill:
- `rtk proxy npx skills find "AVFoundation QR scanning"`
- Result: `npx` unavailable in current environment (`program not found`)

No install action taken.

## Sources

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `backend/dashboard/cashier/cashier_routes.py`
- `backend/dashboard/web_app.py`
- `arduino/bankongseton_r4/bankongseton_r4.ino`
- `.gsd/REQUIREMENTS.md`
