# NFC Integration Guide — BankongSeton v2 Android HCE

## Overview

This guide covers everything a future Android developer needs to implement NFC tap-to-pay in BankongSeton v2 without consulting the original author.

**What is HCE?** Host Card Emulation (HCE) lets an Android phone emulate a contactless smart card. When a student taps their phone at the cashier's NFC terminal, the terminal sends a SELECT AID command (APDU). The phone's `BankoHceService` responds with the student's virtual card tokens. The cashier POS software then calls the backend `/api/nfc/pay` endpoint to process the payment.

**What ships in v1 backend:**
- `POST /api/nfc/register` — Android calls this after login to get a virtual card token
- `POST /api/nfc/pay` — Cashier POS calls this after reading the NFC payload
- `VirtualCards` Google Sheet — stores one active virtual card per student

**What the Android developer builds in v2:**
1. `BankoHceService` (extends `HostApduService`) — responds to NFC SELECT AID
2. Registration flow — call `/api/nfc/register` after login, store tokens in `EncryptedSharedPreferences`
3. Payment flow is cashier-side — the phone only needs to respond to the NFC read

---

## Architecture & Token Flow

```
Android App                BankongSeton Backend         Google Sheets
     |                              |                         |
     |-- POST /api/nfc/register --->|                         |
     |   Authorization: Bearer      |                         |
     |   <session_token>            |                         |
     |                              |-- ensure_virtual_cards_sheet() -->|
     |                              |-- deactivate old row (if any) --> |
     |                              |-- append new VirtualCard row ---> |
     |<-- 200 { virtual_card_token, |                         |
     |   device_token, money_card,  |                         |
     |   message }                  |                         |
     |                              |                         |
     | (stores both tokens in EncryptedSharedPreferences)     |
     |                                                        |
[Student holds phone over NFC terminal]                      |
     |                                                        |
Cashier NFC Reader                                           |
     |-- APDU SELECT AID (F049494F4E41) ------------------>  |
     |<-- "virtual_card_token|device_token" UTF-8 + 0x9000 --+
     |                                                        |
Cashier POS Software                                         |
     |-- POST /api/nfc/pay --------------------------------->|
     |   Authorization: Bearer <cashier_jwt>                  |
     |   X-Device-Token: <device_token>                       |
     |   { virtual_card_token, items, total }                 |
     |                              |-- validate cashier JWT -->
     |                              |-- check X-Device-Token -------> VirtualCards sheet
     |                              |-- debit balance ----------------> Money Accounts
     |                              |-- log NFC Purchase row ---------> Transactions Log
     |<-- 200 { success: true,      |
     |   new_balance, timestamp }   |
```

**NFC payload format:** `"virtual_card_token|device_token"` — a pipe-delimited UTF-8 string. The cashier POS splits on `|` to extract both values. There is no JSON envelope.

---

## API Reference

### Base URL

Same server as all `/api/student/*` endpoints (port 5001 by default).

---

### POST /api/nfc/register

Register a virtual NFC card for the logged-in student. Call this after a successful login. Re-registration silently deactivates the previous virtual card.

**Authentication:** Session token from `POST /api/auth/login`  
```
Authorization: Bearer <session_token>
```
> **Important:** This endpoint uses session-token auth (same as `/api/student/*`), NOT a JWT. Do not send a JWT here.

**Request body:** None required. Student identity comes from the session token.

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
| `virtual_card_token` | string | UUID v4. What the NFC payload transmits (first half). |
| `device_token` | string | 44-char URL-safe random string. Sent as `X-Device-Token` header in pay requests (second half of NFC payload). |
| `money_card` | string | Student's RFID card UID (hex). For display/debugging. |
| `message` | string | Always `"Virtual card registered"` on success. |

**Error responses:**

| HTTP Status | JSON body | Cause | Resolution |
|-------------|-----------|-------|------------|
| 401 | `{"error": "Invalid or expired token"}` | Session token missing, expired, or not in active_sessions | Re-login via `POST /api/auth/login` |
| 403 | `{"error": "No money card registered"}` | Student has no RFID card linked in Money Accounts sheet | Admin must register RFID card for this student |
| 503 | `{"error": "Service unavailable, please try again"}` | Google Sheets API unreachable or unexpected error | Retry with exponential backoff |

---

### POST /api/nfc/pay

Process an NFC virtual card payment. Called by the **cashier POS software** after reading the NFC payload — the student Android app does not call this endpoint.

**Authentication:** Two headers required:
```
Authorization: Bearer <cashier_jwt_token>
X-Device-Token: <device_token>
```
- `Authorization` — cashier's JWT (role: `cashier` or `admin`), obtained from cashier login
- `X-Device-Token` — the `device_token` from the NFC payload (second part after `|`)

**Request body:**
```json
{
  "virtual_card_token": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {"name": "Burger", "qty": 1, "price": 55.00},
    {"name": "Juice", "qty": 2, "price": 25.00}
  ],
  "total": 105.00
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `virtual_card_token` | string | Yes | UUID from the NFC payload (first part before `\|`) |
| `items` | array | Yes | Array of item objects. Each must have `name`, `qty`, `price`. |
| `total` | float | Yes | Must be > 0. Must match sum of items (validated by POS, not backend). |

**Success response — HTTP 200:**
```json
{
  "success": true,
  "new_balance": 245.50,
  "timestamp": "2026-02-28 10:30:45"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` on success. |
| `new_balance` | float | Student's balance after deduction (in Thai Baht). |
| `timestamp` | string | Transaction time in Asia/Manila timezone, format `YYYY-MM-DD HH:MM:SS`. |

**Error responses:**

| HTTP Status | JSON body | Cause | Resolution |
|-------------|-----------|-------|------------|
| 400 | `{"error": "Invalid transaction data"}` | Missing `virtual_card_token`, empty `items`, or `total` ≤ 0 | Check request body format |
| 401 | `{"error": "No token provided"}` | Missing `Authorization` header | Send cashier JWT in Authorization header |
| 401 | `{"error": "Invalid or expired token"}` | Bad or expired cashier JWT | Re-authenticate cashier |
| 401 | `{"error": "X-Device-Token header required"}` | Missing `X-Device-Token` header | Include X-Device-Token extracted from NFC payload |
| 401 | `{"error": "Invalid virtual card token or device token"}` | Token mismatch, inactive card, or wrong device token | Student must re-register; old card was replaced |
| 400 | `{"error": "Insufficient funds", "balance": 15.00}` | Student balance below `total` | Show `balance` value to student |
| 503 | `{"error": "Service unavailable, please try again"}` | Google Sheets API unreachable or unexpected error | Retry with exponential backoff |

---

## Android Implementation Guide

### 4.1 Android Manifest Entries

Add inside the `<application>` tag in `AndroidManifest.xml`:

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

Create `res/xml/apdu_service.xml`:

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

> **AID:** `F049494F4E41` is a custom AID (not a payment AID). The cashier NFC reader hardware must be configured to SELECT this AID. It does not conflict with Visa/Mastercard AIDs.

---

### 4.2 BankoHceService.kt

Copy-paste ready Kotlin. Place in `app/src/main/java/com/example/bankongseton/nfc/BankoHceService.kt`:

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

**Gradle dependencies** (add to `app/build.gradle`):
```groovy
implementation "androidx.security:security-crypto:1.1.0-alpha06"
```

---

### 4.3 Registration API Call (Kotlin)

Call this after a successful login. Stores both tokens securely for later NFC reads.

```kotlin
// Retrofit interface
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
        // Use the session_token from POST /api/auth/login, NOT a JWT
    )
    if (response.isSuccessful) {
        val body = response.body()!!
        // Store both tokens securely — these are read by BankoHceService
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
        // Handle error — see error table for /api/nfc/register
    }
}
```

---

### 4.4 Payment Flow (Cashier POS → Backend)

The Android app is **passive** during payment. The cashier's NFC reader reads the phone and the POS software calls the backend. The Android developer does not need to build this side, but it is documented here for completeness.

1. Cashier NFC reader sends APDU SELECT AID `F049494F4E41`
2. Phone's `BankoHceService.processCommandApdu()` responds with `"virtual_card_token|device_token"` as UTF-8 bytes + `0x9000`
3. Cashier POS splits the payload on `|`:
   - Part 1 → `virtual_card_token` (goes in request body)
   - Part 2 → `device_token` (goes in `X-Device-Token` header)
4. Cashier POS sends `POST /api/nfc/pay`:
   ```
   Authorization: Bearer <cashier_jwt>
   X-Device-Token: <device_token>
   Content-Type: application/json

   {
     "virtual_card_token": "<part_1>",
     "items": [{"name": "Lunch", "qty": 1, "price": 75.00}],
     "total": 75.00
   }
   ```
5. Backend responds with `{ "success": true, "new_balance": 225.00, "timestamp": "..." }`

---

## VirtualCards Google Sheet Schema

The backend creates this sheet automatically on first registration if it does not exist.

| Column | Header | Example Value | Notes |
|--------|--------|---------------|-------|
| A | `StudentID` | `2024-001` | FK to Users sheet |
| B | `VirtualCardToken` | `550e8400-e29b-...` | UUID v4; transmitted in NFC payload (first half) |
| C | `DeviceToken` | `abc123xyz...` | 44-char URL-safe random string; sent as X-Device-Token (second half) |
| D | `MoneyCardNumber` | `5F6E7D8C` | RFID UID linked to this student (from Money Accounts sheet) |
| E | `CreatedAt` | `2026-02-28T10:30:00+08:00` | Asia/Manila ISO timestamp |
| F | `IsActive` | `TRUE` | `FALSE` = deactivated (replaced by re-registration). Only `TRUE` rows are matched. |

---

## Important Notes for v2 Implementation

1. **No token expiry.** Tokens are valid until the student re-registers. Re-registration silently sets the old row's `IsActive` to `FALSE` and appends a fresh row.

2. **If `401 Invalid virtual card token or device token` after a valid registration:** the student has re-registered from another device (or logged in again and re-registered). The Android app must detect this and call `/api/nfc/register` again with the current session token.

3. **NFC payload format is `virtual_card_token|device_token` (pipe, no JSON).** Do not wrap in a JSON envelope. The pipe delimiter is what the cashier POS expects.

4. **Cashier hardware must support ISO 14443-4 (HCE/T=CL).** Existing RFID readers used for `MoneyCardNumber` reads use ISO 14443-3 (Mifare). NFC HCE requires the reader to also support ISO 14443-4. Verify with cashier hardware vendor.

5. **`TransactionType` in the Transactions Log is `NFC Purchase`** (not `Purchase`). This lets the Android transaction history screen distinguish NFC payments from RFID tap payments.

6. **Do NOT use `docs/NFC_IMPLEMENTATION.md` as a reference.** That document describes a superseded design (APDU-based PIN flow, biometric, `NFCPaymentManager`). The current design has no PIN, no biometrics, and uses `NFCService` (stateless).

7. **CORS header `X-Device-Token` is already allowed.** The backend Flask-CORS config includes `X-Device-Token` in `allow_headers`, so Android preflight OPTIONS requests will not be blocked.
