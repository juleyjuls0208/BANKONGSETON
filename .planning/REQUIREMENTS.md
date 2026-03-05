# Requirements: BankongSeton v1.1 Platform Expansion

**Defined:** 2026-03-04
**Core Value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app

---

## v1.1 Requirements

Requirements for this milestone. Six feature areas: NFC Android HCE, Dashboard overhaul, Arduino WiFi, Parent portal, Student app redesign, Admin features.

---

### NFC Android HCE

- [ ] **NFCA-01**: Android app registers phone as NFC virtual card via HCE (`BankoHceService`)
- [x] **NFCA-02**: Student taps phone at cashier terminal to pay (HCE emulates card UID sent to backend)
- [x] **NFCA-03**: NFC payment receipt navigation works in Android (tapping `NFC Purchase` transaction opens `ReceiptActivity` with itemized view)
- [x] **NFCA-04**: Card registration flow in Android app (link phone NFC to student account)
- [x] **NFCA-05**: `ReceiptActivity` displays line items for NFC Purchase transactions (not just RFID Purchase)

---

### Dashboard Overhaul

- [ ] **DASH-01**: Dashboard uses modern CSS framework (Bootstrap 5 or Tailwind) — full visual redesign
- [x] **DASH-02**: Dashboard homepage shows spending analytics charts (daily/weekly/monthly spend trends)
- [ ] **DASH-03**: Admin can export transaction history as CSV from the dashboard
- [ ] **DASH-04**: Admin can top-up a student's balance directly from the dashboard
- [ ] **DASH-05**: Dashboard remains deployable on PythonAnywhere free tier (no paid add-ons required)

---

### Arduino UNO R4 WiFi Upgrade

- [ ] **ARDW-01**: Arduino UNO R4 firmware sends card read events over WiFi directly to Flask API (no serial USB dependency)
- [ ] **ARDW-02**: Flask backend has a dedicated WiFi card-read endpoint that accepts Arduino POST requests
- [ ] **ARDW-03**: Cashier computer UI still handles order entry (item selection) — Arduino WiFi only handles card UID delivery
- [ ] **ARDW-04**: Fallback: system can still operate in serial/USB mode if WiFi is unavailable

---

### Parent Portal

- [ ] **PAR-01**: Parent role exists in the system (read-only access, scoped to their linked student)
- [ ] **PAR-02**: Parent can view their linked student's current balance
- [ ] **PAR-03**: Parent can view their linked student's spending history (transactions list)
- [ ] **PAR-04**: Parent email is optionally collected at student card registration (not required)
- [ ] **PAR-05**: Student card registration accepts two emails: student (required) and parent (optional)
- [ ] **PAR-06**: Parent portal is accessible via web browser (part of Flask dashboard, not a separate app)

---

### Student App Redesign

- [ ] **APPA-01**: Full UI/UX overhaul of Android student app (modern visual design, improved layout)
- [ ] **APPA-02**: Student app supports dark mode
- [ ] **APPA-03**: Student app has a monthly budget tracker (student sets a monthly spending limit)
- [ ] **APPA-04**: Student app sends an in-app alert when spending approaches or exceeds monthly budget
- [ ] **APPA-05**: Student can report a lost card from within the app (triggers card deactivation)

---

### Admin Features

- [ ] **ADM-01**: Admin can top-up a student balance (balance load) from admin dashboard (covered by DASH-04)
- [ ] **ADM-02**: Admin can export transaction CSV with optional date range filter

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
| NFCA-01 | Phase 16 - NFC Android HCE | Pending |
| NFCA-02 | Phase 16 - NFC Android HCE | Complete |
| NFCA-03 | Phase 16 - NFC Android HCE | Complete |
| NFCA-04 | Phase 16 - NFC Android HCE | Complete |
| NFCA-05 | Phase 16 - NFC Android HCE | Complete |
| DASH-01 | Phase 17 - Dashboard Overhaul | Pending |
| DASH-02 | Phase 17 - Dashboard Overhaul | Complete |
| DASH-03 | Phase 17 - Dashboard Overhaul | Pending |
| DASH-04 | Phase 17 - Dashboard Overhaul | Pending |
| DASH-05 | Phase 17 - Dashboard Overhaul | Pending |
| ARDW-01 | Phase 18 - Arduino WiFi Upgrade | Pending |
| ARDW-02 | Phase 18 - Arduino WiFi Upgrade | Pending |
| ARDW-03 | Phase 18 - Arduino WiFi Upgrade | Pending |
| ARDW-04 | Phase 18 - Arduino WiFi Upgrade | Pending |
| PAR-01 | Phase 19 - Parent Portal | Pending |
| PAR-02 | Phase 19 - Parent Portal | Pending |
| PAR-03 | Phase 19 - Parent Portal | Pending |
| PAR-04 | Phase 19 - Parent Portal | Pending |
| PAR-05 | Phase 19 - Parent Portal | Pending |
| PAR-06 | Phase 19 - Parent Portal | Pending |
| APPA-01 | Phase 20 - Student App Redesign | Pending |
| APPA-02 | Phase 20 - Student App Redesign | Pending |
| APPA-03 | Phase 20 - Student App Redesign | Pending |
| APPA-04 | Phase 20 - Student App Redesign | Pending |
| APPA-05 | Phase 20 - Student App Redesign | Pending |
| ADM-01 | Phase 17 - Dashboard Overhaul | Pending |
| ADM-02 | Phase 17 - Dashboard Overhaul | Pending |

**Coverage:**
- v1.1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---

*Requirements defined: 2026-03-04*
