---
id: T01
parent: S02
milestone: M007
provides:
  - Hardened QR scan ingestion with dual URL/token payload parsing, non-scanning duplicate-scan gating, and explicit scanner permission/setup failure transitions.
key_files:
  - mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - tests/test_verify_m007_s02_qr_behavior_contract.py
  - .gsd/milestones/M007/slices/S02/S02-PLAN.md
key_decisions:
  - Followed existing M007 S02 decision (D077) by enforcing dual-format QR ingestion + explicit no-dead-control scanner-failure UX contract.
patterns_established:
  - Gate scan ingestion with `guard case .scanning = state` before async cart fetch to prevent duplicate camera-frame races.
  - Emit explicit `QRPayState` transition reasons for scan classification and failure-path diagnosis.
observability_surfaces:
  - QRPayViewModel transition logs (`[QRPayViewModel] ... reason=...`), scanner permission/setup failure messages in UI, and contract assertions in `tests/test_verify_m007_s02_qr_behavior_contract.py`.
duration: 1h 15m
verification_result: partial
completed_at: 2026-03-22
blocker_discovered: false
---

# T01: Harden QR scan ingestion and permission/error behavior contract

**Added dual-format QR parsing, duplicate-scan gating, and actionable camera failure UX/state transitions with executable behavior-contract tests.**

## What Happened

I activated the requested skills, then attempted qodo rules load and found no `~/.qodo/config.json` / QODO env in this environment, so execution proceeded with local project rules only.  
I applied the preflight observability fix by adding an explicit failure-path inspection verification step in `.gsd/milestones/M007/slices/S02/S02-PLAN.md`.  
I refactored `QRPayViewModel` to parse both `/api/qr/<token>` URL payloads and bare token payloads, reject malformed/empty payloads deterministically into explicit error state, and ignore scan callbacks once state leaves `.scanning`.  
I added explicit transition logging with reason tags (including scan source classification `url` vs `token`, duplicate-scan ignore, and scanner-failure reasons) to preserve runtime diagnosability.  
I extended `QRScannerView` with scanner failure propagation for camera permission denied/restricted, first-time permission rejection, and capture-session setup failures, each with actionable user-facing message text.  
I wired scanner failure callbacks into `QRPayView` and upgraded error-state controls to include `Retry Scan` always and `Open Settings` for camera-access failures.
I created `tests/test_verify_m007_s02_qr_behavior_contract.py` with assertions for parser behavior, duplicate-scan gating, scanner failure contract, and actionable QR error controls.

## Verification

Executed the T01 required checks and the slice-level verification list; behavior-contract tests passed, while platform/tooling-dependent checks failed in this Windows executor due missing bash/WSL and missing Xcode toolchain.  
Also ran direct observability grep checks to validate the new state/failure signals in Swift sources.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py` | 0 | ✅ pass | 0.31s |
| 2 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (tool unavailable) | n/a |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py tests/test_verify_m007_s02_home_qr_design_contract.py` | 4 | ❌ fail (files not yet created in T01 scope) | n/a |
| 4 | `rtk proxy bash scripts/verify-m007-s02.sh` | 1 | ❌ fail (`/bin/bash` unavailable in this executor) | n/a |
| 5 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | 1 | ❌ fail (tool unavailable) | n/a |
| 6 | `rtk proxy bash -lc "rtk grep -n \"permission denied|Camera access|scanner|expired QR|Retry|Cancel\" ..."` | 1 | ❌ fail (`/bin/bash` unavailable in this executor) | n/a |
| 7 | `rtk grep -n "Camera access|Retry Scan|onScannerFailure|scan_accepted_url|scan_accepted_token|Ignoring duplicate scan|invalid_scan_payload" mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` | 0 | ✅ pass | n/a |

## Diagnostics

- Inspect transition reasons and source classification in `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` (`transition(... reason: ...)`, `scan_accepted_...`, `invalid_scan_payload`, duplicate-scan ignore log).  
- Inspect scanner permission/setup failure branches and user messaging in `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` (`.denied`, `.restricted`, requestAccess rejection, setup `reportScannerFailure(...)`).  
- Inspect UI actionability in `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` (`onScannerFailure` wiring, `Retry Scan`, conditional `Open Settings`).  
- Re-run `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py` for contract-level regression checks.

## Deviations

- Added one preflight verification item in `.gsd/milestones/M007/slices/S02/S02-PLAN.md` for inspectable failure-path messaging/state surface validation, per the execution preflight instruction.
- Due this executor’s missing `/bin/bash`, ran equivalent direct `rtk grep` observability check to validate failure-state surfaces after the required `rtk proxy bash ...` command failed.

## Known Issues

- `xcodebuild` is unavailable in this environment (`program not found`), so simulator build verification must be executed on a macOS runner/device stage.
- Slice-level T02/T03 verification test files are not present yet (expected at this task boundary), so full slice verification remains partial until later tasks complete.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — Added dual-format QR payload parsing, malformed payload rejection, duplicate-scan state gate, scanner failure handler, and transition-reason logging.
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` — Added scanner failure callback contract and explicit permission/setup failure handling with actionable messages.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — Wired scanner failure into view model and added actionable error controls (`Retry Scan`, conditional `Open Settings`).
- `tests/test_verify_m007_s02_qr_behavior_contract.py` — Added behavior-contract assertions for parser coverage, duplicate-scan gating, scanner failures, and UI actionability.
- `.gsd/milestones/M007/slices/S02/S02-PLAN.md` — Added inspectable failure-path verification step and marked T01 as complete.
