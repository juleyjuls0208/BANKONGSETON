---
estimated_steps: 5
estimated_files: 4
skills_used:
  - qodo-get-rules
  - swiftui
  - debug-like-expert
  - feature-dev
  - accessibility
  - test
---

# T01: Harden QR scan ingestion and permission/error behavior contract

**Slice:** S02 — Home + QR Flow Redesign (QR-Only)
**Milestone:** M007

## Description

Stabilize QR scan entry behavior first so the redesigned UI does not hide runtime dead-ends: accept real token payload shapes, prevent duplicate scan races, and expose camera permission/setup failures as actionable state.

## Steps

1. Load coding rules via `qodo-get-rules`, then inspect current `handleScannedURL` and scanner delegate flow for URL-only assumptions and duplicate-callback race risk.
2. Refactor `QRPayViewModel` token extraction to accept both full `/api/qr/<token>` URLs and bare token payloads while rejecting malformed scans deterministically.
3. Add guard logic so repeated camera frames do not re-trigger fetch/confirm transitions once state is no longer `.scanning`.
4. Extend `QRScannerView`/`QRPayView` coordination so camera permission denied or capture-session setup failure can move the flow into explicit actionable UI state.
5. Add `tests/test_verify_m007_s02_qr_behavior_contract.py` with real assertions for parser behavior, duplicate-scan gating, and presence of explicit failure-path handling symbols/messages.

## Must-Haves

- [ ] Both URL QR payloads and token-only payloads are supported by scan ingestion.
- [ ] Duplicate scan frames cannot trigger multiple overlapping cart fetches.
- [ ] Camera denied/setup failure is surfaced to the user with an actionable state transition.
- [ ] Behavior-contract tests fail if payload parsing or scan-gating protections regress.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: QR scan ingestion path classification (URL vs token), non-scanning duplicate-scan ignore behavior, and scanner permission/setup failure state transitions.
- How a future agent inspects this: run `tests/test_verify_m007_s02_qr_behavior_contract.py` and inspect `QRPayViewModel.swift` / `QRScannerView.swift` state-handling branches.
- Failure state exposed: instead of silent scanner stall, denied/setup failures become explicit UI error/permission states with retry/exit affordances.

## Inputs

- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — current URL-only parser and state transition logic.
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` — current AVFoundation bridge with no explicit permission-denied UX state.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — current state rendering entrypoint that consumes scanner callbacks.
- `.gsd/milestones/M007/slices/S02/S02-RESEARCH.md` — documented token-only payload and dead-control risks to retire first.

## Expected Output

- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — resilient dual-format payload parsing + duplicate-scan guard logic.
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` — permission/setup error propagation contract for scanner failures.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — integration hooks for scanner failure-path state transitions.
- `tests/test_verify_m007_s02_qr_behavior_contract.py` — executable assertions for payload parsing + no-dead-control scan behavior.
