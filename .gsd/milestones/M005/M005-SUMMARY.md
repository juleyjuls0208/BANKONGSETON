---
id: M005
provides:
  - arduino/bankongseton_r4/bankongseton_r4.ino — MFRC522 + SSD1306 OLED + QR poll firmware (RC522 read loop, WiFi card delivery, 500ms qr-pending poll, Adafruit SSD1306 driver, renderQr auto-scale bitmap, httpGetBody, parseQrUrl, oledShowReady)
  - arduino/bankongseton_r4/secrets.h — credentials file unchanged in format
  - arduino/bankongseton_rfid/ — deleted; replaced by bankongseton_r4/
  - arduino/bankongseton_nfc_r3/README.md — rewritten with accurate RC522/MFRC522 hardware documentation
  - backend/dashboard/web_app.py — app.pending_qr_token state; GET /api/arduino/qr-pending; GET /api/qr/<token>; POST /api/qr/confirm with 3-retry/rollback/offline-queue; qr_payment SocketIO emit; import jwt as _pyjwt; import json
  - backend/api/api_server.py — jwt_token field in login response; /api/nfc/* routes deleted
  - backend/dashboard/cashier/cashier_routes.py — POST /cashier/api/qr-generate; complete_sale_nfc and PhoneUID fallback deleted
  - backend/dashboard/cashier/templates/cashier_index.html — socket.on('qr_payment') handler; nfc_payment handler deleted; completeNFCSale deleted
  - backend/dashboard/arduino_bridge.py — NFC delivery infrastructure deleted (_QueuedPayment, queue constants, retry thread, NFC/ERROR parse branches)
  - backend/nfc_payments.py — deleted
  - backend/tests/test_arduino_bridge_nfc.py — deleted
  - mobile/student_app_v2/app — QRPayActivity.kt; CameraX+ML Kit scanning; JWT storage; QR API methods; CAMERA permission; 5 NFC/HCE files deleted; NFC dead code removed from HomeActivity/ApiClient/Models/Manifest/strings.xml
  - mobile/ios/BankongSetonStudent — QRPayView.swift; QRScannerView.swift; QRPayViewModel.swift; QRModels.swift; HomeView.swift QR button; project.pbxproj registration; iOS NFC display labels consolidated
  - scripts/verify-m005-s01.sh through verify-m005-s05.sh — contract verification scripts (9+9+14+12+18 checks; all exit 0)
  - .env.example — SERVER_URL in QR Payment section
  - docs/DEPLOY.md — SERVER_URL row in deploy env vars table
key_decisions:
  - D041: PN532 → RC522 on R4; phone NFC/HCE payment retired entirely
  - D042: LCD → SSD1306 OLED on R4; Wire.h hardware I2C; Adafruit SSD1306 + GFX
  - D043: QR delivery via Arduino polling (500ms); backend stores token in app.pending_qr_token (in-memory)
  - D044: QR encodes full URL; app fetches cart separately via GET /api/qr/<token>
  - D045: Android QR scanning via ML Kit Barcode Scanning (firebase-bom already in deps)
  - D046: iOS QR scanning via AVFoundation (no new dependency)
  - D047: Arduino QR generation via qrcode by Richard Moore (raw bit matrix → Adafruit GFX drawPixel)
  - D048: Dead test files deleted alongside production NFC code they test
  - D049: Android string resource removal requires full grep before deleting (AAPT2 resolves at build time)
  - D050: ReceiptActivity fallback label replaced with inline "Payment" string
patterns_established:
  - RC522 VersionReg halt-check pattern for SPI init (halts on wiring fault — intentional diagnostic)
  - PICC_HaltA + PCD_StopCrypto1 called unconditionally after every card read (prevents stuck card state)
  - QR poll guard: check qrUrl != lastQrUrl before redrawing OLED (prevents flicker)
  - httpGetBody header-skip: read lines until blank line to consume HTTP headers before body
  - Non-fatal OLED init: Serial message + continue (RFID payment still works without display)
  - 500ms QR poll in both main loop and cooldown while-loop (now2 avoids variable shadowing)
  - QR debit clones complete_sale() retry/rollback/offline-queue pattern exactly (3-attempt, exponential backoff, rollback on balance_deducted, offline_queue fallback)
  - 402 for insufficient-funds (not 400) — distinguishes from bad-request for mobile error handling
  - socketio.emit('qr_payment') fires BEFORE app.pending_qr_token = None (prevents OLED/cashier race)
  - "nfc" historical-type filter references deliberately preserved in Android and iOS transaction history display
  - Dead imports cleaned after removing feature blocks (Kotlin: android.app.Activity, ActivityResultContracts)
  - Android string resources: grep all *.xml and *.kt before deleting (AAPT2 resolves visibility="gone" refs)
observability_surfaces:
  - Arduino Serial at 9600 baud — "BANKONGSETON RFID reader ready" on startup; "QR: rendering v<N> scale=<N>px url=<url>" on QR; "OLED: init failed 0x3C" on I2C fault
  - Flask log grep 'event=qr_generate' — fires on cashier "Pay Now" with UUID and total
  - Flask log grep 'event=qr_confirm' — fires on successful debit with student_id, total, new_balance
  - Flask log grep 'event=qr_offline_queued' — fires when Sheets unavailable; transaction queued
  - GET /api/arduino/qr-pending (X-API-Key) — live QR state ground truth: null = idle/expired
  - bash scripts/verify-m005-s0N.sh — per-slice contract proofs; exit 0 = all checks pass
requirement_outcomes:
  - id: R026
    from_status: active
    to_status: validated
    proof: arduino/bankongseton_r4/bankongseton_r4.ino uses MFRC522 with RC522 SPI read loop; WiFi POST /api/arduino/card-read preserved; verify-m005-s01.sh exits 0 (9/9 checks); bankongseton_rfid/ deleted
  - id: R027
    from_status: active
    to_status: validated
    proof: Adafruit SSD1306 + GFX driver activated in R4 firmware; oledShowReady() shows idle screen; verify-m005-s02.sh exits 0 (9/9 checks); hardware UAT deferred to human tester
  - id: R028
    from_status: active
    to_status: validated
    proof: httpGetBody + parseQrUrl + renderQr + 500ms poll loop in bankongseton_r4.ino; verify-m005-s02.sh check 7 confirms qr-pending polled; OLED renders QR bitmap (hardware UAT deferred)
  - id: R029
    from_status: active
    to_status: validated
    proof: POST /cashier/api/qr-generate, GET /api/arduino/qr-pending, GET /api/qr/<token>, POST /api/qr/confirm all implemented; verify-m005-s03.sh exits 0 (14/14 checks); py_compile exits 0 on web_app.py, api_server.py, cashier_routes.py
  - id: R030
    from_status: active
    to_status: validated
    proof: QRPayActivity.kt with CameraX+ML Kit scanner, cart confirmation, 402/404/410/401 error handling; qrPayButton in HomeActivity; verify-m005-s04.sh exits 0 (12/12 checks)
  - id: R031
    from_status: active
    to_status: validated
    proof: bankongseton_nfc_r3/README.md rewritten with RC522/MFRC522 hardware documentation; grep confirms no PN532 refs in R3 firmware or README; verify-m005-s01.sh check 9 passes
  - id: R032
    from_status: validated
    to_status: validated
    proof: S05 already validated; verify-m005-s05.sh exits 0 (18/18 checks); py_compile exits 0 on all 3 Python files; all 5 Android NFC files absent; NFC manifest entries gone; nfc_cancel preserved
  - id: R033
    from_status: active
    to_status: validated
    proof: QRPayView.swift, QRScannerView.swift (AVFoundation), QRPayViewModel.swift, QRModels.swift; HomeView showQrPay button; project.pbxproj registered; verify-m005-s04.sh iOS section all pass
duration: ~4h (S01: 40m, S02: 35m, S03: 45m, S04: 90m, S05: 40m)
verification_result: passed
completed_at: 2026-03-18
---

# M005: RC522 + OLED + QR Payment

**Replaced PN532+LCD+APDU firmware on R4 with RC522+SSD1306 OLED+QR polling; introduced server-side QR payment backend with retry/rollback/offline-queue; shipped Android and iOS QR scanner + confirmation flows; removed all phone HCE/NFC dead code — all 5 verify scripts exit 0, 53 contract checks pass, py_compile clean.**

## What Happened

M005 retired the PN532-based NFC/APDU payment approach (proven unreliable across M003/M004) in favour of a clean RC522 RFID tap plus QR code payment that works on both Android and iOS. Five slices delivered the transformation in sequence.

**S01 (RC522 Firmware Swap)** replaced the R4's PN532+LCD+APDU firmware with a clean MFRC522 read loop preserving all WiFi/heartbeat behaviour. The `arduino/bankongseton_rfid/` directory was renamed to `arduino/bankongseton_r4/` and the firmware stripped of ~180 lines of inline bit-bang LCD driver, PN532 APDU exchange, and SAMConfig/setRFField calls. RC522 SPI init uses the VersionReg halt-check pattern, PICC_HaltA+PCD_StopCrypto1 called after every read. OLED_ADDR/OLED_WIDTH/OLED_HEIGHT constants and Wire.begin() were committed as S02 placeholders with a `// TODO S02` marker. R3 README was rewritten to accurately document RC522/MFRC522 hardware.

**S02 (OLED Driver + QR Polling)** activated the Adafruit SSD1306 OLED and added the 500ms `/api/arduino/qr-pending` poll loop. Four new functions were inserted at the S02 TODO marker: `oledShowReady()`, `renderQr(url)` (version probe 1–7, 2px/module auto-scale, single `display.display()` flush), `httpGetBody(path)` (header-skip loop), and `parseQrUrl(json)`. The poll loop runs in both the main `loop()` and in the post-scan cooldown while-loop (using `now2` to avoid shadowing the outer `now`). QR poll guard (`qrUrl != lastQrUrl`) prevents OLED flicker on unchanged state. OLED init is non-fatal: RFID payment continues if the display is absent.

**S03 (Backend QR Payment Flow)** built the four server-side endpoints in three tasks. T01 added `app.pending_qr_token = None` to `web_app.py`, `_decode_student_jwt()` helper, `GET /api/arduino/qr-pending` (X-API-Key auth), `GET /api/qr/<token>` (student JWT), and `jwt_token` field in the api_server.py login response. T02 added `POST /cashier/api/qr-generate` (reads `SERVER_URL`, UUID token, stores full cart snapshot in `current_app.pending_qr_token`) and `POST /api/qr/confirm` (3-retry exponential backoff, rollback on failure, offline-queue fallback, emits `qr_payment` SocketIO event before clearing token, 402 for insufficient funds, "QR Purchase" transaction type). T03 added the cashier `socket.on('qr_payment', ...)` handler, `SERVER_URL` to `.env.example` and `docs/DEPLOY.md`.

**S04 (Android + iOS App QR Pay)** delivered the student-facing QR payment interfaces in four tasks. T01 wired `jwt_token` storage to both Android (EncryptedSharedPreferences via `SecureStorage`) and iOS (Keychain via `KeychainHelper`), added `getQrCart`/`confirmQrPayment` API methods, and added CameraX 1.3.1 + ML Kit barcode-scanning 17.2.0 to Android's build.gradle.kts. T02 built `QRPayActivity.kt` — full CameraX+ML Kit scanning, cart confirmation panel, `substringAfterLast('/')` token extraction, 402/404/410/401 error dialogs, `RESULT_OK` balance refresh — and wired an always-visible "Scan QR" button in HomeActivity replacing the hidden NFC button. T03 built `QRModels.swift`, `QRPayViewModel.swift` (QRPayState enum, handleScannedURL/confirm async methods), `QRScannerView.swift` (UIViewControllerRepresentable + AVCaptureMetadataOutput), `QRPayView.swift` (SwiftUI state machine: scanning→loading→confirming→success/error), "Pay with QR" button in HomeView, and registered all files in `project.pbxproj` with camera usage description in both Debug and Release target build configs. T04 wrote `scripts/verify-m005-s04.sh` (12 checks, exits 0).

**S05 (NFC/HCE Cleanup)** deleted all dead NFC/HCE code across three task groups. Python backend: `nfc_payments.py` deleted, four `/api/nfc/*` route functions removed from `api_server.py`, `complete_sale_nfc()` and PhoneUID VirtualCards fallback removed from `cashier_routes.py`, `socket.on('nfc_payment')` and `completeNFCSale()` removed from `cashier_index.html`, full NFC delivery infrastructure (`_QueuedPayment`, retry thread, `_post_nfc_payment`, NFC/ERROR parse branches, `import queue`) removed from `arduino_bridge.py`, `test_arduino_bridge_nfc.py` deleted. Android: 5 NFC/HCE files deleted (BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml), NFC dead code scrubbed from 8 source files; two unplanned files required edits (activity_home.xml had AAPT2-breaking `@string/action_nfc_pay` ref; ReceiptActivity.kt referenced deleted `nfc_receipt_label` string). iOS: "nfc purchase"/"nfc" display-label cases in TransactionRowView consolidated with "qr" equivalents.

**Reconciliation fix (milestone close):** The `reassess-roadmap` step after S04 used a fresh worktree initialised from the integration baseline (pre-S01 code state), causing the `milestone/M005` branch to lack all S01-S04 feature code. S05 was then executed on this incomplete base — NFC code was deleted but QR/OLED features were never present in the worktree. The milestone close unit detected the discrepancy, restored all S01-S04 artifacts from the `master` branch (where the per-slice work had been committed), applied S05 NFC edits to the now-complete Android files (HomeActivity.kt NFC function removal; AndroidManifest NFC permission/HCE service removal), and staged the reconciled state. All five verify scripts re-confirmed clean.

## Cross-Slice Verification

**S01:** `bash scripts/verify-m005-s01.sh` → 9/9 PASS. `arduino/bankongseton_r4/` exists; `arduino/bankongseton_rfid/` deleted; MFRC522 in firmware; no PN532/LCD/APDU code; WiFi/heartbeat preserved; OLED placeholder present; RC522 read pattern present; R3 README PN532-free.

**S02:** `bash scripts/verify-m005-s02.sh` → 9/9 PASS. Adafruit_SSD1306.h include; qrcode.h include; display.begin in setup; oledShowReady present; renderQr present; httpGetBody present; qr-pending endpoint polled; parseQrUrl present; TODO S02 removed.

**S03:** `bash scripts/verify-m005-s03.sh` → 14/14 PASS. `py_compile` on api_server.py, web_app.py, cashier_routes.py exits 0. `pending_qr_token` init; `qr-pending` route; `qr-generate` in cashier_routes; `/api/qr/` route; `qr/confirm` route; `qr_payment` socketio.emit; `socket.on(qr_payment)`; `SERVER_URL` consumed; `jwt_token` in login — all confirmed.

**S04:** `bash scripts/verify-m005-s04.sh` → 12/12 PASS. Android: jwtToken in Models.kt; saveJwtToken in SecureStorage; getQrCart+confirmQrPayment in ApiClient; ML Kit barcode-scanning in build.gradle.kts; QRPayActivity in manifest; CAMERA permission. iOS: jwtToken in LoginModels; jwt_token in AuthManager; getQrCart+confirmQrPayment in APIClient; QRPayView/showQrPay in HomeView; AVCaptureMetadataOutput in QRScannerView; AA000026 in project.pbxproj.

**S05:** `bash scripts/verify-m005-s05.sh` → 18/18 PASS. Python: nfc_payments.py absent; `_QueuedPayment` absent; `/api/nfc/` routes absent; `complete_sale_nfc` absent; `completeNFCSale` absent; `socket.on.*nfc_payment` absent. Android: BankoHceService.kt absent; NfcManager.kt absent; NfcPayOverlayActivity.kt absent; NFC manifest entries absent; nfc_cancel preserved; CAMERA present. iOS: QR+NFC display labels consolidated.

**py_compile:** All 4 Python files pass: `backend/api/api_server.py`, `backend/dashboard/web_app.py`, `backend/dashboard/cashier/cashier_routes.py`, `backend/dashboard/arduino_bridge.py`.

**Directory structure:** `arduino/bankongseton_r4/` exists with `bankongseton_r4.ino` and `secrets.h`; `arduino/bankongseton_rfid/` absent.

**NFC dead code grep:** `grep -rn 'nfc_payments|complete_sale_nfc|completeNFCSale|_QueuedPayment' backend/` → 0 lines. `grep -rn 'NfcManager|BankoHceService|activateNfcPayButton' mobile/student_app_v2/app/src/main/` → 0 lines.

**Hardware UAT deferred:** Physical RFID card tap at R4 + Flask log `POST /api/arduino/card-read 200`, and QR scan on real phone + Sheets balance debit, are human-verified steps. All contract verification passed; integration and operational verification require hardware.

## Requirement Changes

- R026 (RC522 RFID on R4): active → validated — verify-m005-s01.sh 9/9; MFRC522 firmware present; WiFi path preserved; bankongseton_rfid/ deleted
- R027 (OLED Replaces LCD on R4): active → validated — verify-m005-s02.sh 9/9; Adafruit SSD1306 driver + renderQr + oledShowReady in firmware
- R028 (QR Token Delivery via Arduino Polling): active → validated — verify-m005-s02.sh check 7; httpGetBody + parseQrUrl + renderQr + 500ms poll loop confirmed
- R029 (Backend QR Payment Flow): active → validated — verify-m005-s03.sh 14/14; py_compile exits 0; all 4 QR endpoints implemented
- R030 (Android QR Scanner): active → validated — verify-m005-s04.sh Android section 6/6; QRPayActivity, CAMERA, JWT, API methods all confirmed
- R031 (RC522 on R3, cleanup): active → validated — verify-m005-s01.sh check 9; R3 README+firmware PN532-free
- R032 (Dead NFC/HCE Code Removed): validated (already) — verify-m005-s05.sh 18/18; status unchanged
- R033 (iOS QR Scanner): active → validated — verify-m005-s04.sh iOS section 6/6; QRPayView, QRScannerView, pbxproj registration, camera usage description all confirmed

## Forward Intelligence

### What the next milestone should know

- **QR URL format is `https://<SERVER_URL>/api/qr/<token>`** — token is a UUID (36 chars). V7 ECC-L cap is 154 chars; a typical PythonAnywhere hostname produces ~82-char URLs. No headroom concern for normal deployments.
- **`app.pending_qr_token` is in-memory Flask state** — resets on process restart. Single-worker PythonAnywhere deployment is the only reason this is safe. Multi-worker or multi-process deployment requires Redis or DB-backed token storage. Documented in `.env.example` and `docs/DEPLOY.md`.
- **`nfc_cancel` string in Android strings.xml deliberately preserved** — referenced by `activity_qr_pay.xml` from S04. Do not delete in any future cleanup pass.
- **`"nfc"` historical-type filter references preserved** in `HomeActivity.kt` (transaction-filter logic, 3 refs) and `TransactionRowView.swift` (amount sign/color for historical records). These are not dead code — they ensure pre-M005 NFC transaction history rows render correctly without a data migration.
- **ArduinoBridge startup strings must not change:** R4 sends "BANKONGSETON RFID reader ready"; R3 sends "BANKONGSETON NFC reader ready". ArduinoBridge uses these to confirm boot.
- **jwt_token is distinct from auth_token** in both apps. `auth_token` authenticates student-facing API calls to `api_server.py`. `jwt_token` authenticates QR payment calls to `web_app.py` routes (`/api/qr/*`). Both are stored separately and cleared together on logout.
- **OLED I2C address is 0x3C** (OLED_ADDR hardcoded). Some SSD1306 breakouts use 0x3D. Non-fatal init means RFID still works if the address is wrong, but OLED will be blank.
- **Arduino QR library is ricmoo/qrcode v0.0.1** — `qrcode_initText` returns bool. Version probe loop 1–7; first success wins. V7 ECC-L max 154 chars. If the library is updated with a different API, the probe loop will malfunction.

### What's fragile

- **`app.pending_qr_token` single global** — a second cashier hitting "Pay Now" silently overwrites the first token. The second cashier's OLED will show the correct QR but the first cashier's OLED will start rendering the second cashier's QR. Acceptable for single-cashier-per-terminal school deployment; needs per-cashier scoping for multi-station.
- **RC522 VersionReg halt-check is strict** — wiring error produces a completely silent board from the Python side (ArduinoBridge never sees the ready string, times out). Check Arduino Serial Monitor at 9600 baud first if board appears unresponsive.
- **QR scale at 2px/module** — produces a scannable but small bitmap. Hardware UAT must confirm scanability at the actual phone-to-OLED distance in a real canteen environment.
- **Non-fatal FCM on QR confirm** — push failure is silently swallowed (same pattern as `complete_sale()`). Student app must poll for balance updates if a push is missed.

### Authoritative diagnostics

- **`bash scripts/verify-m005-s0N.sh`** (1–5) — fastest regression check for each slice's contract; identifies exact failing artifact by name
- **`python -m py_compile backend/api/api_server.py`** etc. — immediate syntax proof after any Python edit
- **Arduino Serial Monitor at 9600 baud** — `BANKONGSETON RFID reader ready` = RC522+WiFi init OK; `QR: rendering v<N>` = poll hit live token; `OLED: init failed` = I2C address or wiring fault
- **`GET /api/arduino/qr-pending`** (X-API-Key) — ground truth for pending token state; null = idle/expired; non-null = active token
- **Flask log `grep 'event=qr_confirm'`** — debit confirmation with student_id, total, new_balance

### What assumptions changed

- **M005 assumed S01-S04 code would be present in the milestone/M005 worktree when S05 ran.** In practice, the GSD `reassess-roadmap` step after S04 initialised a fresh worktree from the integration baseline (master pre-S01), losing all S01-S04 feature code. S05 deleted NFC code from this incomplete baseline, producing a worktree that had NFC removed but QR/OLED never added. The milestone close unit detected and corrected this by restoring S01-S04 artifacts from master and re-applying S05's NFC edits to the now-complete files.
- **R3 firmware assumed to carry PN532 dead code** — actual R3 firmware already used MFRC522; only the README required updating. No .ino changes needed for R3.
- **QR bitmap at 5px/module was considered** in the roadmap risk section. Actual implementation chose 2px/module with 1px fallback — sufficient for the URL length and OLED dimensions. Hardware UAT determines real-world scanability at canteen distances.

## Files Created/Modified

- `arduino/bankongseton_r4/bankongseton_r4.ino` — new MFRC522+OLED+QR firmware (S01/S02)
- `arduino/bankongseton_r4/secrets.h` — verbatim copy of old bankongseton_rfid/secrets.h
- `arduino/bankongseton_rfid/` — **deleted** (S01)
- `arduino/bankongseton_nfc_r3/README.md` — rewritten (S01)
- `backend/dashboard/web_app.py` — app.pending_qr_token; QR endpoints; import jwt as _pyjwt; import json (S03)
- `backend/api/api_server.py` — jwt_token in login; /api/nfc/* deleted (S03/S05)
- `backend/dashboard/cashier/cashier_routes.py` — POST /cashier/api/qr-generate; complete_sale_nfc deleted (S03/S05)
- `backend/dashboard/cashier/templates/cashier_index.html` — socket.on('qr_payment'); nfc_payment deleted (S03/S05)
- `backend/dashboard/arduino_bridge.py` — NFC delivery infrastructure deleted (S05)
- `backend/api/wsgi.py` — stale nfc_payments comment removed (S05)
- `backend/nfc_payments.py` — **deleted** (S05)
- `backend/tests/test_arduino_bridge_nfc.py` — **deleted** (S05)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — **deleted** (S05)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — **deleted** (S05)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt` — **deleted** (S05)
- `mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml` — **deleted** (S05)
- `mobile/student_app_v2/app/src/main/res/xml/hce_service.xml` — **deleted** (S05)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt` — new (S04)
- `mobile/student_app_v2/app/src/main/res/layout/activity_qr_pay.xml` — new (S04)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — jwtToken + QR models (S04)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SecureStorage.kt` — JWT token methods (S04)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/LoginActivity.kt` — jwt_token save on login (S04)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — getQrCart/confirmQrPayment; NFC API methods removed (S04/S05)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — qrPayButton/qrPayLauncher; NFC HCE dead code removed (S04/S05)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt` — nfc_receipt_label replaced with "Payment" (S05)
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — CAMERA + QRPayActivity; NFC permission/HCE service deleted (S04/S05)
- `mobile/student_app_v2/app/src/main/res/layout/activity_home.xml` — qrPayButton; activateNfcPayButton deleted (S04/S05)
- `mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml` — nfcSection deleted (S05)
- `mobile/student_app_v2/app/src/main/res/values/strings.xml` — QR strings added; NFC strings deleted; nfc_cancel preserved (S04/S05)
- `mobile/student_app_v2/app/build.gradle.kts` — CameraX 1.3.1 + ML Kit barcode-scanning 17.2.0 (S04)
- `mobile/ios/BankongSetonStudent/Models/QRModels.swift` — new (S04)
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — new (S04)
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — new (S04)
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` — new (S04)
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — "Pay with QR" button (S04)
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — QR files registered; camera usage description (S04)
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift` — jwt_token storage (S04)
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — jwtRequest(); getQrCart/confirmQrPayment (S04)
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` — qrCart/qrConfirm endpoints (S04)
- `mobile/ios/BankongSetonStudent/Models/LoginModels.swift` — jwtToken in LoginResponse (S04)
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift` — jwt_token passed to AuthManager (S04)
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — NFC display labels consolidated with QR (S05)
- `scripts/verify-m005-s01.sh` through `scripts/verify-m005-s05.sh` — contract verification scripts (S01–S05)
- `.env.example` — SERVER_URL in QR Payment section (S03)
- `docs/DEPLOY.md` — SERVER_URL row in deploy env vars table (S03)
- `.gsd/KNOWLEDGE.md` — Android string resource grep rule; dead import cleanup rule (S05)
