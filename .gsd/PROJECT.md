# BankongSeton — Cashless Canteen System

## What This Is

A cashless payment system for a school canteen. Students carry RFID cards or use the mobile app (Android + iOS). Cashiers run a browser-based POS terminal backed by Flask + Google Sheets. An Arduino UNO R4 WiFi acts as the wireless payment terminal; an Arduino UNO R3 handles card registration and lost-card replacement only.

## Core Value

Physical RFID card tapped at the cashier counter completes a sale — balance debited, parent notified, cashier sees confirmation. Everything else extends this loop.

## Current State

- Flask backend deployed on PythonAnywhere (dashboard app + API server)
- Google Sheets as the primary datastore
- Cashier browser UI with real-time SocketIO events
- Arduino UNO R4 WiFi: currently uses PN532 (NFC/RFID) + LCD — WiFi card-read routing, heartbeat, WiFi badge all working (M003)
- Arduino UNO R3: uses RC522 RFID — card registration and lost-card replacement only
- Android app (student_app_v2): balance, transactions, FCM push, NFC HCE pay (being removed)
- iOS app (mobile/ios/BankongSetonStudent): balance, transactions, FCM push — no payment method yet

## Architecture / Key Patterns

- Dashboard Flask app: `backend/dashboard/web_app.py` (routes + SocketIO), `cashier/cashier_routes.py` (payment logic)
- API Flask app: `backend/api/api_server.py` (student-facing REST)
- Cache layer: `backend/cache.py` — get_cached/set_cached/invalidate_pattern
- Offline queue: `backend/offline_queue.py` — SQLite WAL, syncs on reconnect
- Arduino R4: `arduino/bankongseton_rfid/bankongseton_rfid.ino` (→ renamed `bankongseton_r4/` in M005)
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
- [ ] M005: RC522 + OLED + QR Payment — swap PN532→RC522 on R4, LCD→OLED on R4, QR payment on both Android and iOS
