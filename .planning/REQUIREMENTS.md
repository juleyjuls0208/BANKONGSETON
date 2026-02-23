# Requirements: BankongSeton

**Defined:** 2026-02-22
**Core Value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app

## v1 Requirements

Requirements for this milestone. Backend-first, then mobile improvements, then documentation.

### Bug Fixes

- [ ] **BUG-01**: Cashier POS app displays the product menu correctly (currently broken — no products shown)
- [ ] **BUG-02**: Null/empty card UID is rejected at input boundary (not silently treated as valid)
- [ ] **BUG-03**: Google Sheets API failures return graceful error responses (not 500 crashes)
- [ ] **BUG-04**: Admin login requires non-empty credentials (empty string is not a valid login)
- [ ] **BUG-05**: Transaction balance deduction is protected against partial failure (no half-committed state)

### Security

- [x] **SEC-01**: Credentials (admin username/password) are never printed to stdout or logs at startup
- [x] **SEC-02**: FLASK_SECRET_KEY is required non-empty (system refuses to start with default key)
- [x] **SEC-03**: CORS is restricted to known origins (no wildcard `*` in production)
- [ ] **SEC-04**: Card UIDs are validated (regex format check) before use in Sheets queries
- [ ] **SEC-05**: Test files do not contain hardcoded secrets (JWT keys, passwords use env vars)

### Code Quality

- [ ] **QUAL-01**: All 60+ debug print() statements replaced with structured logging (get_logger())
- [ ] **QUAL-02**: Card UID normalization centralized in a single utility function (backend/utils.py)
- [ ] **QUAL-03**: Global state in admin_dashboard.py wrapped in thread-safe singleton with locking
- [ ] **QUAL-04**: Dead code removed (BankongSetonApp folder, unused files)
- [ ] **QUAL-05**: oauth2client replaced with google-auth library (deprecated dependency)

### Product Management

- [ ] **PROD-01**: Admin can add a canteen product (name, price, category)
- [ ] **PROD-02**: Admin can edit an existing product (name, price, category)
- [ ] **PROD-03**: Admin can delete/deactivate a product
- [ ] **PROD-04**: Cashier POS displays all active products in a grid with name and price
- [ ] **PROD-05**: Products are stored in Google Sheets (a dedicated Products sheet)
- [ ] **PROD-06**: Cashier can select multiple products and process them as one transaction

### Student App — Balance & History

- [ ] **APP-01**: Student can see their current card balance on the home screen
- [ ] **APP-02**: Student can see a scrollable list of all their transactions (date, amount, type)
- [ ] **APP-03**: Student can tap a canteen purchase transaction and see the itemized receipt (what was bought, price per item, total)
- [ ] **APP-04**: Student app shows balance update immediately after a transaction is processed
- [ ] **APP-05**: Student app handles API errors gracefully (shows error message, not crash)

### Notifications

- [ ] **NOTF-01**: Student receives a push notification when their balance drops below a configurable threshold
- [ ] **NOTF-02**: Admin can configure the low-balance threshold value per student or globally

### NFC Architecture Preparation (Backend Only)

- [ ] **NFC-01**: NFC payment API endpoints exist and are documented (`/api/nfc/register`, `/api/nfc/pay`)
- [ ] **NFC-02**: VirtualCard model in nfc_payments.py is fully integrated with Google Sheets (persisted, not just in-memory)
- [ ] **NFC-03**: Transaction flow accepts both RFID card UID and NFC virtual card token as payment sources
- [ ] **NFC-04**: API authentication supports NFC device token alongside JWT (ready for Android HCE integration)
- [ ] **NFC-05**: NFC integration guide written in docs/ explaining exactly what the Android app needs to implement for v2

### Documentation

- [ ] **DOC-01**: `docs/architecture.md` — system overview, layers, data flow, entry points
- [ ] **DOC-02**: `docs/api-reference.md` — all REST API endpoints, request/response format, auth
- [ ] **DOC-03**: `docs/google-sheets-schema.md` — all Sheets structure (columns, purpose, relationships)
- [ ] **DOC-04**: `docs/cashier-guide.md` — how cashier POS works, Arduino setup, card reading flow
- [ ] **DOC-05**: `docs/student-app.md` — Android app architecture, screens, API calls
- [ ] **DOC-06**: `docs/nfc-integration-guide.md` — step-by-step guide for implementing NFC in Android (v2 prep)
- [ ] **DOC-07**: `docs/admin-guide.md` — admin dashboard features, roles, product management
- [ ] **DOC-08**: `docs/setup.md` — environment setup, Google Sheets creation, credentials, first run

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
| BUG-01 | Phase 1 - Critical Fixes + Security | Pending |
| BUG-02 | Phase 1 - Critical Fixes + Security | Pending |
| BUG-03 | Phase 1 - Critical Fixes + Security | Pending |
| BUG-04 | Phase 1 - Critical Fixes + Security | Pending |
| BUG-05 | Phase 1 - Critical Fixes + Security | Pending |
| SEC-01 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-02 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-03 | Phase 1 - Critical Fixes + Security | Complete |
| SEC-04 | Phase 1 - Critical Fixes + Security | Pending |
| SEC-05 | Phase 1 - Critical Fixes + Security | Pending |
| QUAL-01 | Phase 2 - Code Quality | Pending |
| QUAL-02 | Phase 2 - Code Quality | Pending |
| QUAL-03 | Phase 2 - Code Quality | Pending |
| QUAL-04 | Phase 2 - Code Quality | Pending |
| QUAL-05 | Phase 2 - Code Quality | Pending |
| PROD-01 | Phase 3 - Product Management | Pending |
| PROD-02 | Phase 3 - Product Management | Pending |
| PROD-03 | Phase 3 - Product Management | Pending |
| PROD-04 | Phase 3 - Product Management | Pending |
| PROD-05 | Phase 3 - Product Management | Pending |
| PROD-06 | Phase 3 - Product Management | Pending |
| APP-01 | Phase 4 - Student App + Notifications | Pending |
| APP-02 | Phase 4 - Student App + Notifications | Pending |
| APP-03 | Phase 4 - Student App + Notifications | Pending |
| APP-04 | Phase 4 - Student App + Notifications | Pending |
| APP-05 | Phase 4 - Student App + Notifications | Pending |
| NOTF-01 | Phase 4 - Student App + Notifications | Pending |
| NOTF-02 | Phase 4 - Student App + Notifications | Pending |
| NFC-01 | Phase 5 - NFC Architecture Prep | Pending |
| NFC-02 | Phase 5 - NFC Architecture Prep | Pending |
| NFC-03 | Phase 5 - NFC Architecture Prep | Pending |
| NFC-04 | Phase 5 - NFC Architecture Prep | Pending |
| NFC-05 | Phase 5 - NFC Architecture Prep | Pending |
| DOC-01 | Phase 6 - Documentation | Pending |
| DOC-02 | Phase 6 - Documentation | Pending |
| DOC-03 | Phase 6 - Documentation | Pending |
| DOC-04 | Phase 6 - Documentation | Pending |
| DOC-05 | Phase 6 - Documentation | Pending |
| DOC-06 | Phase 6 - Documentation | Pending |
| DOC-07 | Phase 6 - Documentation | Pending |
| DOC-08 | Phase 6 - Documentation | Pending |

**Coverage:**
- v1 requirements: 41 total
- Mapped to phases: 41
- Unmapped: 0

---
*Requirements defined: 2026-02-22*
*Last updated: 2026-02-22 — Traceability finalized after roadmap creation*
