# Roadmap: BankongSeton

## Overview

BankongSeton is a school canteen cashless payment system that already exists but has critical bugs,
security holes, and missing features. This roadmap sequences work goal-backward: fix what is broken
first (cashier POS, security), tighten the codebase, add the missing product and student-app
features, prepare the NFC backend architecture for the next version, then document everything so the
system can be handed off or extended. Each phase delivers a complete, verifiable capability before
the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Critical Fixes + Security** - System runs without critical bugs and is no longer a security liability
- [ ] **Phase 2: Code Quality** - Codebase is clean, safe, and maintainable
- [ ] **Phase 3: Product Management** - Admin can manage the canteen menu; cashier POS shows and sells products
- [ ] **Phase 4: Student App + Notifications** - Students can see their balance and transaction history; low-balance alerts work
- [ ] **Phase 5: NFC Architecture Prep** - Backend is ready for Android NFC integration in the next version
- [ ] **Phase 6: Documentation** - System is fully documented and can be understood by any developer

## Phase Details

### Phase 1: Critical Fixes + Security
**Goal**: The system runs without crashing on real inputs and does not expose credentials or allow trivial unauthorized access
**Depends on**: Nothing (first phase)
**Requirements**: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05, SEC-01, SEC-02, SEC-03, SEC-04, SEC-05
**Success Criteria** (what must be TRUE):
  1. Cashier POS loads and shows the product grid (not a blank screen)
  2. Scanning an empty or malformed card UID produces an error message, not a silent match or crash
  3. A Google Sheets API outage returns a readable error to the client, not a 500 traceback
  4. Submitting an empty username and password to admin login is rejected with an error
  5. Server startup produces no credentials or secret keys in stdout or log files; system refuses to start with a blank FLASK_SECRET_KEY
**Plans**: TBD

### Phase 2: Code Quality
**Goal**: The codebase is safe to modify, with consistent logging, centralized utilities, and no dead code or deprecated dependencies
**Depends on**: Phase 1
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. Running the server produces structured log output with log levels; no bare print() statements appear in any log capture
  2. Card UID normalization is called from one function in backend/utils.py everywhere it is needed; no duplicated normalization logic remains
  3. Global state variables in admin_dashboard.py are wrapped in a thread-safe class; concurrent card reads do not race
  4. The BankongSetonApp folder and all identified unused files are gone from the repository
  5. The project installs successfully with google-auth in place of oauth2client; no deprecation warnings from that dependency
**Plans**: TBD

### Phase 3: Product Management
**Goal**: Admin can maintain the canteen menu in the dashboard, and the cashier POS displays and sells those products in a single transaction
**Depends on**: Phase 1
**Requirements**: PROD-01, PROD-02, PROD-03, PROD-04, PROD-05, PROD-06
**Success Criteria** (what must be TRUE):
  1. Admin can open the product management page and add a new item (name, price, category); it appears immediately in the list
  2. Admin can edit an existing product and the change is reflected in the POS within one page refresh
  3. Admin can deactivate a product and it no longer appears in the cashier grid
  4. Cashier POS displays all active products in a grid with name and price visible
  5. Cashier can select multiple products, see the running total, and complete the transaction as one charge to the student card
**Plans**: TBD

### Phase 4: Student App + Notifications
**Goal**: Students can see their real balance and full transaction history in the app, with itemized receipts for canteen purchases, and receive a push notification when their balance is low
**Depends on**: Phase 3
**Requirements**: APP-01, APP-02, APP-03, APP-04, APP-05, NOTF-01, NOTF-02
**Success Criteria** (what must be TRUE):
  1. Student opens the app and sees their current balance on the home screen without navigating anywhere
  2. Student can scroll a list of all their transactions showing date, amount, and type
  3. Student taps a canteen purchase in the history and sees an itemized receipt (item name, price per item, total)
  4. After a card tap at the cashier, the app balance refreshes to the new value within the next app open or background sync
  5. When a student's balance drops below the configured threshold, they receive a push notification on their Android device
  6. Admin can set the low-balance threshold globally or per student from the dashboard
**Plans**: TBD

### Phase 5: NFC Architecture Prep
**Goal**: The backend exposes complete, documented NFC payment endpoints and persists VirtualCard state so the Android app can implement NFC in the next version without backend changes
**Depends on**: Phase 1
**Requirements**: NFC-01, NFC-02, NFC-03, NFC-04, NFC-05
**Success Criteria** (what must be TRUE):
  1. Calling GET /api/nfc/register and POST /api/nfc/pay with valid inputs returns documented success responses; invalid inputs return documented error codes
  2. A VirtualCard registered via the API is saved to Google Sheets and survives a server restart
  3. A payment request that supplies an NFC virtual card token instead of an RFID UID is accepted and debits the same student account
  4. The NFC endpoints authenticate via a device token header in addition to the existing JWT flow
  5. docs/nfc-integration-guide.md exists and contains the exact API calls, token format, and HCE flow an Android developer needs to implement NFC in v2
**Plans**: TBD

### Phase 6: Documentation
**Goal**: Every major system component has a clear Markdown document in docs/ so any developer can understand, set up, and extend the system without asking the original author
**Depends on**: Phase 5
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, DOC-08
**Success Criteria** (what must be TRUE):
  1. A developer can follow docs/setup.md alone to get the system running from a fresh machine with Google Sheets credentials
  2. docs/api-reference.md lists every REST endpoint with request format, response format, and auth requirement
  3. docs/google-sheets-schema.md describes every sheet, every column, and the relationships between sheets
  4. docs/cashier-guide.md explains the full card-tap-to-transaction flow including Arduino wiring and serial protocol
  5. docs/architecture.md, docs/student-app.md, docs/admin-guide.md, and docs/nfc-integration-guide.md all exist and are accurate to the shipped code
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
Note: Phases 2, 3, and 5 all depend on Phase 1 and can be started independently once Phase 1 is complete.
Phase 4 depends on Phase 3. Phase 6 depends on Phase 5.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Critical Fixes + Security | 0/? | Not started | - |
| 2. Code Quality | 0/? | Not started | - |
| 3. Product Management | 0/? | Not started | - |
| 4. Student App + Notifications | 0/? | Not started | - |
| 5. NFC Architecture Prep | 0/? | Not started | - |
| 6. Documentation | 0/? | Not started | - |
