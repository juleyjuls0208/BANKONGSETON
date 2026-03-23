---
id: T02
parent: S02
milestone: M007
provides:
  - Stitch-faithful QR state surfaces with actionable controls and QR-only design contract coverage for scanning/loading/confirming/success/error.
key_files:
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - tests/test_verify_m007_s02_qr_design_contract.py
  - .gsd/milestones/M007/slices/S02/S02-PLAN.md
key_decisions:
  - Standardized each QR state onto `AppTheme` + `StitchCard` surfaces and used `StitchPrimaryButtonStyle` for primary actions to keep state/action mapping visually consistent.
patterns_established:
  - Keep QR flow state rendering centralized through a single `switch viewModel.state` surface with per-state action buttons wired directly to real view-model or navigation actions.
observability_surfaces:
  - `tests/test_verify_m007_s02_qr_design_contract.py` plus inspectable state-specific copy/action strings in `QRPayView.swift` (scan/loading/confirm/error guidance).
duration: 1h 10m
verification_result: partial
completed_at: 2026-03-22
blocker_discovered: false
---

# T02: Restyle all QR states with stitch primitives while preserving QR-only actions

**Restyled all five QR payment states with stitch primitives, preserved real confirm/retry/cancel/done behavior wiring, and added QR-only design contract tests.**

## What Happened

I activated the requested skills, validated T02/S02 task artifacts, and then refactored `QRPayView` state-by-state to use stitch primitives instead of ad hoc styling.
I introduced a themed state scaffold (`AppTheme.Palette.background`) and rebuilt `scanning`, `loading`, `confirming`, `success`, and `error` surfaces with `StitchCard`, `AppTheme` spacing/typography/palette tokens, and `StitchPrimaryButtonStyle` for primary CTAs.
I preserved runtime behavior contracts by keeping existing `QRScannerView` callbacks, existing confirm API flow (`viewModel.confirm(token:token, apiClient: apiClient)`), success dismissal callback wiring (`onSuccess` + `dismiss`), and retry/reset action wiring.
I kept the QR-only invariant by using explicit QR-specific copy (scan cashier QR, loading QR details, confirm QR payment) and avoiding payment-method chooser labels/actions.
I created `tests/test_verify_m007_s02_qr_design_contract.py` to enforce state-case coverage, stitch primitive usage, actionable CTA wiring, and absence of payment-method chooser copy.
I marked T02 as done in `.gsd/milestones/M007/slices/S02/S02-PLAN.md`.

## Verification

I ran the T02 task checks and slice-level checks relevant at this stage.
`tests/test_verify_m007_s02_qr_design_contract.py` passed, and prior T01 behavior contract tests still passed after the UI refactor.
Slice-level aggregate checks that depend on future tasks (missing home QR design contract file) or unavailable runtime tools in this Windows executor (`xcodebuild`, `/bin/bash` via `rtk proxy bash`) failed as expected and are recorded explicitly.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py` | 0 | ✅ pass | 1s |
| 2 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (xcodebuild unavailable in this executor) | 36.2s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py` | 0 | ✅ pass | 1s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py tests/test_verify_m007_s02_home_qr_design_contract.py` | 4 | ❌ fail (T03 contract file not created yet) | 1s |
| 5 | `rtk proxy bash scripts/verify-m007-s02.sh` | 1 | ❌ fail (`/bin/bash` unavailable via WSL proxy) | 1s |
| 6 | `rtk proxy bash -lc "rtk grep -n \"permission denied|Camera access|scanner|expired QR|Retry|Cancel\" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift"` | 1 | ❌ fail (`/bin/bash` unavailable via WSL proxy) | 0s |
| 7 | `rtk grep -n "permission denied|Camera access|scanner|expired QR|Retry|Cancel|Confirm QR Payment|Loading QR payment details" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` | 0 | ✅ pass (direct fallback inspection) | 0s |

## Diagnostics

- Inspect per-state stitch implementation and CTA wiring in `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` (`stateContent`, `scanningView`, `loadingView`, `confirmView`, `successView`, `errorView`).
- Re-run `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py` for state coverage + QR-only design contract assertions.
- Re-run `rtk grep -n "Confirm QR Payment|Retry Scan|Open Settings|Loading QR payment details" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` for quick UI-surface action/copy inspection.

## Deviations

- The slice-required `rtk proxy bash ...` checks could not run in this environment due missing `/bin/bash` via WSL proxy, so I executed an equivalent direct `rtk grep` fallback to preserve inspectable failure-path evidence.

## Known Issues

- `xcodebuild` is unavailable in this executor, so iOS simulator build verification must be completed on macOS.
- `tests/test_verify_m007_s02_home_qr_design_contract.py` is not present yet (planned for T03), so the combined slice design-contract command is expected to fail at T02 boundary.
- `scripts/verify-m007-s02.sh` is planned for T04, so slice closure command cannot fully pass at T02.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — Restyled all QR states with stitch primitives and preserved actionable QR flow controls.
- `tests/test_verify_m007_s02_qr_design_contract.py` — Added executable design contract assertions for state coverage, stitch primitive usage, actionable controls, and QR-only copy.
- `.gsd/milestones/M007/slices/S02/S02-PLAN.md` — Marked T02 checklist item as complete (`[x]`).
