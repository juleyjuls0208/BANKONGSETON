# BankongSeton

## What This Is

BankongSeton is a school canteen cashless payment system for students. Students tap RFID cards at cashier stations (Arduino + card reader) to pay for food. An Android app lets students check their balance, view purchase history with itemized receipts, and receive low-balance push notifications. Admins manage the canteen menu and monitor transactions through a web dashboard that runs both locally (with Arduino hardware) and as a hosted web app (PythonAnywhere, manual payment mode). The NFC backend is fully built and ready for Android HCE integration in v2.

## Core Value

Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app — no cash needed.

## Requirements

### Validated

- ✓ RFID card payment via Arduino cashier stations — existing
- ✓ Student dual-card system (student ID card + money card) — existing
- ✓ Google Sheets persistence via gspread — existing
- ✓ JWT authentication (admin, cashier, student roles) — existing
- ✓ Flask REST API for Android app — existing
- ✓ Admin web dashboard with role-based access — existing
- ✓ Lost card reporting — existing
- ✓ Email notifications — existing
- ✓ Multi-station transaction sync with locking — existing
- ✓ Analytics engine (spending patterns, reports) — existing
- ✓ Cashier POS displays and sells products correctly — v1.0 (BUG-01, BUG-02–05)
- ✓ All credentials secured; CORS restricted; startup guard on FLASK_SECRET_KEY — v1.0 (SEC-01–05)
- ✓ 60+ print() statements replaced with structured logging — v1.0 (QUAL-01–05)
- ✓ Product/menu management system (add, edit, deactivate items) — v1.0 (PROD-01–06)
- ✓ Student balance, transaction history, itemized receipts in Android app — v1.0 (APP-01–05)
- ✓ Low-balance FCM push notification from cashier POS path — v1.0 (NOTF-01–02)
- ✓ NFC backend: VirtualCard, /api/nfc/register, /api/nfc/pay, simulation UI — v1.0 (NFC-01–05)
- ✓ Full documentation (architecture, API, Sheets schema, cashier, student app, NFC guide, admin, setup) — v1.0 (DOC-01–08)
- ✓ Web-deployable dashboard with manual payment fallback (PythonAnywhere-compatible) — v1.0
- ✓ Cashier credentials and JWT secret loaded from environment only (no hardcoded fallbacks) — v1.0

### Active

- [ ] NFC Android HCE implementation (BankoHceService + registration flow in student app)
- [ ] NFC Purchase receipt navigation in TransactionsAdapter (currently only 'Purchase' type opens ReceiptActivity)
- [ ] ReceiptActivity: display items for NFC Purchase type (distinct from cashier receipt path)
- [ ] Admin web dashboard: full UI/UX overhaul (modern CSS framework, charts, analytics)
- [ ] Arduino UNO R4 WiFi: firmware + Flask WiFi endpoint (cable-free card reader)
- [ ] Parent portal: view-only balance + spending history (new parent role, linked at card registration)
- [ ] Card registration: dual email (student required, parent optional)
- [ ] Student app redesign: modern UI/UX + dark mode
- [ ] Student app: spending summary / monthly budget with alerts
- [ ] Student app: in-app lost card report
- [ ] Admin: balance top-up (credit student cards from dashboard)
- [ ] Admin: transaction CSV export

### Out of Scope

- Android full rewrite — app is functional; targeted improvements only for v1.1
- SMS notifications — FCM push covers the use case
- Production cloud deployment — PythonAnywhere hosting is sufficient
- SQL database migration — Google Sheets is working well; migration adds risk without clear benefit
- Flutter/iOS port — Android Kotlin only

## Context

- **Codebase:** ~12,700 LOC Python, ~3,600 LOC Kotlin, ~20,900 LOC HTML/templates; 226 commits
- **Tech stack:** Flask (Python), gspread (Google Sheets DB), Flask-SocketIO, Firebase Admin SDK (FCM), Kotlin + Jetpack Compose, Arduino/RFID (pyserial)
- **Deployment:** PythonAnywhere via wsgi.py; web_app.py is the web-mode entry point (no Arduino dependency); cashier_routes.py blueprint shared by both modes
- **Hardware:** Arduino + RFID readers at cashier stations; serial comms via pyserial; NFC hardware not yet deployed (backend ready)
- **Mobile app:** `mobile/student_app_v2/` — active Kotlin+Compose app with all v1 screens (Home, Transactions, Receipt, Settings)
- **Known limitations:** WebSocket silently rejected on PythonAnywhere (acceptable); Arduino bridge path is hardware-dependent (tech debt TD-01)

## Constraints

- **Database:** Google Sheets via gspread — keep as-is; no migration to SQL
- **Hardware:** RFID for v1; NFC hardware pending (backend architected for next version)
- **Language:** Python (Flask) for backend; Kotlin (Jetpack Compose) for Android
- **Timezone:** Asia/Manila (Philippines) throughout
- **Platform:** Android min SDK 24; Flask on PythonAnywhere (WSGI)
- **Deployment:** Live on PythonAnywhere — changes must remain WSGI-compatible; no serial port in production

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep Google Sheets as database | Already working; visual data in Sheets; no migration needed | ✓ Good — worked well throughout; gspread stable |
| Fix backend first, mobile app second | Cashier POS broken — most critical blocker | ✓ Good — backend stability unlocked all other features |
| NFC: architect now, implement Android side next version | RFID only; can't test NFC hardware yet | ✓ Good — full NFC backend ready; simulation UI added |
| Documentation as Markdown files in /docs/ | User needs to explain codebase to peers | ✓ Good — 8 docs files fully cover all subsystems |
| Startup guard at module level (not __main__) | Fires on WSGI import too, not just direct run | ✓ Good — catches misconfiguration before first request |
| CORS dev-mode localhost auto-allow | Simplifies local development without env var changes | ✓ Good — no dev friction reported |
| Field-specific 400 errors for empty credentials | Better UX than generic "invalid login" | ✓ Good — clearer error messages |
| threading.Lock (not RLock) for CardReaderState | get/set/update don't call each other; no re-entrancy needed | ✓ Good — no deadlocks |
| web_app.py web-deployable mode via try/except serial import | Allows same codebase for local + PythonAnywhere | ✓ Good — PythonAnywhere deployment works |
| JWT_SECRET guard blocks empty/missing only | Secrets startup pattern already catches insecure defaults | ✓ Good — belt-and-suspenders with record_once callback |
| Single card token for NFC pay (no X-Device-Token) | Simpler contract; APDU path can't add HTTP headers | ✓ Good — NFC-04 gap closed; Android integration straightforward |
| Transaction type 'NFC Purchase' distinct from 'Purchase' | Enables Android filtering by payment type | ✓ Good — TransactionsAdapter can separate NFC vs cashier |

---
*Last updated: 2026-03-09 after v1.3 planning complete (Phases 25–34 defined)*

## Previous Milestone: v1.2 — v1.1 Gap Closure + v1.2 Features

**Goal:** Close NFCA-01 and PAR-01–06 regressions, harden production config, and ship five v1.2 features: low-balance email, SMS notifications, multi-canteen station support, Arduino R3 auto-connect, and bulk CSV student import.

**Status: ✓ Complete (2026-03-08)**

## Current Milestone: v1.3 — Stability, Performance & Quality

**Goal:** Fix every known bug, close security holes, activate unused performance infrastructure (`cache.py` and `resilience.py` exist but are never imported), and clean up tech debt across all four components: Flask backend, dashboard/web app, Android app, and iOS app.

**Phases:** 25–34 (10 phases)
**Requirements:** 57 REQ-IDs across 7 categories (see REQUIREMENTS.md)
**Status: In Progress — Phase 25 next**
