# NFC Integration Guide

## Overview

BankongSeton supports NFC payments via Android Host Card Emulation (HCE). When a student taps their phone at the cashier's NFC reader, the reader receives a virtual card token. The cashier POS software then calls the backend to process the payment.

**What is already built (backend, v1):**
- `POST /api/nfc/register` — student app calls this to get virtual card tokens after login
- `GET /api/nfc/status` — check if student has an active virtual card
- `POST /api/nfc/unregister` — deactivate the student's active virtual card
- `POST /api/nfc/pay` — cashier POS calls this after reading the NFC payload
- `VirtualCards` Google Sheet — stores one active virtual card per student

**What needs to be built (Android app, v2):**
- `BankoHceService` (extends `HostApduService`) — responds to NFC SELECT AID APDU
- Registration flow — call `/api/nfc/register` after login, store tokens in `EncryptedSharedPreferences`
- The payment flow is cashier-side only; the phone only needs to respond to the NFC read

> **Note: NFC is not yet implemented in the Android app.** This guide is the specification for implementing it in v2. The backend API is complete and ready.

---

## How It Works

```
Android App                    BankongSeton Backend        Google Sheets
     |                                  |                        |
     |--- POST /api/nfc/register ------>|                        |
     |    Authorization: Bearer         |                        |
     |    <session_token>               |                        |
     |                                  |-- deactivate old row ->|
     |                                  |-- append VirtualCard ->|
     |<-- 200 { virtual_card_token,     |                        |
     |    device_token, money_card }    |                        |
     |                                  |                        |
     | (stores both tokens in EncryptedSharedPreferences)        |
     |                                                           |
[Student holds phone over NFC terminal]                         |
     |                                                           |
Cashier NFC Reader                                              |
     |--- APDU SELECT AID (F049494F4E41) ------------------->   |
     |<-- "virtual_card_token|device_token" UTF-8 + 0x9000 --+  |
     |                                                           |
Cashier POS Software                                            |
     |--- POST /api/nfc/pay --------------------------------->   |
     |    Authorization: Bearer <cashier_jwt>                    |
     |    X-Device-Token: <device_token>                         |
     |    { virtual_card_token, items, total }                   |
     |                                  |-- validate cashier JWT |
     |                                  |-- check X-Device-Token -> VirtualCards
     |                                  |-- debit balance -------> Money Accounts
     |                                  |-- log NFC Purchase ----> Transactions Log
     |<-- 200 { success: true,          |
     |    new_balance, timestamp }      |
```

**NFC payload format:** `"virtual_card_token|device_token"` — a pipe-delimited UTF-8 string. No JSON envelope. The cashier POS splits on `|` to get both values.

---

## NFC Registration

### Endpoint: `POST /api/nfc/register`

Call this after a successful student login. Re-registration silently deactivates the previous virtual card and creates a new one.

**Authentication:** Session Bearer token (same token from `POST /api/auth/login`).

```
Authorization: Bearer <session_token>
```

> **Important:** This endpoint uses **session token** auth, **not** a cashier JWT. Send the same token used for `/api/student/balance`.

**Request body:** None. Student identity comes from the session.

**Success response — HTTP 200:**
```json
{
  "virtual_card_token": "550e8400-e29b-41d4-a716-446655440000",
  "device_token": "abc123xyz_url_safe_44_char_string",
  "money_card": "5F6E7D8C",
  "message": "Virtual card registered"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `virtual_card_token` | string | UUID v4. First half of the NFC payload (before `\|`). |
| `device_token` | string | 44-char URL-safe random string. Second half of the NFC payload (after `\|`); also sent as `X-Device-Token` header by the cashier. |
| `money_card` | string | Student's RFID card UID (hex). For display/debug only. |
| `message` | string | Always `"Virtual card registered"` on success. |

**Error responses:**

| HTTP | Body | Cause | Fix |
|------|------|-------|-----|
| 401 | `{"error": "Invalid or expired token"}` | Session token missing or expired | Re-login |
| 403 | `{"error": "No money card registered"}` | Student has no RFID card linked in Money Accounts sheet | Admin must register student's RFID card first |
| 503 | `{"error": "Service unavailable, please try again"}` | Google Sheets unreachable | Retry with exponential backoff |

**Store tokens in EncryptedSharedPreferences** (key names: `virtual_card_token`, `device_token`) so `BankoHceService` can read them at NFC tap time.

---

## NFC Status

### Endpoint: `GET /api/nfc/status`

Check whether the student currently has an active virtual NFC card registered.

**Authentication:** Session Bearer token (same token from `POST /api/auth/login`).

```
Authorization: Bearer <session_token>
```

**Request body:** None.

**Success response — HTTP 200:**
```json
{
  "is_registered": true,
  "device_id": "abc123xyz_url_safe_44_char_string",
  "registered_at": "2026-03-01T14:32:00+08:00"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `is_registered` | boolean | `true` if the student has an active virtual card; `false` otherwise. |
| `device_id` | string \| null | The device token issued at registration. `null` when `is_registered` is `false`. |
| `registered_at` | string \| null | ISO 8601 timestamp of registration. `null` when `is_registered` is `false`. |

**Error responses:**

| HTTP | Body | Cause | Fix |
|------|------|-------|-----|
| 401 | `{"error": "Invalid or expired token"}` | Session token missing or expired | Re-login |
| 503 | `{"error": "Service unavailable, please try again"}` | Google Sheets unreachable | Retry with exponential backoff |

---

## NFC Unregister

### Endpoint: `POST /api/nfc/unregister`

Deactivate the student's current virtual NFC card. The card can no longer be used for payments after this call.

**Authentication:** Session Bearer token (same token from `POST /api/auth/login`).

```
Authorization: Bearer <session_token>
```

**Request body:**
```json
{
  "device_id": "abc123xyz_url_safe_44_char_string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_id` | string | yes | The device token stored at registration. |

**Success response — HTTP 200:**
```json
{
  "message": "Virtual card unregistered"
}
```

**Error responses:**

| HTTP | Body | Cause | Fix |
|------|------|-------|-----|
| 401 | `{"error": "Invalid or expired token"}` | Session token missing or expired | Re-login |
| 404 | `{"error": "No active virtual card found"}` | Student has no active virtual card | Nothing to unregister |
| 503 | `{"error": "Service unavailable, please try again"}` | Google Sheets unreachable | Retry with exponential backoff |

---

## HCE Implementation

### Application Identifier (AID)

The cashier's NFC reader sends a SELECT AID command to find the card emulation service. The AID for BankongSeton is:

```
F049494F4E41
```

This AID is a custom (non-payment) AID. The cashier NFC hardware must be configured to SELECT this AID. It does not conflict with Visa/Mastercard AIDs.

---

### AndroidManifest.xml

Add inside the `<application>` tag:

```xml
<!-- AndroidManifest.xml — add inside <application> tag -->
<uses-permission android:name="android.permission.NFC" />

<service
    android:name=".nfc.BankoHceService"
    android:exported="true"
    android:permission="android.permission.BIND_NFC_SERVICE">
    <intent-filter>
        <action android:name="android.nfc.cardemulation.action.HOST_APDU_SERVICE" />
        <category android:name="android.intent.category.DEFAULT" />
    </intent-filter>
    <meta-data
        android:name="android.nfc.cardemulation.host_apdu_service"
        android:resource="@xml/apdu_service" />
</service>
```

---

### res/xml/apdu_service.xml

Create this file at `app/src/main/res/xml/apdu_service.xml`:

```xml
<!-- res/xml/apdu_service.xml -->
<host-apdu-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:description="@string/app_name"
    android:requireDeviceUnlock="false">
    <aid-group
        android:description="@string/app_name"
        android:category="other">
        <aid-filter android:name="F049494F4E41"/>
    </aid-group>
</host-apdu-service>
```

---

### BankoHceService.kt

Place in `app/src/main/java/com/example/bankongseton/nfc/BankoHceService.kt`:

```kotlin
package com.example.bankongseton.nfc

import android.nfc.cardemulation.HostApduService
import android.os.Bundle
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys

class BankoHceService : HostApduService() {

    private val SELECT_AID_HEADER = byteArrayOf(0x00, 0xA4.toByte(), 0x04, 0x00)
    private val RESPONSE_OK = byteArrayOf(0x90.toByte(), 0x00)
    private val RESPONSE_UNKNOWN = byteArrayOf(0x6D, 0x00)

    override fun processCommandApdu(apdu: ByteArray, extras: Bundle?): ByteArray {
        // Respond only to SELECT AID command
        if (apdu.size >= 4 && apdu.sliceArray(0..3).contentEquals(SELECT_AID_HEADER)) {
            val payload = getStoredPayload() ?: return RESPONSE_UNKNOWN
            // NFC payload: "virtual_card_token|device_token" (pipe-delimited)
            // Cashier POS splits on '|' to extract both values
            return payload.toByteArray(Charsets.UTF_8) + RESPONSE_OK
        }
        return RESPONSE_UNKNOWN
    }

    override fun onDeactivated(reason: Int) {
        // no-op
    }

    /**
     * Returns "virtual_card_token|device_token" from EncryptedSharedPreferences.
     * Returns null if the student has not registered yet.
     */
    private fun getStoredPayload(): String? {
        val prefs = EncryptedSharedPreferences.create(
            "nfc_prefs",
            MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC),
            applicationContext,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        val token = prefs.getString("virtual_card_token", null) ?: return null
        val deviceToken = prefs.getString("device_token", null) ?: return null
        return "$token|$deviceToken"
    }
}
```

**Gradle dependency** (add to `app/build.gradle`):
```groovy
implementation "androidx.security:security-crypto:1.1.0-alpha06"
```

**What this does:**
- Extends `HostApduService` — Android calls `processCommandApdu()` when the NFC reader sends an APDU command
- Checks for the SELECT AID header (`00 A4 04 00`)
- Reads `virtual_card_token` and `device_token` from `EncryptedSharedPreferences`
- Returns `"virtual_card_token|device_token"` as UTF-8 bytes followed by `0x9000` (ISO 7816 success status word)
- Returns `0x6D00` (unknown command) if the AID is not recognised or tokens are not stored

---

## APDU Response Format

When the cashier reader sends SELECT AID `F049494F4E41`, the HCE service responds:

```
Response bytes: <virtual_card_token>|<device_token>  (UTF-8 encoded)
Status word:    0x90 0x00  (ISO 7816-4 "success")
```

The `|` character is the literal separator. There is no JSON envelope.

On error (tokens not stored, unrecognised command): respond with `0x6D 0x00`.

The cashier POS splits the response on `|`:
- Part 1 → `virtual_card_token` (goes into request body for `/api/nfc/pay`)
- Part 2 → `device_token` (goes into `X-Device-Token` header for `/api/nfc/pay`)

---

## NFC Registration API Call (Kotlin)

Call this after a successful login. Store the returned tokens for use by `BankoHceService`.

```kotlin
// Retrofit interface addition
interface BankoApiService {
    @POST("/api/nfc/register")
    suspend fun registerNfcCard(
        @Header("Authorization") authorization: String
        // No request body needed
    ): Response<NfcRegistrationResponse>
}

// Response data class
data class NfcRegistrationResponse(
    @SerializedName("virtual_card_token") val virtualCardToken: String,
    @SerializedName("device_token") val deviceToken: String,
    @SerializedName("money_card") val moneyCard: String,
    val message: String
)

// Call after successful login
suspend fun registerNfcCard(sessionToken: String, context: Context) {
    val response = apiService.registerNfcCard(
        authorization = "Bearer $sessionToken"
        // Use the session_token from POST /api/auth/login, NOT a cashier JWT
    )
    if (response.isSuccessful) {
        val body = response.body()!!
        // Store both tokens securely — BankoHceService reads these at NFC tap time
        val prefs = EncryptedSharedPreferences.create(
            "nfc_prefs",
            MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC),
            context,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        prefs.edit()
            .putString("virtual_card_token", body.virtualCardToken)
            .putString("device_token", body.deviceToken)
            .apply()
    } else {
        // Handle error — see error table for /api/nfc/register above
    }
}
```

---

## NFC Payment Endpoint

The Android app is **passive** during payment. The cashier's NFC reader reads the phone; the cashier POS software calls the backend. The Android developer does not build this side, but it is documented here for completeness.

### Endpoint: `POST /api/nfc/pay`

**Authentication:** Two headers required:
```
Authorization: Bearer <cashier_jwt_token>
X-Device-Token: <device_token>
```
- `Authorization` — cashier's JWT (role: `cashier` or `admin`), from cashier login
- `X-Device-Token` — the `device_token` extracted from the NFC payload (part after `|`)

**Request body:**
```json
{
  "virtual_card_token": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {"name": "Rice", "qty": 1, "price": 35.00},
    {"name": "Juice", "qty": 2, "price": 20.00}
  ],
  "total": 75.00
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `virtual_card_token` | string | Yes | UUID from NFC payload (part before `\|`) |
| `items` | array | Yes | Each item: `name`, `qty`, `price` |
| `total` | float | Yes | Must be > 0 |

**Success response — HTTP 200:**
```json
{
  "success": true,
  "new_balance": 225.00,
  "timestamp": "2026-03-01 10:30:45"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` on success |
| `new_balance` | float | Student's balance after deduction (Thai Baht) |
| `timestamp` | string | Transaction time, Asia/Manila timezone, `YYYY-MM-DD HH:MM:SS` |

**Error responses:**

| HTTP | Body | Cause | Fix |
|------|------|-------|-----|
| 400 | `{"error": "Invalid transaction data"}` | Missing `virtual_card_token`, empty `items`, or `total` ≤ 0 | Check request body |
| 401 | `{"error": "No token provided"}` | Missing `Authorization` header | Send cashier JWT |
| 401 | `{"error": "Invalid or expired token"}` | Bad or expired cashier JWT | Re-authenticate cashier |
| 401 | `{"error": "X-Device-Token header required"}` | Missing `X-Device-Token` header | Include device token from NFC payload |
| 401 | `{"error": "Invalid virtual card token or device token"}` | Token mismatch, inactive card, or wrong device token | Student must re-register |
| 400 | `{"error": "Insufficient funds", "balance": 15.00}` | Balance below `total` | Show remaining balance to student |
| 503 | `{"error": "Service unavailable, please try again"}` | Google Sheets unreachable | Retry with exponential backoff |

**Transaction type:** The backend logs this as `TransactionType='NFC Purchase'` (distinct from `'Purchase'`). This allows the Android app's transaction history screen to distinguish NFC payments from RFID tap payments.

---

## VirtualCards Google Sheet Schema

The backend creates this sheet automatically on the first `POST /api/nfc/register` call if it does not exist.

| Column | Header | Example | Notes |
|--------|--------|---------|-------|
| A | `StudentID` | `2024-001` | FK to Users sheet |
| B | `VirtualCardToken` | `550e8400-e29b-...` | UUID v4; first half of NFC payload |
| C | `DeviceToken` | `abc123xyz...` | 44-char URL-safe string; sent as `X-Device-Token` |
| D | `MoneyCardNumber` | `5F6E7D8C` | RFID UID linked to this student (from Money Accounts sheet) |
| E | `CreatedAt` | `2026-02-28T10:30:00+08:00` | Asia/Manila ISO timestamp |
| F | `IsActive` | `TRUE` | Only `TRUE` rows are matched. `FALSE` = deactivated by re-registration. |

---

## Security Considerations

- **Virtual card token** — server-generated UUID, stored in VirtualCards sheet. Not guessable.
- **Device token** — 44-char URL-safe random string generated server-side. Passed via `X-Device-Token` header, stored in VirtualCards sheet.
- **Dual auth on `/api/nfc/pay`** — requires both a valid cashier JWT (proves cashier identity) and `X-Device-Token` (proves phone identity). Both are required.
- **`IsActive` flag** — backend can deactivate a virtual card by setting `IsActive=FALSE` without touching the phone. Only active rows are matched.
- **No token expiry** — tokens are valid until the student re-registers. Re-registration silently sets the old row's `IsActive` to `FALSE` and appends a new row.
- **Shared money account** — physical RFID card and NFC virtual card share the same money account (`MoneyCardNumber` link in VirtualCards sheet).
- **CORS** — the `X-Device-Token` header is already included in the backend's Flask-CORS `allow_headers` config. Android preflight OPTIONS requests will not be blocked.

---

## Important Notes for v2 Implementation

1. **Token re-registration:** If a student re-registers (e.g., logs in on a new device), the old virtual card is deactivated. The Android app should call `/api/nfc/register` after every login to ensure the stored tokens are current.

2. **Handling `401 Invalid virtual card token or device token`:** This means the student re-registered from another device and the stored tokens are stale. Detect this error and call `/api/nfc/register` again with the current session token.

3. **NFC payload format is pipe-delimited, not JSON.** Do not wrap in a JSON envelope. The cashier POS splits on `|` to get both values.

4. **Cashier hardware must support ISO 14443-4 (HCE / T=CL).** Existing RFID readers used for Money Card reads use ISO 14443-3 (Mifare Classic). NFC HCE requires ISO 14443-4. Verify with your cashier hardware vendor before purchasing.

5. **`EncryptedSharedPreferences` file name:** `BankoHceService` reads from `"nfc_prefs"`. Your registration code must write to the same file name using the same encryption scheme.

6. **`TransactionType` for NFC is `NFC Purchase`**, not `Purchase`. The transaction history adapter checks for `Purchase` (exact, case-insensitive) to decide whether to show the receipt screen. NFC Purchase rows are currently not clickable — see `student-app.md` for details.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `POST /api/nfc/register` returns 401 | Session token missing or expired | Student must be logged in first; re-login |
| `POST /api/nfc/register` returns 403 "No money card registered" | Student has no RFID card in Money Accounts sheet | Admin must link an RFID card to the student first |
| NFC pay returns 401 "Invalid virtual card token or device token" | Student re-registered from another device; stored tokens stale | Call `/api/nfc/register` again; old card was deactivated |
| NFC pay returns 400 "Insufficient funds" | Student balance below transaction total | Display the `balance` field from the error response |
| APDU not recognised by cashier reader | AID in `apdu_service.xml` incorrect | Verify AID is exactly `F049494F4E41` (no spaces, uppercase hex) |
| Phone not responding to NFC tap | Tokens not stored or `BankoHceService` not registered | Check `EncryptedSharedPreferences` write in registration; verify manifest entries |
| `BankoHceService` returns `0x6D00` | Tokens not yet stored (student not registered) | Call `/api/nfc/register` after login before attempting NFC payment |

See also: [API Reference](api-reference.md), [Google Sheets Schema](google-sheets-schema.md).
