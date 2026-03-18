# M005: RC522 + OLED + QR Payment

**Vision:** Replace the PN532 NFC reader with RC522 RFID on both Arduinos, swap the R4's LCD for an SSD1306 OLED, and introduce QR-based payment that works on both Android and iOS — retiring all phone HCE/NFC code in the process.

## Success Criteria

- Physical RFID card tapped at powerbank-powered R4 completes a sale end-to-end: balance debited in Sheets, cashier sees success modal
- R4 OLED renders a QR code within ~1s of cashier hitting Pay Now; returns to idle when payment completes or cashier cancels
- Student scans OLED QR in Android app → sees cart → Confirm → balance debited → cashier success modal
- Student scans OLED QR in iOS app → sees cart → Confirm → balance debited → cashier success modal
- All HCE/NFC code gone: BankoHceService, NfcManager, NfcPayOverlayActivity, nfc_payments.py, /api/nfc/* routes, complete_sale_nfc, socket.on('nfc_payment')
- Both apps build without NFC/HCE references; `python -m py_compile` exits 0 on all modified Python files

## Key Risks / Unknowns

- QR bitmap on 128×64 OLED — a ~35-char URL at Version 2 ECC-L is 25×25 modules; at 5px/module = 125×125 which overflows 128×64; need to use a smaller version or landscape orientation with scaling; needs hardware proof
- RC522 SPI on R4 WiFi — pinout identical to R3 (D10/D11/D12/D13/RST=D8) but R4 WiFi SPI behaviour with MFRC522 library needs confirmation; R3 already proves it works on UNO-class hardware

## Proof Strategy

- QR bitmap risk → retire in S02 by rendering a hardcoded test QR on real OLED hardware and confirming it is scannable with a phone camera
- RC522 on R4 risk → retire in S01 by tapping a physical card at R4 and confirming POST /api/arduino/card-read 200 in Flask log

## Verification Classes

- Contract verification: `python -m py_compile` exits 0 on all modified Python files; `scripts/verify-m005-s0N.sh` grep checks; Android build exits 0; iOS build exits 0
- Integration verification: physical RFID card tap at R4 → Flask log; QR scan on real phone → Sheets debit confirmed
- Operational verification: R4 WiFi heartbeat still fires at 30s interval after firmware swap; powerbank behaviour unchanged
- UAT / human verification: cashier tests card tap + QR payment on actual hardware before milestone is called done

## Milestone Definition of Done

This milestone is complete only when all are true:

- S01: RC522 card read on R4 confirmed — POST /api/arduino/card-read 200 in Flask log from powerbank-powered R4
- S02: OLED QR confirmed scannable — test QR rendered on real hardware and scanned by phone camera
- S03: QR payment round-trip verified — qr-generate → qr-pending → qr/confirm all pass verify script; Sheets balance debited
- S04: Both apps build and complete a real QR payment end-to-end
- S05: All NFC dead code deleted; `python -m py_compile` exits 0; both apps build clean
- `arduino/bankongseton_r4/` exists; `arduino/bankongseton_rfid/` is gone

## Requirement Coverage

- Covers: R026, R027, R028, R029, R030, R031, R032, R033
- Partially covers: none
- Leaves for later: none
- Orphan risks: none

## Slices

- [x] **S01: RC522 Firmware Swap (R4 + R3)** `risk:high` `depends:[]`
  > After this: Physical RFID card tapped at powerbank-powered R4 POSTs to /api/arduino/card-read over WiFi and fires card_read in cashier UI — verified by POST appearing in Flask log. R3 reads UID via RC522 and echoes serial. Directory renamed to bankongseton_r4/.

- [x] **S02: OLED Driver + QR Polling on R4** `risk:high` `depends:[S01]`
  > After this: R4 OLED shows "Ready" at idle; when backend has a pending QR token, OLED renders the QR bitmap within one poll cycle (~500ms); QR is scannable by a phone camera — verified on real hardware.

- [x] **S03: Backend QR Payment Flow** `risk:medium` `depends:[]`
  > After this: POST /cashier/api/qr-generate creates a token; GET /api/arduino/qr-pending returns it; POST /api/qr/confirm (JWT) debits balance and emits qr_payment socket event to cashier — all verified by scripts/verify-m005-s03.sh.

- [x] **S04: Android + iOS App QR Pay** `risk:medium` `depends:[S03]`
  > After this: Android student taps "Pay with QR", scans OLED, sees cart, taps Confirm — sale completes. iOS student does the same. Both apps build. End-to-end verified on real devices against real backend.

- [ ] **S05: NFC/HCE Cleanup + Rename** `risk:low` `depends:[S01,S03,S04]`
  > After this: BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt deleted; nfc_payments.py deleted; /api/nfc/* routes gone; complete_sale_nfc and socket.on('nfc_payment') removed; both apps build clean; python -m py_compile exits 0.

## Boundary Map

### S01 → S02

Produces:
- `arduino/bankongseton_r4/bankongseton_r4.ino` — RC522 card read loop + WiFi POST to /api/arduino/card-read + heartbeat; OLED pins assigned (hardware I2C SDA/SCL); no OLED driver code yet — just pin reservation and includes placeholder
- `arduino/bankongseton_r4/secrets.h` — unchanged format from bankongseton_rfid/secrets.h
- RC522 SPI wiring confirmed working on R4 WiFi hardware

Consumes:
- nothing (first slice)

### S01 → S05

Produces:
- `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` — cleaned of any PN532/NFC references; role comment updated to registration-only
- Directory rename: `arduino/bankongseton_rfid/` → `arduino/bankongseton_r4/`

Consumes:
- nothing (first slice)

### S03 → S02

Produces:
- `GET /api/arduino/qr-pending` (API key auth) — returns `{token, url}` when pending, `{token: null}` when idle
- `POST /cashier/api/qr-generate` (JWT auth) — creates UUID token, stores as `app.pending_qr_token`, returns `{token, url}`
- `POST /api/qr/confirm` (student JWT) — validates token, debits balance via complete_sale logic, emits `qr_payment` SocketIO event, clears pending token
- `GET /api/qr/<token>` (student JWT) — returns pending cart `{items, total, cashier}` for app to display before confirm
- `app.pending_qr_token` — Flask app-level dict `{token, cart_snapshot, created_at, cashier_session}`

Consumes:
- nothing (parallel to S01)

### S03 → S04

Produces:
- All backend QR endpoints above — Android and iOS call these directly
- QR URL format: `https://<SERVER_URL>/api/qr/<token>` — this is what gets encoded in the QR bitmap

Consumes:
- nothing (parallel to S01)

### S02 → S04

Produces:
- Scannable QR on OLED — Android and iOS camera can read it

Consumes from S01:
- `bankongseton_r4.ino` base firmware (RC522 loop + WiFi working)

### S04 → S05

Produces:
- `QRPayActivity.kt` + `activity_qr_pay.xml` — Android QR scanner + confirmation screen
- `QRPayView.swift` + `QRScannerView.swift` + `QRPayViewModel.swift` — iOS QR scanner + confirmation
- `BangkoApiService` updated — adds `getQrCart()` and `confirmQrPayment()` endpoints
- `APIEndpoints.swift` updated — adds `/api/qr/<token>` and `/api/qr/confirm`
- NFC/HCE entry points removed from HomeActivity.kt and HomeView.swift

Consumes from S03:
- GET /api/qr/<token> and POST /api/qr/confirm endpoints

### S01,S03,S04 → S05

S05 deletes:
- `BankoHceService.kt`, `NfcManager.kt`, `NfcPayOverlayActivity.kt`
- `activity_nfc_pay_overlay.xml`, `xml/hce_service.xml`
- `nfc_payments.py`
- `/api/nfc/register`, `/api/nfc/status`, `/api/nfc/unregister`, `/api/nfc/pay` routes in api_server.py
- `complete_sale_nfc()` and `socket.on('nfc_payment')` in cashier_routes.py / cashier_index.html
- NFC permissions from AndroidManifest.xml
- `nfc` type string handling in iOS TransactionRowView / ReceiptView (rename to "QR Payment" display string)

Consumes from S01: R3 firmware cleaned (no PN532 refs to clean up in S05)
Consumes from S03: /api/nfc/* confirmed replaced by /api/qr/*
Consumes from S04: Android + iOS confirmed not importing NfcManager/BankoHceService
