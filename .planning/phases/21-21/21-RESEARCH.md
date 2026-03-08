# Phase 21: v1.1 Gap Closure + v1.2 Feature Implementation — Research

**Researched:** 2026-03-08
**Domain:** Full-stack (Python/Flask, Android/Kotlin, Arduino/C++, Google Sheets, Firebase FCM)
**Confidence:** HIGH (all findings are from direct code inspection of the live codebase)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Google Sheets remains the data store — no database migration
- Firebase FCM via Admin SDK (`firebase_admin`) for push notifications
- PythonAnywhere hosts the web-facing app (`web_app.py`); the local machine runs `admin_dashboard.py`
- Arduino UNO R3 + PN532 (SPI) is the target hardware; the new sketch is already at `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` (quick-2)
- SMS gateway = Twilio (pre-selected in CONTEXT.md)
- Bulk import = CSV upload, not a third-party ETL tool
- Parent portal stays in the `admin_dashboard.py` / `web_app.py` monolith — no separate service

### Claude's Discretion
- Low-balance email threshold value (suggest 50 THB as default, configurable via env var)
- CSV import field mapping details (canonical column order)
- Station-ID injection mechanism (header vs. query param vs. body field)
- Exact error message wording for new endpoints

### Deferred Ideas (OUT OF SCOPE)
- Full database migration away from Google Sheets
- Separate microservice architecture
- iOS app support
- Real-time SocketIO updates on the parent portal
</user_constraints>

---

## Summary

Phase 21 has two missions running in parallel: **v1.1 Gap Closure** (verify and fix NFCA-01 and PAR-01–06 end-to-end) and **v1.2 Feature Implementation** (Arduino R3 fix, dashboard web/local split, FCM background notifications, low-balance email, SMS via Twilio, bulk CSV student import, multi-canteen station support, production hardening).

Direct code inspection confirms that most v1.1 features are structurally present but have concrete, fixable gaps: the FCM token is never sent to the backend on login, `BankoHceService.currentToken` is not restored on app restart, parent login swallows Sheets errors silently, and the `api/fcm/register` endpoint exists but is never called from the Android app. None of these require architectural changes.

For v1.2, the Arduino R3 fix is already completed (quick-2 produced `bankongseton_nfc_r3.ino`). The remaining work is purely backend Python and Android Kotlin: wire low-balance email into the payment path, add `station_id` to NFC pay, write a CSV import endpoint, add Twilio SMS, and flip two debug defaults to `false`.

**Primary recommendation:** Execute tasks in dependency order — fix the three silent failure bugs first (FCM token registration, HCE token restore, parent error handling), then layer in v1.2 features on top of the corrected foundation.

---

## Standard Stack

### Core (already in use — no new dependencies unless noted)

| Library / Tool | Version in Use | Purpose | Notes |
|----------------|---------------|---------|-------|
| Flask | ≥2.x | HTTP API + dashboard routing | `api_server.py`, `admin_dashboard.py`, `web_app.py` |
| gspread | ≥5.x | Google Sheets read/write | All data persistence |
| firebase_admin | ≥6.x | FCM push notifications | `fcm_sender.py` — service account at `config/firebase-credentials.json` |
| smtplib (stdlib) | Python stdlib | Email sending | Already used in `notifications.py` |
| Adafruit_PN532 | latest | Arduino NFC reader library | Sketch already written in quick-2 |
| Kotlin + Android SDK | — | Mobile app | `student_app_v2/` |
| EncryptedSharedPreferences | AndroidX Security | Token storage on device | Already used in `SecureStorage.kt` |

### New Dependencies (v1.2)

| Library | Purpose | Install |
|---------|---------|---------|
| `twilio` (Python) | SMS gateway | `pip install twilio` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Twilio SMS | vonage, messagebird | Twilio is pre-selected in CONTEXT.md — do not swap |
| smtplib | sendgrid, mailgun | smtplib already works; no new dep needed |

---

## Architecture Patterns

### Existing Project Structure (relevant paths)

```
backend/
├── api/
│   ├── api_server.py          # Student-facing API (port 5001) — 1506 lines
│   └── fcm_sender.py          # Firebase FCM wrapper — 148 lines
├── dashboard/
│   ├── admin_dashboard.py     # Local admin UI + hardware (port 5000) — 2966 lines
│   ├── web_app.py             # PythonAnywhere web version — 2538 lines
│   ├── arduino_bridge.py      # Serial bridge to Arduino — 173 lines
│   └── templates/
│       ├── dashboard.html     # Admin UI — 1322 lines (has debug console.log)
│       ├── parent_dashboard.html  # Parent portal UI — 170 lines
│       └── students.html      # Student management — 435 lines
├── nfc_payments.py            # VirtualCard registration logic
└── notifications.py           # Email + FCM batch notifications

mobile/student_app_v2/
├── app/
│   └── src/
│       ├── google-services.json   ← CORRECT location
│       └── main/
│           └── java/com/bankongseton/student/
│               ├── FCMService.kt
│               ├── NfcManager.kt
│               ├── BankoHceService.kt
│               ├── SettingsActivity.kt
│               └── StudentApp.kt

arduino/
└── bankongseton_nfc_r3/
    ├── bankongseton_nfc_r3.ino   ← built in quick-2
    └── README.md
```

### Pattern: Fix-in-place (v1.1 gaps)

All v1.1 bugs are single-file fixes that don't require new endpoints or new classes. Each fix is localized:

- Android: add a `FCMService.onNewToken()` HTTP call to `POST /api/fcm/register`
- Android: restore `BankoHceService.currentToken` from `SecureStorage` in `BankoHceService.onHostEmulationActivated()` or on service start
- Python: replace bare `except Exception: pass` in parent login with explicit error logging and a 503 response

### Pattern: Low-Balance Email Wired to Payment Path

The `notify_low_balance_accounts()` batch scan in `notifications.py` already sends email for low balances when called. The gap is that it is never triggered per-transaction. The fix is to add a non-blocking call after the transaction commits in `api_server.py`, exactly mirroring the existing FCM push pattern (lines 1098–1111):

```python
# After send_purchase_push(), add:
try:
    if new_balance < LOW_BALANCE_THRESHOLD:
        from notifications import email_notifier
        parent_email = ...  # look up from Users sheet (already fetched above)
        if parent_email:
            email_notifier.send_low_balance_alert(nfc_student_id, new_balance)
except Exception as email_err:
    logger.warning("event=low_balance_email_failed error=%s", email_err)
```

`LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", "50"))` at module level.

### Pattern: Station ID — Header Injection

Add `X-Station-ID` request header to NFC pay POSTs from `ArduinoBridge`. The API endpoint reads `request.headers.get("X-Station-ID", "main")` and writes it to the `Transactions Log` sheet as a new `StationID` column. This is the least invasive change — no body schema change, backward compatible.

### Anti-Patterns to Avoid

- **Silent `except: pass`** — already present in parent login (line 423 `api_server.py`). Do not add more. Always log at `WARNING` minimum.
- **Blocking Sheets calls in notification path** — the existing FCM push is already wrapped in non-blocking try/except. Email and SMS must follow the same pattern.
- **Placing `google-services.json` outside `app/src/`** — misplaced copies exist at `app/src/google-services.json` (correct), `app/google-services.json` (wrong level), and inside the java source tree (wrong). Only `app/src/google-services.json` is correct for the project's Gradle structure; the other two should be deleted.
- **`debug=True` in production** — `admin_dashboard.py` line 2944 and `web_app.py` line 2516 both default to `"true"`. Must be flipped to `"False"`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SMS sending | Custom HTTP client to SMS API | `twilio` Python SDK | Auth, retry, error handling already solved |
| CSV parsing | Manual `split(",")` | Python `csv.DictReader` | Handles quoted fields, encoding, BOM |
| FCM token send | Raw `urllib` POST | `firebase_admin.messaging` (already in use) | Already authenticated, handles retries |
| Encrypted device storage | Custom XOR/AES | `EncryptedSharedPreferences` (already in use) | OS-backed keystore |

---

## Common Pitfalls

### Pitfall 1: BankoHceService Token Not Restored on App Restart

**What goes wrong:** After the app is killed and relaunched, `BankoHceService.currentToken` is `null` even though the user registered NFC. The HCE service starts fresh and cannot respond to tap events because it has no token.

**Why it happens:** `NfcManager.registerDevice()` sets `BankoHceService.currentToken` at registration time. `StudentApp.onCreate()` only applies the theme — it does not restore the NFC token. `BankoHceService` is a background service; its `companion object` fields reset on process restart.

**How to avoid:** In `BankoHceService.onStartCommand()` or at the top of `processApdu()`, check if `currentToken == null` and load from `SecureStorage` (which persists in `EncryptedSharedPreferences`). `NfcManager.init()` already does this for `NfcManager.currentToken` — replicate the same load for `BankoHceService.currentToken`.

**Warning signs:** NFC tap works immediately after registration but fails after phone reboot/app kill.

---

### Pitfall 2: FCM Token Never Registered with Backend

**What goes wrong:** Push notifications never arrive for a freshly installed app, or after Google Play Services rotates the FCM token.

**Why it happens:** `FCMService.onNewToken()` (line 37) saves the token to `SharedPreferences` only — it never calls `POST /api/fcm/register`. The backend endpoint at `api_server.py` line ~1441 (`/api/fcm/register`) exists and is correct, but is never called from Android.

**How to avoid:** In `FCMService.onNewToken(token: String)`, after saving to prefs, call the registration endpoint:
```kotlin
// In FCMService.onNewToken()
val authToken = SecureStorage(applicationContext).getAuthToken() ?: return
ApiClient.registerFcmToken(token, authToken) // fire-and-forget coroutine
```

Also call it on login (after `authToken` is available) in case the token was rotated while logged out.

**Warning signs:** FCM token in the Users sheet is empty or stale.

---

### Pitfall 3: Parent Login Silently Swallows Sheets Errors

**What goes wrong:** If Google Sheets is unavailable when a parent tries to log in, the `except Exception: pass` (line 423, `api_server.py`) silently falls through and returns a generic 401, indistinguishable from "wrong password."

**Why it happens:** Bare `except: pass` pattern.

**How to avoid:** Replace with:
```python
except (ConnectionError, TimeoutError) as sheets_err:
    logger.error("event=parent_login_sheets_error error=%s", sheets_err)
    return jsonify({"error": "Service temporarily unavailable"}), 503
```

---

### Pitfall 4: CSV Import — Duplicate Handling

**What goes wrong:** Uploading a CSV with a student that already exists causes a 500 or silent duplicate row in the Users sheet.

**Why it happens:** The single-student `/api/student/register` endpoint validates duplicates for StudentID and CardUID individually. A bulk import endpoint must replicate this check per-row and accumulate partial success/failure results rather than aborting the entire batch on first error.

**How to avoid:** Return a structured response `{"imported": N, "skipped": M, "errors": [...]}` and continue processing after per-row validation failures.

---

### Pitfall 5: `google-services.json` in Wrong Location

**What goes wrong:** Build fails or Firebase does not initialize with the correct project.

**Why it happens:** Three copies exist in the repo:
- `mobile/student_app_v2/app/src/google-services.json` ← **CORRECT**
- `mobile/student_app_v2/app/google-services.json` ← wrong (one level up from `src/`)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/google-services.json` ← wrong (inside source tree)

**How to avoid:** Delete the two incorrect copies. Gradle's `google-services` plugin reads from the module root (`app/`), but the correct placement for this project's structure is `app/src/` (matches current working build).

---

### Pitfall 6: `notify_low_balance_accounts()` Scans All Accounts

**What goes wrong:** Calling `notify_low_balance_accounts()` per-transaction would scan every row in the Users sheet on every purchase — O(N) Sheets reads per transaction.

**Why it happens:** The function was designed for batch/cron use, not per-transaction triggering.

**How to avoid:** Do NOT call `notify_low_balance_accounts()` from the payment path. Instead, check `new_balance < threshold` directly in the `nfc/pay` handler (the balance is already computed there) and call `email_notifier.send_low_balance_alert()` directly with the already-known student ID, new balance, and parent email (which was fetched two lines above for the FCM push).

---

### Pitfall 7: Arduino Bridge Has No Auto-Reconnect

**What goes wrong:** If the USB cable is disconnected and reconnected (or the COM port changes on Windows after reboot), the bridge stays in a broken state until the admin manually POSTs to `/api/serial/connect` again.

**Why it happens:** `ArduinoBridge` holds a single `serial.Serial` object. No reconnect loop exists.

**How to avoid (v1.2 scope):** Add a `reconnect()` method to `ArduinoBridge` that detects `serial.SerialException` during read and attempts to reopen the last-known port. For Phase 21, the minimum fix is to document the manual reconnect step clearly in the admin UI and ensure the `loadSerialPorts()` JS function (already in `dashboard.html` line 784) is wired to auto-populate on page load.

---

## Code Examples

### NFCA-01: Verified Registration Flow (api_server.py lines 832–879)

```python
# Source: backend/api/api_server.py lines 832–879
@app.route("/api/nfc/register", methods=["POST"])
@login_required
def register_nfc():
    student_id = session.get("student_id")
    # Looks up MoneyCardNumber from Users sheet
    # Calls nfc_service.register_virtual_card(money_card_number)
    # Returns {"success": True, "device_token": device_token}
```

**Note:** The Android `NfcDeviceRequest(deviceId, pin)` body fields are ignored by this endpoint — only `student_id` from the session is used. The `pin` is stored client-side in `SecureStorage` only. This is by design (server is stateless re: PIN).

---

### FCM Token Registration — Missing Android Call

```kotlin
// Source: FCMService.kt lines 37–45 (current — MISSING the API call)
override fun onNewToken(token: String) {
    Log.d(TAG, "FCM token refreshed: $token")
    // TODO: Save token to preferences
    // MISSING: POST to /api/fcm/register
}

// Fix pattern (to implement):
override fun onNewToken(token: String) {
    SecureStorage(applicationContext).saveFcmToken(token)
    val authToken = SecureStorage(applicationContext).getAuthToken() ?: return
    CoroutineScope(Dispatchers.IO).launch {
        try {
            ApiClient.registerFcmToken(token, authToken)
        } catch (e: Exception) {
            Log.w(TAG, "FCM token registration failed: ${e.message}")
        }
    }
}
```

---

### Low-Balance Email — Wire to Payment Path

```python
# Source: backend/api/api_server.py lines 1098–1111 (existing FCM pattern)
# Add immediately after the FCM push block:
try:
    low_balance_threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", "50"))
    if new_balance < low_balance_threshold and nfc_student_id:
        # parent_email is already available from the Users sheet scan above
        from notifications import email_notifier
        email_notifier.send_low_balance_alert(
            student_id=nfc_student_id,
            balance=new_balance,
            parent_email=parent_email,  # already fetched for FCM lookup
        )
except Exception as email_err:
    logger.warning("event=low_balance_email_failed error=%s", email_err)
```

---

### Station ID — Header Injection in ArduinoBridge

```python
# Source: backend/dashboard/arduino_bridge.py (to modify)
# In _post_nfc_payment():
headers = {
    "Authorization": f"Bearer {_CASHIER_JWT}",
    "Content-Type": "application/json",
    "X-Station-ID": os.getenv("STATION_ID", "main"),  # new
}
```

```python
# Source: backend/api/api_server.py /api/nfc/pay handler (to modify)
station_id = request.headers.get("X-Station-ID", "main")
# Add to Transactions Log append_row:
# [...existing fields..., station_id]
```

---

### Production Debug Fix

```python
# admin_dashboard.py line 2944 — CHANGE:
# FROM:
debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
# TO:
debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# web_app.py line 2516 — same change
# api_server.py line 1502 — already correct: os.getenv("API_DEBUG", "False") == "True"
```

---

### dashboard.html Debug console.log — Remove

```
Lines to remove (confirmed by code inspection):
  line 448: console.log('[DEBUG] Loading dashboard stats...');
  line 452: console.log('[DEBUG] Stats data:', data);
  line 786: console.log('[DEBUG] Loading serial ports...');
  line 790: console.log('[DEBUG] Serial ports response:', data);
  line 807: console.log(`[DEBUG] Loaded ${data.ports.length} ports`);
  line 809: console.log('[DEBUG] No ports available');
```

---

### Bulk CSV Import — Endpoint Pattern

```python
# New endpoint in admin_dashboard.py (local) and web_app.py (web)
@app.route("/api/students/import", methods=["POST"])
@admin_required
def bulk_import_students():
    file = request.files.get("csv_file")
    reader = csv.DictReader(io.StringIO(file.read().decode("utf-8-sig")))
    # utf-8-sig handles Excel BOM automatically
    imported, skipped, errors = 0, 0, []
    for row in reader:
        student_id = row.get("StudentID", "").strip()
        # validate, check duplicate, append_row to Users sheet
        # accumulate results
    return jsonify({"imported": imported, "skipped": skipped, "errors": errors})
```

**Required CSV columns:** `StudentID`, `Name`, `ParentEmail`, `MoneyCardNumber` (optional: `PhoneNumber`, `IDCardUID`)

---

## NFCA-01 Verification Findings

| Check | Status | Evidence |
|-------|--------|----------|
| `POST /api/nfc/register` endpoint exists | ✅ PASS | `api_server.py` line 832 |
| Endpoint requires active session | ✅ PASS | `@login_required` decorator |
| Generates `virtual_card_token` (UUID v4) | ✅ PASS | `nfc_payments.py` line 104 |
| Generates `device_token` (urlsafe 32B) | ✅ PASS | `nfc_payments.py` line 105 |
| Deactivates old VirtualCard row | ✅ PASS | `nfc_payments.py` line 97 |
| Android sends registration request | ✅ PASS | `NfcManager.registerDevice()` line 100 |
| `BankoHceService.currentToken` set at registration | ✅ PASS | `NfcManager.kt` line 124 |
| Token persisted in `EncryptedSharedPreferences` | ✅ PASS | `SecureStorage` usage confirmed |
| Token restored on app restart | ❌ **GAP** | `BankoHceService.currentToken` not restored; `StudentApp.onCreate()` only sets theme |
| FCM token sent to backend on new token | ❌ **GAP** | `FCMService.onNewToken()` saves to prefs only — never calls `/api/fcm/register` |
| `google-services.json` in correct location | ⚠️ WARN | Correct copy at `app/src/`; two incorrect copies also exist |

---

## PAR-01–06 Verification Findings

| Check | Status | Evidence |
|-------|--------|----------|
| `parent_only` decorator enforces role | ✅ PASS | `api_server.py` line 325 — checks `session["role"] == "parent"` |
| Parent login route exists | ✅ PASS | `api_server.py` lines 400–424 |
| Parent login checks `ParentEmail` + `ParentPasswordHash` | ✅ PASS | Lines 405–418 |
| `/parent` route renders dashboard | ✅ PASS | Line 438 |
| `/api/parent/data` returns balance + transactions | ✅ PASS | Lines 456–538 |
| Monthly spend computed | ✅ PASS | Computed in `/api/parent/data` response |
| `parent_dashboard.html` shows balance + transaction history | ✅ PASS | Lines 44–80, confirmed Bootstrap 5 UI |
| Parent login error handling for Sheets unavailability | ❌ **GAP** | `except Exception: pass` at line 423 — silently falls through to 401 |
| `students.html` Set Parent modal works | ✅ PASS | Lines 400–432 — POST to `/api/students/{id}/set-parent` |

---

## Arduino R3 Fix — Root Cause Analysis

The Arduino R3 issue was the mismatch between the R4-targeted `bankongseton_nfc.ino` (MFRC522 + WiFiS3) and the hardware on hand (UNO R3 + PN532).

**Root cause confirmed:** `quick-2` already resolved this by building a new sketch `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` with:
- Adafruit_PN532 in SPI mode (`nfc(PN532_SS)` single-pin constructor, SS=D10)
- Serial output format `CARD|<UIDHEX>` — matches `ArduinoBridge._read_serial_line` regex exactly
- Inline bit-bang I2C for LCD (no SoftwareWire library — avoids version conflicts)
- No WiFi, no `secrets.h`, no MFRC522 — clean UNO R3 target

**Remaining gap:** `ArduinoBridge` has no auto-connect on startup and no auto-reconnect on serial drop. The `POST /api/serial/connect` endpoint requires the admin to manually POST with the correct COM port. For Windows, the COM port may change after reboot. The `loadSerialPorts()` function in `dashboard.html` (line 784) fetches available ports — it runs on page load but does not auto-connect.

**Phase 21 fix scope:** Document reconnect steps in admin UI; optionally add a `STATION_SERIAL_PORT` env var that `ArduinoBridge` attempts to connect to on startup.

---

## Web/Local Dashboard Separation

| File | Lines | Has Hardware Routes | Has SocketIO | Deployment |
|------|-------|--------------------|-----------|----|
| `admin_dashboard.py` | 2,966 | ✅ Yes (`/api/serial/*`, Arduino bridge startup) | ✅ Yes | Local machine |
| `web_app.py` | 2,538 | ❌ No | ❌ No (or minimal) | PythonAnywhere |

**Delta: ~428 lines.** The local version contains:
- `ArduinoBridge` import and initialization
- `/api/serial/connect`, `/api/serial/disconnect`, `/api/serial/ports` routes
- Arduino bridge startup code in `__main__` block
- SocketIO for real-time cashier terminal UI

**Phase 21 scope:** Any new backend endpoint (CSV import, bulk register, etc.) must be added to **both** files. Low-balance email and SMS changes live in `api_server.py` (shared), so only one file needs editing for those.

---

## FCM Background Notifications

| Check | Status | Finding |
|-------|--------|---------|
| FCM v1 API used | ✅ | `firebase_admin.messaging` — correct |
| `notification` payload type used | ✅ | `fcm_sender.py` uses `messaging.Notification` |
| OS handles background notification display | ✅ | Android OS intercepts `notification` payloads when app is in background/killed |
| `FCMService.onMessageReceived()` handles foreground | ✅ | Lines 20–50 — checks `message.notification` |
| FCM token stored on device | ✅ | `FCMService.onNewToken()` saves to prefs |
| FCM token sent to backend | ❌ **GAP** | `onNewToken()` never calls `/api/fcm/register` |
| FCM token sent on login | ❌ **GAP** | No token registration on login in `MainActivity` or `LoginActivity` |
| `POST /api/fcm/register` endpoint exists | ✅ | `api_server.py` line ~1441 |

**Fix:** In `FCMService.onNewToken()`, call `POST /api/fcm/register` as a fire-and-forget coroutine. Also call it on successful login (pass the saved FCM token + new auth token). This ensures the backend always has a valid, current FCM token for the logged-in user.

---

## Low Balance Email

**Current state:** `email_notifier.send_low_balance_alert()` exists in `notifications.py` and sends email. It is only called from `notify_low_balance_accounts()` (batch scan). It is **never called per-transaction**.

**Fix:** Wire directly into the `POST /api/nfc/pay` handler, after the transaction is committed and after the FCM push. Use `new_balance` (already computed) and `parent_email` (already fetched from the Users sheet scan for the FCM push). No new Sheets reads required.

**Threshold:** `LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", "50"))` — 50 THB default, overridable via env var.

---

## SMS Gateway Recommendation

**Decision:** Twilio (locked in CONTEXT.md).

**Implementation pattern:**
```python
# backend/notifications.py — add TwilioSMSNotifier class
from twilio.rest import Client as TwilioClient

class TwilioSMSNotifier:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.client = TwilioClient(self.account_sid, self.auth_token) if self.account_sid else None

    def send_low_balance_sms(self, to_number: str, student_name: str, balance: float):
        if not self.client:
            logger.warning("Twilio not configured — SMS skipped")
            return
        self.client.messages.create(
            body=f"BankongSeton: {student_name}'s balance is ฿{balance:.2f}. Please top up.",
            from_=self.from_number,
            to=to_number,
        )
```

Required env vars: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`

The `PhoneNumber` column already exists (or should be added) in the Users sheet for SMS delivery.

---

## Bulk Student Import

**Current state:** `POST /api/student/register` accepts single student. No bulk route exists.

**Design:**
- Endpoint: `POST /api/students/import` (multipart form, `csv_file` field)
- Protected by `@admin_required`
- Parses with `csv.DictReader` + `utf-8-sig` encoding (handles Excel BOM)
- Required columns: `StudentID`, `Name`, `ParentEmail`
- Optional columns: `MoneyCardNumber`, `PhoneNumber`, `IDCardUID`
- Per-row validation mirrors single-student validation (duplicate StudentID, duplicate CardUID)
- Returns `{"imported": N, "skipped": M, "errors": [{"row": N, "error": "..."}]}`
- Must be added to both `admin_dashboard.py` and `web_app.py`

---

## Multi-Station Support

**Current state:** `ArduinoBridge._post_nfc_payment()` POSTs `{"token": token}` with no station identifier. The Transactions Log has no `StationID` column.

**Design:**
- Add `STATION_ID` env var (default `"main"`) read at `arduino_bridge.py` import time
- Inject as `X-Station-ID` HTTP header in `_post_nfc_payment()`
- `api_server.py` `/api/nfc/pay` reads `request.headers.get("X-Station-ID", "main")`
- Append `station_id` as new column in `Transactions Log` `append_row()`
- Google Sheets API serializes writes server-side — concurrent `append_row()` from multiple stations is safe (no data loss), though row ordering may be nondeterministic under high concurrency

---

## Production Hardening Findings

| File | Issue | Line | Fix |
|------|-------|------|-----|
| `admin_dashboard.py` | `FLASK_DEBUG` defaults to `"true"` | 2944 | Change default to `"false"` |
| `web_app.py` | `FLASK_DEBUG` defaults to `"true"` | 2516 | Change default to `"false"` |
| `api_server.py` | `API_DEBUG` defaults to `"False"` | 1502 | ✅ Already correct |
| `dashboard.html` | 6 `console.log('[DEBUG]...')` lines | 448, 452, 786, 790, 807, 809 | Remove all 6 |
| `app/google-services.json` | Misplaced copy | — | Delete |
| `app/src/main/java/.../google-services.json` | Misplaced copy inside source tree | — | Delete |

---

## Open Questions

1. **`PhoneNumber` column in Users sheet**
   - What we know: `MoneyCardNumber`, `ParentEmail`, `StudentID`, `Name`, `FCMToken`, `ParentPasswordHash` columns confirmed in Users sheet
   - What's unclear: Whether `PhoneNumber` already exists as a column
   - Recommendation: Check during implementation; add if missing, document expected column order in CSV import template

2. **`send_low_balance_alert()` signature**
   - What we know: Method exists in `notifications.py` around line 640–669
   - What's unclear: Exact signature — whether it takes `parent_email` directly or fetches it internally
   - Recommendation: Read lines 640–669 of `notifications.py` at task start; adapt call site accordingly

3. **Arduino auto-connect on startup**
   - What we know: No auto-connect exists; admin must POST to `/api/serial/connect`
   - What's unclear: Whether adding a `STATION_SERIAL_PORT` env var auto-connect is in scope for Phase 21 or deferred
   - Recommendation: Treat as optional stretch goal; minimum fix is UI clarity

---

## Sources

### Primary (HIGH confidence — direct code inspection)

All findings are from direct read of the live codebase files listed below:

- `backend/api/api_server.py` — lines 325–424, 832–879, 1090–1120, 1441–1506
- `backend/api/fcm_sender.py` — full file (148 lines)
- `backend/dashboard/admin_dashboard.py` — lines 315–544, 1706–1760, 2127–2186, 2930–2966
- `backend/dashboard/web_app.py` — lines 2505–2538
- `backend/dashboard/arduino_bridge.py` — full file (173 lines)
- `backend/dashboard/templates/dashboard.html` — lines 440–469, 780–809
- `backend/dashboard/templates/parent_dashboard.html` — lines 1–80
- `backend/dashboard/templates/students.html` — lines 400–435
- `backend/nfc_payments.py` — lines 80–139
- `backend/notifications.py` — lines 1–100, 640–719
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/FCMService.kt` — full (66 lines)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — full (244 lines)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — full (105 lines)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SettingsActivity.kt` — full (259 lines)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/StudentApp.kt` — full (23 lines)
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — full
- `.planning/quick/2-arduino-uno-r3-pn532-nfc-code-with-spi-p/2-SUMMARY.md` — full (108 lines)
- `.planning/phases/21-21/21-CONTEXT.md` — full

---

## Metadata

**Confidence breakdown:**
- NFCA-01 / PAR-01–06 verification: HIGH — direct code inspection, specific line numbers
- Arduino R3 fix status: HIGH — quick-2 SUMMARY.md confirms completion with commit hashes
- FCM gaps: HIGH — `FCMService.onNewToken()` body confirmed empty of API call
- Production hardening: HIGH — debug default strings confirmed in both files
- Twilio SMS integration: MEDIUM — pattern is standard; actual env var names TBC at implementation
- Bulk CSV import: MEDIUM — pattern is standard Python; sheet column names for `PhoneNumber` TBC

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable codebase, 30-day window)
