# Student App

## Overview

The BankongSeton Student App is an Android application written in Kotlin. It allows students to check their canteen card balance, view transaction history, and receive push notifications when their balance is low. Authentication is done with a student ID; no password is required.

The app communicates with the BankongSeton API server (Flask, port 5001) over HTTP. Currency is Thai Baht (฿) throughout.

---

## Architecture

### Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Kotlin |
| HTTP client | Retrofit 2 + OkHttp (30 s timeouts) |
| JSON parsing | Gson |
| Auth token storage | EncryptedSharedPreferences (`androidx.security.crypto`) |
| Push notifications | Firebase Cloud Messaging (FCM) |
| Currency | Thai Baht (฿) |
| Min SDK | Modern Android (API 23+) |

### Project Structure

| File | Purpose |
|------|---------|
| `ApiClient.kt` | Retrofit singleton; `BangkoApiService` interface; **BASE_URL hardcoded here** |
| `Models.kt` | All Retrofit request/response data classes (DTOs) |
| `SecureStorage.kt` | EncryptedSharedPreferences wrapper — stores auth token, student ID, dark mode preference, last balance |
| `LoginActivity.kt` | Student ID login screen; saves session token; registers FCM token after login |
| `HomeActivity.kt` | Balance display; swipe-to-refresh; navigates to Transactions and Settings |
| `TransactionsActivity.kt` | Paginated transaction history with infinite scroll |
| `TransactionsAdapter.kt` | RecyclerView adapter; color-codes amounts; tapping a Purchase row opens ReceiptActivity |
| `ReceiptActivity.kt` | Itemized receipt for a single Purchase transaction |
| `SettingsActivity.kt` | Dark mode toggle; logout button (calls `POST /api/auth/logout`) |
| `FCMService.kt` | Handles incoming FCM messages; shows system notifications |
| `MainActivity.kt` | Entry point; redirects to LoginActivity or HomeActivity based on login state |

---

## Configuration

### API Server URL

> ⚠️ **IMPORTANT:** The API server URL is hardcoded in `ApiClient.kt`. You **must** change it before building for a new deployment.

```kotlin
// ApiClient.kt line 38
private const val BASE_URL = "http://192.168.68.104:5001/api/"
```

Replace `192.168.68.104` with your server's actual IP address and port. **Do not use `localhost` or `127.0.0.1`** — on an Android device these refer to the device itself, not the backend PC.

| Environment | Example BASE_URL |
|-------------|-----------------|
| Local WiFi (physical phone) | `http://192.168.1.100:5001/api/` |
| Android Emulator | `http://10.0.2.2:5001/api/` |
| Production | `https://api.bankongseton.com/api/` |

For detailed steps on finding your server IP, see `mobile/student_app_v2/BASE_URL_SETUP.md`.

After changing `BASE_URL`, rebuild the app:
```bash
cd mobile/student_app_v2
gradlew clean assembleDebug
```

### Firebase Setup

Push notifications require Firebase Cloud Messaging. The `google-services.json` in the repository is configured for the original development environment and **will not work for a new deployment**.

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Add an Android app with package name `com.bankongseton.student`
3. Download `google-services.json` and place it at `mobile/student_app_v2/app/google-services.json` (replace the existing file)
4. Ensure `google-services` plugin is applied in `app/build.gradle`

---

## Screens

### Login Screen (`LoginActivity`)

**Purpose:** Authenticate the student with their student ID.

**Flow:**
1. Student enters their student ID
2. App calls `POST /api/auth/login` with `{ "student_id": "..." }`
3. On success: session token and student ID are saved to EncryptedSharedPreferences via `SecureStorage`
4. If an FCM token was previously cached in `SharedPreferences` (key `fcm_token`), it is registered via `POST /api/users/fcm-token` — this call is **fire-and-forget** (silent success and silent failure; login is not blocked by this call)
5. App navigates to Home Screen

**Validation:**
- Empty student ID shows inline error: "Student ID required"
- Login button and input are disabled while request is in flight

---

### Home Screen (`HomeActivity`)

**Purpose:** Show the student's current canteen card balance.

**Flow:**
- Calls `GET /api/student/balance` on create and on swipe-to-refresh
- Balance is displayed as `฿250.00` (Thai Baht, 2 decimal places)
- On load failure: falls back to the last cached balance (stored in EncryptedSharedPreferences as a `Float`; `-1f` sentinel means "no cached value")
- Shows a Snackbar error if the API call fails
- Navigation buttons: **Transaction History** (→ `TransactionsActivity`), **Settings** (→ `SettingsActivity`)
- Manual refresh icon in addition to swipe-to-refresh

---

### Transaction History (`TransactionsActivity`)

**Purpose:** Show a paginated list of all transactions for the logged-in student.

**Flow:**
- Calls `GET /api/student/transactions?limit=20&offset=0` on load
- Infinite scroll: when the user scrolls within 4 rows of the bottom, the next page is fetched with `offset += 20` (page size = 20)
- Empty state: shows "No transactions yet" if the list is empty
- Tapping a **Purchase** row navigates to `ReceiptActivity` (passing the transaction as JSON in an Intent extra)
- Tapping a **Top-Up** or other transaction type does nothing (not clickable)

**Row display:**
- Transaction type (e.g., `Purchase`, `Top-Up`, `NFC Purchase`)
- Timestamp
- Amount — red for Purchase, green for Top-Up, default color for other types (e.g., NFC Purchase)
- Running balance after the transaction

---

### Receipt Screen (`ReceiptActivity`)

**Purpose:** Show an itemized receipt for a single Purchase transaction.

**Launched from:** Tapping a `Purchase` row in Transaction History (via `transaction_json` Intent extra).

> **Note: `NFC Purchase` transactions do not launch the Receipt screen.** The `TransactionsAdapter` only launches `ReceiptActivity` for rows where `type.equals("Purchase", ignoreCase = true)`. NFC Purchase rows are not clickable. This is a known limitation — NFC Purchase receipt navigation is not yet implemented.

**Displays:**
- Date (formatted as `dd MMM yyyy`)
- Time (formatted as `HH:mm`)
- Total amount: `฿<amount>`
- Balance before transaction: `฿<balanceBefore>`
- Balance after transaction: `฿<balance>`
- Line items (from `Transaction.items`): item name, unit price (฿), quantity (×N), line total (฿)

---

### Settings Screen (`SettingsActivity`)

**Purpose:** App preferences and logout.

**Features:**
- **Dark mode toggle** — persisted in EncryptedSharedPreferences; applies immediately via `AppCompatDelegate`
- **Logout button** — calls `POST /api/auth/logout` (removes session from backend's `active_sessions` dict), then clears local auth data and returns to Login Screen. Local data is cleared even if the server call fails.

---

## Authentication

The app uses **session token auth** — not JWT.

| Step | Detail |
|------|--------|
| Login | `POST /api/auth/login` with `{ "student_id": "..." }` |
| Response | `{ "token": "...", "student": { ... } }` — the `token` is a **session token** |
| Storage | Session token stored in EncryptedSharedPreferences (`bangko_secure_prefs`, key `auth_token`) |
| API calls | All requests include `Authorization: Bearer <session_token>` header |
| Logout | `POST /api/auth/logout` — removes the session from the backend's in-memory `active_sessions` dict |

> **Do not send the session token to NFC endpoints** (`POST /api/nfc/register` uses the same session token, but `POST /api/nfc/pay` requires a **cashier JWT** and `X-Device-Token` header — see [NFC Integration Guide](nfc-integration-guide.md)).

---

## Push Notifications (FCM)

`FCMService.kt` handles Firebase Cloud Messaging:

- **`onNewToken`:** When FCM assigns a new token to the device, it is saved to plain (non-encrypted) `SharedPreferences` (`bangko_prefs`, key `fcm_token`). It will be registered with the backend on the next login.
- **`onMessageReceived`:** Displays the notification message as a system notification using `NotificationCompat`. Notification channel ID: `bangko_notifications`. Tapping the notification opens `MainActivity`.
- **Backend trigger:** The backend sends low-balance FCM notifications after a transaction reduces the student's balance below the configured threshold in the Settings Google Sheet.
- **FCM token registration:** Handled in `LoginActivity` after successful login — fire-and-forget (does not block login if it fails).

---

## Data Models

Defined in `Models.kt`:

### `LoginRequest`
```kotlin
data class LoginRequest(
    @SerializedName("student_id") val studentId: String
)
```

### `LoginResponse`
```kotlin
data class LoginResponse(
    val token: String,      // session token (NOT JWT)
    val student: Student
)

data class Student(
    val id: String,
    val name: String,
    @SerializedName("id_card") val idCard: String,
    @SerializedName("money_card") val moneyCard: String,
    val status: String
)
```

### `Balance`
```kotlin
data class Balance(
    val balance: Double,
    @SerializedName("money_card") val moneyCard: String
)
```

### `TransactionsResponse`
```kotlin
data class TransactionsResponse(
    val transactions: List<Transaction>,
    val count: Int,
    val total: Int? = null,
    @SerializedName("has_more") val hasMore: Boolean? = null
)
```

### `Transaction`
```kotlin
data class Transaction(
    val timestamp: String,
    val type: String,           // e.g. "Purchase", "Top-Up", "NFC Purchase"
    val amount: Double,
    val balance: Double,        // balance AFTER transaction
    @SerializedName("balance_before") val balanceBefore: Double = 0.0,
    val description: String,
    val items: List<TransactionItem>? = null   // present for Purchase/NFC Purchase
)
```

### `TransactionItem`
```kotlin
data class TransactionItem(
    val name: String,
    val price: Double,
    val qty: Int = 1
)
```

### `FCMTokenRequest`
```kotlin
data class FCMTokenRequest(
    @SerializedName("fcm_token") val fcmToken: String
)
```

### `MessageResponse`
```kotlin
data class MessageResponse(
    val message: String
)
```

### `ErrorResponse`
```kotlin
data class ErrorResponse(
    val error: String
)
```

---

## API Calls Summary

All API calls use `Authorization: Bearer <session_token>`. Base URL is defined in `ApiClient.kt`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Login with student ID; returns session token |
| `POST` | `/api/auth/logout` | Invalidate session on backend |
| `GET` | `/api/student/balance` | Get current canteen card balance |
| `GET` | `/api/student/transactions?limit=20&offset=0` | Get transaction history (paginated) |
| `POST` | `/api/users/fcm-token` | Register FCM push token (fire-and-forget after login) |

See [API Reference](api-reference.md) for full request/response schemas and error codes.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Unable to resolve host" / network error on login | `BASE_URL` still points to the original dev IP | Change `BASE_URL` in `ApiClient.kt` to your server's IP; rebuild |
| Login fails for a valid student ID | Student not in Users sheet, or server not running | Verify student ID in Google Sheets; confirm API server is up on port 5001 |
| Balance shows as stale / not updating | API call failing; cached value displayed | Check API connectivity; pull down to swipe-refresh; verify backend is running |
| Balance shows incorrectly formatted or ₱ symbol | Old build with pre-Phase 4 code | Rebuild — the Thai Baht (฿) fix was applied in Phase 4 |
| Push notifications not arriving | FCM not configured, or FCM token not stored | Replace `google-services.json` with your own Firebase project file; ensure student has FCMToken in Users sheet |
| "Cleartext traffic not permitted" crash | Android blocking HTTP | Already handled via `android:usesCleartextTraffic="true"` in `AndroidManifest.xml`; see `BASE_URL_SETUP.md` if issue persists |
| App crashes on notification tap | `MainActivity` not found or missing | Ensure `MainActivity` is declared in `AndroidManifest.xml` |

See also: [API Reference](api-reference.md), [Setup Guide](setup.md).
