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
| 19 | Parent Portal | PAR-01–06 | ✓ Complete (2026-03-07) |
| 20 | Student App Redesign | Complete    | 2026-03-07 |
| 21 | 8/8 | Complete    | 2026-03-08 |

**Total phases:** 6
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

**Plans:** 3/3 complete ✓

Plans:
- [x] 19-01-PLAN.md — Parent auth backend: `parent_only` decorator, login extension, `/parent` + `/parent/logout` routes, `set_parent_credentials` API
- [x] 19-02-PLAN.md — Parent portal UI: `GET /api/parent/data` endpoint + `parent_dashboard.html` (balance + transaction history)
- [x] 19-03-PLAN.md — Students UI: parent badge + Set Parent modal + login role-aware redirect

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

**Plans:** 4/4 plans complete

Plans:
- [ ] 20-01-PLAN.md — M3 theme migration: colors.xml, themes.xml, type.xml, Inter font (APPA-01, APPA-02)
- [ ] 20-02-PLAN.md — Dark mode 3-way + ₱ currency fix across all files (APPA-01, APPA-02) [Wave 2]
- [ ] 20-03-PLAN.md — Budget tracker: backend sheet + Android UI + Snackbar alerts (APPA-03, APPA-04) [Wave 3]
- [ ] 20-04-PLAN.md — Lost card flow: POST /api/student/lost-card + Android UI (APPA-05) [Wave 3]

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

### Phase 21: v1.1 Gap Closure + v1.2 Features

**Goal:** Close NFCA-01 and PAR-01–06 regressions from Phases 16/19, harden production config, and ship five v1.2 features: low-balance email, SMS notifications, multi-canteen station support, Arduino R3 auto-connect, and bulk CSV student import.

**Requirements:** V11-NFCA-01, V11-PAR-01-06, PROD-HARDEN, V12-EMAIL, V12-STATION, V12-ARDUINO-R3, V12-SMS, V12-CSV

**Depends on:** Phase 20.1

**Status:** ✓ Complete

**Plans:** 8/8 plans complete

Plans:
- [x] 21-01-PLAN.md — v1.1 Bug Fixes: FCM token registration, HCE token restore, parent login 503, delete stray google-services.json [Wave 1]
- [x] 21-02-PLAN.md — Production Hardening: remove 6 debug console.log, flip FLASK_DEBUG to false [Wave 1]
- [x] 21-03-PLAN.md — Low Balance Email + Multi-Station + Arduino R3 auto-connect [Wave 1]
- [x] 21-04-PLAN.md — SMS Notifications via Twilio [Wave 1]
- [x] 21-05-PLAN.md — Bulk CSV Student Import endpoint [Wave 1]
- [x] 21-06-PLAN.md — NFCA-01 Verification artifact [Wave 2]
- [x] 21-07-PLAN.md — PAR-01–06 Verification artifact [Wave 2]
- [x] 21-08-PLAN.md — Planning file updates: REQUIREMENTS, ROADMAP, STATE, PROJECT, CHANGELOG [Wave 3]

### Phase 22: 22

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 21
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 22 to break down)

### Phase 23: iPhone App Version

**Goal:** Build a native SwiftUI iOS student app (iOS 16+) with 7 screens: Login, Home, Transaction History, Receipt, Budget Tracker, Settings, Report Lost Card. Deployed via Codemagic CI/CD.

**Requirements:** REQ-23-01 through REQ-23-10

**Depends on:** Phase 22

**Status: ✓ Complete (2026-03-09)**

**Plans:** 6/6 complete ✓

Plans:
- [x] 23-01-PLAN.md — Xcode project scaffold: SwiftUI app target, folder structure, Info.plist, Codemagic CI setup
- [x] 23-02-PLAN.md — Auth layer: LoginView (PIN-based), AuthManager, KeychainHelper, APIClient/APIEndpoints stubs
- [x] 23-03-PLAN.md — Home + Transactions: HomeView (balance + recent txns), TransactionsView (paginated), TransactionRowView
- [x] 23-04-PLAN.md — Receipt + Budget: ReceiptView (line items + synthetic fallback), BudgetView (progress ring + alerts)
- [x] 23-05-PLAN.md — Settings + Lost Card: SettingsView (theme toggle + logout), LostCardView (POST /student/lost-card + Keychain flag)
- [x] 23-06-PLAN.md — Final build verification, Codemagic green build, Xcode Simulator human checkpoint, planning artifact updates

### Phase 24: Admin & Cashier Improvements

**Goal:** Add product soft-delete, dynamic product categories management, transaction void capability, and per-shift sales summary to the admin dashboard and cashier interface.

**Requirements:** ADM-24-01 (product delete), ADM-24-02 (dynamic categories), ADM-24-03 (void transactions), CASH-24-01 (shift summary)

**Depends on:** Phase 23

**Status:** ✓ Complete (2026-03-09)

**Plans:** 5/5 plans complete

Plans:
- [x] 24-01-PLAN.md — Bookkeeping: mark PAR-01–06 complete, add Phase 24 to ROADMAP, update STATE
- [x] 24-02-PLAN.md — Product soft-delete: DELETE /api/products/<id> backend + Delete button in products.html
- [x] 24-03-PLAN.md — Dynamic categories: _ensure_categories_sheet(), GET/POST/DELETE /api/categories backend + products.html UI
- [x] 24-04-PLAN.md — Void transactions: POST /api/transactions/<id>/void backend + ItemsJson in get_recent_transactions + transactions.html Actions column
- [x] 24-05-PLAN.md — Shift summary: session counters in cashier login + complete_sale + GET/POST shift endpoints + cashier_index.html panel

---

## Milestone v1.3 — Stability, Performance & Quality

**Created:** 2026-03-09
**Milestone:** v1.3 Stability, Performance & Quality
**Phase numbering:** Continues from v1.2 (Phase 24 completed)

Fix every known bug, close security holes, activate unused performance infrastructure (cache.py + resilience.py already exist but are never imported), and clean up tech debt across all four components: Flask backend, dashboard/web app, Android app, iOS app.

| Phase | Name | Requirements | Status |
|-------|------|--------------|--------|
| 25 | 1/2 | Complete    | 2026-03-09 |
| 26 | 1/1 | Complete    | 2026-03-09 |
| 27 | Critical Mobile Fixes | Complete    | 2026-03-09 |
| 28 | Backend Performance: Cache Infrastructure | Complete    | 2026-03-09 |
| 29 | Android Security & P1 Bugs | REQ-SEC-04, REQ-SEC-05, REQ-BUG-MOB-06, REQ-BUG-MOB-07 | Pending |
| 30 | iOS Bugs & UX | REQ-BUG-MOB-04, REQ-BUG-MOB-05, REQ-UX-01, REQ-UX-02, REQ-UX-03, REQ-UX-04, REQ-UX-05 | Pending |
| 31 | Dashboard & Backend P1 Fixes | REQ-BUG-05, REQ-BUG-06, REQ-BUG-07, REQ-BUG-08, REQ-SEC-06, REQ-QUAL-01, REQ-QUAL-02, REQ-CURR-01 | Pending |
| 32 | Mobile Budget Performance | REQ-PERF-06, REQ-PERF-07, REQ-PERF-08, REQ-PERF-09, REQ-PERF-10 | Pending |
| 33 | Backend Code Quality | REQ-BUG-09, REQ-QUAL-03, REQ-QUAL-04, REQ-QUAL-05, REQ-QUAL-06, REQ-QUAL-07, REQ-PERF-05 | Pending |
| 34 | Dashboard, Mobile Quality & Final Cleanup | REQ-BUG-10, REQ-BUG-11, REQ-BUG-12, REQ-QUAL-08, REQ-BUG-MOB-08, REQ-BUG-MOB-09, REQ-QUAL-09, REQ-QUAL-10, REQ-QUAL-11, REQ-QUAL-12, REQ-QUAL-13 | Pending |

**Total phases:** 10
**Total requirements:** 57

---

### Phase 25: Critical Backend Stability

**Goal:** The backend cannot double-spend a student's balance, cannot crash on email failure after a committed transaction, cannot serve to unauthorized origins, and its TTL cache is active.

**Requirements:** REQ-SEC-01, REQ-BUG-01, REQ-BUG-04, REQ-PERF-01

**Depends on:** Phase 24

**Status:** Pending

**Success criteria:**
- Balance debit uses atomic read-modify-write; two concurrent requests to the same card result in exactly one deduction (no double-spend)
- CORS in production `wsgi.py` is restricted to configured origins; `*` wildcard is gone
- Email failure during an already-committed cashier transaction is caught silently; the transaction still returns 200 to the client
- `cache.py` TTLCache is imported and active in `api_server.py`; repeated calls within TTL period skip Google Sheets entirely

**Plans:** 2/2 plans complete

Plans:
- [x] 25-01-PLAN.md — Per-card threading locks in nfc_pay() + process_cashier_transaction(); silent email try/except (REQ-BUG-01, REQ-BUG-04)
- [x] 25-02-PLAN.md — CORS wildcard → production domain in wsgi.py; TTL cache wired to all users_sheet reads (REQ-SEC-01, REQ-PERF-01)

---

### Phase 26: Critical Dashboard Stability

**Goal:** No dashboard route crashes with a NameError; the Thai Baht symbol is gone from every UI string.

**Requirements:** REQ-BUG-02, REQ-BUG-03, REQ-CURR-02

**Depends on:** Phase 25

**Status:** Pending

**Success criteria:**
- Navigating to `add_category`, `delete_category`, and `void_transaction` routes returns 200/302 (no `NameError` on `@admin_required`)
- Calling `GET /api/categories` returns data (no `NameError` from undefined `get_db()`)
- All ฿ occurrences in cashier UI and dashboard HTML templates are replaced with ₱

**Plans:** 1/1 plans complete

Plans:
- [ ] 26-01-PLAN.md — Fix @admin_required NameError, get_db() NameError, and replace ฿ with ₱ (REQ-BUG-02, REQ-BUG-03, REQ-CURR-02)

---

### Phase 27: Critical Mobile Fixes

**Goal:** Lost card state persists across app restarts on both platforms; iOS never crashes via `fatalError`; Android release build uses HTTPS only and NFC payment authorization is not publicly bypassable.

**Requirements:** REQ-BUG-MOB-01, REQ-BUG-MOB-02, REQ-BUG-MOB-03, REQ-SEC-02, REQ-SEC-03

**Depends on:** Phase 24 (can run parallel to 25/26)

**Status:** Pending

**Success criteria:**
- Reporting a lost card on iOS, killing the app, and relaunching still shows the lost card state
- Reporting a lost card on Android, killing the app, and relaunching still shows the lost card state
- No `fatalError()` call paths remain in `APIClient.swift`; URL construction errors produce a logged error instead of a crash
- Android release manifest does not contain `usesCleartextTraffic="true"` (all API traffic is HTTPS)
- `BankoHceService.isPaymentAuthorized` is not a public writable static field; external code cannot authorize a payment without the PIN/biometric gate

**Plans:** 2/2 plans complete

Plans:
- [ ] 27-01-PLAN.md — iOS Critical Fixes: add cardStatus to Student model, add invalidURL to APIError, replace fatalErrors, fix isCardLost persistence (REQ-BUG-MOB-01, REQ-BUG-MOB-03)
- [ ] 27-02-PLAN.md — Android Critical Fixes: clear isCardLost on login, move cleartext to debug-only source set, encapsulate NFC payment state (REQ-BUG-MOB-02, REQ-SEC-02, REQ-SEC-03)

---

### Phase 28: Backend Performance — Cache Infrastructure

**Goal:** NFC payment path drops from 7–9 sequential Sheets API calls to ≤3; cashier transaction reads the users sheet once (not thrice); per-user transaction query filters at the sheet level.

**Requirements:** REQ-PERF-02, REQ-PERF-03, REQ-PERF-04

**Depends on:** Phase 25 (cache.py wired first)

**Status:** Pending

**Success criteria:**
- NFC payment path makes ≤3 Google Sheets API calls (verifiable by code review or gspread call instrumentation)
- Cashier transaction handler reads the users sheet exactly once per transaction (not 3×)
- Per-user transaction listing fetches only that student's rows from the sheet; no all-users fetch + Python filter

**Plans:** 2/2 plans complete

Plans:
- [ ] 28-01-PLAN.md — Cache VirtualCards + Transactions Log in api_server.py; eliminate redundant Money Accounts header call; add missing invalidations
- [ ] 28-02-PLAN.md — Import cache helpers into cashier_routes.py; replace both raw Users sheet reads with shared users_all cache

---

### Phase 29: Android Security & P1 Bugs

**Goal:** Android backup does not expose the NFC card token; PIN is stored as a one-way hash; budget tracks only spending (not top-ups); recycled list rows always respond to taps.

**Requirements:** REQ-SEC-04, REQ-SEC-05, REQ-BUG-MOB-06, REQ-BUG-MOB-07

**Depends on:** Phase 27 (mobile P0 fixes complete)

**Status:** Pending

**Success criteria:**
- Android backup rules exclude the NFC card token key/file; Google Drive restore does not restore a token
- PIN is verified via a one-way hash (SHA-256 or equivalent); the raw PIN string is never persisted
- Budget tracker monthly spend sum includes only `Purchase` and `NFC Purchase` transaction types; top-ups are excluded
- Tapping any row in the transactions `RecyclerView` (including reused ViewHolders) fires the click handler reliably

**Plans:** TBD (run `/gsd-plan-phase 29` to break down)

Plans:
- [ ] TBD

---

### Phase 30: iOS Bugs & UX

**Goal:** iOS correctly distinguishes lost card from unauthorized; handles token expiry gracefully; and closes five UX papercuts on the budget, transactions, and login screens.

**Requirements:** REQ-BUG-MOB-04, REQ-BUG-MOB-05, REQ-UX-01, REQ-UX-02, REQ-UX-03, REQ-UX-04, REQ-UX-05

**Depends on:** Phase 27 (mobile P0 fixes complete)

**Status:** Pending

**Success criteria:**
- A blocked/lost card shows "card reported lost" (not "wrong PIN") to the student
- A 401 response triggers an automatic re-authentication prompt; the app does not stay in a broken authenticated state
- Typing in the budget input field before the server response arrives keeps the user's typed value (server load does not overwrite it)
- Transactions list shows a "No transactions yet" empty state when the list is empty
- Sign In button is fully visible on iPhone SE when the keyboard is open (no keyboard overlap)
- PIN login field does not trigger iOS password autofill suggestions

**Plans:** TBD (run `/gsd-plan-phase 30` to break down)

Plans:
- [ ] TBD

---

### Phase 31: Dashboard & Backend P1 Fixes

**Goal:** Socket errors surface correct messages; TXN IDs are collision-free; WriteQueue discards poisoned items; sessions expire under multi-worker deployment; Finance credential is env-guarded; auth is consolidated to one system; dashboard code lives in one place; FCM uses ₱.

**Requirements:** REQ-BUG-05, REQ-BUG-06, REQ-BUG-07, REQ-BUG-08, REQ-SEC-06, REQ-QUAL-01, REQ-QUAL-02, REQ-CURR-01

**Depends on:** Phase 26 (dashboard P0 fixes done), Phase 28 (backend P1 perf done)

**Status:** Pending

**Success criteria:**
- `card_error` socket event modal displays the actual error message (not "undefined")
- Two transactions submitted within the same second receive distinct TXN IDs
- A permanently-failing `WriteQueue` item is dropped after configured retries and an error is logged; no infinite loop
- `active_sessions` entries expire after their TTL; behavior is consistent across gunicorn workers (no shared-memory assumption)
- Finance dashboard raises a startup error if `FINANCE_PASSWORD` is missing or set to the default `finance2025` value
- `generate_jwt_token()` dead code is removed; one auth system handles all student sessions
- `admin_dashboard.py` / `web_app.py` duplication is eliminated; fixes need only be applied once
- FCM low-balance push notification body uses ₱ (not ฿)

**Plans:** TBD (run `/gsd-plan-phase 31` to break down)

Plans:
- [ ] TBD

---

### Phase 32: Mobile Budget Performance

**Goal:** Budget spend calculation no longer requires loading 200 transactions on either mobile platform; a new backend endpoint serves pre-aggregated monthly spend; iOS DateFormatter is not re-allocated on every render.

**Requirements:** REQ-PERF-06, REQ-PERF-07, REQ-PERF-08, REQ-PERF-09, REQ-PERF-10

**Depends on:** Phase 28 (backend perf groundwork), Phase 29 (Android P1 bugs), Phase 30 (iOS P1 bugs)

**Status:** Pending

**Success criteria:**
- `GET /api/budget-summary` endpoint returns the authenticated student's current-month spend total without returning individual transactions
- iOS `BudgetViewModel` calls `/api/budget-summary`; it does not fetch the full transactions list to calculate spend
- Android budget screen calls `/api/budget-summary`; it does not fetch 200 transactions client-side
- iOS `DateFormatter` instance is static/cached; not created on every `ReceiptView` or `BudgetViewModel` render pass
- Android `TransactionsAdapter` uses `DiffUtil` for list updates; `notifyDataSetChanged()` is removed

**Plans:** TBD (run `/gsd-plan-phase 32` to break down)

Plans:
- [ ] TBD

---

### Phase 33: Backend Code Quality

**Goal:** Backend has one canonical time utility; no bare excepts; no null-body crashes; sys.path mutations are module-level; ConnectionPool is used; Firebase initializes safely.

**Requirements:** REQ-BUG-09, REQ-QUAL-03, REQ-QUAL-04, REQ-QUAL-05, REQ-QUAL-06, REQ-QUAL-07, REQ-PERF-05

**Depends on:** Phase 31 (auth consolidation and duplication removal first)

**Status:** Pending

**Success criteria:**
- `get_philippines_time()` exists in exactly one shared utility module; all four previous inline copies removed
- Zero bare `except:` clauses remain in backend Python files; all use specific exception types
- Any endpoint receiving `Content-Type: application/json` with an empty or missing body returns `400 Bad Request` (not 500 crash)
- All `sys.path.insert` calls are at module level; none are inside request handler functions
- `ConnectionPool` from `connection_pool.py` is used for gspread client acquisition; the pool module is no longer dead code
- `firebase_admin.initialize_app()` is called exactly once; concurrent-init race condition is eliminated
- Hardcoded column `C` for balance in cashier transaction handler is replaced with a header-name lookup

**Plans:** TBD (run `/gsd-plan-phase 33` to break down)

Plans:
- [ ] TBD

---

### Phase 34: Dashboard, Mobile Quality & Final Cleanup

**Goal:** Dashboard PWA installs cleanly; no phantom 404 polls; products page has no stacked listeners; login backgrounds load from stable URLs; server URLs are environment-configurable on both mobile platforms; Android coroutine and iOS Keychain papercuts resolved.

**Requirements:** REQ-BUG-10, REQ-BUG-11, REQ-BUG-12, REQ-QUAL-08, REQ-BUG-MOB-08, REQ-BUG-MOB-09, REQ-QUAL-09, REQ-QUAL-10, REQ-QUAL-11, REQ-QUAL-12, REQ-QUAL-13

**Depends on:** Phase 31 (dashboard duplication removed), Phase 32 (mobile perf done)

**Status:** Pending

**Success criteria:**
- PWA service worker references only files that exist; `npm run build` (or equivalent) confirms no 404 on install
- Browser network tab shows zero polling requests to `/api/queue/status` or `/api/queue/process`
- Products page makes exactly one API call per button click regardless of how many times `renderTable()` has been called
- Dashboard login background images load successfully (no expired CDN token URLs)
- Android server base URL is read from `BuildConfig` / environment variable; `ApiClient.kt` contains no hardcoded production URL
- iOS server base URL is read from a build config plist or environment; `APIEndpoints.swift` contains no hardcoded URL
- Android `NfcManager` coroutines use the Activity/ViewModel lifecycle scope; no `CoroutineScope(Dispatchers.IO).launch` memory leaks
- iOS theme preference is stored in `UserDefaults` (not Keychain)
- `isPurchaseType` helper exists in exactly one iOS file; the duplicate is removed
- Android `ReceiptActivity` cast uses safe `as?` with a null-check; unchecked `as LinearLayout` cast removed

---

## v1.3 Requirements Coverage

| Requirement | Phase | Priority | Status |
|-------------|-------|----------|--------|
| REQ-SEC-01 | 25 | P0 | ✅ Complete |
| REQ-BUG-01 | 25 | P0 | ✅ Complete |
| REQ-BUG-04 | 25 | P0 | ✅ Complete |
| REQ-PERF-01 | 25 | P0 | ✅ Complete |
| REQ-BUG-02 | 26 | P0 | Pending |
| REQ-BUG-03 | 26 | P0 | Pending |
| REQ-CURR-02 | 26 | P1 | Pending |
| REQ-BUG-MOB-01 | 27 | P0 | Pending |
| REQ-BUG-MOB-02 | 27 | P0 | Pending |
| REQ-BUG-MOB-03 | 27 | P0 | Pending |
| REQ-SEC-02 | 27 | P0 | Pending |
| REQ-SEC-03 | 27 | P0 | Pending |
| REQ-PERF-02 | 28 | P1 | Pending |
| REQ-PERF-03 | 28 | P1 | Pending |
| REQ-PERF-04 | 28 | P1 | Pending |
| REQ-SEC-04 | 29 | P1 | Pending |
| REQ-SEC-05 | 29 | P1 | Pending |
| REQ-BUG-MOB-06 | 29 | P1 | Pending |
| REQ-BUG-MOB-07 | 29 | P1 | Pending |
| REQ-BUG-MOB-04 | 30 | P1 | Pending |
| REQ-BUG-MOB-05 | 30 | P1 | Pending |
| REQ-UX-01 | 30 | P2 | Pending |
| REQ-UX-02 | 30 | P2 | Pending |
| REQ-UX-03 | 30 | P2 | Pending |
| REQ-UX-04 | 30 | P2 | Pending |
| REQ-UX-05 | 30 | P2 | Pending |
| REQ-BUG-05 | 31 | P1 | Pending |
| REQ-BUG-06 | 31 | P1 | Pending |
| REQ-BUG-07 | 31 | P1 | Pending |
| REQ-BUG-08 | 31 | P1 | Pending |
| REQ-SEC-06 | 31 | P1 | Pending |
| REQ-QUAL-01 | 31 | P1 | Pending |
| REQ-QUAL-02 | 31 | P1 | Pending |
| REQ-CURR-01 | 31 | P1 | Pending |
| REQ-PERF-06 | 32 | P2 | Pending |
| REQ-PERF-07 | 32 | P2 | Pending |
| REQ-PERF-08 | 32 | P2 | Pending |
| REQ-PERF-09 | 32 | P2 | Pending |
| REQ-PERF-10 | 32 | P2 | Pending |
| REQ-BUG-09 | 33 | P2 | Pending |
| REQ-QUAL-03 | 33 | P2 | Pending |
| REQ-QUAL-04 | 33 | P2 | Pending |
| REQ-QUAL-05 | 33 | P2 | Pending |
| REQ-QUAL-06 | 33 | P2 | Pending |
| REQ-QUAL-07 | 33 | P2 | Pending |
| REQ-PERF-05 | 33 | P2 | Pending |
| REQ-BUG-10 | 34 | P2 | Pending |
| REQ-BUG-11 | 34 | P2 | Pending |
| REQ-BUG-12 | 34 | P2 | Pending |
| REQ-QUAL-08 | 34 | P2 | Pending |
| REQ-BUG-MOB-08 | 34 | P2 | Pending |
| REQ-BUG-MOB-09 | 34 | P2 | Pending |
| REQ-QUAL-09 | 34 | P2 | Pending |
| REQ-QUAL-10 | 34 | P2 | Pending |
| REQ-QUAL-11 | 34 | P2 | Pending |
| REQ-QUAL-12 | 34 | P3 | Pending |
| REQ-QUAL-13 | 34 | P3 | Pending |

**57 / 57 requirements covered. 0 unmapped.**

---

### Phase 20.1: Arduino PN532 NFC Backend Integration, Student App Payment & Firmware Hardening (INSERTED)

**Goal:** Complete the end-to-end NFC phone-tap payment flow: R3 firmware adds APDU HCE exchange to read 48-char token from student phones; R4 firmware swaps MFRC522 for PN532 and POSTs to `/api/nfc/pay`; ArduinoBridge parses `NFC|<token>` serial lines and forwards payment; Cashier UI shows blue NFC modal and result state.

**Requirements:** NFC-R3-APDU, NFC-R4-SWAP, NFC-BRIDGE-PARSE, NFC-BRIDGE-EMIT, NFC-BRIDGE-POST, NFC-UI-MODAL, NFC-UI-RESULT

**Depends on:** Phase 20

**Status: ✓ Complete (2026-03-07)**

**Plans:** 3/3 complete ✓

Plans:
- [x] 20.1-01-PLAN.md — Firmware: R3 APDU dual-mode (NFC|token + CARD|uid fallback) + R4 PN532 swap with /api/nfc/pay POST [Wave 1]
- [x] 20.1-02-PLAN.md — Backend: ArduinoBridge NFC serial parsing, nfc_payment SocketIO emit, _post_nfc_payment daemon thread [Wave 2]
- [x] 20.1-03-PLAN.md — Cashier UI: nfc_payment blue modal (#2196F3), nfc_payment_result handler, retry button [Wave 2]
