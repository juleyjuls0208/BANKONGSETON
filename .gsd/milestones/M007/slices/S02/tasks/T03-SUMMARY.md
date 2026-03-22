---
id: T03
parent: S02
milestone: M007
provides:
  - Redesigned Home QR entry hierarchy with a single prominent QR CTA, stable automation identifier, and explicit post-success Home refresh continuity path.
key_files:
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift
  - tests/test_verify_m007_s02_home_qr_design_contract.py
  - .gsd/milestones/M007/slices/S02/S02-PLAN.md
key_decisions:
  - Introduced a dedicated `refreshAfterQRSuccess(...)` view-model callback path (with explicit log signal) so Home refresh continuity is both observable and source-contract-testable.
patterns_established:
  - Keep Home payment-entry contract deterministic by isolating the QR CTA in a dedicated stitch card and locking identifier + sheet callback wiring via source assertions.
observability_surfaces:
  - `HomeViewModel.refreshAfterQRSuccess` log signal (`[HomeViewModel] Refreshing Home data after QR payment success dismiss`) and `tests/test_verify_m007_s02_home_qr_design_contract.py` for structural callback/CTA contract checks.
duration: 1h 00m
verification_result: partial
completed_at: 2026-03-22
blocker_discovered: false
---

# T03: Redesign Home QR entry surface and preserve post-payment refresh continuity

**Redesigned Home’s QR payment entry into a stitch card with one clear QR CTA while preserving and instrumenting post-success Home refresh continuity.**

## What Happened

I polished `HomeView` layout hierarchy by adding a dedicated `qrEntryCard` beneath the balance card, keeping QR as the single obvious payment action and avoiding any payment-method chooser surface.
I preserved the existing `showQrPay` sheet path and stable `.accessibilityIdentifier("home-qr-pay-button")`, and kept QR scanner presentation through `QRPayView`.
I hardened callback continuity by moving post-success refresh into `HomeViewModel.refreshAfterQRSuccess(apiClient:authManager:)`, then wiring `QRPayView(onSuccess:)` to call this method on dismiss.
I added a lightweight observability signal in the refresh continuity path via `[HomeViewModel] ...` logging.
I created `tests/test_verify_m007_s02_home_qr_design_contract.py` to enforce QR-only Home copy, CTA identifier + sheet wiring, and callback-refresh linkage.
I marked T03 complete in `.gsd/milestones/M007/slices/S02/S02-PLAN.md`.

## Verification

I ran the T03 verification commands, then the slice-level verification list from S02.
The new Home design contract test passed, and the combined design/behavior source-contract suites passed with the new file included.
Environment-dependent checks (`xcodebuild`, `rtk proxy bash ...`) failed in this Windows executor due missing toolchain/WSL bash; these were recorded verbatim and complemented by a direct `rtk grep` observability inspection for the new Home continuity signal.
Manual device/UAT checklist execution remains pending for T04 closure work.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_home_qr_design_contract.py` | 0 | ✅ pass | 0.31s |
| 2 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (xcodebuild unavailable in this executor) | n/a |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py` | 0 | ✅ pass | 0.31s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py tests/test_verify_m007_s02_home_qr_design_contract.py` | 0 | ✅ pass | 0.31s |
| 5 | `rtk proxy bash scripts/verify-m007-s02.sh` | 1 | ❌ fail (`/bin/bash` unavailable in this executor) | n/a |
| 6 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (xcodebuild unavailable in this executor) | n/a |
| 7 | `rtk proxy bash -lc "rtk grep -n \"permission denied|Camera access|scanner|expired QR|Retry|Cancel\" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift"` | 1 | ❌ fail (`/bin/bash` unavailable in this executor) | n/a |
| 8 | `rtk grep -n "qrEntryCard|home-qr-pay-button|refreshAfterQRSuccess|Refreshing Home data after QR payment success dismiss|QRPayView" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` | 0 | ✅ pass | n/a |

## Diagnostics

- Inspect Home QR CTA hierarchy and identifier in `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` (`qrEntryCard`, `home-qr-pay-button`, `.sheet(isPresented: $showQrPay)`).
- Inspect post-success continuity path in `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` (`refreshAfterQRSuccess`, log signal, delegated `load(...)`).
- Re-run `rtk proxy python -m pytest -q tests/test_verify_m007_s02_home_qr_design_contract.py` to validate QR-only Home contract and callback linkage.

## Deviations

- None.

## Known Issues

- `xcodebuild` is not available in this executor, so iOS simulator build verification requires macOS.
- `rtk proxy bash ...` commands fail here because `/bin/bash` (WSL path) is unavailable.
- Slice manual device/UAT checklist (`.gsd/milestones/M007/slices/S02/S02-UAT.md`) is not executed in T03 and remains part of T04 closure work.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — Added stitch-based QR entry hierarchy and preserved QR sheet entry with stable CTA identifier.
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift` — Added explicit post-success Home refresh continuity method + log signal.
- `tests/test_verify_m007_s02_home_qr_design_contract.py` — Added deterministic Home QR-only + callback continuity source-contract assertions.
- `.gsd/milestones/M007/slices/S02/S02-PLAN.md` — Marked T03 checklist item as complete (`[x]`).
