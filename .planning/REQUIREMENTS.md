# Requirements: BankongSeton v1.1 Platform Expansion

**Defined:** 2026-03-04
**Core Value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app

---

## v1.1 Requirements

Requirements for this milestone. Six feature areas: NFC Android HCE, Dashboard overhaul, Arduino WiFi, Parent portal, Student app redesign, Admin features.

---

### NFC Android HCE

- [x] **NFCA-01**: Android app registers phone as NFC virtual card via HCE (`BankoHceService`)
- [x] **NFCA-02**: Student taps phone at cashier terminal to pay (HCE emulates card UID sent to backend)
- [x] **NFCA-03**: NFC payment receipt navigation works in Android (tapping `NFC Purchase` transaction opens `ReceiptActivity` with itemized view)
- [x] **NFCA-04**: Card registration flow in Android app (link phone NFC to student account)
- [x] **NFCA-05**: `ReceiptActivity` displays line items for NFC Purchase transactions (not just RFID Purchase)

---

### Dashboard Overhaul

- [x] **DASH-01**: Dashboard uses modern CSS framework (Bootstrap 5 or Tailwind) — full visual redesign
- [x] **DASH-02**: Dashboard homepage shows spending analytics charts (daily/weekly/monthly spend trends)
- [x] **DASH-03**: Admin can export transaction history as CSV from the dashboard
- [x] **DASH-04**: Admin can top-up a student's balance directly from the dashboard
- [x] **DASH-05**: Dashboard remains deployable on PythonAnywhere free tier (no paid add-ons required)

---

### Arduino UNO R4 WiFi Upgrade

- [x] **ARDW-01**: Arduino UNO R4 firmware sends card read events over WiFi directly to Flask API (no serial USB dependency)
- [x] **ARDW-02**: Flask backend has a dedicated WiFi card-read endpoint that accepts Arduino POST requests
- [x] **ARDW-03**: Cashier computer UI still handles order entry (item selection) — Arduino WiFi only handles card UID delivery
- [x] **ARDW-04**: Fallback: system can still operate in serial/USB mode if WiFi is unavailable

---

### Parent Portal

- [x] **PAR-01**: Parent role exists in the system (read-only access, scoped to their linked student)
- [x] **PAR-02**: Parent can view their linked student's current balance
- [x] **PAR-03**: Parent can view their linked student's spending history (transactions list)
- [x] **PAR-04**: Parent email is optionally collected at student card registration (not required)
- [x] **PAR-05**: Student card registration accepts two emails: student (required) and parent (optional)
- [x] **PAR-06**: Parent portal is accessible via web browser (part of Flask dashboard, not a separate app)

---

### Student App Redesign

- [x] **APPA-01**: Full UI/UX overhaul of Android student app (modern visual design, improved layout)
- [x] **APPA-02**: Student app supports dark mode
- [x] **APPA-03**: Student app has a monthly budget tracker (student sets a monthly spending limit)
- [x] **APPA-04**: Student app sends an in-app alert when spending approaches or exceeds monthly budget
- [x] **APPA-05**: Student can report a lost card from within the app (triggers card deactivation)

---

### Admin Features

- [x] **ADM-01**: Admin can top-up a student balance (balance load) from admin dashboard (covered by DASH-04)
- [x] **ADM-02**: Admin can export transaction CSV with optional date range filter
- [x] **ADM-03**: Admin can search students by name or ID with live (debounced) filtering on the students page
- [x] **ADM-04**: Admin can view per-student transaction history in a modal without leaving the students page

---

## Out of Scope (v1.1)

| Feature | Reason |
|---------|--------|
| SMS notifications | Push + email sufficient for now |
| SQL database migration | Google Sheets still working; migration adds risk without clear benefit |
| iOS app | Android-only for this project |
| Multiple canteen stations | Single-station scope |
| Bulk student import (CSV) | Manual registration sufficient at this scale |
| Flutter port | Kotlin/Compose is the target |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NFCA-01 | Phase 16 - NFC Android HCE | Complete |
| NFCA-02 | Phase 16 - NFC Android HCE | Complete |
| NFCA-03 | Phase 16 - NFC Android HCE | Complete |
| NFCA-04 | Phase 16 - NFC Android HCE | Complete |
| NFCA-05 | Phase 16 - NFC Android HCE | Complete |
| DASH-01 | Phase 17 - Dashboard Overhaul | Complete |
| DASH-02 | Phase 17 - Dashboard Overhaul | Complete |
| DASH-03 | Phase 17 - Dashboard Overhaul | Complete |
| DASH-04 | Phase 17 - Dashboard Overhaul | Complete |
| DASH-05 | Phase 17 - Dashboard Overhaul | Complete |
| ARDW-01 | Phase 18 - Arduino WiFi Upgrade | Complete |
| ARDW-02 | Phase 18 - Arduino WiFi Upgrade | Complete |
| ARDW-03 | Phase 18 - Arduino WiFi Upgrade | Complete |
| ARDW-04 | Phase 18 - Arduino WiFi Upgrade | Complete |
| PAR-01 | Phase 19 - Parent Portal | Complete |
| PAR-02 | Phase 19 - Parent Portal | Complete |
| PAR-03 | Phase 19 - Parent Portal | Complete |
| PAR-04 | Phase 19 - Parent Portal | Complete |
| PAR-05 | Phase 19 - Parent Portal | Complete |
| PAR-06 | Phase 19 - Parent Portal | Complete |
| APPA-01 | Phase 20 - Student App Redesign | Complete |
| APPA-02 | Phase 20 - Student App Redesign | Complete |
| APPA-03 | Phase 20 - Student App Redesign | Complete |
| APPA-04 | Phase 20 - Student App Redesign | Complete |
| APPA-05 | Phase 20 - Student App Redesign | Complete |
| ADM-01 | Phase 17 - Dashboard Overhaul | Complete |
| ADM-02 | Phase 17 - Dashboard Overhaul | Complete |
| ADM-03 | Phase 17 - Dashboard Overhaul | Complete |
| ADM-04 | Phase 17 - Dashboard Overhaul | Complete |

**Coverage:**
- v1.1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0

---

*Requirements defined: 2026-03-04*

---

## Phase 21: v1.1 Gap Closure + v1.2 Features

### Gap Closure (v1.1)

| ID | Description |
|----|-------------|
| V11-NFCA-01 | Fix NFCA-01 regressions: FCM token not sent to backend; HCE token not restored on app restart; stray google-services.json copies causing build failures |
| V11-PAR-01-06 | Fix PAR-01–06 regression: parent login silently swallows Google Sheets connection errors instead of returning HTTP 503 |

### Production Hardening

| ID | Description |
|----|-------------|
| PROD-HARDEN | Remove 6 debug console.log calls from dashboard.html; flip FLASK_DEBUG default to false in admin_dashboard.py and web_app.py |

### New Features (v1.2)

| ID | Description |
|----|-------------|
| V12-EMAIL | Send low-balance email alert to parent when student balance drops below configurable threshold after NFC payment |
| V12-STATION | Multi-canteen station support: STATION_ID env var injected as X-Station-ID header in ArduinoBridge; recorded in Transactions Log |
| V12-ARDUINO-R3 | Arduino R3 auto-connect: STATION_SERIAL_PORT env var triggers automatic serial connection on ArduinoBridge startup |
| V12-SMS | SMS notification via Twilio: send low-balance or payment SMS to parent/student phone number after NFC payment |
| V12-CSV | Bulk CSV student import: POST /api/students/import endpoint in both admin_dashboard.py and web_app.py; handles Excel BOM; per-row error reporting without aborting batch |

---

## Phase 23 — iPhone App Version

- [x] **REQ-23-01**: Xcode project compiles with no errors (iOS 16+, SwiftUI)
- [x] **REQ-23-02**: Login screen with PIN authentication and Keychain token storage
- [x] **REQ-23-03**: Home screen shows ₱ balance and recent transactions
- [x] **REQ-23-04**: Transaction history with pagination and receipt navigation
- [x] **REQ-23-05**: Budget tracker with monthly spending computation and threshold alerts
- [x] **REQ-23-06**: Settings with theme toggle (Keychain-persisted) and logout
- [x] **REQ-23-07**: Report Lost Card screen (POST /student/lost-card, Keychain isCardLost flag)
- [x] **REQ-23-08**: CARD_LOST 403 handling throughout app (distinct APIError.cardLost case)
- [x] **REQ-23-09**: ₱ (Philippine Peso) currency symbol used throughout iOS app
- [x] **REQ-23-10**: No NFC Pay features on iOS (Apple HCE restriction)

## Phase 24 — Admin & Cashier Improvements

- [x] **ADM-24-01**: Admin can soft-delete a product (sets Active=FALSE, prefixes name with [DELETED]); deleted products hidden from cashier
- [x] **ADM-24-02**: Product categories are managed via a Google Sheets tab (add/delete); active-product safety check blocks deleting in-use categories
- [x] **ADM-24-03**: Admin can void a completed Purchase transaction; void is logged as a reversal entry
- [x] **CSH-24-01**: Cashier shift summary panel shows total sales (₱), transaction count, and items sold for the current session; Reset button clears counters
