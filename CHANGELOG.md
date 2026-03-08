# Changelog

All notable changes to BankongSeton are documented here.

---

## [v1.2] — 2026-03-08

### Bug Fixes (v1.1 Gap Closure)
- **FCM token registration**: `FCMService.onNewToken()` now calls `ApiClient.registerFcmToken()` so push notifications are registered with the backend; also called on login
- **HCE token restore**: `BankoHceService.processApdu()` now reloads token from `SecureStorage` when `currentToken` is null after process kill
- **Parent login error handling**: `api_server.py` no longer silently swallows `ConnectionError`/`TimeoutError` from Google Sheets — now returns HTTP 503 with JSON error body
- **Build fix**: Removed stray `google-services.json` copies from `app/` and `app/src/main/java/…/`; canonical copy is `app/src/google-services.json`

### Production Hardening
- Removed 6 `console.log('[DEBUG]…')` calls from `dashboard.html`
- `FLASK_DEBUG` now defaults to `"false"` in `admin_dashboard.py` and `web_app.py`

### New Features
- **Low balance email**: Parent receives email alert when student balance drops below configurable threshold (env: `LOW_BALANCE_THRESHOLD`, default 50) after NFC payment
- **Multi-canteen station support**: `STATION_ID` env var (default `"main"`) sent as `X-Station-ID` header in ArduinoBridge requests and recorded in Transactions Log
- **Arduino R3 auto-connect**: `STATION_SERIAL_PORT` env var triggers automatic serial port connection on ArduinoBridge startup
- **SMS notifications (Twilio)**: `TwilioSMSNotifier` class added to `notifications.py`; triggered after NFC payment if `TWILIO_*` env vars set
- **Bulk CSV student import**: `POST /api/students/import` in `admin_dashboard.py` and `web_app.py`; handles Excel BOM (`utf-8-sig`); per-row validation without aborting batch; returns `{imported, skipped, errors}`

---

## [v1.1] — 2026-03-07

### NFC Android HCE (Phase 16)
- `BankoHceService` + `NfcManager` implemented in Android student app
- Student can register phone as NFC virtual card; tapping phone at cashier triggers payment via `/api/nfc/pay`
- NFC Purchase receipt navigation: tapping `NFC Purchase` transaction opens `ReceiptActivity` with itemized view

### Dashboard Overhaul (Phase 17)
- Full Bootstrap 5 visual redesign of admin dashboard
- Spending analytics charts (daily/weekly/monthly) using Chart.js
- Admin CSV export with date range filter
- Admin balance top-up from dashboard
- Live debounced student search with per-student transaction modal

### Arduino UNO R4 WiFi (Phase 18)
- R4 firmware sends card reads over WiFi directly to Flask `/api/arduino/card-read`
- Serial/USB mode retained as fallback

### Parent Portal (Phase 19)
- Parent role (read-only, scoped to linked student)
- Parent can view student balance and transaction history via web portal
- Dual email at card registration (student required, parent optional)

### Student App Redesign (Phase 20)
- Modern UI/UX overhaul (Home, Transactions, Receipt, Settings screens)
- Dark mode support
- Monthly budget tracker with in-app spending alerts
- In-app lost card report

### Arduino PN532 NFC Integration (Phase 20.1)
- R3 firmware: APDU HCE exchange reads 48-char token from student phones; CARD|UID fallback
- R4 firmware: PN532 swap; POSTs `NFC|<token>` to `/api/nfc/pay`
- ArduinoBridge parses `NFC|<token>` serial lines and forwards payment
- Cashier UI: blue NFC payment modal with result state and retry button

---

## [v1.0] — 2026-03-05

Initial stable release. Cashier POS, admin dashboard, Android student app, Google Sheets persistence, JWT auth, FCM push notifications, NFC backend architecture, full documentation.
