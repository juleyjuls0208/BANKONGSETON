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
- [ ] **Phase 2: Code Quality** - Codebase is clean, safe, and maintainable ✓ complete
- [ ] **Phase 3: Product Management** - Admin can manage the canteen menu; cashier POS shows and sells products ✓ complete
- [ ] **Phase 4: Student App + Notifications** - Students can see their balance and transaction history; low-balance alerts work
- [ ] **Phase 5: NFC Architecture Prep** - Backend is ready for Android NFC integration in the next version
- [x] **Phase 6: Documentation** - System is fully documented and can be understood by any developer (completed 2026-03-01)
- [x] **Phase 7: Fix Cashier Payment Path** - RFID card payment executes end-to-end; receipts show correct balances; FCM notifications fire from cashier POS (gap closure) (completed 2026-03-01)
- [ ] **Phase 8: Security + Reliability Fixes** - JWT secret guard added to api_server; exception text no longer leaked via WebSocket; cashier routes use ensure_products_sheet (gap closure)
- [ ] **Phase 9: NFC Android Compatibility** - NFC Purchase transactions navigable to receipt; missing NFC endpoints added; mobile/android field mapping corrected (gap closure)
- [x] **Phase 10: Documentation Gaps** - Cashier blueprint endpoints documented; cashier-guide updated with FCM operational note (gap closure) (completed 2026-03-02)
- [x] **Phase 11: Cashier Security Hardening** - cashier_routes.py no longer uses hardcoded credentials or JWT secret (gap closure) (completed 2026-03-02)
- [x] **Phase 12: Receipt & FCM Wiring** - BalanceBefore (APP-03) and FCM notification (NOTF-01) verified present in cashier_routes.py; fixed if audit contradictions are confirmed (gap closure) (completed 2026-03-02)
- [x] **Phase 13: NFC Payment Contract Fix** - NfcRegistrationResponse field name corrected; /api/nfc/pay accepts card token without requiring X-Device-Token header (gap closure) (completed 2026-03-02)
- [ ] **Phase 14: NFC Simulation UI** - Dashboard includes NFC simulation panel wired to existing simulate endpoint; WEB-02 fulfilled (gap closure)

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
**Plans**: 5 plans
Plans:
- [x] 01-01-PLAN.md -- Startup hardening (secret key guard, CORS restriction, credential redaction) [SEC-01, SEC-02, SEC-03]
- [x] 01-02-PLAN.md -- Fix cashier POS blank screen (template corruption rewrite) [BUG-01]
- [x] 01-03-PLAN.md -- Empty credential login guard, test file secrets cleanup, wsgi.py fix [BUG-04, SEC-05]
- [x] 01-04-PLAN.md -- Card UID input validation (regex hex format check at all entry points) [BUG-02, SEC-04]
- [x] 01-05-PLAN.md -- Graceful Sheets error handling and transaction atomicity with retry/rollback [BUG-03, BUG-05]

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
**Plans**: 8 plans
Plans:
- [x] 02-01-PLAN.md — Create backend/utils.py: normalize_card_uid + CardReaderState + concurrency tests
- [x] 02-02-PLAN.md — Fix errors.py console-only logging + archive dead code to _archive/
- [x] 02-03-PLAN.md — Migrate oauth2client → google-auth, pin requirements.txt, smoke test
- [x] 02-04-PLAN.md — Replace all print() with structured key=value logger calls across 6 files
- [x] 02-05-PLAN.md — Wire utils.py into admin_dashboard.py + cashier_routes.py + api_server.py
- [x] 02-06-PLAN.md — Gap closure: fix get_logger() hierarchy + add setup_logging() to entry points
- [x] 02-07-PLAN.md — Gap closure: fix normalize_card_uid(None) to return None (QUAL-02)
- [x] 02-08-PLAN.md — Gap closure: install Flask runtime deps, verify structured server startup (QUAL-01)

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
**Plans**: 4 plans
Plans:
- [x] 03-01-PLAN.md — Backend: ensure_products_sheet(), merge-on-update, /api/products/toggle-status, resilience fixes
- [x] 03-02-PLAN.md — Admin UI: rewrite products.html with inline-edit table, always-visible add form, toggle, toasts
- [x] 03-03-PLAN.md — Cashier POS: fix category names (Snacks/Other), verify active filter and checkout flow
- [x] 03-04-PLAN.md — Human verification: end-to-end admin CRUD + cashier POS flow

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
**Plans**: 6 plans
Plans:
- [ ] 04-01-PLAN.md — Backend API fixes: FCM auth mismatch, offset pagination, balance_before in response + transaction log [APP-02, APP-03, APP-04, APP-05]
- [ ] 04-02-PLAN.md — FCM sender + low-balance push notification wired into cashier transaction [NOTF-01]
- [ ] 04-03-PLAN.md — Admin threshold settings: GET/POST /api/settings/threshold + dashboard UI [NOTF-02]
- [ ] 04-04-PLAN.md — Android models/API client/LoginActivity FCM registration/SecureStorage last-balance [APP-01, APP-04, APP-05]
- [ ] 04-05-PLAN.md — Android UI: HomeActivity refresh+persistence, TransactionsActivity infinite scroll, TransactionsAdapter color+receipt nav, ReceiptActivity [APP-01, APP-02, APP-03, APP-04, APP-05]
- [ ] 04-06-PLAN.md — Human verification checkpoint: balance, transactions, receipt, threshold, FCM notification [APP-01, APP-02, APP-03, APP-04, APP-05, NOTF-01, NOTF-02]

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
**Plans**: 3 plans
Plans:
- [ ] 05-01-PLAN.md — NFCService + Google Sheets VirtualCards persistence (nfc_payments.py rewrite)
- [ ] 05-02-PLAN.md — NFC endpoints: POST /api/nfc/register + POST /api/nfc/pay + CORS update
- [ ] 05-03-PLAN.md — NFC integration guide: docs/nfc-integration-guide.md

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
**Plans**: 5 plans
Plans:
- [ ] 06-01-PLAN.md — Write docs/architecture.md + docs/setup.md (system overview, developer onboarding)
- [ ] 06-02-PLAN.md — Write docs/api-reference.md + docs/google-sheets-schema.md (API and database reference)
- [ ] 06-03-PLAN.md — Write docs/cashier-guide.md + docs/admin-guide.md (operational guides)
- [x] 06-04-PLAN.md — Write docs/student-app.md + docs/nfc-integration-guide.md (app and NFC guides)
- [ ] 06-05-PLAN.md — Write docs/README.md index + archive all 29 existing docs to docs/archive/

### Phase 7: Fix Cashier Payment Path
**Goal**: The RFID card payment path executes completely end-to-end — card tap triggers ArduinoBridge, the transaction Sheets row includes all 8 columns (BalanceBefore present), FCM low-balance notifications fire from the cashier POS, and receipts display correctly formatted timestamps
**Depends on**: Phase 1, Phase 4 (FCM infrastructure)
**Requirements**: BUG-01, APP-02, APP-03, APP-04, NOTF-01
**Gap Closure**: Closes gaps from v1.0 audit (TD-01, TD-02, TD-03, TD-04)
**Success Criteria** (what must be TRUE):
  1. Student taps card at cashier POS → `cashier_request_card` WebSocket event is handled → `arduino_bridge.read_card_with_timeout()` is called and returns a card UID
  2. `cashier_routes.py complete_sale` writes an 8-column row `[ts, uid, name, type, amount, balance_before, new_balance, 'Success']` to the Transactions sheet
  3. Receipt timestamps in the Android app display as a readable date/time string (not raw `"2026-02-28 14:32:00"`)
  4. Balance history in student app shows the correct pre-transaction balance (not ₱0.00) for cashier POS transactions
  5. When a cashier POS transaction drops a student's balance below the threshold, a push notification is sent via FCM
  6. `migrate_users_schema()` is called at api_server startup so fresh deployments register FCM tokens correctly
**Plans**: 3 plans
Plans:
- [ ] 07-01-PLAN.md — Add `cashier_request_card` WebSocket handler in cashier_routes.py + wire ArduinoBridge.read_card_with_timeout() [BUG-01]
- [ ] 07-02-PLAN.md — Fix cashier_routes.py complete_sale: add balance_before column, fix timestamp format, call send_low_balance_push(), call migrate_users_schema() at startup [APP-02, APP-03, APP-04, NOTF-01]
- [ ] 07-03-PLAN.md — Human verification: card tap → payment → correct receipt → FCM notification [BUG-01, APP-02, APP-03, APP-04, NOTF-01]

### Phase 07.1: Web-Deployable Dashboard (INSERTED)

**Goal:** Make the admin dashboard accessible as a publicly hosted website. Hardware-dependent features (COM port, NFC card tap, physical cashier terminal) may be conditionally disabled or stubbed out for web mode; wherever feasible, implement web-friendly alternatives.
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04
**Depends on:** Phase 7
**Plans:** 4/4 plans complete

Plans:
- [ ] 07.1-01-PLAN.md — Create web_app.py: hardware-free copy of admin_dashboard.py (pyserial stripped, arduino_available=False, read_card_thread removed) [WEB-01]
- [ ] 07.1-02-PLAN.md — Update wsgi.py: correct PythonAnywhere path, dotenv loading, absolute credentials path [WEB-02]
- [ ] 07.1-03-PLAN.md — Cashier backend: fix imports, add pyserial ImportError guard, add lookup-student endpoint, extend complete_sale for manual_student_id [WEB-03]
- [ ] 07.1-04-PLAN.md — Cashier frontend: auto-detect manual mode, student lookup modal; dashboard Web Mode badge [WEB-04]

### Phase 8: Security + Reliability Fixes
**Goal**: api_server.py requires a real JWT secret at startup; WebSocket error emissions no longer expose exception text to clients; cashier routes use the resilient ensure_products_sheet() helper instead of direct worksheet access
**Depends on**: Phase 7
**Requirements**: SEC-02, QUAL-01, PROD-04, PROD-05
**Gap Closure**: Closes gaps from v1.0 audit (TD-07, TD-08, TD-09)
**Success Criteria** (what must be TRUE):
  1. api_server.py refuses to start if `JWT_SECRET` env var is empty or missing, matching the guard in admin_dashboard.py
  2. All 4 `socketio.emit('card_error', ...)` calls emit a generic user-facing message; full exception is logged server-side only
  3. cashier_routes.py calls `ensure_products_sheet()` for the Products sheet instead of `db.worksheet('Products')` directly
  4. Cashier `/cashier/api/products` returns a valid product list (not 503) even if the Products sheet does not exist yet
**Plans**: 2 plans
Plans:
- [ ] 08-01-PLAN.md — Add JWT_SECRET startup guard to api_server.py; fix exception text leak in 4 WebSocket emissions [SEC-02, QUAL-01]
- [ ] 08-02-PLAN.md — Replace db.worksheet('Products') with ensure_products_sheet() in cashier_routes.py [PROD-04, PROD-05]

### Phase 9: NFC Android Compatibility
**Goal**: NFC Purchase transactions are navigable to receipt in TransactionsAdapter; the missing /api/nfc/unregister and /api/nfc/status endpoints exist; mobile/android field mapping corrected
**Depends on**: Phase 5
**Requirements**: NFC-03, NFC-04, NFC-05
**Gap Closure**: Closes gaps from v1.0 audit (TD-05, TD-06, TD-12)
**Success Criteria** (what must be TRUE):
  1. Tapping an `"NFC Purchase"` transaction in TransactionsActivity navigates to ReceiptActivity (same as `"Purchase"`)
  2. `GET /api/nfc/status` and `DELETE /api/nfc/unregister` endpoints exist in api_server.py and return documented responses
  3. `mobile/android` LoginResponse correctly maps the `id` field from backend login response (not `student_id`)
  4. NFC integration guide accurately reflects all available endpoints including the new ones
**Plans**: 2 plans
Plans:
- [ ] 09-01-PLAN.md — Extend isPurchase in TransactionsAdapter.kt to include "NFC Purchase" [NFC-03]
- [ ] 09-02-PLAN.md — Add GET /api/nfc/status + POST /api/nfc/unregister to api_server.py; fix StudentData.id @SerializedName; update nfc-integration-guide.md [NFC-04, NFC-05]

### Phase 10: Documentation Gaps
**Goal**: api-reference.md documents all cashier blueprint endpoints; cashier-guide.md includes an operational note that cashier POS does not trigger FCM push notifications
**Depends on**: Phase 7 (FCM clarification confirmed by fix)
**Requirements**: DOC-02, DOC-04
**Gap Closure**: Closes gaps from v1.0 audit (TD-10, TD-11)
**Success Criteria** (what must be TRUE):
  1. `docs/api-reference.md` documents all `/cashier/api/*` endpoints with request format, response format, and auth requirement
  2. `docs/cashier-guide.md` includes a note clarifying that FCM push notifications are triggered by api_server.py (student-side), not by the cashier POS path
**Plans**: 1 plan
Plans:
- [ ] 10-01-PLAN.md — Document /cashier/api/* endpoints in api-reference.md; add FCM operational note to cashier-guide.md [DOC-02, DOC-04]

### Phase 11: Cashier Security Hardening
**Goal**: cashier_routes.py no longer uses hardcoded cashier credentials or a hardcoded JWT secret; both are sourced from environment variables matching the pattern already used in api_server.py
**Depends on**: Phase 8
**Requirements**: SEC-01, SEC-02
**Gap Closure**: Closes gaps from v1.0 audit (SEC-01 cashier creds, SEC-02 cashier JWT secret)
**Success Criteria** (what must be TRUE):
  1. cashier_routes.py contains no hardcoded username/password strings (`cashier`/`cashier123` or equivalent)
  2. cashier_routes.py sources JWT_SECRET exclusively from `os.environ.get("JWT_SECRET")`; no fallback string literal exists
  3. Cashier login still succeeds when the correct credentials are supplied via environment variables
**Plans**: 2 plans
Plans:
- [x] 11-01-PLAN.md — Remove hardcoded cashier username/password from cashier_routes.py; wire to env vars [SEC-01]
- [ ] 11-02-PLAN.md — Replace hardcoded JWT_SECRET fallback in cashier_routes.py with os.environ.get("JWT_SECRET") [SEC-02]

### Phase 12: Receipt & FCM Wiring
**Goal**: The contradiction between Phase 7 VERIFICATION (claims APP-03 and NOTF-01 are fixed) and the Integration Audit (claims both are broken) is resolved by direct code inspection; any actual breakage is fixed
**Depends on**: Phase 7
**Requirements**: APP-03, NOTF-01
**Gap Closure**: Closes gaps from v1.0 audit (APP-03 BalanceBefore column, NOTF-01 FCM not called from cashier)
**Success Criteria** (what must be TRUE):
  1. cashier_routes.py `complete_sale` writes an 8-column transaction row with BalanceBefore as the 6th column
  2. `migrate_users_schema()` is called at api_server startup (confirmed in code, not just claimed)
  3. cashier_routes.py `complete_sale` calls the FCM send function when balance drops below threshold
**Plans**: 2 plans
Plans:
- [x] 12-01-PLAN.md — Confirm APP-03 (transaction_row 11 cols) and NOTF-01 (FCM block) in cashier_routes.py; fix config_validator.py schema; update INTEGRATION_AUDIT.md [APP-03, NOTF-01]
- [x] 12-02-PLAN.md — Confirm migrate_users_schema() startup call in api_server.py; write phase SUMMARY and mark complete [NOTF-01]

### Phase 13: NFC Payment Contract Fix
**Goal**: The Android HCE service can complete an NFC payment end-to-end — the registration response uses the field name the app expects, and the payment endpoint does not require the app to supply a device token it cannot obtain
**Depends on**: Phase 9
**Requirements**: NFC-03, NFC-04
**Gap Closure**: Closes gaps from v1.0 audit (NFC-03 field name mismatch, NFC-04 X-Device-Token contract)
**Success Criteria** (what must be TRUE):
  1. `NfcRegistrationResponse` (Python) returns `virtual_card_token` (not `virtual_token`); Android `NfcRegistrationResponse.kt` deserializes it correctly
  2. `/api/nfc/pay` accepts the card token and performs device-token lookup server-side; client does not need to supply `X-Device-Token` header
  3. A simulated end-to-end NFC pay call (register → pay with card token only) returns a successful payment response
**Plans**: 2 plans
Plans:
- [ ] 13-01-PLAN.md — Fix NfcRegistrationResponse: rename virtual_token → virtual_card_token in Python response and Android model [NFC-03]
- [ ] 13-02-PLAN.md — Modify /api/nfc/pay: accept card token, look up device token server-side, remove X-Device-Token header requirement [NFC-04]

### Phase 14: NFC Simulation UI
**Goal**: The admin dashboard includes a panel that allows a developer or tester to simulate an NFC card tap without physical hardware, completing the WEB-02 requirement that Phase 7.1 left unimplemented
**Depends on**: Phase 7.1, Phase 13
**Requirements**: WEB-02
**Gap Closure**: Closes gap from v1.0 audit (WEB-02 NFC simulation UI never built — Phase 7.1 mislabeled wsgi.py fix as WEB-02)
**Success Criteria** (what must be TRUE):
  1. The admin dashboard contains an NFC Simulation panel with a student selector and a "Simulate Tap" button
  2. Clicking Simulate Tap calls the backend simulate endpoint and displays the result (success or error) in the UI
  3. The simulation panel is only visible when the server is running in web mode (hardware-free)
**Plans**: 1 plan
Plans:
- [ ] 14-01-PLAN.md — Add NFC simulation panel to dashboard template; wire to /api/nfc/simulate endpoint [WEB-02]

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
Note: Phases 2, 3, and 5 all depend on Phase 1 and can be started independently once Phase 1 is complete.
Phase 4 depends on Phase 3. Phase 6 depends on Phase 5.

**Gap Closure Phases (post-audit):**
Phase 7 depends on Phase 1 and Phase 4 (FCM). Phase 8 depends on Phase 7. Phase 9 depends on Phase 5. Phase 10 depends on Phase 7.
Phase 11 depends on Phase 8. Phase 12 depends on Phase 7. Phase 13 depends on Phase 9. Phase 14 depends on Phase 7.1 and Phase 13.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Critical Fixes + Security | 5/5 | Complete | 2026-02-26 |
| 2. Code Quality | 8/8 | Complete | 2026-02-26 |
| 3. Product Management | 4/4 | Complete | 2026-02-26 |
| 4. Student App + Notifications | 3/6 | In Progress|  |
| 5. NFC Architecture Prep | 1/3 | In Progress|  |
| 6. Documentation | 5/5 | Complete   | 2026-03-01 |
| 7. Fix Cashier Payment Path | 3/3 | Complete   | 2026-03-01 |
| 7.1. Web-Deployable Dashboard | 0/4 | Planned |  |
| 8. Security + Reliability Fixes | 0/2 | Pending |  |
| 9. NFC Android Compatibility | 0/2 | Pending |  |
| 10. Documentation Gaps | 1/1 | Complete    | 2026-03-02 |
| 11. Cashier Security Hardening | 2/2 | Complete    | 2026-03-02 |
| 12. Receipt & FCM Wiring | 2/2 | Complete    | 2026-03-02 |
| 13. NFC Payment Contract Fix | 2/2 | Complete    | 2026-03-02 |
| 14. NFC Simulation UI | 0/1 | Planned | |
