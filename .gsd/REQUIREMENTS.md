# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R014 — Requirements File Completeness
- Class: operability
- Status: validated
- Description: Both Flask apps install cleanly from their requirements files on a fresh virtualenv with no missing packages and no file errors
- Why it matters: The api requirements file is missing gspread, firebase-admin, twilio, and bcrypt — a fresh api server deploy fails silently on multiple paths today; dashboard requirements.txt has an unresolved merge conflict that makes it invalid
- Source: execution
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: pip install --dry-run exits 0 on both backend/dashboard/requirements.txt and backend/api/requirements_api.txt; no merge conflict markers; all required packages present
- Notes: Merge conflict (<<<< ==== >>>>) resolved; bcrypt>=4.0.0 and twilio>=9.0.0 both present in dashboard; six previously-missing packages added to api requirements

### R015 — Cache Layer Coverage
- Class: quality-attribute
- Status: validated
- Description: Hot Sheets-reading endpoints (product list, student list, money accounts, transaction recent, analytics summary) serve from cache on repeated requests; mutations (complete_sale, load_balance, void_transaction) invalidate the relevant cache keys
- Why it matters: admin_dashboard.py has 2 cached calls vs 100 raw Sheets calls; cashier_routes.py has 0 cached; api_server.py has 8 cached vs 47 raw — Sheets quota (60 req/min) will be hit during lunch rush
- Source: execution
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: bash scripts/verify-s02.sh — 32/32 checks pass; get_cached/set_cached wired to five admin hot endpoints and three cashier/API endpoints; invalidate_pattern wired to six mutation handlers; balance-deduction reads explicitly uncached; python -m py_compile exits 0 on all three files
- Notes: backend/cache.py is a solid 254-line implementation — wiring work only, no new cache logic needed; balance reads in payment flows (complete_sale, process_cashier_transaction, nfc_pay) intentionally NOT cached to prevent overdraft

### R016 — FraudDetector Worker Safety
- Class: failure-visibility
- Status: validated
- Description: Admin server refuses to start if gunicorn workers > 1 with a clear human-readable error explaining the single-worker constraint
- Why it matters: _fraud_sheets_initialized is a module-level bool — each gunicorn worker gets its own copy, producing split-brain alert state silently
- Source: execution
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: WEB_CONCURRENCY guard at module level in web_app.py and admin_dashboard.py; both WEB_CONCURRENCY and GUNICORN_WORKERS checked; _parse_worker_count helper defaults to 1 on empty/invalid; guard message present in both files; sys.exit(1) confirmed; verify-s03.sh checks 5–8 pass
- Notes: Hard-fail approach chosen over multi-worker refactor; single-worker is acceptable for current PythonAnywhere deployment scale

### R017 — Critical Path Unit Tests
- Class: quality-attribute
- Status: validated
- Description: ~35 unit tests cover complete_sale, load_balance, void_transaction, and cashier login auth with a mocked Sheets client — zero live Sheets calls, completes in under 10 seconds
- Why it matters: admin_dashboard.py and cashier_routes.py are ~3000 lines combined and currently 0% unit-tested; untested money-moving code is the highest operational risk
- Source: execution
- Primary owning slice: M002/S04
- Supporting slices: none
- Validation: pytest tests/test_cashier_routes.py tests/test_admin_critical.py exits 0; 35 tests; 2.40s; zero live Sheets calls (all worksheet mocks); money-moving arithmetic verified (new_balance assertions on complete_sale, load_balance, void_transaction)
- Notes: Bar is risk-based (money-moving paths), not metric-based; broad 60%+ coverage is out of scope for this milestone. Production bugfix discovered: transaction_row pre-built before retry loop in complete_sale (offline fallback UnboundLocalError)

### R018 — Health Check Standardization
- Class: failure-visibility
- Status: validated
- Description: Both app health endpoints return structured JSON with sheets_ok, latency_ms, and queue_pending fields; both return 503 when Sheets is unreachable
- Why it matters: api_server.py health check returns {"status": "ok"} unconditionally — hardcoded, no real check; admin_dashboard.py has a rich HealthMonitor but currently returns 200 even when Sheets is down
- Source: execution
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: All three health handlers (dashboard_core.py, admin_dashboard.py, api_server.py) return {status, sheets_ok, latency_ms, queue_pending, timestamp}; 503 on Sheets failure confirmed in dashboard_core.py and api_server.py; verify-s03.sh checks 9–18 pass; all four files compile cleanly
- Notes: api_server.py health uses fresh get_sheets_client() per request (not stale module-level db); latency_ms=0 is a sentinel for client-not-initialized

### R019 — Deployment Runbook
- Class: operability
- Status: validated
- Description: docs/DEPLOY.md covers PythonAnywhere setup, required env vars, Sheets service account config, first-run migration steps, health check sequence, and known operational constraints
- Why it matters: No runbook exists; backend/api/wsgi.py targets PythonAnywhere but the setup steps, env vars, and first-run sequence are undocumented
- Source: execution
- Primary owning slice: M002/S05
- Supporting slices: none
- Validation: test -f docs/DEPLOY.md exits 0; all 8 grep checks pass (FLASK_SECRET_KEY, WEB_CONCURRENCY, E.164, migrate_transactions.py, queue_pending, offline_queue.db, firebase-credentials.json, YOUR_USERNAME); 11-section runbook covers env vars (22 Dashboard + 10 API vars), WSGI corrected templates, startup guard quick-reference, health check failure-interpretation table, and all 8 known operational constraints
- Notes: Audience is the developer (Python/git familiar); no screenshots required; single-worker constraint, E.164 phone format requirement, and offline queue behavior on fresh deploy all documented in Known Operational Constraints section

## Validated

### R001 — Fraud Alerts Admin UI
- Class: failure-visibility
- Status: validated
- Description: Admin can view fraud alerts generated by FraudDetector, resolve them, and manually suspend/unsuspend cards from the admin dashboard
- Why it matters: The fraud engine ran but was invisible — admins had no way to act on alerts without direct database access
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: validated
- Notes: All 6 API endpoints and admin dashboard panel verified. 33-test suite in tests/test_fraud_api.py.

### R002 — Card Suspension Management
- Class: admin/support
- Status: validated
- Description: Admin can manually suspend and unsuspend a money card from the dashboard UI
- Why it matters: Cards could only be auto-suspended by the fraud engine; admin had no manual override
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: validated
- Notes: POST /api/fraud/cards/<uid>/suspend and /unsuspend verified; admin_only decorator confirmed.

### R003 — Transaction Filter & Search (Admin)
- Class: operability
- Status: validated
- Description: Admin can filter the transactions page by date range, student ID/name, and transaction type
- Why it matters: All transactions loaded in a flat list with no filter; unusable at scale
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: validated
- Notes: GET /api/transactions/filtered verified; filter bar wired in transactions.html.

### R004 — SMS Notifications (Twilio)
- Class: integration
- Status: validated
- Description: Parents receive SMS for purchases, loads, and low-balance events if TWILIO_* env vars are configured
- Why it matters: Philippine parents often have unreliable internet; SMS is more reliable than email
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: validated
- Notes: Three NFC SMS bugs fixed (wrong field name, wrong kwarg, missing send_purchase_sms call); twilio added to requirements_api.txt.

### R005 — Cashier Account Management
- Class: admin/support
- Status: validated
- Description: Admin can create, list, update, and deactivate cashier accounts; cashier login uses dynamic credentials stored in Google Sheets
- Why it matters: Hardcoded cashier/cashier123 is a security risk; multi-station deployment needs named accounts
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated
- Notes: _ensure_cashier_accounts_sheet() auto-creates with seeded default; full CRUD API live.

### R006 — Transaction Void / Correction
- Class: admin/support
- Status: validated
- Description: Admin can void a transaction with a reason; the student's balance is restored and a void record is appended to the Transactions Log
- Why it matters: No way to correct erroneous transactions; balance errors accumulate over time
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated
- Notes: POST /api/admin/transactions/<txn_id>/void verified; double-void guard in place; void modal in transactions.html.

### R007 — Offline Cashier Queue
- Class: continuity
- Status: validated
- Description: Cashier continues processing sales during a Google Sheets outage; transactions queue to SQLite and sync automatically on reconnect
- Why it matters: Sheets outages would halt all sales; cash fallback is disruptive in a cashless canteen
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: validated
- Notes: SQLiteWriteQueue (WAL mode) in offline_queue.py; complete_sale() fallback verified; /cashier/api/queue/status endpoint live.

### R008 — Cashier Quick-Pay Shortcut
- Class: primary-user-loop
- Status: validated
- Description: Cashier can tap Quick Pay on any product to skip the cart and scan a card immediately for a single-item sale
- Why it matters: Cart-based flow is too slow for high-volume lunch rush with common single-item purchases
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: validated
- Notes: Quick Pay button per product tile in cashier_index.html; single-item payload to complete_sale().

### R009 — Push Notification for Every Transaction
- Class: integration
- Status: validated
- Description: Every purchase and load triggers an FCM push to the student's device; card replacement triggers a push notifying the student
- Why it matters: Students and parents only knew about transactions via delayed email; real-time awareness was missing
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated
- Notes: send_purchase_push, send_load_push, send_card_replaced_push all wired to their respective endpoints.

### R010 — Android Transaction Filter
- Class: primary-user-loop
- Status: validated
- Description: Student can filter transaction history by type and date in the Android app
- Why it matters: Flat transaction list is unusable for students tracking spending
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated
- Notes: TransactionsActivity filter bar (type chip + date range picker) in student_app_v2.

### R011 — Monthly Budget Auto-Reset
- Class: primary-user-loop
- Status: validated
- Description: Student's monthly budget auto-resets on the 1st of each month with a re-prompt in the Android app
- Why it matters: Monthly budget was a one-time setup; students had no way to reset for a new month
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated
- Notes: SecureStorage KEY_BUDGET_MONTH; on app resume, if stored month ≠ current month → clear budget + show prompt.

### R012 — Lost Card Status Feedback (Android)
- Class: primary-user-loop
- Status: validated
- Description: Student sees real-time lost card status in-app; receives FCM push when admin processes the replacement
- Why it matters: Students had no visibility into whether their lost card report was being processed
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated
- Notes: HomeActivity badge reads /api/student/lost-card-status; FCMService handles card_replaced message type.

### R013 — Daily Low-Balance Batch Email
- Class: integration
- Status: validated
- Description: Backend scheduler runs a daily job emailing parents of all students below LOW_BALANCE_THRESHOLD; admin can trigger manually
- Why it matters: Parents had no proactive notification of low balances until a purchase was rejected
- Source: user
- Primary owning slice: M001/S06
- Supporting slices: none
- Validation: validated
- Notes: DailyScheduler + run_low_balance_batch() in scheduler.py; POST /api/admin/batch/low-balance-email manual trigger; logs to Scheduler Log sheet.

## Active

### R020 — Correct WiFi Payment Routing
- Class: primary-user-loop
- Status: active
- Description: Arduino WiFi path routes physical card UIDs to `/api/arduino/card-read` (emits `card_read`) and NFC phone tokens to `/api/nfc/tap` (emits `nfc_payment`) — not both to the same endpoint
- Why it matters: Current firmware sends all WiFi POSTs to `/api/nfc/tap` with `{"token": value}`, so physical RFID card taps over WiFi go to the wrong endpoint and fire the wrong SocketIO event; the bug is masked today only because serial fallback via ArduinoBridge routes correctly — with a standalone powerbank Arduino (no serial/PC), every physical card tap silently fails
- Source: execution
- Primary owning slice: M003/S01
- Supporting slices: none
- Validation: unmapped
- Notes: `deliver()` in bankongseton_rfid.ino must use two httpPost targets distinguished by prefix ("CARD" vs "NFC"); CARD → `{"uid": value}` to `/api/arduino/card-read`; NFC → `{"token": value}` to `/api/nfc/tap`

### R021 — Phone NFC Payment at Cashier
- Class: primary-user-loop
- Status: active
- Description: Student can tap an Android HCE phone at the cashier to complete a payment; cashier UI handles `nfc_payment` socket event and processes the sale via a new `/cashier/api/complete-sale-nfc` endpoint
- Why it matters: The `nfc_payment` socket event from the Arduino is emitted but unhandled in the cashier UI — phone taps do nothing at the cashier today; cashier UI only listens for `card_read`
- Source: user
- Primary owning slice: M003/S02
- Supporting slices: none
- Validation: unmapped
- Notes: New `complete_sale_nfc(token)` endpoint in cashier_routes.py resolves virtual_card_token → money_card_number via Sheets (same pattern as api_server.py nfc_pay), then debits balance and emits same success/failure as `complete_sale`

### R022 — Arduino WiFi Status in Cashier UI
- Class: operability
- Status: active
- Description: Cashier UI shows a WiFi status badge (green/red) indicating whether the Arduino is reachable wirelessly; "Pay Now" enables when Arduino is WiFi-connected even without a COM port selected
- Why it matters: Currently `arduinoConnected` only goes true via the COM port selector; with a powerbank Arduino (no USB to PC), the checkout button stays disabled forever, blocking all payments
- Source: user
- Primary owning slice: M003/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Arduino POSTs to `/api/arduino/heartbeat` every 30s; backend stores `last_arduino_wifi_seen` and emits `arduino_wifi_status` SocketIO event; cashier UI sets `arduinoConnected = true` on either serial connect OR WiFi heartbeat

### R023 — Arduino Stable on Powerbank
- Class: continuity
- Status: active
- Description: Arduino UNO R4 WiFi runs reliably for a full school day on a USB powerbank without auto-shutoff; WiFi reconnects automatically if the connection drops between customers
- Why it matters: Many powerbanks cut power when current drops below ~100mA; without active mitigation, the Arduino may shut off during quiet periods between card taps; WiFi drops must also self-heal without a person rebooting the Arduino
- Source: user
- Primary owning slice: M003/S04
- Supporting slices: none
- Validation: unmapped
- Notes: Heartbeat POST every 30s provides consistent RF burst to keep powerbank alive; PN532 polling loop baseline draw is ~180-200mA which should keep most powerbanks above cutoff threshold; WiFi reconnect on ensureWiFi() call before each heartbeat and before each card POST

### R024 — Wireless Deployment Documentation
- Class: operability
- Status: active
- Description: `arduino/README-wireless.md` documents the complete standalone powerbank setup: hardware list, wiring, `secrets.h` configuration, flashing steps, and how to verify the Arduino is connected to the school LAN
- Why it matters: Without docs, whoever sets up the cashier counter has no guide for the WiFi-only configuration — they'll fall back to USB serial mode
- Source: user
- Primary owning slice: M003/S04
- Supporting slices: none
- Validation: unmapped
- Notes: Should cover: powerbank selection (minimum 2A output port), secrets.h fields, ARDUINO_API_KEY in .env, school LAN IP of Flask server, how to check the WiFi status badge in cashier UI

## Out of Scope

### R050 — GCash / Maya Online Top-Up
- Class: integration
- Status: out-of-scope
- Description: Parents top up student balances directly via GCash or Maya payment gateway
- Why it matters: Scope clarification — prevents scope creep toward payment gateway integration
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Out of scope for current school deployment; requires merchant account setup.

### R051 — iOS App
- Class: core-capability
- Status: out-of-scope
- Description: Native iOS student app with NFC HCE virtual card
- Why it matters: Scope clarification — Android-only for current deployment
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: iOS NFC HCE is more restricted than Android; not planned.

## Traceability

| ID | Class | Status | Primary Owner | Supporting | Proof |
|----|-------|--------|---------------|------------|-------|
| R001 | failure-visibility | validated | M001/S01 | none | validated |
| R002 | admin/support | validated | M001/S01 | none | validated |
| R003 | operability | validated | M001/S02 | none | validated |
| R004 | integration | validated | M001/S02 | none | validated |
| R005 | admin/support | validated | M001/S03 | none | validated |
| R006 | admin/support | validated | M001/S03 | none | validated |
| R007 | continuity | validated | M001/S04 | none | validated |
| R008 | primary-user-loop | validated | M001/S04 | none | validated |
| R009 | integration | validated | M001/S05 | none | validated |
| R010 | primary-user-loop | validated | M001/S05 | none | validated |
| R011 | primary-user-loop | validated | M001/S05 | none | validated |
| R012 | primary-user-loop | validated | M001/S05 | none | validated |
| R013 | integration | validated | M001/S06 | none | validated |
| R014 | operability | validated | M002/S01 | none | pip --dry-run exit 0 on both files |
| R015 | quality-attribute | validated | M002/S02 | none | bash scripts/verify-s02.sh 32/32; python -m py_compile exit 0 |
| R016 | failure-visibility | validated | M002/S03 | none | WEB_CONCURRENCY guard at module level; verify-s03.sh checks 5–8 pass |
| R017 | quality-attribute | validated | M002/S04 | none | pytest exit 0; 35 tests; 2.40s; zero live Sheets calls |
| R018 | failure-visibility | validated | M002/S03 | none | All three health handlers return structured JSON + 503; verify-s03.sh checks 9–18 pass |
| R019 | operability | validated | M002/S05 | none | test -f docs/DEPLOY.md exit 0; 8/8 grep checks pass |
| R020 | primary-user-loop | active | M003/S01 | none | unmapped |
| R021 | primary-user-loop | active | M003/S02 | none | unmapped |
| R022 | operability | active | M003/S03 | none | unmapped |
| R023 | continuity | active | M003/S04 | none | unmapped |
| R024 | operability | active | M003/S04 | none | unmapped |
| R050 | integration | out-of-scope | none | none | n/a |
| R051 | core-capability | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 5
- Mapped to slices: 5
- Validated: 19
- Unmapped active requirements: 0
