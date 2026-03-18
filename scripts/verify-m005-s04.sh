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
