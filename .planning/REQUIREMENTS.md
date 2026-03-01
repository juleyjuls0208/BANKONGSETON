# Requirements: BankongSeton

**Defined:** 2026-02-22
**Core Value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app

## v1 Requirements

Requirements for this milestone. Backend-first, then mobile improvements, then documentation.

### Bug Fixes

- [x] **BUG-01**: Cashier POS app displays the product menu correctly (currently broken — no products shown)
- [x] **BUG-02**: Null/empty card UID is rejected at input boundary (not silently treated as valid)
- [x] **BUG-03**: Google Sheets API failures return graceful error responses (not 500 crashes)
- [x] **BUG-04**: Admin login requires non-empty credentials (empty string is not a valid login)
- [x] **BUG-05**: Transaction balance deduction is protected against partial failure (no half-committed state)

### Security

- [x] **SEC-01**: Credentials (admin username/password) are never printed to stdout or logs at startup
- [x] **SEC-02**: FLASK_SECRET_KEY is required non-empty (system refuses to start with default key)
- [x] **SEC-03**: CORS is restricted to known origins (no wildcard `*` in production)
- [x] **SEC-04**: Card UIDs are validated (regex format check) before use in Sheets queries
- [x] **SEC-05**: Test files do not contain hardcoded secrets (JWT keys, passwords use env vars)

### Code Quality

- [x] **QUAL-01**: All 60+ debug print() statements replaced with structured logging (get_logger())
- [x] **QUAL-02**: Card UID normalization centralized in a single utility function (backend/utils.py)
- [x] **QUAL-03**: Global state in admin_dashboard.py wrapped in thread-safe singleton with locking
- [x] **QUAL-04**: Dead code removed (BankongSetonApp folder, unused files)
- [x] **QUAL-05**: oauth2client replaced with google-auth library (deprecated dependency)

### Product Management

- [ ] **PROD-01**: Admin can add a canteen product (name, price, category)
- [ ] **PROD-02**: Admin can edit an existing product (name, price, category)
- [ ] **PROD-03**: Admin can delete/deactivate a product
- [ ] **PROD-04**: Cashier POS displays all active products in a grid with name and price
- [ ] **PROD-05**: Products are stored in Google Sheets (a dedicated Products sheet)
- [ ] **PROD-06**: Cashier can select multiple products and process them as one transaction

### Student App — Balance & History

- [x] **APP-01**: Student can see their current card balance on the home screen
- [x] **APP-02**: Student can see a scrollable list of all their transactions (date, amount, type)
- [x] **APP-03**: Student can tap a canteen purchase transaction and see the itemized receipt (what was bought, price per item, total)
- [x] **APP-04**: Student app shows balance update immediately after a transaction is processed
- [x] **APP-05**: Student app handles API errors gracefully (shows error message, not crash)

### Notifications

- [x] **NOTF-01**: Student receives a push notification when their balance drops below a configurable threshold
- [x] **NOTF-02**: Admin can configure the low-balance threshold value per student or globally

### NFC Architecture Preparation (Backend Only)

- [x] **NFC-01**: NFC payment API endpoints exist and are documented (`/api/nfc/register`, `/api/nfc/pay`)
- [x] **NFC-02**: VirtualCard model in nfc_payments.py is fully integrated with Google Sheets (persisted, not just in-memory)
- [x] **NFC-03**: Transaction flow accepts both RFID card UID and NFC virtual card token as payment sources
- [x] **NFC-04**: API authentication supports NFC device token alongside JWT (ready for Android HCE integration)
- [x] **NFC-05**: NFC integration guide written in docs/ explaining exactly what the Android app needs to implement for v2

### Documentation

- [x] **DOC-01**: `docs/architecture.md` — system overview, layers, data flow, entry points
- [x] **DOC-02**: `docs/api-reference.md` — all REST API endpoints, request/response format, auth
- [x] **DOC-03**: `docs/google-sheets-schema.md` — all Sheets structure (columns, purpose, relationships)
- [x] **DOC-04**: `docs/cashier-guide.md` — how cashier POS works, Arduino setup, card reading flow
- [x] **DOC-05**: `docs/student-app.md` — Android app architecture, screens, API calls
- [x] **DOC-06**: `docs/nfc-integration-guide.md` — step-by-step guide for implementing NFC in Android (v2 prep)
- [x] **DOC-07**: `docs/admin-guide.md` — admin dashboard features, roles, product management
- [x] **DOC-08**: `docs/setup.md` — environment setup, Google Sheets creation, credentials, first run

## v2 Requirements

Deferred to next version (not in current roadmap).

### NFC Android

- **NFCA-01**: Android app registers phone as NFC virtual card via HCE
- **NFCA-02**: Student taps phone at NFC-enabled cashier terminal to pay
- **NFCA-03**: NFC payment syncs with RFID card balance (same account)

### Advanced Features

- **ADV-01**: CSV/Excel export of transaction reports with date range filter
- **ADV-02**: Bulk student registration (import from CSV)
- **ADV-03**: Multiple canteen stations with consolidated reporting

## Out of Scope

| Feature | Reason |
|---------|--------|
| NFC Android implementation | Hardware only supports RFID; architected for next version |
| SMS notifications | Email + push only for now |
| Production cloud deployment | Out of milestone scope |
| SQL database migration | Google Sheets working; migration adds complexity without clear benefit |
| Flutter port | Android (Kotlin/Compose) is the target |
| iOS app | Android-only for this project |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUG-01 | Phase 1 - Critical Fixes + Security | Complete |
| BUG-02 | Phase 1 - Critical Fixes + Security | Complete |
| BUG-03 | Phase 1 - Critical Fixes + Security | Complete |
| BUG-04 | Phase 1 - Critical Fixes + Security | Complete |
| BUG-05 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-01 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-02 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-03 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-04 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-05 | Phase 1 - Critical Fixes + Security | Complete |
| QUAL-01 | Phase 2 - Code Quality | Complete |
| QUAL-02 | Phase 2 - Code Quality | Complete |
| QUAL-03 | Phase 2 - Code Quality | Complete |
| QUAL-04 | Phase 2 - Code Quality | Complete |
| QUAL-05 | Phase 2 - Code Quality | Complete |
| PROD-01 | Phase 3 - Product Management | Pending |
| PROD-02 | Phase 3 - Product Management | Pending |
| PROD-03 | Phase 3 - Product Management | Pending |
| PROD-04 | Phase 3 - Product Management | Pending |
| PROD-05 | Phase 3 - Product Management | Pending |
| PROD-06 | Phase 3 - Product Management | Pending |
| APP-01 | Phase 4 - Student App + Notifications | Complete |
| APP-02 | Phase 4 - Student App + Notifications | Complete |
| APP-03 | Phase 4 - Student App + Notifications | Complete |
| APP-04 | Phase 4 - Student App + Notifications | Complete |
| APP-05 | Phase 4 - Student App + Notifications | Complete |
| NOTF-01 | Phase 4 - Student App + Notifications | Complete |
| NOTF-02 | Phase 4 - Student App + Notifications | Complete |
| NFC-01 | Phase 5 - NFC Architecture Prep | Complete |
| NFC-02 | Phase 5 - NFC Architecture Prep | Complete |
| NFC-03 | Phase 5 - NFC Architecture Prep | Complete |
| NFC-04 | Phase 5 - NFC Architecture Prep | Complete |
| NFC-05 | Phase 5 - NFC Architecture Prep | Complete |
| DOC-01 | Phase 6 - Documentation | Complete |
| DOC-02 | Phase 6 - Documentation | Complete |
| DOC-03 | Phase 6 - Documentation | Complete |
| DOC-04 | Phase 6 - Documentation | Complete |
| DOC-05 | Phase 6 - Documentation | Complete |
| DOC-06 | Phase 6 - Documentation | Complete |
| DOC-07 | Phase 6 - Documentation | Complete |
| DOC-08 | Phase 6 - Documentation | Complete |

**Coverage:**
- v1 requirements: 41 total
- Mapped to phases: 41
- Unmapped: 0

---
*Requirements defined: 2026-02-22*
*Last updated: 2026-02-22 — Traceability finalized after roadmap creation*
