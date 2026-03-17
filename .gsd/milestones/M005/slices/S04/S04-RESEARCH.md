# S04: Android + iOS App QR Pay — Research

**Date:** 2026-03-17
**Status:** Ready for planning

## Summary

S04 adds QR-based payment to both mobile apps — replacing the NFC Pay button with a "Pay with QR" flow. The backend is fully ready (S03 complete): `POST /cashier/api/qr-generate`, `GET /api/qr/<token>`, and `POST /api/qr/confirm` all exist and are verified. The Arduino OLED renders the QR (S02 complete). The apps need a scanner, a confirmation screen, and the right auth token for the QR endpoints.

The work is moderate-complexity: both apps need new files, a dependency addition (Android only), and a critical auth fix. The iOS app does **not** use a PIN-based login — it sends `pin` in the login body but the backend ignores it; there's nothing to fix there. The key integration constraint is that both apps currently store the session `token` from login (not the `jwt_token`), but `/api/qr/*` on `web_app.py` requires a Bearer **JWT** (signed with `JWT_SECRET`, issued by `api_server.py`). This storage gap must be fixed in both apps before any QR call can succeed.

## Recommendation

Implement in three parallel tracks: (1) fix JWT storage and add QR client methods in both apps, (2) build the Android `QRPayActivity` with ML Kit + CameraX camera preview, (3) build the iOS `QRPayView`/`QRScannerView`/`QRPayViewModel` with AVFoundation. The auth fix must land first in each app before the QR flow can be tested. Android requires a `build.gradle.kts` dependency addition (ML Kit + CameraX); iOS needs no new dependencies (AVFoundation is built-in).

## Implementation Landscape

### Key Files

#### Android (`mobile/student_app_v2/`)
- `app/src/main/java/com/bankongseton/student/Models.kt` — add `jwtToken` field to `LoginResponse`; add `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` data classes
- `app/src/main/java/com/bankongseton/student/SecureStorage.kt` — add `saveJwtToken()` / `getJwtToken()` / `clearJwtToken()` methods (same EncryptedSharedPreferences pattern)
- `app/src/main/java/com/bankongseton/student/ApiClient.kt` — add `getQrCart()` and `confirmQrPayment()` to `BangkoApiService`; update `BASE_URL` note (endpoints are on `web_app.py` dashboard app, same base URL `/api/`)
- `app/src/main/java/com/bankongseton/student/LoginActivity.kt` — on login success, additionally call `secureStorage.saveJwtToken(loginResponse.jwtToken)` alongside existing `saveAuthToken(loginResponse.token)`
- `app/src/main/java/com/bankongseton/student/HomeActivity.kt` — replace `activateNfcPayButton` wiring with `qrPayButton`; always show QR Pay (no hardware check needed); launch `QRPayActivity`
- `app/src/main/java/com/bankongseton/student/QRPayActivity.kt` — **new file**; CameraX preview + ML Kit barcode scanning; on scan extracts token from URL, calls `getQrCart()`, shows cart items + total, confirms via `confirmQrPayment()`
- `app/src/main/res/layout/activity_home.xml` — rename/repurpose `activateNfcPayButton` → `qrPayButton`; remove `android:visibility="gone"` (always show); update icon and string reference
- `app/src/main/res/layout/activity_qr_pay.xml` — **new file**; camera preview + item list + confirm/cancel buttons
- `app/src/main/res/values/strings.xml` — add `action_qr_pay`, `qr_pay_scanning`, `qr_pay_confirm_title` strings
- `app/src/main/AndroidManifest.xml` — add `CAMERA` permission; add `QRPayActivity` declaration; add `uses-feature android:name="android.hardware.camera" android:required="false"`
- `app/build.gradle.kts` — add ML Kit barcode-scanning and CameraX dependencies

#### iOS (`mobile/ios/BankongSetonStudent/`)
- `Core/Network/APIEndpoints.swift` — add `static let qrCart = "/qr/"` and `static let qrConfirm = "/qr/confirm"`
- `Core/Network/APIClient.swift` — add `getQrCart(token:)` and `confirmQrPayment(token:)` methods; needs `jwtToken` (separate from session token — see Auth gap below)
- `Core/Auth/AuthManager.swift` — on `login(token:student:)`, also save the `jwtToken` to Keychain under `"jwt_token"` key
- `Models/LoginModels.swift` — add `jwtToken: String?` field to `LoginResponse` with `CodingKeys` mapping to `"jwt_token"`
- `Models/QRModels.swift` — **new file**; `QrCartResponse` (items, total, cashier), `QrCartItem`, `QrConfirmRequest`, `QrConfirmResponse`
- `Views/QR/QRPayView.swift` — **new file**; SwiftUI wrapper: opens scanner sheet, shows confirmation view
- `Views/QR/QRScannerView.swift` — **new file**; `UIViewControllerRepresentable` wrapping `AVCaptureSession` + `AVCaptureMetadataOutput` for QR code scanning
- `Views/QR/QRPayViewModel.swift` — **new file**; `@MainActor ObservableObject`; calls `getQrCart()` on token scan, `confirmQrPayment()` on confirm tap; handles 402/404/410 errors
- `Views/Home/HomeView.swift` — add "Pay with QR" button (NavigationLink or sheet trigger) — always visible (no NFC availability check needed)
- `ViewModels/LoginViewModel.swift` — on login success, calls `authManager.login(token:student:jwtToken:)` or reads `response.jwtToken` directly
- `BankongSetonStudent.xcodeproj/project.pbxproj` — add all new Swift files to `PBXBuildFile` and `PBXFileReference` sections, and to the `PBXSourcesBuildPhase`

### Critical Auth Gap (must fix first)

The `/api/qr/<token>` and `/api/qr/confirm` endpoints on `web_app.py` (Flask dashboard, port same as cashier) decode a **Bearer JWT** issued by `api_server.py` using `_decode_student_jwt()` with `_jwt_secret = os.getenv("JWT_SECRET")`. This is distinct from the session `token` (a `secrets.token_urlsafe(32)` opaque string) that the apps currently store.

Login response from `api_server.py` already returns both:
```json
{
  "token": "<opaque-session-token>",
  "jwt_token": "<HS256-JWT-signed-with-JWT_SECRET>",
  "student": { ... }
}
```

**Android fix:** Add `@SerializedName("jwt_token") val jwtToken: String` to `LoginResponse`. In `LoginActivity.onResponse`, call `secureStorage.saveJwtToken(loginResponse.jwtToken)`. Use `"Bearer ${secureStorage.getJwtToken()}"` as the Authorization header in QR calls.

**iOS fix:** Add `jwtToken: String?` to `LoginResponse` with `CodingKeys` `"jwt_token"`. In `AuthManager.login()`, save `jwtToken` under key `"jwt_token"`. In `APIClient`, add a `jwtToken` computed property that reads `KeychainHelper.read(forKey: "jwt_token")` and use it (not `token`) for QR endpoint requests.

The existing session token (`secureStorage.getAuthToken()` / `KeychainHelper.read(forKey: "auth_token")`) is used by all other endpoints on `api_server.py` — those are unaffected.

### Android: ML Kit + CameraX Setup

Current `app/build.gradle.kts` has no camera or barcode dependencies. Add:

```kotlin
// CameraX
implementation("androidx.camera:camera-core:1.3.1")
implementation("androidx.camera:camera-camera2:1.3.1")
implementation("androidx.camera:camera-lifecycle:1.3.1")
implementation("androidx.camera:camera-view:1.3.1")

// ML Kit Barcode Scanning (via firebase-bom already in project)
implementation("com.google.mlkit:barcode-scanning:17.2.0")
```

The `firebase-bom:32.7.0` is already declared — ML Kit barcode-scanning is independently versioned (not in the BOM), so pin it explicitly.

### QR Activity Flow (Android)

`QRPayActivity` lifecycle:
1. `onCreate` → request CAMERA permission if not granted; start CameraX preview + ML Kit analyzer
2. On QR scan → extract token from URL last path segment; stop preview; call `GET /api/qr/<token>` with JWT Bearer header
3. On 200 → switch UI to confirmation view: show items (RecyclerView or ListView), total, cashier name; show Confirm + Cancel buttons
4. On Confirm → call `POST /api/qr/confirm` with `{"token": "<token>"}`; show loading
5. On 200 → show success toast "Payment successful!"; `setResult(RESULT_OK)` with the transaction data; `finish()`
6. On 402 → show "Insufficient balance" dialog; finish (student must add balance)
7. On 404/410 → show "QR expired, ask cashier to regenerate" dialog; finish
8. On Cancel → `finish()` with `RESULT_CANCELED`

`HomeActivity` registers the result launcher: on `RESULT_OK`, refresh balance.

### QR View Flow (iOS)

`QRPayView` → sheet presenting `QRScannerView`:
1. `QRScannerView` is a `UIViewControllerRepresentable` with a `Coordinator : NSObject, AVCaptureMetadataOutputObjectsDelegate` that calls `didFindCode(_ code: String)` on the presenting view model when a valid URL is detected
2. `QRPayViewModel` receives the URL string, extracts the token, calls `apiClient.getQrCart(token:)`
3. On success → dismiss scanner sheet; show inline confirmation: items list, total, cashier, Confirm + Cancel buttons
4. Confirm taps `confirmQrPayment(token:)` → on success, navigate to ReceiptView (or show inline success state) and pop
5. Handle 402 (insufficient funds), 404/410 (expired), network errors with specific messages

`HomeView` adds a "Pay with QR" Button in the balance card area (or a new quick-action row). The button is always visible — no `nfcManager.isNfcAvailable()` gate needed.

### iOS Project File Update

New Swift files must be added to `project.pbxproj` manually (the project file at `BankongSetonStudent.xcodeproj/project.pbxproj`). The existing file uses sequential IDs (`AA000001`/`BB000001` pattern). The next free pair is `AA000026`/`BB000026`. Add entries for:
- `QRModels.swift`
- `QRPayView.swift`
- `QRScannerView.swift`
- `QRPayViewModel.swift`

Each needs: PBXBuildFile entry, PBXFileReference entry, PBXGroup child, and PBXSourcesBuildPhase child.

### Camera Permission (iOS)

Add `NSCameraUsageDescription` to the iOS Info.plist (or directly in the Xcode project settings). The existing project has no `Info.plist` separate from the build settings, so add it in the `project.pbxproj` under `INFOPLIST_FILE` — or add an `Info.plist` file. Check the existing project structure first; if the xcodeproj has `GENERATE_INFOPLIST_FILE = YES`, the key needs to go in `project.pbxproj` under `INFOPLIST_KEY_NSCameraUsageDescription`.

### Cart Item Shape

`GET /api/qr/<token>` returns:
```json
{
  "items": [{"name": "...", "price": 12.0, "qty": 2}, ...],
  "total": 24.0,
  "cashier": "cashier01"
}
```
This matches the existing `TransactionItem` model in both apps (Android `data class TransactionItem(name, price, qty)`; iOS `struct TransactionItem: Codable` with same fields). Reuse for display — no new model needed for items. Do add `QrCartResponse` wrapper and `QrConfirmRequest`/`QrConfirmResponse` models.

### Verification Approach

Create `scripts/verify-m005-s04.sh` with checks:
1. `grep -q 'QRPayActivity'` in `AndroidManifest.xml`
2. `grep -q 'barcode-scanning'` in `app/build.gradle.kts`
3. `grep -q 'jwtToken'` in `mobile/student_app_v2/.../Models.kt`
4. `grep -q 'saveJwtToken'` in `SecureStorage.kt`
5. `grep -q 'getQrCart\|confirmQrPayment'` in `ApiClient.kt`
6. `grep -q 'QRPayView'` in iOS `HomeView.swift`
7. `grep -q 'jwtToken'` in iOS `LoginModels.swift`
8. `grep -q 'getQrCart\|confirmQrPayment'` in iOS `APIClient.swift`
9. `grep -q 'AVCaptureMetadataOutput'` in `QRScannerView.swift`
10. `grep -q 'barcode-scanning\|QRPayActivity' ...` (cross-check)

Build verification: `./gradlew assembleDebug` on Android (exit 0); `xcodebuild -scheme BankongSetonStudent -sdk iphonesimulator build` on iOS (exit 0). End-to-end integration deferred to UAT.

### Build Order

1. **Fix JWT storage first** (Models.kt + SecureStorage.kt + LoginActivity.kt on Android; LoginModels.swift + AuthManager.swift on iOS) — both QR API calls are blocked until the JWT is stored and sent correctly
2. **Android QR Activity** — new files QRPayActivity.kt + activity_qr_pay.xml + build.gradle.kts deps + AndroidManifest.xml + HomeActivity.kt wiring
3. **iOS QR Views** — new files QRModels.swift + QRPayViewModel.swift + QRScannerView.swift + QRPayView.swift + project.pbxproj registration + HomeView.swift button + APIClient.swift + APIEndpoints.swift
4. **Verify script** — scripts/verify-m005-s04.sh

Steps 2 and 3 are parallel (different codebases).

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Android QR/barcode scanning | ML Kit `BarcodeScanning.getClient()` + `BarcodeScannerOptions` | Already decided (D045); firebase-bom in deps; no ZXing XML parsing needed |
| iOS QR scanning | `AVCaptureMetadataOutput` + `AVMetadataObjectTypeQRCode` | Built-in; decided (D046); zero new dependencies |
| Android camera preview | CameraX `PreviewView` | Modern API; lifecycle-aware; avoids Camera2 boilerplate |
| Android item display in QR activity | Existing `item_receipt_line.xml` layout | Already exists with name/qty/price TextViews — reuse for cart display |
| iOS item display | `List { ForEach(items) }` | Same pattern as TransactionsView/ReceiptView |

## Constraints

- `android:minSdk = 24` — CameraX 1.3.x supports minSdk 21; ML Kit barcode supports minSdk 21; no version conflict
- `targetSdk = 34` — CameraX + ML Kit fully support 34; no issues
- The `activateNfcPayButton` LinearLayout is `android:visibility="gone"` by default and only made visible when NFC is available. For QR, use the same slot (rename id to `qrPayButton`) and remove the `gone` default — QR is always available on any device
- iOS `LoginRequest` sends `pin` field but backend ignores it; do not change the login body — no breakage risk
- `/api/qr/*` routes are on `web_app.py` (dashboard Flask app, `https://juley2823.pythonanywhere.com/`), NOT on `api_server.py`. Both apps have `BASE_URL = "https://juley2823.pythonanywhere.com/api/"` which is correct — the QR endpoints are at `/api/qr/<token>` and `/api/qr/confirm`, both prefixed with `/api/` in `web_app.py`, so the same base URL works

## Common Pitfalls

- **Storing the wrong token for QR calls** — both apps currently store `loginResponse.token` (opaque session token for `api_server.py`). The QR endpoints need `loginResponse.jwt_token` (HS256 JWT for `web_app.py`). Sending the session token to `/api/qr/confirm` will always return 401. Fix: store `jwt_token` separately at login time.
- **Token in URL vs. token in POST body** — the scanned QR URL is `https://<server>/api/qr/<token>`. The app must extract the token from the last path segment and send it as `{"token": "<token>"}` in the `POST /api/qr/confirm` body. The URL itself is not the Bearer token.
- **CameraX lifecycle binding** — bind `ProcessCameraProvider` to `viewLifecycleOwner` (or activity lifecycle), not Application context, to avoid camera not releasing after QR confirm
- **ML Kit analyzer on non-main thread** — `ImageAnalysis.Builder().setBackpressureStrategy(STRATEGY_KEEP_ONLY_LATEST)` with executor; result callback must dispatch to main thread before updating UI
- **iOS `AVCaptureSession` must run on background thread** — call `session.startRunning()` / `session.stopRunning()` off the main queue; update UI state on `DispatchQueue.main`
- **project.pbxproj new file IDs** — must follow the existing `AA`/`BB` prefix pattern and increment correctly; incorrect IDs will cause Xcode to fail to find source files
- **402 vs other errors for insufficient funds** — the backend returns HTTP 402 (not 400/500) for insufficient balance; apps must branch on status code 402 specifically to show the right message (D054)

## Open Risks

- The iOS app login sends `pin` in the request body but the backend does not validate it. If the backend ever enforces the PIN field, iOS login will break (but this is outside S04 scope).
- `jwt_token` expiry: the JWT expires after 24 hours (`JWT_EXPIRY_HOURS = 24` in `api_server.py`). If a student is logged in for >24 hours without re-login, `GET /api/qr/<token>` will return 401. The app should handle 401 on QR calls by prompting re-login — same as other 401 flows.
- CameraX + ML Kit can add ~2-3 MB to the APK. With `isMinifyEnabled = true` and ProGuard, dead code is stripped. No action needed but worth noting for release APK size budgets.

## Sources

- S03 Forward Intelligence section (S03-SUMMARY.md) — JWT Bearer requirement for QR endpoints; cart response shape; 402/404/410 status codes; `{"token": ...}` confirm body
- M005-CONTEXT.md — D045 (ML Kit), D046 (AVFoundation), D044 (URL format), D054 (402 for insufficient funds)
