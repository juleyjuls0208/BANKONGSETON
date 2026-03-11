# M001: Operational Hardening & Feature Completion — Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

## Project Description

Bangko ng Seton is an RFID-based school canteen money management system. Students tap RFID cards or Android phones at the cashier to pay. Parents are notified. Admins manage everything via a web dashboard. The system uses Google Sheets as the database, Flask as the backend, and an Arduino with RC522/PN532 RFID reader at the cashier station.

## Why This Milestone

The core transaction flow works. This milestone addresses 13 gaps discovered during review: invisible fraud alerts, hardcoded cashier credentials, missing transaction filters, unimplemented SMS, no transaction void, in-memory-only offline queue, no quick-pay shortcut, incomplete push notification wiring, no Android transaction filter, budget not resetting monthly, no lost card status feedback, and no daily low-balance batch email.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Admin sees fraud alerts in the dashboard, resolves them, and manually suspends/unsuspends cards
- Admin filters the transactions page by date, student, and type
- Admin creates/deactivates cashier accounts (no more hardcoded credentials)
- Admin voids a transaction with a reason; balance is restored and the void is logged
- Cashier taps a product's Quick Pay button and scans card directly — no cart steps
- Cashier continues processing sales during a Google Sheets outage; transactions sync when back online
- Student receives FCM push for every purchase and load (not just low balance)
- Student filters transaction history by type and date in the Android app
- Student sees budget auto-reset at start of new month with a prompt to set new limit
- Student sees real-time status after reporting a lost card; gets notified when admin processes it
- Parent receives SMS (if configured) for purchases, loads, and low-balance events
- Admin receives daily batch email of all students below the low-balance threshold

### Entry point / environment

- Entry point: `python backend/dashboard/admin_dashboard.py` (port 5000), `python backend/api/api_server.py` (port 5001)
- Environment: Local dev / production (pythonanywhere.com for API)
- Live dependencies: Google Sheets API, Firebase FCM, SMTP email, Twilio SMS (optional)

## Completion Class

- Contract complete means: All API endpoints return correct responses verified by manual curl or test assertions
- Integration complete means: Admin dashboard UI works end-to-end in browser; Android app changes compile and run on device/emulator
- Operational complete means: Offline queue syncs after reconnect; daily scheduler fires; SMS sends when env vars set

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Admin can see a fraud alert in the dashboard, click resolve, and the alert disappears
- A sale processed while Google Sheets returns 503 is buffered and appears in the transactions log after reconnect
- Student receives an FCM push within 5 seconds of a cashier completing a sale
- Parent receives an SMS (Twilio test credentials) after an NFC payment that triggers low balance

## Risks and Unknowns

- Fraud alert UI integration — FraudDetector is in-memory; the admin dashboard and cashier are separate processes; alerts won't cross process boundaries unless stored persistently or the dashboard process owns the detector instance. Risk: high. Mitigation: store alerts in a dedicated Google Sheet or JSON file on disk.
- SQLite offline queue — must handle concurrent writes from the cashier Blueprint and main app on the same process. Risk: medium. Mitigation: use Python's built-in sqlite3 with WAL mode; single process means no true concurrency issue.
- Twilio package not installed — needs to be added to requirements.txt. Risk: low. Mitigation: add twilio to requirements.txt; gate on env var presence.
- APScheduler not installed — needed for daily batch email. Risk: low. Mitigation: use threading.Timer loop (already in stdlib) or add apscheduler to requirements.
- Android budget reset — no month key stored; need to add KEY_BUDGET_MONTH to SecureStorage and check on app resume. Risk: low.
- Lost card FCM notification — admin_dashboard.py must call fcm_sender.send_card_replaced_push after a successful card replacement; need to add a new FCM helper for this.

## Existing Codebase / Prior Art

- `backend/fraud_detection.py` — Full FraudDetector with alerts, suspend/unsuspend, get_stats. Instantiate via get_fraud_detector(). Not yet exposed via any route.
- `backend/api/fcm_sender.py` — send_low_balance_push, send_purchase_push, send_load_push. All implemented. purchase and load not yet called from transaction flows.
- `backend/notifications.py` — EmailNotifier with send_low_balance_alert, send_load_confirmation etc. TwilioSMSNotifier referenced in CHANGELOG but NOT implemented.
- `backend/resilience.py` — WriteQueue (in-memory Queue). Needs SQLite backing for persistence.
- `backend/dashboard/admin_dashboard.py` — load_balance() at line 878 sends email but not FCM push. get_recent_transactions() at line 994.
- `backend/dashboard/cashier/cashier_routes.py` — complete_sale() at line 222. Hardcoded cashier/cashier123 at line 62. No offline fallback.
- `backend/analytics.py` — filter_by_date_range() and other helpers. Used in exports but not in transactions UI.
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt` — getBudgetLimit/setBudgetLimit; no month key.
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsActivity.kt` — flat RecyclerView, no filter controls.
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — loadBudget(), calcMonthlySpend(), showBudgetDialog().
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — BangkoApiService interface, BASE_URL = https://juley2823.pythonanywhere.com/api/

## Relevant Requirements

- R001, R002 — Fraud alerts and card suspension UI
- R003 — Transaction filter/search in admin
- R004 — SMS notifications
- R005 — Cashier account management
- R006 — Transaction void
- R007 — Offline cashier queue
- R008 — Quick-pay shortcut
- R009, R010, R011, R012 — Android/push notification improvements
- R013 — Daily low-balance batch email

## Scope

### In Scope

- Backend API endpoints for fraud alert management, cashier accounts, transaction void, offline queue sync
- Admin dashboard UI additions (fraud panel, transaction filter, cashier accounts page, void UI)
- Cashier UI quick-pay shortcut + offline mode indicator
- TwilioSMSNotifier implementation and wiring
- FCM push for every purchase and load (cashier + NFC flows)
- Android app: transaction filter, monthly budget reset, lost card status tracking
- APScheduler or threading-based daily batch email job
- SQLite persistence for offline write queue

### Out of Scope / Non-Goals

- Payment gateway integration (GCash, Maya)
- iOS app
- Product inventory/stock tracking
- Parent top-up request flow
- PDF statement generation

## Technical Constraints

- Google Sheets is the only database; no PostgreSQL or MySQL
- sqlite3 is stdlib — no additional install for SQLite
- Twilio SDK must be added to requirements.txt (not currently installed)
- APScheduler or threading.Timer for scheduling (APScheduler preferred if installable)
- Android app changes must be in Kotlin, Material 3 style matching existing code
- All new API endpoints follow existing patterns: JWT Bearer auth, jsonify responses, 503 for Sheets errors

## Integration Points

- Google Sheets — reads/writes for fraud alert persistence, cashier accounts sheet, void log
- Firebase FCM — extended to purchase + load events via existing fcm_sender.py
- Twilio — new integration; gated on TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM env vars
- Android app — new API endpoints consumed by updated ApiClient.kt

## Open Questions

- Where to persist fraud alerts across restarts? Decision: new "Fraud Alerts" sheet in Google Sheets (same pattern as all other data). Keep the in-memory detector as a hot cache; flush resolved/new alerts to sheet.
- Cashier accounts storage? Decision: new "Cashier Accounts" sheet in Google Sheets; admin dashboard manages it.
- Daily scheduler approach? Decision: use APScheduler BackgroundScheduler if pip-installable at runtime; else fall back to threading.Timer restart loop. Check at startup.
