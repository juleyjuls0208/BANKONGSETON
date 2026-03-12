# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001 | arch | Fraud alert persistence | Google Sheets "Fraud Alerts" worksheet | Consistent with all other data storage; no new infra; readable by admin | Yes — if volume demands a real DB |
| D002 | M001 | arch | Cashier accounts storage | Google Sheets "Cashier Accounts" worksheet | Same pattern as Users; admin can view/edit directly in Sheets if needed | Yes — if security requirements tighten |
| D003 | M001 | arch | Offline queue persistence | SQLite (stdlib sqlite3, WAL mode) | Survives process restart; no new package; single-process so no contention | No |
| D004 | M001 | pattern | Cashier password storage | bcrypt hash in Cashier Accounts sheet | Passwords must never be stored plaintext; bcrypt is the standard | No |
| D005 | M001 | library | SMS notifications | Twilio Python SDK | CHANGELOG referenced it; widely used in PH; gated on env vars | Yes — if another SMS gateway preferred |
| D006 | M001 | library | Daily scheduler | APScheduler BackgroundScheduler with threading.Timer fallback | APScheduler is cleaner; fallback ensures it works even without pip install | Yes — if moving to a task queue |
| D007 | M001 | pattern | Transaction void | Append new void record to Transactions Log + restore balance | Preserves audit trail; no row deletion; consistent with existing log pattern | No |
| D008 | M001 | pattern | Lost card FCM message type | New FCM data message type "card_replaced" handled in FCMService | Decoupled from notification; app can update state on receive | No |
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> gsd/M001/S01
=======
>>>>>>> gsd/M001/S01
| D009 | M001/S01 | pattern | Fraud Sheets lazy init | _get_fraud_detector_with_sheets() called on first API request, not at app startup | Avoids blocking app boot when Sheets is unavailable; acceptable latency tradeoff on first fraud-page load | Yes — if strict cold-start time SLA required |
| D010 | M001/S01 | pattern | Fraud sheet persistence non-fatal | Sheet write/read failures logged at WARNING level; in-memory FraudDetector remains source of truth | Sheets outage should not hard-block fraud detection in-process; data can be re-persisted on reconnect | No |
| D011 | M001/S01 | security | resolve_fraud_alert authorization | @login_required only (finance role can resolve); suspend/unsuspend require @admin_only | Finance staff handle day-to-day alert triage; only admins should lock/unlock cards | Yes — if tighter access control needed |
| D012 | M001/S01 | pattern | load_from_sheets consolidation | load_from_sheets(fraud_ws, suspended_ws) loads both worksheets in one call instead of two separate methods | Reduces Sheets round-trips; both datasets are always needed together on init | No |
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> gsd/M001/S01
=======
>>>>>>> gsd/M001/S01
=======
>>>>>>> gsd/M001/S01
=======
>>>>>>> gsd/M001/S02
