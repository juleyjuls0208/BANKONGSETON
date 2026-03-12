# M001: Operational Hardening & Feature Completion

**Vision:** Wire all 13 identified gaps — fraud alert visibility, cashier account management, transaction filters, SMS notifications, transaction void, offline resilience, quick-pay shortcut, complete push notification coverage, Android transaction filter, monthly budget reset, lost card feedback, and daily low-balance batch email — turning a working prototype into a fully operational school canteen system.

## Success Criteria

- Admin sees live fraud alerts, can resolve them, and can manually suspend/unsuspend any card
- Admin can create, rename, and deactivate named cashier accounts (no hardcoded credentials)
- Admin can filter transactions by date range, student, and type directly in the dashboard
- Admin can void a transaction with a reason; the void is logged and balance is restored
- Cashier can tap Quick Pay on any product and scan a card — skipping the cart — for fast single-item sales
- Cashier continues processing sales during a Google Sheets outage and syncs automatically on reconnect
- Every purchase and load triggers an FCM push to the student's device within 5 seconds
- Parent receives an SMS alert for purchases and loads when TWILIO_* env vars are configured
- Student can filter transaction history by type and date in the Android app
- Student's monthly budget auto-resets on the 1st of each month with a re-prompt
- Student sees real-time lost card status in-app; receives FCM push when admin processes the replacement
- Daily batch email sends to parents of all students below the LOW_BALANCE_THRESHOLD

## Key Risks / Unknowns

- FraudDetector is in-memory per-process — alerts don't survive restarts or cross to admin dashboard if running in a different process. Must persist alerts to Google Sheets.
- Offline queue: resilience.py WriteQueue is in-memory. Needs SQLite backing for crash survival.
- Twilio package not installed; APScheduler not installed. Both need pip install and requirements.txt update.
- Lost card FCM: need a new send_card_replaced_push helper in fcm_sender.py and wiring in replace_lost_card() endpoint.

## Proof Strategy

- In-memory FraudDetector persistence risk → retire in S01 by proving alerts survive a process restart (sheet-backed)
- Offline queue data loss risk → retire in S04 by proving a transaction buffered during simulated outage appears in Sheets after reconnect
- Twilio integration risk → retire in S02 by sending a real SMS to a test number via Twilio API
- Lost card FCM risk → retire in S05 by triggering replace_lost_card and verifying FCM push fires

## Verification Classes

- Contract verification: API endpoint responses checked with curl/requests; Python assertions on business logic
- Integration verification: Admin dashboard browser flows; Android APK compilation check
- Operational verification: Offline queue survives process restart; daily scheduler fires on time; SMS delivers
- UAT / human verification: Cashier quick-pay flow on real device; lost card status visible in app after admin processes replacement

## Milestone Definition of Done

This milestone is complete only when all are true:

- All 6 slices are complete with verified must-haves
- Fraud alerts panel visible and functional in admin dashboard
- Cashier accounts page replaces hardcoded credentials end-to-end
- Transaction void endpoint tested and balance correctly restored
- SQLite offline queue tested: sale buffered during simulated outage, synced on reconnect
- FCM push fires for every purchase (cashier + NFC flows)
- SMS fires for purchase + low balance when TWILIO_* set
- Android app compiles with filter, budget reset, and lost card status changes
- Daily batch email scheduler starts on backend launch
- STATE.md updated and final commit on gsd/M001 branch

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011, R012, R013
- Partially covers: none
- Leaves for later: R050 (GCash), R051 (iOS)
- Orphan risks: none

## Slices

- [x] **S01: Fraud Alerts Panel & Card Suspension** `risk:high` `depends:[]`
  > After this: Admin can open the Fraud Alerts page in the dashboard, see all alerts with risk levels, resolve individual alerts, and manually suspend or unsuspend any student's money card.

<<<<<<< HEAD
- [x] **S02: SMS Notifications & Transaction Filter** `risk:medium` `depends:[S01]`
=======
- [x] **S02: SMS Notifications & Transaction Filter** `risk:medium` `depends:[S01]`
>>>>>>> gsd/M001/S02
  > After this: Admin can filter transactions by date range, student, and type in the dashboard; parents receive SMS for purchases and low balance when Twilio env vars are set.

- [ ] **S03: Cashier Account Management & Transaction Void** `risk:medium` `depends:[S01]`
  > After this: Admin manages named cashier accounts from the dashboard (no more hardcoded credentials); admin can void a transaction with a reason and the student's balance is restored.

- [ ] **S04: Offline Cashier Queue & Quick-Pay Shortcut** `risk:medium` `depends:[S03]`
  > After this: Cashier processes sales during a Google Sheets outage with a visual offline indicator, and transactions sync automatically on reconnect; cashier can tap Quick Pay on any product to skip the cart.

- [ ] **S05: Complete Push Notifications & Android Enhancements** `risk:low` `depends:[S04]`
  > After this: Every purchase and load fires an FCM push to the student; Android app has transaction type/date filter; monthly budget auto-resets; student sees lost card status and gets FCM push when admin processes replacement.

- [ ] **S06: Daily Low-Balance Batch Email** `risk:low` `depends:[S05]`
  > After this: Backend scheduler runs a daily job at configurable time, emails parents of all students below LOW_BALANCE_THRESHOLD, and logs the run result; admin can trigger it manually from the dashboard.

## Boundary Map

### S01 → S02, S03, S04, S05, S06

Produces:
- `GET /api/fraud/alerts` — list alerts with filters (money_card, risk_level, unresolved_only, limit)
- `POST /api/fraud/alerts/<id>/resolve` — mark alert resolved with notes
- `POST /api/fraud/cards/<uid>/suspend` — manually suspend a card
- `POST /api/fraud/cards/<uid>/unsuspend` — manually unsuspend a card
- `GET /api/fraud/suspended` — list all suspended cards
- `GET /api/fraud/stats` — alert counts by type and risk level
- Google Sheets "Fraud Alerts" worksheet — columns: AlertID, MoneyCard, FraudType, RiskLevel, Description, CreatedAt, Resolved, ResolvedAt, ResolutionNotes, AutoAction
- Fraud alerts panel in admin dashboard (new nav item, table with resolve button, card suspend/unsuspend action)
- FraudDetector now persists alerts to/from Sheets on init and on each new alert

Consumes: nothing (first slice)

### S02 → S04, S05

Produces:
- `TwilioSMSNotifier` class in `backend/notifications.py` — send_sms(to, body), send_purchase_sms(), send_low_balance_sms(), gated on TWILIO_* env vars
- Transaction filter controls in `/transactions` admin page — date-from, date-to, student search, type dropdown; calls existing analytics endpoints with new query params
- `GET /api/transactions/filtered` — accepts date_from, date_to, student_id, txn_type query params; returns filtered transaction list
- twilio added to `backend/dashboard/requirements.txt`

Consumes from S01: nothing directly (parallel concern)

### S03 → S04

Produces:
- Google Sheets "Cashier Accounts" worksheet — columns: AccountID, Username, PasswordHash, DisplayName, Status, CreatedAt, LastLogin
- `POST /api/cashier-accounts` — create account (admin only)
- `GET /api/cashier-accounts` — list accounts (admin only)
- `PUT /api/cashier-accounts/<id>` — update display name or status (admin only)
- Cashier accounts page in admin dashboard (new nav item, table, create form, activate/deactivate button)
- cashier_routes.py login now validates against Cashier Accounts sheet instead of hardcoded credentials
- `POST /api/admin/transactions/<txn_id>/void` — void transaction (admin only); restores balance, appends void record to Transactions Log
- Void button + reason modal in admin transactions page

Consumes from S01: nothing directly

### S04 → S05, S06

Produces:
- `backend/offline_queue.py` — SQLiteWriteQueue class: enqueue(op, sheet, data), process_queue(sheets_client), get_status(); backed by `offline_queue.db` SQLite file
- cashier_routes.py complete_sale() falls back to SQLiteWriteQueue on Sheets error; returns success with `{"offline": true}` flag
- `GET /cashier/api/queue/status` — pending count, failed count, last sync time
- Offline indicator in cashier UI (yellow banner when queue has pending items; syncs on next successful Sheets call)
- Quick Pay button on each product tile in cashier UI — triggers card scan immediately, bypasses cart; uses existing complete_sale() with single-item payload

Consumes from S03: cashier login now uses Cashier Accounts sheet (S03 must be done first so cashier auth works)

### S05 → S06

Produces:
- `fcm_sender.send_purchase_push()` called from cashier `complete_sale()` and NFC payment endpoint after successful deduction
- `fcm_sender.send_load_push()` called from admin `load_balance()` after successful load
- `fcm_sender.send_card_replaced_push(fcm_token, student_name)` — new helper, called from `replace_lost_card()` after successful replacement
- Android: `TransactionsActivity` filter bar (type chip group + date range picker) — filters local adapter; no new API call
- Android: `SecureStorage` new keys `KEY_BUDGET_MONTH` (string "YYYY-MM"); on app resume, if stored month ≠ current month, clear budget limit and show prompt
- Android: `HomeActivity` lost card status — after report, store `KEY_LOST_CARD_REPORTED=true`; show "Pending" badge; on FCM card_replaced message, clear flag and show "Resolved" toast
- Android: new FCM message type `card_replaced` handled in `FCMService.onMessageReceived()`
- `POST /api/student/lost-card-status` — returns `{reported: bool, processed: bool}` for the logged-in student

Consumes from S04: nothing directly

### S06 → (milestone end)

Produces:
- `backend/scheduler.py` — DailyScheduler class using APScheduler BackgroundScheduler (falls back to threading.Timer); job: run_low_balance_batch(sheets_client, email_notifier)
- `POST /api/admin/batch/low-balance-email` — trigger manually from admin dashboard
- Scheduler started in admin_dashboard.py `if __name__ == '__main__'` block
- Daily batch email sends one email per parent of students below LOW_BALANCE_THRESHOLD; logs result to "Scheduler Log" sheet

Consumes from S05: FCM push wiring (S05) ensures push + email + SMS are all consistent notification paths
