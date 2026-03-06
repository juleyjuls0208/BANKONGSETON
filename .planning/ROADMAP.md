# Roadmap: BankongSeton v1.1 Platform Expansion

**Created:** 2026-03-04
**Milestone:** v1.1 Platform Expansion
**Phase numbering:** Continues from v1.0 (15 phases completed)

---

## Overview

5 phases covering all v1.1 feature areas. Each phase is independently deliverable. Phases 16–18 touch backend first (NFC, dashboard, Arduino), then 19–20 add portal and mobile polish.

| Phase | Name | Requirements | Status |
|-------|------|-------------|--------|
| 16 | NFC Android HCE | NFCA-01–05 | ✓ Complete (2026-03-05) |
| 17 | Dashboard Overhaul + Admin | DASH-01–05, ADM-01–04 | ✓ Complete (2026-03-05) |
| 18 | Arduino UNO R4 WiFi Upgrade | Complete    | 2026-03-06 |
| 19 | Parent Portal | PAR-01–06 | Pending |
| 20 | Student App Redesign | APPA-01–05 | Pending |

**Total phases:** 5
**Total plans (estimated):** 16–21

---

## Phase 16: NFC Android HCE

**Goal:** Implement Android HCE so students can tap their phone at the cashier terminal to pay, and fix NFC Purchase receipt navigation.

**Why now:** NFC backend endpoints are fully wired from v1.0 (Phase 5 + 13). The Android side is the only missing piece.

**Requirements:** NFCA-01, NFCA-02, NFCA-03, NFCA-04, NFCA-05

**Success criteria:**
- `BankoHceService` implemented in Android app
- Student can register phone as NFC virtual card (card registration flow)
- Tapping phone at terminal triggers an NFC payment via existing `/api/nfc/pay` endpoint
- Tapping an `NFC Purchase` transaction in the transactions list navigates to `ReceiptActivity` (not silently ignored)
- `ReceiptActivity` shows line items for NFC purchases

**Key risks:**
- HCE requires NFC-capable Android device — emulator testing limited
- Backend `/api/nfc/pay` uses single-token lookup (fixed in Phase 13) — verify contract before Android implementation

**Out of scope:** NFC hardware reader on cashier side (cashier still uses RFID reader; phone tap emulates card UID)

**Plans:** 4/4 complete ✓

Plans:
- [x] 16-01-PLAN.md — HCE infrastructure: port BankoHceService + NfcManager, update Models/ApiClient/Manifest/build.gradle
- [x] 16-02-PLAN.md — Receipt fix: null-items fallback + transaction type label in ReceiptActivity
- [x] 16-03-PLAN.md — Card registration UX: NFC section in SettingsActivity (register/remove)
- [x] 16-04-PLAN.md — NFC pay flow: "Activate NFC Pay" button + NfcPayOverlayActivity countdown

**Post-phase bug fixes (2026-03-05):**
- Backend `nfc_register`: money card lookup switched from `Money Accounts` sheet to `Users` sheet (fixes 403 for all students)
- Mobile `ApiClient`: `@DELETE` → `@POST` for `nfc/unregister`; HTTP body logging enabled in debug builds
- Mobile `SettingsActivity`: shows actual server error instead of generic failure toast

---

## Phase 17: Dashboard Overhaul + Admin Features

**Goal:** Modernize the admin dashboard with Bootstrap 5, add analytics charts, CSV export, and balance top-up. Must remain PythonAnywhere-free-tier deployable.

**Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, ADM-01, ADM-02, ADM-03, ADM-04

**Success criteria:**
- Dashboard uses Bootstrap 5 (or equivalent) — old styling fully replaced
- Homepage shows at least one analytics chart (e.g. daily spend bar chart using Chart.js or similar CDN)
- Admin can click "Export CSV" and download all transactions (with optional date range)
- Admin can top-up a student's balance from the dashboard (POST endpoint + UI form)
- App deploys and runs on PythonAnywhere free tier without modification

**Key risks:**
- PythonAnywhere free tier: no background workers, no websockets in production, limited CPU seconds — charts must use CDN JS (no server-side rendering)
- Bootstrap 5 migration: existing Jinja templates may have Bootstrap 3/4 class conflicts

**Out of scope:** Real-time live dashboard updates (no WebSocket charts)

**Estimated plans:** 4–5
1. Bootstrap 5 migration + layout redesign
2. Analytics charts (Chart.js via CDN, data from existing transactions endpoint)
3. CSV export endpoint + UI
4. Balance top-up endpoint + UI
5. (if needed) PythonAnywhere compatibility verification

**Plans:** 6/6 complete ✓

Plans:
- [x] 17-01-PLAN.md — Bootstrap 5 migration + shared base.html + dashboard.css
- [x] 17-02-PLAN.md — Analytics charts (Chart.js CDN + spending data endpoint)
- [x] 17-03-PLAN.md — CSV export endpoint + transactions page UI
- [x] 17-04-PLAN.md — Admin balance top-up endpoint + modal UI
- [x] 17-05-PLAN.md — Live student search (ADM-03) + per-student transaction history modal (ADM-04)
- [x] 17-06-PLAN.md — Gap closure: requirement ID traceability fixes

---

## Phase 18: Arduino UNO R4 WiFi Upgrade

**Goal:** Update Arduino firmware to POST card UID events over WiFi to Flask API, eliminating the serial USB dependency for card reading.

**Requirements:** ARDW-01, ARDW-02, ARDW-03, ARDW-04

**Success criteria:**
- Arduino firmware uses built-in ESP32 WiFi to POST `{uid: "..."}` to `/api/arduino/card-read` (or equivalent new endpoint)
- Flask has a new WiFi card-read endpoint secured by a shared secret (API key in Arduino firmware + Flask env var)
- Cashier order-entry UI still works (computer still used for item selection)
- Serial/USB mode still functional as fallback (no code removed, only new WiFi path added)

**Key risks:**
- Arduino UNO R4 WiFi uses `WiFiS3.h` library (not ESP8266/ESP32 standard) — verify library availability
- Network reliability on school WiFi — Arduino must handle connection drops gracefully
- Shared secret management: Arduino firmware has hardcoded WiFi/API credentials — document security implications

**Out of scope:** Removing serial support, OTA firmware updates

**Plans:** 3/3 plans complete

Plans:
- [x] 18-01-PLAN.md — Flask POST /api/arduino/card-read endpoint + ARDUINO_API_KEY env examples
- [x] 18-02-PLAN.md — Arduino UNO R4 WiFi firmware (WiFiS3 + MFRC522 + HTTP POST + serial fallback) + .gitignore
- [x] 18-03-PLAN.md — Automated smoke-test + human verification checkpoint

---

## Phase 19: Parent Portal

**Goal:** Add a read-only parent role accessible via web browser. Parents linked at card registration can view their student's balance and spending history.

**Requirements:** PAR-01, PAR-02, PAR-03, PAR-04, PAR-05, PAR-06

**Success criteria:**
- Parent role exists with read-only access scoped to their linked student
- Parent can log in via web and see student balance + transaction history
- Student card registration form has optional parent email field
- Parent receives no admin capabilities (cannot top-up, cannot manage products)
- Portal is part of existing Flask dashboard (no new app/domain)

**Key risks:**
- Google Sheets Users sheet may need new columns (ParentEmail, ParentPasswordHash) — migration plan needed
- Parent authentication: session-based (consistent with existing admin auth) vs separate JWT path

**Out of scope:** Parent push notifications, parent mobile app

**Estimated plans:** 3–4
1. Google Sheets schema migration (add parent fields) + parent auth routes
2. Parent portal UI (balance view + transaction history)
3. Card registration form update (optional parent email)
4. (if needed) Security review + access control hardening

---

## Phase 20: Student App Redesign

**Goal:** Full UI/UX overhaul of the Android student app: modern design, dark mode, monthly budget tracker with alerts, lost card reporting.

**Requirements:** APPA-01, APPA-02, APPA-03, APPA-04, APPA-05

**Success criteria:**
- All screens redesigned with consistent modern visual language (Material 3 or equivalent)
- Dark mode toggle works and persists preference
- Budget tracker: student sets monthly limit in settings, app tracks spend against it
- In-app alert shown when monthly spend reaches 80% and 100% of limit
- Lost card report flow: student taps "Report Lost Card" → triggers card deactivation API call → shows confirmation

**Key risks:**
- Full redesign is scope-heavy — may need to split into sub-phases if plans exceed 5
- Dark mode: Jetpack Compose theming (`isSystemInDarkTheme()`) needs to apply consistently across all composables
- Lost card API: needs new backend endpoint (`POST /api/student/lost-card`) — plan must include backend + Android

**Out of scope:** Lost card physical replacement workflow, multi-account switching

**Estimated plans:** 4–5
1. Material 3 theme + design system setup (colors, typography, dark mode)
2. Home screen + transactions screen redesign
3. Monthly budget tracker (settings + tracking logic + in-app alerts)
4. Lost card report flow (backend endpoint + Android UI)
5. (if needed) Polish pass + edge cases

---

## Dependency Order

```
Phase 16 (NFC Android)     — depends on v1.0 Phase 13 backend ✓
Phase 17 (Dashboard)       — independent, can run in parallel with 16
Phase 18 (Arduino WiFi)    — independent, can run in parallel with 16/17
Phase 19 (Parent Portal)   — independent
Phase 20 (Student App)     — independent; Phase 16 should complete first (NFC in app)
```

Recommended execution order: **16 → 17 → 18 → 19 → 20**
(NFC first since it completes the most critical missing feature; Dashboard second since it's highest admin value)

---

## v1.1 Requirements Coverage

| Requirement | Phase | Covered |
|-------------|-------|---------|
| NFCA-01–05 | 16 | ✓ |
| DASH-01–05 | 17 | ✓ |
| ADM-01–04 | 17 | ✓ |
| ARDW-01–04 | 18 | ✓ |
| PAR-01–06 | 19 | ✓ |
| APPA-01–05 | 20 | ✓ |

**29 / 29 requirements covered. 0 unmapped.**

---

*Roadmap created: 2026-03-04*
