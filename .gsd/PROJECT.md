# Project

## What This Is

Bangko ng Seton is an RFID-based school money management system for a Philippine school canteen. Students use physical RFID cards (or NFC-enabled Android phones as virtual cards) to pay at the cashier. Parents receive notifications. Admins manage students, products, balances, and analytics via a web dashboard.

## Core Value

A student should be able to tap their card at the cashier, have the transaction processed, and have their parent notified — reliably, every time.

## Current State

- Flask backend (Python 3.14) with Google Sheets as the database
- Admin web dashboard (Bootstrap 5, Flask-SocketIO, PWA)
- Cashier UI with Arduino RFID card reader integration
- Android student app (Kotlin, Material 3, NFC HCE virtual card)
- Parent portal (read-only balance + transaction view)
- FCM push notifications (low balance only wired end-to-end)
- Fraud detection engine exists but has no admin UI
- JWT auth for mobile API; session auth for admin dashboard
- Multi-station support via STATION_ID env var
- 170 passing tests

## Architecture / Key Patterns

- `backend/dashboard/admin_dashboard.py` — main Flask app (SocketIO, RFID card management, analytics, load balance)
- `backend/dashboard/cashier/cashier_routes.py` — cashier Blueprint (JWT, process-sale, complete-sale)
- `backend/api/api_server.py` — mobile REST API (student login, balance, transactions, NFC)
- `backend/fraud_detection.py` — FraudDetector engine (in-memory, not yet wired to admin UI)
- `backend/notifications.py` — EmailNotifier, NotificationManager
- `backend/api/fcm_sender.py` — Firebase push (send_low_balance_push, send_purchase_push, send_load_push)
- `backend/resilience.py` — WriteQueue (in-memory, not yet persisted to disk/SQLite)
- Google Sheets worksheets: Users, Money Accounts, Transactions Log, Products
- Android app: `mobile/student_app_v2/`

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: Operational Hardening & Feature Completion — Wire fraud alerts to admin UI, cashier account management, transaction filter, SMS notifications, transaction void/correction, offline cashier queue, quick-pay shortcut, push notifications for every transaction, Android transaction filter, monthly budget auto-reset, lost card status feedback, and daily low-balance batch email.
