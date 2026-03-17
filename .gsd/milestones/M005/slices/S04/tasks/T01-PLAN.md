---
estimated_steps: 8
estimated_files: 9
---

# T01: Fix JWT token storage and add QR API client methods in both apps

**Slice:** S04 — Android + iOS App QR Pay
**Milestone:** M005

## Description

The `/api/qr/<token>` and `/api/qr/confirm` endpoints on `web_app.py` require `Authorization: Bearer <jwt_token>` — an HS256 JWT issued by `api_server.py`, distinct from the opaque session token the apps currently store. Neither app saves `jwt_token` from the login response. This task fixes that storage gap and adds the two QR API methods to each app's API client. It also adds CameraX + ML Kit dependencies to Android's build.gradle, which T02 needs to compile.

## Steps

### Android

1. **`Models.kt`** — add `@SerializedName("jwt_token") val jwtToken: String? = null` to `LoginResponse`. Also add three new data classes at the end of the file:
   ```kotlin
   data class QrCartItem(
       val name: String,
       val price: Double,
       val qty: Int = 1
   )
   data class QrCartResponse(
       val items: List<QrCartItem>,
       val total: Double,
       val cashier: String
   )
   data class QrConfirmRequest(
       val token: String
   )
   data class QrConfirmResponse(
       val message: String,
       @SerializedName("new_balance") val newBalance: Double
   )
   ```

2. **`SecureStorage.kt`** — add JWT token methods alongside the existing `saveAuthToken` / `getAuthToken` pattern. Add new constant `KEY_JWT_TOKEN = "jwt_token"` to the companion object. Add three methods:
   ```kotlin
   fun saveJwtToken(token: String) {
       sharedPreferences.edit().putString(KEY_JWT_TOKEN, token).apply()
   }
   fun getJwtToken(): String? {
       return sharedPreferences.getString(KEY_JWT_TOKEN, null)
   }
   fun clearJwtToken() {
       sharedPreferences.edit().remove(KEY_JWT_TOKEN).apply()
   }
   ```
   Also add `remove(KEY_JWT_TOKEN)` to the `clearAuth()` method's edit chain.

3. **`LoginActivity.kt`** — in `performLogin()`, inside the `response.body()?.let { loginResponse -> ... }` block, after `secureStorage.saveAuthToken(loginResponse.token)`, add:
   ```kotlin
   loginResponse.jwtToken?.let { secureStorage.saveJwtToken(it) }
   ```

4. **`ApiClient.kt`** (`BangkoApiService` interface) — add two new methods:
   ```kotlin
   @GET("qr/{token}")
   fun getQrCart(
       @Header("Authorization") bearerJwt: String,
       @Path("token") token: String
   ): Call<QrCartResponse>

   @POST("qr/confirm")
   fun confirmQrPayment(
       @Header("Authorization") bearerJwt: String,
       @Body request: QrConfirmRequest
   ): Call<QrConfirmResponse>
   ```
   Note: base URL is `https://juley2823.pythonanywhere.com/api/` — these paths are `qr/{token}` and `qr/confirm`, matching the `/api/qr/<token>` and `/api/qr/confirm` routes in `web_app.py`.

5. **`app/build.gradle.kts`** — in the `dependencies { }` block, after the Firebase section, add:
   ```kotlin
   // CameraX
   implementation("androidx.camera:camera-core:1.3.1")
   implementation("androidx.camera:camera-camera2:1.3.1")
   implementation("androidx.camera:camera-lifecycle:1.3.1")
   implementation("androidx.camera:camera-view:1.3.1")

   // ML Kit Barcode Scanning (independently versioned; not in firebase-bom)
   implementation("com.google.mlkit:barcode-scanning:17.2.0")
   ```

### iOS

6. **`Models/LoginModels.swift`** — add `jwtToken: String?` to `LoginResponse` with a `CodingKeys` mapping:
   ```swift
   struct LoginResponse: Codable {
       let token: String
       let student: Student
       let jwtToken: String?

       enum CodingKeys: String, CodingKey {
           case token
           case student
           case jwtToken = "jwt_token"
       }
   }
   ```

7. **`Core/Auth/AuthManager.swift`** — update `login(token:student:)` signature to `login(token:student:jwtToken:)`. Inside the function body, save the JWT token:
   ```swift
   func login(token: String, student: Student, jwtToken: String? = nil) {
       KeychainHelper.save(token, forKey: "auth_token")
       if let jwt = jwtToken {
           KeychainHelper.save(jwt, forKey: "jwt_token")
       }
       // ... rest of existing body unchanged ...
   }
   ```
   Also add `"jwt_token"` to the `keysToDelete` array in `clearAll()`.

8. **`Core/Network/APIEndpoints.swift`** — add:
   ```swift
   static let qrCart = "/qr/"          // append token: /qr/<token>
   static let qrConfirm = "/qr/confirm"
   ```

9. **`Core/Network/APIClient.swift`** — add a `jwtToken` computed property and two new API methods:
   ```swift
   private var jwtToken: String? { KeychainHelper.read(forKey: "jwt_token") }

   private func jwtRequest(
       path: String,
       method: String = "GET",
       body: Data? = nil
   ) throws -> URLRequest {
       guard let url = URL(string: APIEndpoints.baseURL + path) else {
           throw APIError.invalidURL
       }
       var request = URLRequest(url: url)
       request.httpMethod = method
       request.setValue("application/json", forHTTPHeaderField: "Content-Type")
       if let jwt = jwtToken {
           request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
       }
       request.httpBody = body
       return request
   }

   func getQrCart(token: String) async throws -> QrCartResponse {
       let req = try jwtRequest(path: APIEndpoints.qrCart + token)
       return try await perform(req)
   }

   func confirmQrPayment(token: String) async throws -> QrConfirmResponse {
       let body = QrConfirmRequest(token: token)
       let bodyData = try encoder.encode(body)
       let req = try jwtRequest(path: APIEndpoints.qrConfirm, method: "POST", body: bodyData)
       return try await perform(req)
   }
   ```
   The `perform<T>` function already handles 402 as `httpError(402)` — no changes needed there. The caller (`QRPayViewModel`, built in T03) will branch on 402.

   Also add `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` model structs — either in `APIClient.swift` below the `BudgetSummaryResponse` struct, or by creating `Models/QRModels.swift` in T03. Prefer creating `QRModels.swift` in T03 — just ensure the types are declared before they are used. If putting them in `APIClient.swift`, add them at the bottom of the file now.

   **Recommended:** put the QR model structs in `Models/QRModels.swift` (T03 creates this file). In T01 just declare the method signatures referencing the types by name — they will be in the same module so Swift will resolve them at compile time.

10. **`ViewModels/LoginViewModel.swift`** — in the `login()` function, update the call to `authManager.login`:
    ```swift
    authManager.login(token: response.token, student: response.student, jwtToken: response.jwtToken)
    ```

## Must-Haves

- [ ] `LoginResponse` in `Models.kt` has `jwtToken: String?` mapped via `@SerializedName("jwt_token")`
- [ ] `SecureStorage.kt` has `saveJwtToken()`, `getJwtToken()`, `clearJwtToken()`; `clearAuth()` also clears jwt token
- [ ] `LoginActivity.kt` calls `secureStorage.saveJwtToken(it)` on login success
- [ ] `BangkoApiService` in `ApiClient.kt` has `getQrCart()` and `confirmQrPayment()` methods
- [ ] `app/build.gradle.kts` has `camera-core:1.3.1`, `camera-camera2:1.3.1`, `camera-lifecycle:1.3.1`, `camera-view:1.3.1`, `barcode-scanning:17.2.0`
- [ ] iOS `LoginResponse` has `jwtToken: String?` with CodingKey `"jwt_token"`
- [ ] iOS `AuthManager.login()` saves jwtToken to Keychain under key `"jwt_token"`; `clearAll()` deletes it
- [ ] iOS `APIClient` has `jwtRequest()`, `getQrCart(token:)`, `confirmQrPayment(token:)` methods
- [ ] iOS `APIEndpoints` has `qrCart` and `qrConfirm` static strings
- [ ] iOS `LoginViewModel` passes `jwtToken: response.jwtToken` to `authManager.login()`

## Verification

```bash
# Android: check Models.kt has jwtToken
grep -q 'jwtToken' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt && echo "OK: Models.kt"

# Android: check SecureStorage has saveJwtToken
grep -q 'saveJwtToken' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt && echo "OK: SecureStorage.kt"

# Android: check build.gradle has barcode-scanning
grep -q 'barcode-scanning' mobile/student_app_v2/app/build.gradle.kts && echo "OK: build.gradle.kts"

# Android: check ApiClient has getQrCart
grep -q 'getQrCart\|confirmQrPayment' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt && echo "OK: ApiClient.kt"

# iOS: check LoginModels has jwtToken
grep -q 'jwtToken' mobile/ios/BankongSetonStudent/Models/LoginModels.swift && echo "OK: LoginModels.swift"

# iOS: check AuthManager saves jwt_token
grep -q 'jwt_token' mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift && echo "OK: AuthManager.swift"

# iOS: check APIClient has getQrCart
grep -q 'getQrCart\|confirmQrPayment' mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift && echo "OK: APIClient.swift"
```

## Observability Impact

- Signals added: `SecureStorage.getJwtToken()` returns non-null after login → confirms JWT is stored; nil → login didn't save it (check `loginResponse.jwtToken` is non-null from server; verify `api_server.py` login response includes `jwt_token`)
- How a future agent inspects this: `adb shell` + read EncryptedSharedPreferences is not feasible, but placing a debug log `Log.d("JWT", "jwt_token present: ${secureStorage.getJwtToken() != null}")` in `HomeActivity.onCreate` can confirm storage; for iOS, add `print("jwt_token stored: \(KeychainHelper.read(forKey: "jwt_token") != nil)")` in `AuthManager.login`

## Inputs

- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — add `jwtToken` to `LoginResponse`; add 4 new data classes
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt` — add JWT methods
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt` — save JWT on login
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — add 2 API methods
- `mobile/student_app_v2/app/build.gradle.kts` — add 5 new dependencies
- `mobile/ios/BankongSetonStudent/Models/LoginModels.swift` — add `jwtToken` field + CodingKeys to `LoginResponse`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — update `login()` to save JWT; update `clearAll()`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — add `jwtRequest()`, `getQrCart()`, `confirmQrPayment()`
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` — add `qrCart` and `qrConfirm`
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift` — pass `jwtToken` to `authManager.login()`
- S03 forward intelligence: `jwt_token` is in login response; `/api/qr/<token>` returns `{items, total, cashier}`; `/api/qr/confirm` body is `{"token": "<token>"}`; 402 = insufficient funds; 5-minute expiry

## Expected Output

- `Models.kt` has `jwtToken: String? = null` in `LoginResponse` and 4 new QR data classes
- `SecureStorage.kt` has `saveJwtToken`, `getJwtToken`, `clearJwtToken`; `clearAuth()` also clears JWT
- `LoginActivity.kt` saves JWT on login success
- `ApiClient.kt` `BangkoApiService` interface has `getQrCart` and `confirmQrPayment` methods
- `app/build.gradle.kts` has CameraX 1.3.1 (4 artifacts) and ML Kit barcode-scanning 17.2.0
- `LoginModels.swift` `LoginResponse` has `jwtToken: String?` with CodingKeys
- `AuthManager.swift` saves `jwt_token` to Keychain; clears it on logout
- `APIClient.swift` has `jwtRequest()` helper and two QR methods
- `APIEndpoints.swift` has `qrCart` and `qrConfirm`
- `LoginViewModel.swift` passes `jwtToken` on login
