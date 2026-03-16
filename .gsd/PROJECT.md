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
- TTL cache (cache.py) wired to all hot Sheets-reading endpoints (30s products/users, 10s transactions); mutations invalidate on write
- WEB_CONCURRENCY startup guard in both WSGI entry points (hard-fail on multi-worker config)
- Standardized /api/health on all three app files ({status, sheets_ok, latency_ms, queue_pending, timestamp}; 503 on Sheets failure)
- 35-test critical-path unit test suite (complete_sale, load_balance, void_transaction, cashier auth); 2.40s; zero live Sheets calls
- docs/DEPLOY.md — complete PythonAnywhere deployment runbook (11 sections)
- Arduino UNO R4 WiFi firmware (`arduino/bankongseton_rfid/`) — dual-mode: APDU (HCE phone) + UID (physical RFID), WiFiS3, PN532 over SPI, HTTP POST to Flask backend, serial fallback; **M003/S01 fix: `httpPostCard(uid)` → `/api/arduino/card-read`, `httpPostNFC(token)` → `/api/nfc/tap`, dispatched by prefix in `deliver()`**; **M004/S01 fix: `inDataExchange` wrapped in 3-attempt retry loop (`APDU_MAX_RETRIES=3`, `APDU_RETRY_DELAY_MS=150`); per-attempt `"APDU attempt N/3 ok=YES/NO rspLen=N"` diagnostic in Serial Monitor**
- Arduino 30s heartbeat POST loop — `lastHeartbeatMs` file-scope variable + timer block in loop() before `if (!found) return`; keeps powerbank alive during idle; drives cashier #wifiBadge green via S03 backend
- `arduino/README-wireless.md` — complete standalone wireless deployment guide (hardware, wiring, secrets.h field-by-field with explicit port 5003 + ARDUINO_API_KEY, flashing, powerbank selection, verification, troubleshooting)
- `scripts/verify-m003-s04.sh` — 8-check assertion script; exits 0
- Phone NFC payment wired at cashier (M003/S02): `POST /cashier/api/complete-sale-nfc` resolves virtual card token via VirtualCards sheet, debits balance, returns same payload as physical card tap; `socket.on('nfc_payment', ...)` in cashier UI calls `completeNFCSale(token)` — no arduinoConnected gate on inbound event

## Architecture / Key Patterns

- `backend/dashboard/admin_dashboard.py` — main Flask app (SocketIO, fraud panel, cashier accounts, transaction void, batch email trigger)
- `backend/dashboard/cashier/cashier_routes.py` — cashier Blueprint (JWT, complete-sale with SQLite fallback, Quick Pay, queue sync)
- `backend/api/api_server.py` — mobile REST API (student login, balance, transactions, NFC, lost card status)
- `backend/dashboard/web_app.py` — cashier-facing Flask app; `/api/arduino/card-read` receives WiFi card reads (emits `card_read`); `/api/nfc/tap` receives WiFi NFC tokens (emits `nfc_payment`)
- `backend/dashboard/dashboard_core.py` — shared Flask app factory; registers `/api/nfc/tap` endpoint
- `backend/dashboard/arduino_bridge.py` — ArduinoBridge (serial path: reads `CARD|UID` + `NFC|token` lines, emits SocketIO events, calls `/api/nfc/pay` for phone taps)
- `backend/fraud_detection.py` — FraudDetector (in-memory, Sheets-persisted; single-worker only — multi-worker causes split-brain)
- `backend/notifications.py` — EmailNotifier, TwilioSMSNotifier (gated on env vars)
- `backend/api/fcm_sender.py` — Firebase push (send_purchase_push, send_load_push, send_card_replaced_push)
- `backend/offline_queue.py` — SQLiteWriteQueue (WAL mode; get_offline_queue() singleton)
- `backend/scheduler.py` — DailyScheduler (APScheduler + threading.Timer fallback); run_low_balance_batch()
- `backend/resilience.py` — legacy stub; replaced by offline_queue.py
- Google Sheets worksheets: Users, Money Accounts, Transactions Log, Products, Fraud Alerts, Suspended Cards, Cashier Accounts, Scheduler Log
- Android app: `mobile/student_app_v2/` (mobile/android/ is archived)
- Arduino firmware: `arduino/bankongseton_rfid/bankongseton_rfid.ino` (R4 WiFi, payment reader) + `arduino/bankongseton_nfc_r3/` (R3, registration reader only)

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: Operational Hardening & Feature Completion — All 13 gaps closed. See `.gsd/milestones/M001/M001-SUMMARY.md`.
- [x] M002: Production Readiness & Deployment Stability — All 5 slices complete. Requirements fixed (R014), cache wired (R015), startup guard + health standardized (R016, R018), 35-test critical-path suite (R017), deployment runbook (R019). See `.gsd/milestones/M002/M002-SUMMARY.md`.
- [x] M003: Wireless Cashier Payment Terminal — All 4 slices complete (37/37 contract assertions pass; py_compile exit 0; R024 validated). Hardware UAT gate remaining: flash firmware → confirm POST /api/arduino/card-read on card tap → badge green within 30s → 30-min powerbank soak. See `.gsd/milestones/M003/M003-SUMMARY.md`.
- [ ] M004: NFC Phone Payment Fix — Fix APDU timing bug that causes all phone NFC taps to fail with "Card not found"; add firmware retry loop; validate complete_sale_nfc on real hardware for the first time.
  - [x] S01: Firmware APDU Retry — complete (`verify-m004.sh` 5/5 pass; APDU_MAX_RETRIES=3 + retry loop in firmware; hardware tap + Serial Monitor confirmation pending S02)
  - [x] S02: End-to-End Validation + Backend Cleanup — complete (verify-m004.sh 7/7 pass; D038 alignment in complete_sale_nfc() — direct str().strip() comparison, normalized_money_card removed; full signal chain statically verified; hardware UAT S02-UAT.md ready for human operator)
