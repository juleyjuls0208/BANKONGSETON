---
id: T04
parent: S02
milestone: M007
provides:
  - Added a deterministic one-command S02 closure verifier and a device-ready QR UAT checklist with explicit failure-class diagnostics.
key_files:
  - scripts/verify-m007-s02.sh
  - .gsd/milestones/M007/slices/S02/S02-UAT.md
  - .gsd/milestones/M007/slices/S02/S02-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D079 — use `rtk proxy python` literal checks for static QR/Home markers in the verifier for cross-shell determinism.
patterns_established:
  - Phase-scoped fail-fast verifier output (`behavior-contract`, `design-contracts`, `static-scope`) with actionable guidance lines.
observability_surfaces:
  - `[verify-m007-s02] phase=... status=...` logs, explicit `guidance=` failure messages, and `.gsd/milestones/M007/slices/S02/S02-UAT.md` pass/fail checklist rows.
duration: 1h 10m
verification_result: partial
completed_at: 2026-03-22T20:53:00+08:00
blocker_discovered: false
---

# T04: Add slice closure harness and device-ready QR manual checklist

**Shipped a deterministic S02 verifier script plus a concrete on-device QR checklist, and wired slice tracking to closed for T04.**

## What Happened

Implemented `scripts/verify-m007-s02.sh` as a fail-fast closure harness that: (1) runs S02 behavior/design pytest contracts, (2) enforces static QR-only/state-coverage/camera-key guards, and (3) emits clear phase/failure guidance for fast diagnosis.

Added `.gsd/milestones/M007/slices/S02/S02-UAT.md` with concise pass/fail device scenarios covering Home QR-only entry, valid token-only flow, invalid/expired QR, insufficient balance, camera-denied behavior, and retry recovery.

During verification, two environment-specific execution constraints were handled without changing slice intent:
- `rtk proxy bash ...` fails on this host (`/bin/bash` missing), so equivalent bash checks were run via `rtk proxy "C:/Program Files/Git/bin/bash.exe" ...`.
- `xcodebuild` is unavailable on this Windows host (`program not found`), so iOS build verification remains pending on macOS.

Marked T04 complete in `.gsd/milestones/M007/slices/S02/S02-PLAN.md`.

## Verification

Executed T04 and slice-level checks, including contract suites, the new closure harness, static grep surface check, and UAT checklist presence. Re-ran one pytest command serially after a known `.coverage` race triggered by parallel execution.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy "C:/Program Files/Git/bin/bash.exe" scripts/verify-m007-s02.sh` | 0 | ✅ pass | ~2s |
| 2 | `rtk proxy "C:/Program Files/Git/bin/bash.exe" -lc "test -s .gsd/milestones/M007/slices/S02/S02-UAT.md"` | 0 | ✅ pass | <1s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py` | 0 | ✅ pass | ~0.31s |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_design_contract.py tests/test_verify_m007_s02_home_qr_design_contract.py` | 0 | ✅ pass | ~0.34s |
| 5 | `rtk proxy "C:/Program Files/Git/bin/bash.exe" scripts/verify-m007-s02.sh` (slice verification command equivalent) | 0 | ✅ pass | ~2s |
| 6 | `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination "platform=iOS Simulator,name=iPhone 15" build` | 1 | ❌ fail | 14.1s |
| 7 | `rtk proxy "C:/Program Files/Git/bin/bash.exe" -lc "rtk grep -n 'permission denied|Camera access|scanner|expired QR|Retry|Cancel' mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift"` | 0 | ✅ pass | <1s |

## Diagnostics

- Run `scripts/verify-m007-s02.sh` (or `rtk proxy "C:/Program Files/Git/bin/bash.exe" scripts/verify-m007-s02.sh` on Windows hosts without `/bin/bash`) to see exact failing phase.
- Use verifier logs: `phase=behavior-contract`, `phase=design-contracts`, `phase=static-scope`.
- For manual runtime readiness, execute the checklist in `.gsd/milestones/M007/slices/S02/S02-UAT.md` on simulator/device and record pass/fail per scenario row.

## Deviations

- Used Git Bash invocation for bash-based checks because canonical `rtk proxy bash ...` fails in this environment (`/bin/bash` missing).
- Could not complete `xcodebuild` slice check on this host because `xcodebuild` is not installed/available.

## Known Issues

- Slice verification is **partial** in this environment: iOS build gate requires a macOS/Xcode host.
- Manual device/UAT execution remains a human-run step; checklist is authored and ready.

## Files Created/Modified

- `scripts/verify-m007-s02.sh` — New fail-fast S02 closure harness (pytest + static QR/state/camera contract checks).
- `.gsd/milestones/M007/slices/S02/S02-UAT.md` — New manual device-ready QR pass/fail checklist.
- `.gsd/milestones/M007/slices/S02/S02-PLAN.md` — Marked T04 as complete (`[x]`).
- `.gsd/DECISIONS.md` — Added D079 documenting verifier static-check mechanism choice.
- `.gsd/KNOWLEDGE.md` — Added cross-shell static-check gotcha/pattern for future agents.
