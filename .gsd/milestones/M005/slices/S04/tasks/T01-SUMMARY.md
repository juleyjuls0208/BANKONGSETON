---
id: T01
parent: S04
milestone: M005
provides:
  - JWT token storage in both Android and iOS apps
  - QR API client methods (getQrCart, confirmQrPayment) in both apps
  - CameraX 1.3.1 + ML Kit barcode-scanning 17.2.0 Android dependencies for T02
key_files:
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt
  - mobile/student_app_v2/app/build.gradle.kts
  - mobile/ios/BankongSetonStudent/Models/LoginModels.swift
  - mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift
  - mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
  - mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift
  - mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift
key_decisions:
  - QR model structs (QrCartResponse, QrConfirmRequest, QrConfirmResponse) deferred to T03's QRModels.swift per plan — same Swift module, compile-time resolved
patterns_established:
  - Android JWT storage follows same EncryptedSharedPreferences pattern as auth_token; clearAuth() now clears both
  - iOS JWT uses same KeychainHelper pattern as auth_token; clearAll() now deletes jwt_token key
  - iOS jwtRequest() is a parallel helper to authenticatedRequest() — same shape, reads from "jwt_token" keychain key instead of "auth_token"
observability_surfaces:
  - Android: Log.d("JWT","jwt stored: ${secureStorage.getJwtToken() != null}") in HomeActivity.onCreate confirms post-login storage
  - iOS: print("jwt stored: \(KeychainHelper.read(forKey:"jwt_token") != nil)") in AuthManager.login confirms post-login storage
  - 401 on QR endpoints → jwtToken is nil → check server login response includes jwt_token field
duration: 20m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T01: Fix JWT token storage and add QR API client methods in both apps

**Added jwtToken storage to Android (EncryptedSharedPreferences) and iOS (Keychain) login flows, wired getQrCart/confirmQrPayment API methods in both apps, and added CameraX 1.3.1 + ML Kit barcode-scanning 17.2.0 to Android build.gradle.kts.**

## What Happened

Both apps stored only the session token (`auth_token`) from the login response, dropping the `jwt_token` field that the `/api/qr/<token>` and `/api/qr/confirm` endpoints require. 

**Android changes:**
- `Models.kt`: Added `@SerializedName("jwt_token") val jwtToken: String? = null` to `LoginResponse`; added 4 new data classes: `QrCartItem`, `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse`
- `SecureStorage.kt`: Added `KEY_JWT_TOKEN` constant; added `saveJwtToken()`, `getJwtToken()`, `clearJwtToken()` methods; updated `clearAuth()` to also remove `KEY_JWT_TOKEN`
- `LoginActivity.kt`: After `saveAuthToken()`, calls `loginResponse.jwtToken?.let { secureStorage.saveJwtToken(it) }`
- `ApiClient.kt`: Added `getQrCart(@Header bearerJwt, @Path token)` and `confirmQrPayment(@Header bearerJwt, @Body request)` to `BangkoApiService` interface
- `app/build.gradle.kts`: Added camera-core, camera-camera2, camera-lifecycle, camera-view (all 1.3.1) and mlkit barcode-scanning 17.2.0

**iOS changes:**
- `LoginModels.swift`: Added `jwtToken: String?` to `LoginResponse` with `CodingKeys` mapping `jwt_token`
- `AuthManager.swift`: Updated `login()` signature to `login(token:student:jwtToken:=nil)`; saves JWT to Keychain under `"jwt_token"`; added `"jwt_token"` to `clearAll()` deletion list
- `APIEndpoints.swift`: Added `qrCart = "/qr/"` and `qrConfirm = "/qr/confirm"` static strings
- `APIClient.swift`: Added `jwtToken` computed property reading from Keychain; added `jwtRequest()` helper (parallel to `authenticatedRequest()`, uses jwt_token); added `getQrCart(token:)` and `confirmQrPayment(token:)` methods
- `LoginViewModel.swift`: Updated `authManager.login()` call to pass `jwtToken: response.jwtToken`

Note: `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` types referenced in `APIClient.swift` will be declared in `Models/QRModels.swift` by T03 — same Swift module, no forward-declaration needed.

## Verification

All 7 plan verification checks passed:

```
OK: Models.kt        — jwtToken present in LoginResponse + 4 QR data classes
OK: SecureStorage.kt — saveJwtToken method present
OK: build.gradle.kts — barcode-scanning dependency present
OK: ApiClient.kt     — getQrCart + confirmQrPayment declared
OK: LoginModels.swift — jwtToken field present
OK: AuthManager.swift — jwt_token keychain key present
OK: APIClient.swift  — getQrCart + confirmQrPayment methods present
```

Extended checks confirmed:
- `clearAuth()` removes `KEY_JWT_TOKEN` (3-key removal chain)
- All 5 CameraX/ML Kit deps present in build.gradle.kts
- iOS `jwtRequest()` helper correctly uses `jwtToken` computed property
- `LoginViewModel` passes `jwtToken: response.jwtToken` to `authManager.login()`

## Diagnostics

- **Android 401 on QR endpoints** → `getJwtToken()` returned null → add `Log.d("JWT","jwt stored: ${secureStorage.getJwtToken() != null}")` in `HomeActivity.onCreate` to confirm; if false, check server login response includes `jwt_token` field
- **iOS 401 on QR endpoints** → `KeychainHelper.read(forKey:"jwt_token")` is nil → add `print("jwt stored: \(KeychainHelper.read(forKey:"jwt_token") != nil)")` in `AuthManager.login` to confirm
- **JWT never arrives from server** → check `api_server.py` login response includes `jwt_token` key (S03 scope)

## Deviations

- `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` Swift types are referenced in `APIClient.swift` but not yet defined — this is the plan's recommended approach (T03 creates `Models/QRModels.swift`). The Swift compiler resolves same-module types at compile time, so no forward declaration stub is needed.

## Known Issues

- iOS build will not compile until T03 creates `Models/QRModels.swift` declaring the QR model types referenced in `APIClient.swift`. This is expected and documented in the plan.

## Files Created/Modified

- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — added `jwtToken` to `LoginResponse`; added 4 QR data classes
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt` — added JWT storage methods + constant; updated `clearAuth()`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt` — saves JWT token on successful login
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — added `getQrCart` and `confirmQrPayment` to `BangkoApiService`
- `mobile/student_app_v2/app/build.gradle.kts` — added CameraX 1.3.1 (4 artifacts) + ML Kit barcode-scanning 17.2.0
- `mobile/ios/BankongSetonStudent/Models/LoginModels.swift` — added `jwtToken: String?` with `CodingKeys` to `LoginResponse`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — updated `login()` to save JWT; added `jwt_token` to `clearAll()`
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` — added `qrCart` and `qrConfirm` endpoints
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — added `jwtToken` property, `jwtRequest()` helper, `getQrCart()`, `confirmQrPayment()`
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift` — passes `jwtToken` to `authManager.login()`
