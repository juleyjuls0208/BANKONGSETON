---
estimated_steps: 2
estimated_files: 1
---

# T04: Write verification script scripts/verify-m005-s04.sh

**Slice:** S04 — Android + iOS App QR Pay
**Milestone:** M005

## Description

Creates the objective stopping condition for S04. The script runs 12 grep/file-existence checks across both codebases. All 12 must pass for the slice to be considered contract-verified. The script follows the same pattern as `scripts/verify-m005-s03.sh`.

**Prerequisite:** T01, T02, T03 must all be complete.

## Steps

1. **Create `scripts/verify-m005-s04.sh`** with the following content:

   ```bash
   #!/usr/bin/env bash
   # verify-m005-s04.sh — S04: Android + iOS App QR Pay
   # Exits 0 if all checks pass; non-zero on first failure.
   set -e

   PASS=0
   FAIL=0

   check() {
     local desc="$1"
     shift
     if "$@" 2>/dev/null; then
       echo "  [PASS] $desc"
       PASS=$((PASS + 1))
     else
       echo "  [FAIL] $desc"
       FAIL=$((FAIL + 1))
     fi
   }

   echo "=== M005-S04: Android + iOS App QR Pay ==="
   echo ""

   # ── Android checks ──────────────────────────────────────────────────────────

   echo "-- Android --"

   # [1] jwtToken in Models.kt
   check "jwtToken field in Android LoginResponse (Models.kt)" \
     grep -q 'jwtToken' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt

   # [2] saveJwtToken in SecureStorage.kt
   check "saveJwtToken method in Android SecureStorage.kt" \
     grep -q 'saveJwtToken' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt

   # [3] getQrCart / confirmQrPayment in ApiClient.kt
   check "getQrCart and confirmQrPayment in Android ApiClient.kt" \
     grep -q 'getQrCart\|confirmQrPayment' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt

   # [4] barcode-scanning dependency in build.gradle.kts
   check "ML Kit barcode-scanning in app/build.gradle.kts" \
     grep -q 'barcode-scanning' mobile/student_app_v2/app/build.gradle.kts

   # [5] QRPayActivity in AndroidManifest.xml
   check "QRPayActivity declared in AndroidManifest.xml" \
     grep -q 'QRPayActivity' mobile/student_app_v2/app/src/main/AndroidManifest.xml

   # [6] CAMERA permission in AndroidManifest.xml
   check "CAMERA permission in AndroidManifest.xml" \
     grep -q 'android.permission.CAMERA' mobile/student_app_v2/app/src/main/AndroidManifest.xml

   # ── iOS checks ───────────────────────────────────────────────────────────────

   echo ""
   echo "-- iOS --"

   # [7] jwtToken in LoginModels.swift
   check "jwtToken field in iOS LoginModels.swift" \
     grep -q 'jwtToken' mobile/ios/BankongSetonStudent/Models/LoginModels.swift

   # [8] jwt_token saved in AuthManager.swift
   check "jwt_token saved in iOS AuthManager.swift" \
     grep -q 'jwt_token' mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift

   # [9] getQrCart / confirmQrPayment in iOS APIClient.swift
   check "getQrCart and confirmQrPayment in iOS APIClient.swift" \
     grep -q 'getQrCart\|confirmQrPayment' mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift

   # [10] QRPayView / showQrPay in HomeView.swift
   check "QRPayView or showQrPay button in iOS HomeView.swift" \
     grep -q 'QRPayView\|showQrPay' mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift

   # [11] AVCaptureMetadataOutput in QRScannerView.swift
   check "AVCaptureMetadataOutput in iOS QRScannerView.swift" \
     grep -q 'AVCaptureMetadataOutput' mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift

   # [12] new pbxproj IDs (AA000026) present
   check "New Swift files registered in project.pbxproj (AA000026)" \
     grep -q 'AA000026' mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj

   # ── Summary ──────────────────────────────────────────────────────────────────

   echo ""
   echo "Results: $PASS passed, $FAIL failed"

   if [ "$FAIL" -gt 0 ]; then
     echo "FAIL — $FAIL check(s) did not pass"
     exit 1
   else
     echo "PASS — all $PASS checks passed"
     exit 0
   fi
   ```

2. **Make the script executable:**
   ```bash
   chmod +x scripts/verify-m005-s04.sh
   ```

3. **Run the script and confirm exit 0:**
   ```bash
   bash scripts/verify-m005-s04.sh
   ```
   All 12/12 checks must pass.

## Must-Haves

- [ ] Script exists at `scripts/verify-m005-s04.sh`
- [ ] Script is executable (`chmod +x`)
- [ ] All 12 checks pass; script exits 0

## Verification

```bash
bash scripts/verify-m005-s04.sh
# Expected output:
# === M005-S04: Android + iOS App QR Pay ===
# -- Android --
#   [PASS] jwtToken field in Android LoginResponse (Models.kt)
#   [PASS] saveJwtToken method in Android SecureStorage.kt
#   [PASS] getQrCart and confirmQrPayment in Android ApiClient.kt
#   [PASS] ML Kit barcode-scanning in app/build.gradle.kts
#   [PASS] QRPayActivity declared in AndroidManifest.xml
#   [PASS] CAMERA permission in AndroidManifest.xml
# -- iOS --
#   [PASS] jwtToken field in iOS LoginModels.swift
#   [PASS] jwt_token saved in iOS AuthManager.swift
#   [PASS] getQrCart and confirmQrPayment in iOS APIClient.swift
#   [PASS] QRPayView or showQrPay button in iOS HomeView.swift
#   [PASS] AVCaptureMetadataOutput in iOS QRScannerView.swift
#   [PASS] New Swift files registered in project.pbxproj (AA000026)
# Results: 12 passed, 0 failed
# PASS — all 12 checks passed
```

## Observability Impact

- **Primary inspection surface:** `bash scripts/verify-m005-s04.sh 2>&1` — each of the 12 checks prints `[PASS]` or `[FAIL]` with a human-readable label, so failure pinpoints exactly which T01/T02/T03 artifact is absent or incomplete without reading source files.
- **Failure-state visibility:** Script exits non-zero with `FAIL — N check(s) did not pass` printed to stdout; the individual `[FAIL]` lines identify the exact missing artifact (e.g. "getQrCart and confirmQrPayment in Android ApiClient.kt").
- **Exit-code contract:** Exit 0 means all 12 S04 contract conditions are met; any non-zero exit means the slice is not complete — the label of each failing check identifies the exact gap.
- **No runtime signals introduced:** This task creates only a static check script; it does not modify any app code or add runtime logging.

## Inputs

- All T01, T02, T03 outputs present in the filesystem

## Expected Output

- `scripts/verify-m005-s04.sh` — 12-check verification script; exits 0 when all S04 contract conditions are met; prints `[PASS]`/`[FAIL]` per check with totals
