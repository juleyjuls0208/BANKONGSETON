# M005: RC522 + OLED + QR Payment

**Gathered:** 2026-03-17
**Status:** Ready for planning

## Project Description

BankongSeton cashless canteen system. Students pay using RFID cards or the mobile app (Android + iOS). This milestone retires all PN532/NFC/HCE code and introduces a new QR-based payment path that works on both platforms.

## Why This Milestone

PN532 (NFC) is being replaced with RC522 (RFID-only) on the R4 payment terminal. The phone HCE payment path (Android-only, fragile APDU timing) is replaced with QR code payment that works on both Android and iOS. The R4 LCD is replaced with an OLED so the QR bitmap can actually be rendered. The R3 role is locked to registration/replacement only.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Cashier builds cart, clicks Pay Now → R4 OLED immediately shows a QR code
- Student opens Android or iOS app, taps "Pay with QR", scans the OLED → sees cart items and total → taps Confirm → cashier sees success modal → balance debited in Sheets
- Physical RFID card tap at R4 still works exactly as before (M003 WiFi path preserved)
- R3 still handles card registration and lost-card replacement via RFID

### Entry point / environment

- Entry point: Cashier browser UI (Pay Now button) + student mobile app (Pay with QR button)
- Environment: School LAN (R4 WiFi), PythonAnywhere backend, Android + iOS devices
- Live dependencies involved: R4 Arduino over WiFi, Google Sheets, Firebase FCM

## Completion Class

- Contract complete means: verify scripts pass; `python -m py_compile` exits 0; Android + iOS build without errors; QR token round-trip verified by script
- Integration complete means: R4 OLED renders QR when cashier hits Pay Now (live hardware); student app scans and confirms a real sale
- Operational complete means: R4 WiFi + heartbeat still functional after firmware swap; powerbank behaviour unchanged

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Physical RFID card tapped at powerbank-powered R4 → POST /api/arduino/card-read 200 → cashier success modal
- Student scans R4 OLED QR on Android app → cart confirmation screen → Confirm → Sheets balance debited → cashier success modal
- Student scans R4 OLED QR on iOS app → cart confirmation screen → Confirm → Sheets balance debited → cashier success modal

## Risks and Unknowns

- QR bitmap rendering on 128×64 OLED — a QR code for a URL (~40 chars) generates a Version 2 or 3 symbol (~25×25 modules); scaling to 128×64 at 4–5px per module is tight but feasible with Adafruit GFX; needs hardware verification
- RC522 SPI pinout on R4 WiFi — R3 uses D10(SS)/D8(RST)/D11/D12/D13; R4 currently uses D10(SS) for PN532 on the same SPI bus; pin assignments should be identical, but R4 WiFi SPI behaviour needs confirmation
- OLED I2C address conflict — SSD1306 default is 0x3C; the old LCD was on D6/D7 bit-bang at 0x27; OLED will use hardware I2C (Wire) on R4's SDA/SCL pins (A4/A5 on UNO, or the dedicated I2C header); no conflict expected but needs hardware confirmation
- Arduino QR library for embedded — `qrcode` by Richard Moore is the standard lightweight choice for Arduino; generates a raw bit matrix which Adafruit GFX can render pixel-by-pixel; no font rendering required
- Android QR scanning — no existing camera/ZXing dependency in build.gradle.kts; need to add ML Kit Barcode Scanning or ZXing Android Embedded
- iOS QR scanning — AVFoundation built-in; no new dependency needed

## Existing Codebase / Prior Art

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — R4 firmware being rewritten (→ renamed `bankongseton_r4/`)
- `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` — R3 firmware; already uses MFRC522, needs cleanup
- `backend/dashboard/web_app.py` — add /api/arduino/qr-pending and /api/arduino/heartbeat already present
- `backend/dashboard/cashier/cashier_routes.py` — add /cashier/api/qr-generate; remove complete_sale_nfc
- `backend/api/api_server.py` — add /api/qr/confirm; remove all /api/nfc/* routes
- `backend/nfc_payments.py` — delete entirely
- `mobile/student_app_v2/` — Android app; add QR scanner activity; remove NfcManager, BankoHceService, NfcPayOverlayActivity
- `mobile/ios/BankongSetonStudent/` — iOS SwiftUI app; add QRPayView + QRScannerView + QRPayViewModel

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R026 — RC522 on R4
- R027 — OLED on R4
- R028 — QR token delivery via Arduino polling
- R029 — Backend QR payment flow
- R030 — Android QR Pay
- R031 — RC522 cleanup on R3
- R032 — Dead NFC/HCE code removed
- R033 — iOS QR Pay

## Scope

### In Scope

- R4 firmware: PN532 → RC522, LCD → SSD1306 OLED, QR polling loop
- R3 firmware: cleanup only (already uses MFRC522), no feature changes
- Backend: QR generate/pending/confirm endpoints; remove all NFC endpoints and nfc_payments.py
- Android app: QR Pay button + scanner + confirmation screen; remove all HCE/NFC files
- iOS app: QR Pay button + AVFoundation scanner + confirmation view
- Cashier UI: remove nfc_payment socket handler and completeNFCSale; QR flow is entirely app-initiated (no cashier UI change beyond removing dead code)
- Directory rename: `arduino/bankongseton_rfid/` → `arduino/bankongseton_r4/`

### Out of Scope / Non-Goals

- QR payment on R3 (registration terminal only)
- iOS native app rebuild (existing SwiftUI app is extended, not replaced)
- GCash/Maya payment gateway
- Any changes to RFID card registration, lost-card flow, admin dashboard

## Technical Constraints

- R4 WiFi: SPI bus shared between RC522 and any other SPI device is not present here; RC522 uses hardware SPI D10/D11/D12/D13 + RST on D8 — identical to R3
- OLED: use hardware I2C (Wire.h); Adafruit SSD1306 + Adafruit GFX; SSD1306 default I2C address 0x3C
- QR library: `qrcode` by Richard Moore (Arduino) — generates raw bit matrix, no bitmap font needed
- Android QR scanning: add ML Kit Barcode Scanning (`com.google.mlkit:barcode-scanning`) — already have firebase-bom in deps, so ML Kit is a natural fit
- iOS QR scanning: AVFoundation `AVCaptureMetadataOutput` — no new dependency, built-in
- Backend QR token: store in Flask app state (same pattern as `app.arduino_last_heartbeat`); token is a UUID4; URL encoded is `https://<SERVER_URL>/api/qr/<token>`; expires after 5 minutes if unclaimed
- `python -m py_compile` must exit 0 on all modified Python files before any slice is considered done

## Integration Points

- Arduino R4 ↔ backend: polls `GET /api/arduino/qr-pending` (API key auth, same as heartbeat); existing WiFi/heartbeat path unchanged
- Student app ↔ backend: `GET /api/qr/<token>` (JWT auth) to fetch cart; `POST /api/qr/confirm` (JWT auth) to pay
- Cashier ↔ backend: `POST /cashier/api/qr-generate` (JWT auth) to create QR; existing `card_read` SocketIO event unchanged; new `qr_payment` SocketIO event for app-confirmed payments
- Cashier UI ↔ OLED: indirect — cashier generates token, Arduino polls and renders; no direct cashier→Arduino channel

## Open Questions

- QR code version / error correction level — Version 2 (25×25 modules) with ECC level M fits a ~35-char URL; at 4px/module = 100×100px on a 128×64 OLED with top/bottom padding; ECC level L if the URL is longer than ~35 chars. To be confirmed when backend URL format is finalised.
- Pending QR storage: in-memory dict on Flask app object (same as `arduino_last_heartbeat`) is fine for single-worker PythonAnywhere; document in DEPLOY.md that this resets on restart.
