# S04: Android + iOS App QR Pay

**Goal:** Both mobile apps can complete a QR payment end-to-end — student taps "Pay with QR", scans the OLED QR, sees the pending cart, taps Confirm, and balance is debited via the S03 backend.
**Demo:** Android student scans OLED QR → QRPayActivity shows cart items + total → taps Confirm → toast "Payment successful!" → balance refreshes. iOS student does the same via QRPayView → inline confirmation → success. Both apps build without errors.

## Must-Haves

- Android: `jwtToken` stored at login; `GET /api/qr/<token>` and `POST /api/qr/confirm` called with Bearer JWT
- Android: `QRPayActivity` with CameraX + ML Kit scanning; extracts token from URL last path segment; shows cart; confirms; handles 402/404/410 error cases
- Android: `HomeActivity` has always-visible "Scan QR" button (`qrPayButton`) replacing the hidden NFC button
- Android: `app/build.gradle.kts` includes CameraX 1.3.1 and ML Kit barcode-scanning 17.2.0 dependencies
- Android: `AndroidManifest.xml` declares `CAMERA` permission and `QRPayActivity`
- iOS: `jwtToken` stored at login in Keychain under key `"jwt_token"`; used for QR endpoint requests
- iOS: `QRScannerView` (AVFoundation), `QRPayViewModel`, `QRPayView` fully implemented
- iOS: `HomeView` has always-visible "Pay with QR" button
- iOS: 4 new Swift files registered in `project.pbxproj` (IDs AA000026–BB000029) with correct groups and build phases; camera key in build settings
- `scripts/verify-m005-s04.sh` exits 0 (12 checks)

## Proof Level

- This slice proves: contract + integration (code in place and build-clean)
- Real runtime required: no (contract-level verify; UAT on real device deferred)
- Human/UAT required: yes — end-to-end scan on real hardware before milestone called done

## Verification

```bash
bash scripts/verify-m005-s04.sh
# All 12/12 checks must pass (exits 0)
```

**Failure-state diagnostic checks (run when verify script has failures):**
```bash
# Check each major artifact exists — pinpoints which task's output is missing
test -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt && echo "OK: QRPayActivity.kt" || echo "FAIL: QRPayActivity.kt missing — T02 incomplete"
grep -q 'qrPayButton' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt && echo "OK: qrPayButton wired" || echo "FAIL: HomeActivity still uses activateNfcPayButton"
grep -q 'android.permission.CAMERA' mobile/student_app_v2/app/src/main/AndroidManifest.xml && echo "OK: CAMERA permission" || echo "FAIL: CAMERA permission missing — QR scan will crash"
test -f mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift && echo "OK: QRPayView.swift" || echo "FAIL: QRPayView.swift missing — T03 incomplete"
grep -q 'AA000026' mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj && echo "OK: pbxproj has QR file entries" || echo "FAIL: pbxproj missing QR entries — iOS build will fail"
```

Build-level checks (run manually on dev machine with Android SDK / Xcode):
```bash
# Android
cd mobile/student_app_v2 && ./gradlew assembleDebug   # must exit 0

# iOS
cd mobile/ios/BankongSetonStudent
xcodebuild -scheme BankongSetonStudent -sdk iphonesimulator build   # must exit 0
```

## Observability / Diagnostics

- Runtime signals: Android toast "Payment successful!" / error dialogs for 402/404/410; iOS inline state transitions (scanning → confirming → success/error)
- Inspection surfaces: `grep 'event=qr_confirm' <flask_log>` confirms backend received the confirm; `GET /api/arduino/qr-pending` with API key confirms token cleared after payment
- Failure visibility: 402 → "Insufficient balance" dialog; 404/410 → "QR expired" dialog; 401 → re-login prompt (same as existing 401 handling in both apps)
- Redaction constraints: JWT token in Authorization header only; never logged
- Failure-state diagnostics: `bash scripts/verify-m005-s04.sh 2>&1` prints each failing check with its label so the exact gap is identifiable without reading all source files; Android 401 on QR endpoints means `getJwtToken()` returned null — add `Log.d("JWT","jwt stored: ${secureStorage.getJwtToken() != null}")` in `HomeActivity.onCreate` to confirm storage; iOS 401 means `KeychainHelper.read(forKey:"jwt_token")` is nil — add `print("jwt stored: \(KeychainHelper.read(forKey:"jwt_token") != nil)")` in `AuthManager.login` to confirm

## Integration Closure

- Upstream surfaces consumed: `GET /api/qr/<token>` and `POST /api/qr/confirm` from S03 (Bearer JWT); `jwt_token` field in login response from `api_server.py` (S03 added it)
- New wiring introduced in this slice: both apps store `jwt_token` at login; QRPayActivity/QRPayView call the two QR endpoints with JWT; HomeActivity/HomeView expose the QR entry point
- What remains before the milestone is truly usable end-to-end: physical RFID card tap on R4 (S01 hardware UAT) + OLED QR render (S02 hardware UAT) + actual device QR scan on real backend (S04 UAT) + NFC dead code removal (S05)

## Tasks

- [x] **T01: Fix JWT token storage and add QR API client methods in both apps** `est:45m`
  - Why: `/api/qr/<token>` and `/api/qr/confirm` require `Authorization: Bearer <jwt_token>` — a distinct token from the session token. Neither app stores the `jwt_token` from the login response. All QR calls will return 401 until this is fixed. Also adds CameraX + ML Kit to Android's build.gradle so T02 can compile.
  - Files: `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt`, `SecureStorage.kt`, `LoginActivity.kt`, `ApiClient.kt`, `app/build.gradle.kts`, `mobile/ios/BankongSetonStudent/Models/LoginModels.swift`, `Core/Auth/AuthManager.swift`, `Core/Network/APIClient.swift`, `Core/Network/APIEndpoints.swift`
  - Do: See T01-PLAN.md
  - Verify: `grep -q 'jwtToken' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt && grep -q 'saveJwtToken' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt && grep -q 'barcode-scanning' mobile/student_app_v2/app/build.gradle.kts && grep -q 'jwtToken' mobile/ios/BankongSetonStudent/Models/LoginModels.swift && grep -q 'jwt_token' mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
  - Done when: All 5 greps pass; `getQrCart` and `confirmQrPayment` are declared in both `BangkoApiService` (Android) and `APIClient.swift` (iOS)

- [x] **T02: Build Android QRPayActivity — CameraX scanner, confirmation UI, HomeActivity wiring** `est:1h`
  - Why: Implements the full Android QR payment user flow. Creates the new activity with ML Kit barcode scanning, cart confirmation view, error dialogs, and wires the always-visible "Scan QR" button in HomeActivity.
  - Files: `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt` (new), `app/src/main/res/layout/activity_qr_pay.xml` (new), `HomeActivity.kt`, `app/src/main/res/layout/activity_home.xml`, `AndroidManifest.xml`, `app/src/main/res/values/strings.xml`
  - Do: See T02-PLAN.md
  - Verify: `grep -q 'QRPayActivity' mobile/student_app_v2/app/src/main/AndroidManifest.xml && grep -q 'CAMERA' mobile/student_app_v2/app/src/main/AndroidManifest.xml && grep -q 'qrPayButton' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt`
  - Done when: All 3 greps pass; `activity_qr_pay.xml` exists; `QRPayActivity.kt` compiles (no red underlines on ML Kit / CameraX imports)

- [x] **T03: Build iOS QR views — AVFoundation scanner, confirmation, HomeView wiring, pbxproj registration** `est:1h`
  - Why: Implements the full iOS QR payment user flow. Creates 4 new Swift files (QRModels, QRPayViewModel, QRScannerView, QRPayView), adds the "Pay with QR" button to HomeView, and correctly registers all new files in project.pbxproj so the iOS app compiles.
  - Files: `mobile/ios/BankongSetonStudent/Models/QRModels.swift` (new), `ViewModels/QRPayViewModel.swift` (new), `Views/QR/QRScannerView.swift` (new), `Views/QR/QRPayView.swift` (new), `Views/Home/HomeView.swift`, `BankongSetonStudent.xcodeproj/project.pbxproj`
  - Do: See T03-PLAN.md
  - Verify: `grep -q 'QRPayView' mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift && grep -q 'AVCaptureMetadataOutput' mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift && grep -q 'AA000026' mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
  - Done when: All 3 greps pass; all 4 new Swift files exist; `project.pbxproj` has 4 new PBXBuildFile + 4 new PBXFileReference entries + camera usage description key

- [ ] **T04: Write verification script** `est:15m`
  - Why: Creates the objective stopping condition for the slice. Catches regressions in any of the preceding tasks.
  - Files: `scripts/verify-m005-s04.sh` (new)
  - Do: See T04-PLAN.md
  - Verify: `bash scripts/verify-m005-s04.sh` exits 0
  - Done when: Script exits 0; all 12 checks pass

## Files Likely Touched

- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt` ← new
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt`
- `mobile/student_app_v2/app/src/main/res/layout/activity_qr_pay.xml` ← new
- `mobile/student_app_v2/app/src/main/res/layout/activity_home.xml`
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml`
- `mobile/student_app_v2/app/src/main/res/values/strings.xml`
- `mobile/student_app_v2/app/build.gradle.kts`
- `mobile/ios/BankongSetonStudent/Models/LoginModels.swift`
- `mobile/ios/BankongSetonStudent/Models/QRModels.swift` ← new
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` ← new
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` ← new
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` ← new
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `scripts/verify-m005-s04.sh` ← new
