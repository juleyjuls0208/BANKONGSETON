---
id: T04
parent: S04
milestone: M005
provides:
  - scripts/verify-m005-s04.sh — 12-check bash verification script for S04; exits 0 when all contract conditions are met
key_files:
  - scripts/verify-m005-s04.sh
key_decisions:
  - Script uses same check()/PASS/FAIL pattern as verify-m005-s03.sh for consistency
patterns_established:
  - Slice verification scripts follow the check()-accumulator pattern: each check prints [PASS]/[FAIL] with a human-readable label, accumulates counts, and exits 1 only after all checks run (so every failure is visible in one invocation)
observability_surfaces:
  - bash scripts/verify-m005-s04.sh 2>&1 — each of 12 checks prints [PASS] or [FAIL]; exit code 0 = all pass, non-zero = one or more gaps; individual [FAIL] lines identify the exact missing artifact
duration: ~5m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T04: Write verification script scripts/verify-m005-s04.sh

**Created scripts/verify-m005-s04.sh with 12 contract checks for S04; all 12/12 pass (exit 0).**

## What Happened

Wrote `scripts/verify-m005-s04.sh` following the same `check()`-accumulator pattern as `verify-m005-s03.sh`. The script covers 6 Android checks (jwtToken in Models.kt, saveJwtToken in SecureStorage.kt, getQrCart/confirmQrPayment in ApiClient.kt, ML Kit barcode-scanning in build.gradle.kts, QRPayActivity in AndroidManifest.xml, CAMERA permission in AndroidManifest.xml) and 6 iOS checks (jwtToken in LoginModels.swift, jwt_token in AuthManager.swift, getQrCart/confirmQrPayment in APIClient.swift, QRPayView/showQrPay in HomeView.swift, AVCaptureMetadataOutput in QRScannerView.swift, AA000026 in project.pbxproj). Also added the missing `## Observability Impact` section to T04-PLAN.md per pre-flight requirements.

## Verification

```
bash scripts/verify-m005-s04.sh
=== M005-S04: Android + iOS App QR Pay ===

-- Android --
  [PASS] jwtToken field in Android LoginResponse (Models.kt)
  [PASS] saveJwtToken method in Android SecureStorage.kt
  [PASS] getQrCart and confirmQrPayment in Android ApiClient.kt
  [PASS] ML Kit barcode-scanning in app/build.gradle.kts
  [PASS] QRPayActivity declared in AndroidManifest.xml
  [PASS] CAMERA permission in AndroidManifest.xml

-- iOS --
  [PASS] jwtToken field in iOS LoginModels.swift
  [PASS] jwt_token saved in iOS AuthManager.swift
  [PASS] getQrCart and confirmQrPayment in iOS APIClient.swift
  [PASS] QRPayView or showQrPay button in iOS HomeView.swift
  [PASS] AVCaptureMetadataOutput in iOS QRScannerView.swift
  [PASS] New Swift files registered in project.pbxproj (AA000026)

Results: 12 passed, 0 failed
PASS — all 12 checks passed
```

Exit code: 0. All 12/12 checks pass. Slice S04 is contract-verified.

## Diagnostics

Run `bash scripts/verify-m005-s04.sh 2>&1` at any time to re-verify the S04 contract. Each `[FAIL]` line names the exact artifact and source file, so the failing T0x task is identifiable without reading source. Exit non-zero = slice incomplete.

## Deviations

None — script content matches T04-PLAN.md exactly.

## Known Issues

None.

## Files Created/Modified

- `scripts/verify-m005-s04.sh` — new 12-check verification script for S04; exits 0 on full pass
- `.gsd/milestones/M005/slices/S04/tasks/T04-PLAN.md` — added missing `## Observability Impact` section (pre-flight gap fix)
