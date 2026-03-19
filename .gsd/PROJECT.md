# BankongSeton — Cashless Canteen System

## What This Is

A cashless payment system for a school canteen. Students carry RFID cards or use the mobile app (Android + iOS). Cashiers run a browser-based POS terminal backed by Flask + Google Sheets. An Arduino UNO R4 WiFi acts as the wireless payment terminal; an Arduino UNO R3 handles card registration and lost-card replacement only.

## Core Value

Physical RFID card tapped at the cashier counter completes a sale — balance debited, parent notified, cashier sees confirmation. Everything else extends this loop.

## Current State

- Flask backend deployed on PythonAnywhere (dashboard app + API server)
- Google Sheets as the primary datastore
- Cashier browser UI with real-time SocketIO events
- Arduino UNO R4 WiFi: **RC522 MFRC522 + SSD1306 OLED firmware** (M005/S01+S02 done) — WiFi card-read routing, heartbeat, WiFi badge preserved; Adafruit SSD1306 driver active; QR poll loop (500ms, GET /api/arduino/qr-pending) renders bitmaps on OLED; directory `bankongseton_r4/`
- Arduino UNO R3: uses RC522 RFID — card registration and lost-card replacement only; README updated (M005/S01)
- **Backend QR payment flow** (M005/S03 done): `POST /cashier/api/qr-generate` → `GET /api/arduino/qr-pending` → student scans → `GET /api/qr/<token>` → `POST /api/qr/confirm` → balance debited → `qr_payment` SocketIO → cashier success modal; `app.pending_qr_token` in-memory state; `jwt_token` in student login response; 14/14 contract checks pass
- Android app (student_app_v2): balance, transactions, FCM push, NFC HCE pay (being removed in M005/S05)
- iOS app (mobile/ios/BankongSetonStudent): balance, transactions, FCM push — QR payment coming in M005/S04
- Standalone cashier app (M006/S01+S02+S03): login + JWT cookie auth + `/api/products` + modern POS screen + standalone payment/Arduino/QR APIs on port 5010 (`/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`, `/api/arduino/*`); POS now orchestrates RFID/QR/NFC flows with queue/WiFi diagnostics and no `:5003` dependency verified in runtime UAT (live hardware + non-mocked Sheets sale still recommended for final ops sign-off)

## Architecture / Key Patterns

- Dashboard Flask app: `backend/dashboard/web_app.py` (routes + SocketIO), `cashier/cashier_routes.py` (payment logic)
- API Flask app: `backend/api/api_server.py` (student-facing REST)
- Cache layer: `backend/cache.py` — get_cached/set_cached/invalidate_pattern
- Offline queue: `backend/offline_queue.py` — SQLite WAL, syncs on reconnect
- Arduino R4: `arduino/bankongseton_r4/bankongseton_r4.ino` — RC522 MFRC522 firmware (M005/S01); OLED placeholder ready for S02
- Arduino R3: `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino`
- Android: `mobile/student_app_v2/` — Kotlin, Retrofit, Firebase FCM
- iOS: `mobile/ios/BankongSetonStudent/` — SwiftUI, URLSession, no payment method pre-M005

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: Operational Hardening & Feature Completion — fraud UI, SMS, cashier accounts, void, offline queue, push notifications
- [x] M002: Production Readiness & Deployment Stability — requirements, cache, worker safety, tests, health checks, runbook
- [x] M003: Wireless Cashier Payment Terminal — R4 WiFi routing fix, phone NFC cashier pay, WiFi badge, powerbank hardening
- [x] M004: NFC Phone Payment Fix — APDU retry firmware, end-to-end NFC validation
- [x] M005: RC522 + OLED + QR Payment — swap PN532→RC522 on R4, LCD→OLED on R4, QR payment on both Android and iOS
- [ ] M006: Standalone Cashier Web App — dedicated port-5010 cashier site with modern POS UI, isolated from admin dashboard (**S01 + S02 + S03 complete; perform live hardware + non-mocked Sheets sale UAT for full milestone sign-off**)
