# Project

## What This Is

Bangko ng Seton is an RFID-based school money management system for a Philippine school canteen. Students use physical RFID cards (or NFC-enabled Android phones as virtual cards) to pay at the cashier. Parents receive notifications. Admins manage students, products, balances, and analytics via a web dashboard.

## Core Value

A student should be able to tap their card at the cashier, have the transaction processed, and have their parent notified — reliably, every time.

## Current State

- Flask backend (Python 3.14) with Google Sheets as the database
- Admin web dashboard (Bootstrap 5, Flask-SocketIO, PWA)
- Cashier UI with Arduino RFID card reader integration and Quick Pay shortcut
- Android student app (Kotlin, Material 3, NFC HCE virtual card)
- Parent portal (read-only balance + transaction view)
- FCM push notifications for every purchase, load, and card replacement
- SMS notifications via Twilio (gated on TWILIO_* env vars)
- Fraud detection engine wired to admin dashboard: alerts panel, card suspend/unsuspend, Sheets persistence
- Cashier accounts managed in Google Sheets (no hardcoded credentials)
- Transaction void with balance restoration and audit log
- Offline cashier queue backed by SQLite (survives process restart; syncs on reconnect)
- Daily low-balance batch email via APScheduler; manual trigger endpoint
- JWT auth for mobile API; session auth for admin dashboard
- Multi-station support via STATION_ID env var
- Android: transaction filter, monthly budget auto-reset, lost card status badge

## Architecture / Key Patterns

- `backend/dashboard/admin_dashboard.py` — main Flask app (SocketIO, fraud panel, cashier accounts, transaction void, batch email trigger)
- `backend/dashboard/cashier/cashier_routes.py` — cashier Blueprint (JWT, complete-sale with SQLite fallback, Quick Pay, queue sync)
- `backend/api/api_server.py` — mobile REST API (student login, balance, transactions, NFC, lost card status)
- `backend/fraud_detection.py` — FraudDetector (in-memory, Sheets-persisted; single-worker only — multi-worker causes split-brain)
- `backend/notifications.py` — EmailNotifier, TwilioSMSNotifier (gated on env vars)
- `backend/api/fcm_sender.py` — Firebase push (send_purchase_push, send_load_push, send_card_replaced_push)
- `backend/offline_queue.py` — SQLiteWriteQueue (WAL mode; get_offline_queue() singleton)
- `backend/scheduler.py` — DailyScheduler (APScheduler + threading.Timer fallback); run_low_balance_batch()
- `backend/resilience.py` — legacy stub; replaced by offline_queue.py
- Google Sheets worksheets: Users, Money Accounts, Transactions Log, Products, Fraud Alerts, Suspended Cards, Cashier Accounts, Scheduler Log
- Android app: `mobile/student_app_v2/` (mobile/android/ is archived)

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: Operational Hardening & Feature Completion — All 13 gaps closed. See `.gsd/milestones/M001/M001-SUMMARY.md`.
- [ ] M002: Production Readiness & Deployment Stability — S01 + S02 + S03 complete (requirements fixed; cache layer wired; startup guard + health standardization done). S04–S05 pending. See `.gsd/milestones/M002/M002-ROADMAP.md`.
