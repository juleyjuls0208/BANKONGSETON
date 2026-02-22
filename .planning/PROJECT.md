# BankongSeton

## What This Is

BankongSeton is a school canteen cashless payment system for students. Students tap RFID cards at cashier stations (Arduino + card reader) to pay for food. An Android app lets students check their balance and view purchase history. Admins and finance staff manage the system through a web dashboard.

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

### Active

- [ ] Fix cashier app: products not displaying — critical bug
- [ ] Fix known bugs (null card UID, missing error handling, empty credential login)
- [ ] Security hardening (CORS wildcard, credential exposure in logs, input validation)
- [ ] Replace 60+ debug print statements with proper structured logging
- [ ] Centralize card UID normalization (currently duplicated)
- [ ] Product/menu management system (add, edit, remove canteen items with prices)
- [ ] Transaction detail: show items bought + price when student taps a canteen purchase
- [ ] Student balance view in Android app
- [ ] Student transaction history view in Android app
- [ ] Low-balance push notification to students
- [ ] NFC backend architecture prep (API contracts, VirtualCard integration, so Android NFC works in next version)
- [ ] Comprehensive Markdown documentation in /docs (one file per major component)

### Out of Scope

- Android app full rewrite — backend fixes first; app addressed after backend is solid
- NFC Android implementation — hardware parts only support RFID now; architecture prepared but Android NFC build is next version
- Production cloud deployment — not part of this milestone
- SMS notifications — email only for now

## Context

- **Hardware:** Arduino + RFID readers at each cashier station; serial communication via pyserial
- **Existing NFC module:** `backend/nfc_payments.py` has VirtualCard/HCE infrastructure but Android app doesn't call it yet
- **Mobile app:** `mobile/student_app_v2/` is the active app (Kotlin + Jetpack Compose); original app was wiped
- **Cashier POS:** `backend/dashboard/cashier/cashier_routes.py` — currently broken (products don't display)
- **Two app folders exist:** `BankongSetonApp` and `student_app_v2` — v2 is active; BankongSetonApp can be removed
- **Security issues:** Default credentials printed to stdout at startup; CORS set to wildcard; empty credentials accepted as valid login
- **Tech debt:** 60+ print() statements should be proper logging; card normalization duplicated; global state not thread-safe

## Constraints

- **Database:** Google Sheets via gspread — keep as-is; no migration to SQL
- **Hardware:** RFID only for v1; NFC hardware not available yet (architected for next version)
- **Language:** Python (Flask) for backend; Kotlin (Jetpack Compose) for Android
- **Timezone:** Asia/Manila (Philippines) throughout
- **Platform:** Android min SDK 24; desktop server (Windows/Linux) for Flask

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep Google Sheets as database | Already working; user wants visual data in Sheets; no SQL migration | — Pending |
| Fix backend first, mobile app second | Backend bugs (cashier POS broken) are most critical | — Pending |
| NFC: architect now, implement Android side next version | RFID hardware only; can't test NFC yet | — Pending |
| Documentation as Markdown files in /docs/ | User needs to explain codebase to peers | — Pending |

---
*Last updated: 2026-02-22 after initialization*
