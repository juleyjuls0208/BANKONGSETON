# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R026 — Arduino UNO R4 WiFi uses RC522 RFID module instead of PN532; physical RFID card tap POSTs to /api/arduino/card-read over WiFi and fires card_read event in cashier UI; WiFi, heartbeat, and powerbank behaviour unchanged
- Class: primary-user-loop
- Status: active
- Description: Arduino UNO R4 WiFi uses RC522 RFID module instead of PN532; physical RFID card tap POSTs to /api/arduino/card-read over WiFi and fires card_read event in cashier UI; WiFi, heartbeat, and powerbank behaviour unchanged
- Why it matters: PN532 is being retired; RC522 is the unified reader hardware across both Arduinos; all prior phone HCE/NFC complexity disappears
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: none
- Validation: contract verified (scripts/verify-m005-s01.sh exits 0); hardware integration (physical tap → POST 200) pending human verification

### R027 — Arduino UNO R4 WiFi uses a 128×64 SSD1306 OLED (Adafruit SSD1306 + GFX) instead of the 16×2 LCD with PCF8574 I2C backpack; OLED shows status messages at idle and renders QR codes for payment
- Class: primary-user-loop
- Status: active
- Description: Arduino UNO R4 WiFi uses a 128×64 SSD1306 OLED (Adafruit SSD1306 + GFX) instead of the 16×2 LCD with PCF8574 I2C backpack; OLED shows status messages at idle and renders QR codes for payment
- Why it matters: OLED is the display surface for QR payment — the QR bitmap cannot be rendered on a 16×2 character LCD
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: M005/S02
- Validation: Adafruit SSD1306 driver activated in S02; oledShowReady() and renderQr() implemented; all 9 contract checks pass (scripts/verify-m005-s02.sh exits 0); hardware scan UAT pending

### R028 — Arduino R4 polls GET /api/arduino/qr-pending every ~500ms; when a pending QR token exists (set by cashier hitting Pay Now), Arduino renders the encoded URL as a QR bitmap on the OLED; OLED returns to idle when token is cleared
- Class: primary-user-loop
- Status: active
- Description: Arduino R4 polls GET /api/arduino/qr-pending every ~500ms; when a pending QR token exists (set by cashier hitting Pay Now), Arduino renders the encoded URL as a QR bitmap on the OLED; OLED returns to idle when token is cleared
- Why it matters: The OLED must display the QR without a push connection — polling fits the existing heartbeat/WiFi pattern already proven in M003
- Source: user
- Primary owning slice: M005/S02
- Supporting slices: none
- Validation: httpGetBody() + parseQrUrl() + renderQr() + 500ms poll loop implemented in firmware; contract verified (scripts/verify-m005-s02.sh exits 0); live integration pending S03 backend

### R029 — POST /cashier/api/qr-generate creates a short-lived token and stores it as the pending QR; GET /api/arduino/qr-pending returns {token, url} when a QR is pending; POST /api/qr/confirm (authenticated by student JWT) resolves the token, debits balance via complete_sale logic, emits cashier socket event, and clears the pending QR
- Class: primary-user-loop
- Status: active
- Description: POST /cashier/api/qr-generate creates a short-lived token and stores it as the pending QR; GET /api/arduino/qr-pending returns {token, url} when a QR is pending; POST /api/qr/confirm (authenticated by student JWT) resolves the token, debits balance via complete_sale logic, emits cashier socket event, and clears the pending QR
- Why it matters: This is the server-side backbone of the QR payment flow — without it neither the OLED nor the apps can complete a sale
- Source: user
- Primary owning slice: M005/S03
- Supporting slices: none
- Validation: contract verified — bash scripts/verify-m005-s03.sh exits 0 (14/14 checks pass); live Sheets debit closure is now traced via S04 evidence artifacts `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.{json,md}` (`qr_confirm` must be `live_success`).

### R030 — Android student app has a "Pay with QR" button on the home screen; tapping opens a camera QR scanner; scanning a valid QR URL fetches the pending cart from the server, shows items and total, student taps Confirm, backend debits balance, app shows receipt
- Class: primary-user-loop
- Status: active
- Description: Android student app has a "Pay with QR" button on the home screen; tapping opens a camera QR scanner; scanning a valid QR URL fetches the pending cart from the server, shows items and total, student taps Confirm, backend debits balance, app shows receipt
- Why it matters: NFC HCE phone payment is being removed; QR is the replacement that works on all Android devices
- Source: user
- Primary owning slice: M005/S04
- Supporting slices: none
- Validation: unmapped

### R031 — Arduino UNO R3 uses RC522 RFID module (already in place per R3 firmware); firmware is cleaned up to remove any PN532/NFC references and restricted to card registration and lost-card replacement role only
- Class: operability
- Status: active
- Description: Arduino UNO R3 uses RC522 RFID module (already in place per R3 firmware); firmware is cleaned up to remove any PN532/NFC references and restricted to card registration and lost-card replacement role only
- Why it matters: R3 already uses MFRC522 but the firmware may carry dead NFC/PN532 references; role clarification ensures R3 never attempts payment flows
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: none
- Validation: contract verified — R3 firmware and README confirmed PN532-free (scripts/verify-m005-s01.sh check [9/9]); no firmware changes needed (was already MFRC522); README updated to document RC522 hardware accurately

### R032 — BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt removed from Android; nfc_payments.py deleted; /api/nfc/register|status|unregister|pay routes removed from api_server.py; complete_sale_nfc and socket.on('nfc_payment') removed from cashier; VirtualCards sheet logic removed; Android and iOS build clean
- Class: operability
- Status: active
- Description: BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt removed from Android; nfc_payments.py deleted; /api/nfc/register|status|unregister|pay routes removed from api_server.py; complete_sale_nfc and socket.on('nfc_payment') removed from cashier; VirtualCards sheet logic removed; Android and iOS build clean
- Why it matters: Dead HCE/NFC code is a maintenance liability and causes confusion about the current payment model
- Source: user
- Primary owning slice: M005/S05
- Supporting slices: none
- Validation: unmapped

### R033 — iOS student app (SwiftUI) has a "Pay with QR" button on the home screen; tapping opens AVFoundation camera QR scanner; scanning fetches cart, shows confirmation view, student taps Confirm, backend debits balance, app shows receipt — identical user experience to Android
- Class: primary-user-loop
- Status: active
- Description: iOS student app (SwiftUI) has a "Pay with QR" button on the home screen; tapping opens AVFoundation camera QR scanner; scanning fetches cart, shows confirmation view, student taps Confirm, backend debits balance, app shows receipt — identical user experience to Android
- Why it matters: iOS app exists but has no payment method; QR is the first payment capability for iOS students
- Source: user
- Primary owning slice: M005/S04
- Supporting slices: none
- Validation: unmapped

### R055 — The iOS app is reworked to closely copy the Stitch reference pack (`C:\Users\admin\Downloads\stitch_redesigned_login`) across in-scope screens: login, home, QR flow states, transactions states, budget, receipt, lost-card, and settings; legacy pre-redesign UI on these surfaces is removed, app launches in dark mode, and login no longer exposes a PIN field
- Class: primary-user-loop
- Status: active
- Description: The iOS app is reworked to closely copy the Stitch reference pack (`C:\Users\admin\Downloads\stitch_redesigned_login`) across in-scope screens: login, home, QR flow states, transactions states, budget, receipt, lost-card, and settings; legacy pre-redesign UI on these surfaces is removed, app launches in dark mode, and login no longer exposes a PIN field
- Why it matters: The school demo needs a premium, cohesive iOS UX instead of mixed legacy layouts
- Source: user
- Primary owning slice: M007/S01
- Supporting slices: M007/S02, M007/S03, M007/S04, M007/S05
- Validation: mapped
- Notes: "copy" intent preserved; visual fidelity plus behavior continuity required; override checkpoint enforces dark-mode-first launch and no-PIN login surface. S09 override contracts pass at source level; physical runtime parity remains pending Apple-host/device execution.

### R056 — Every visible in-scope button, toggle, row, and tab in the redesigned iOS app performs meaningful behavior; dead controls are not allowed in demo scope
- Class: quality-attribute
- Status: active
- Description: Every visible in-scope button, toggle, row, and tab in the redesigned iOS app performs meaningful behavior; dead controls are not allowed in demo scope
- Why it matters: Demo credibility collapses when polished UI contains non-functional controls
- Source: user
- Primary owning slice: M007/S02
- Supporting slices: M007/S03, M007/S04, M007/S05, M007/S07
- Validation: mapped
- Notes: Non-mapped decorative/secondary actions are removed, not stubbed

### R057 — Payment-method selection UI is removed from iOS; QR Pay is the default and only payment path surfaced in redesigned flows
- Class: primary-user-loop
- Status: active
- Description: Payment-method selection UI is removed from iOS; QR Pay is the default and only payment path surfaced in redesigned flows
- Why it matters: Product direction is fixed to QR Pay; payment-method UI introduces unnecessary scope and confusion
- Source: user
- Primary owning slice: M007/S02
- Supporting slices: M007/S05
- Validation: mapped
- Notes: Includes removal of payment-method rows/CTAs in settings/transactions/QR confirm surfaces

### R058 — Redesigned transactions screen provides working search and filter behavior on top of existing paginated history/load-more flow, and the only user-visible filter chips are `QR Pay`, `Card Pay`, and `Load` (legacy `Debit`/`Credit Card` labels removed)
- Class: primary-user-loop
- Status: active
- Description: Redesigned transactions screen provides working search and filter behavior on top of existing paginated history/load-more flow, and the only user-visible filter chips are `QR Pay`, `Card Pay`, and `Load` (legacy `Debit`/`Credit Card` labels removed)
- Why it matters: Existing iOS transactions flow lacks search/filter and currently exposes wrong payment taxonomy (`Debit`/`Credit Card`) versus the required `QR Pay`/`Card Pay`/`Load` demo language
- Source: user
- Primary owning slice: M007/S03
- Supporting slices: M007/S07
- Validation: mapped
- Notes: Supersedes prior iOS filter taxonomy for M007 acceptance; `Debit`/`Credit Card` labels are treated as regression markers. S09 override contracts verify the new taxonomy in source/runtime-contract checks; full device UAT sign-off remains pending.

### R059 — Redesign includes realistic loading, empty, error, and success states for transaction and QR flows (not only happy-path static screens)
- Class: failure-visibility
- Status: active
- Description: Redesign includes realistic loading, empty, error, and success states for transaction and QR flows (not only happy-path static screens)
- Why it matters: Demo quality depends on resilient behavior under non-happy-path runtime conditions
- Source: user
- Primary owning slice: M007/S03
- Supporting slices: M007/S02, M007/S07
- Validation: mapped

### R060 — Accent color preference and personal info edit experience persist locally on-device without backend writes
- Class: continuity
- Status: active
- Description: Accent color preference and personal info edit experience persist locally on-device without backend writes
- Why it matters: These settings are needed for interaction depth in demo but do not need server complexity
- Source: user
- Primary owning slice: M007/S05
- Supporting slices: M007/S07
- Validation: mapped
- Notes: User explicitly rejected database persistence for personal info in this milestone

### R061 — Out-of-scope stitch extras are removed from app flows (not shown as placeholders), including receipt PDF/report actions and non-scope settings categories
- Class: constraint
- Status: active
- Description: Out-of-scope stitch extras are removed from app flows (not shown as placeholders), including receipt PDF/report actions and non-scope settings categories
- Why it matters: Prevents accidental expansion and avoids fake behavior during all-audience demo
- Source: user
- Primary owning slice: M007/S05
- Supporting slices: M007/S04, M007/S07
- Validation: mapped

### R062 — Motion and transitions feel premium but restrained; interactions must avoid "too fancy/slow" behavior on iOS 17+ devices
- Class: quality-attribute
- Status: active
- Description: Motion and transitions feel premium but restrained; interactions must avoid "too fancy/slow" behavior on iOS 17+ devices
- Why it matters: User called out speed/feel as a top acceptance condition for school demo quality
- Source: user
- Primary owning slice: M007/S06
- Supporting slices: M007/S07
- Validation: mapped

### R068 — iOS surfaces are restored to the pre-M007 interaction baseline (commit `558d8bc`) before applying M008 upgrades.
- Class: primary-user-loop
- Status: active
- Description: iOS surfaces are restored to the pre-M007 interaction baseline (commit `558d8bc`) before applying M008 upgrades.
- Why it matters: The current iOS direction is explicitly rejected as messy and laggy; rollback is required to recover trust and speed.
- Source: user
- Primary owning slice: M008-l1ngya/S02
- Supporting slices: M008-l1ngya/S03, M008-l1ngya/S04, M008-l1ngya/S05
- Validation: mapped
- Notes: Baseline restoration is structural, not partial visual tweaking.

### R069 — The custom floating tab shell is replaced with native iOS TabView chrome.
- Class: quality-attribute
- Status: active
- Description: The custom floating tab shell is replaced with native iOS TabView chrome.
- Why it matters: Native tab chrome reduces visual heaviness and interaction lag risk in a speed-first minimalist direction.
- Source: user
- Primary owning slice: M008-l1ngya/S02
- Supporting slices: M008-l1ngya/S05
- Validation: mapped
- Notes: Approved as explicit UX change proposal during M008 discussion.

### R070 — Home screen presents student name and current balance in a minimalist credit-card style hero.
- Class: primary-user-loop
- Status: active
- Description: Home screen presents student name and current balance in a minimalist credit-card style hero.
- Why it matters: This is the primary visual anchor requested for the refreshed UX.
- Source: user
- Primary owning slice: M008-l1ngya/S03
- Supporting slices: M008-l1ngya/S05
- Validation: mapped
- Notes: Must preserve readable hierarchy and fast feel.

### R071 — Transactions supports filter chips while removing the search bar entirely.
- Class: primary-user-loop
- Status: active
- Description: Transactions supports filter chips while removing the search bar entirely.
- Why it matters: User requested filtering capability but explicitly does not want search UI.
- Source: user
- Primary owning slice: M008-l1ngya/S04
- Supporting slices: M008-l1ngya/S05
- Validation: mapped
- Notes: Filter taxonomy remains `QR Pay` / `Card Pay` / `Load`.

### R072 — Settings provides appearance controls for theme mode and accent color only.
- Class: continuity
- Status: active
- Description: Settings provides appearance controls for theme mode and accent color only.
- Why it matters: User wants appearance customization without expanding Settings complexity.
- Source: user
- Primary owning slice: M008-l1ngya/S04
- Supporting slices: M008-l1ngya/S05
- Validation: mapped
- Notes: Reduced-motion control is explicitly deferred.

### R075 — M008 closes only after user-performed manual device verification and explicit PASS/FAIL call.
- Class: launchability
- Status: active
- Description: M008 closes only after user-performed manual device verification and explicit PASS/FAIL call.
- Why it matters: Host environment is Windows, so final UX acceptance must be grounded in real-device checks.
- Source: user
- Primary owning slice: M008-l1ngya/S06
- Supporting slices: M008-l1ngya/S03, M008-l1ngya/S04, M008-l1ngya/S05
- Validation: mapped
- Notes: User is the acceptance authority for pass/fail at milestone close.

### R076 — UX rollback and minimalism changes must not break existing QR payment flow continuity.
- Class: constraint
- Status: active
- Description: UX rollback and minimalism changes must not break existing QR payment flow continuity.
- Why it matters: Payment loop remains core product value and cannot regress while visual direction changes.
- Source: inferred
- Primary owning slice: M008-l1ngya/S03
- Supporting slices: M008-l1ngya/S02, M008-l1ngya/S06
- Validation: mapped
- Notes: Home → QR → post-success continuity must remain intact.

## Validated

### R001 — Admin can view fraud alerts generated by FraudDetector, resolve them, and manually suspend/unsuspend cards from the admin dashboard
- Class: failure-visibility
- Status: validated
- Description: Admin can view fraud alerts generated by FraudDetector, resolve them, and manually suspend/unsuspend cards from the admin dashboard
- Why it matters: The fraud engine ran but was invisible — admins had no way to act on alerts without direct database access
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: validated
- Notes: All 6 API endpoints and admin dashboard panel verified. 33-test suite in tests/test_fraud_api.py.

### R002 — Admin can manually suspend and unsuspend a money card from the dashboard UI
- Class: admin/support
- Status: validated
- Description: Admin can manually suspend and unsuspend a money card from the dashboard UI
- Why it matters: Cards could only be auto-suspended by the fraud engine; admin had no manual override
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: validated
- Notes: POST /api/fraud/cards/<uid>/suspend and /unsuspend verified; admin_only decorator confirmed.

### R003 — Admin can filter the transactions page by date range, student ID/name, and transaction type
- Class: operability
- Status: validated
- Description: Admin can filter the transactions page by date range, student ID/name, and transaction type
- Why it matters: All transactions loaded in a flat list with no filter; unusable at scale
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: validated
- Notes: GET /api/transactions/filtered verified; filter bar wired in transactions.html.

### R004 — Parents receive SMS for purchases, loads, and low-balance events if TWILIO_* env vars are configured
- Class: integration
- Status: validated
- Description: Parents receive SMS for purchases, loads, and low-balance events if TWILIO_* env vars are configured
- Why it matters: Philippine parents often have unreliable internet; SMS is more reliable than email
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: validated
- Notes: Three NFC SMS bugs fixed; twilio added to requirements_api.txt.

### R005 — Admin can create, list, update, and deactivate cashier accounts; cashier login uses dynamic credentials stored in Google Sheets
- Class: admin/support
- Status: validated
- Description: Admin can create, list, update, and deactivate cashier accounts; cashier login uses dynamic credentials stored in Google Sheets
- Why it matters: Hardcoded cashier/cashier123 is a security risk; multi-station deployment needs named accounts
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated
- Notes: _ensure_cashier_accounts_sheet() auto-creates with seeded default; full CRUD API live.

### R006 — Admin can void a transaction with a reason; the student's balance is restored and a void record is appended to the Transactions Log
- Class: admin/support
- Status: validated
- Description: Admin can void a transaction with a reason; the student's balance is restored and a void record is appended to the Transactions Log
- Why it matters: No way to correct erroneous transactions; balance errors accumulate over time
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated

### R007 — Cashier continues processing sales during a Google Sheets outage; transactions queue to SQLite and sync automatically on reconnect
- Class: continuity
- Status: validated
- Description: Cashier continues processing sales during a Google Sheets outage; transactions queue to SQLite and sync automatically on reconnect
- Why it matters: Sheets outages would halt all sales; cash fallback is disruptive in a cashless canteen
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: validated

### R008 — Cashier can tap Quick Pay on any product to skip the cart and scan a card immediately for a single-item sale
- Class: primary-user-loop
- Status: validated
- Description: Cashier can tap Quick Pay on any product to skip the cart and scan a card immediately for a single-item sale
- Why it matters: Cart-based flow is too slow for high-volume lunch rush with common single-item purchases
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: validated

### R009 — Every purchase and load triggers an FCM push to the student's device; card replacement triggers a push notifying the student
- Class: integration
- Status: validated
- Description: Every purchase and load triggers an FCM push to the student's device; card replacement triggers a push notifying the student
- Why it matters: Students and parents only knew about transactions via delayed email; real-time awareness was missing
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated

### R010 — Student can filter transaction history by type and date in the Android app
- Class: primary-user-loop
- Status: validated
- Description: Student can filter transaction history by type and date in the Android app
- Why it matters: Flat transaction list is unusable for students tracking spending
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated

### R011 — Student's monthly budget auto-resets on the 1st of each month with a re-prompt in the Android app
- Class: primary-user-loop
- Status: validated
- Description: Student's monthly budget auto-resets on the 1st of each month with a re-prompt in the Android app
- Why it matters: Monthly budget was a one-time setup; students had no way to reset for a new month
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated

### R012 — Student sees real-time lost card status in-app; receives FCM push when admin processes the replacement
- Class: primary-user-loop
- Status: validated
- Description: Student sees real-time lost card status in-app; receives FCM push when admin processes the replacement
- Why it matters: Students had no visibility into whether their lost card report was being processed
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated

### R013 — Backend scheduler runs a daily job emailing parents of all students below LOW_BALANCE_THRESHOLD; admin can trigger manually
- Class: integration
- Status: validated
- Description: Backend scheduler runs a daily job emailing parents of all students below LOW_BALANCE_THRESHOLD; admin can trigger manually
- Why it matters: Parents had no proactive notification of low balances until a purchase was rejected
- Source: user
- Primary owning slice: M001/S06
- Supporting slices: none
- Validation: validated

### R014 — Both Flask apps install cleanly from their requirements files on a fresh virtualenv with no missing packages and no file errors
- Class: operability
- Status: validated
- Description: Both Flask apps install cleanly from their requirements files on a fresh virtualenv with no missing packages and no file errors
- Why it matters: The api requirements file was missing gspread, firebase-admin, twilio, and bcrypt
- Source: execution
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: validated

### R015 — Hot Sheets-reading endpoints serve from cache on repeated requests; mutations invalidate the relevant cache keys
- Class: quality-attribute
- Status: validated
- Description: Hot Sheets-reading endpoints serve from cache on repeated requests; mutations invalidate the relevant cache keys
- Why it matters: Sheets quota (60 req/min) will be hit during lunch rush
- Source: execution
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: validated

### R016 — Admin server refuses to start if gunicorn workers > 1 with a clear human-readable error
- Class: failure-visibility
- Status: validated
- Description: Admin server refuses to start if gunicorn workers > 1 with a clear human-readable error
- Why it matters: Module-level bool causes split-brain alert state silently with multiple workers
- Source: execution
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: validated

### R017 — ~35 unit tests cover complete_sale, load_balance, void_transaction, and cashier login auth with mocked Sheets client
- Class: quality-attribute
- Status: validated
- Description: ~35 unit tests cover complete_sale, load_balance, void_transaction, and cashier login auth with mocked Sheets client
- Why it matters: Money-moving code was 0% unit-tested
- Source: execution
- Primary owning slice: M002/S04
- Supporting slices: none
- Validation: validated

### R018 — Both app health endpoints return structured JSON with sheets_ok, latency_ms, and queue_pending fields; both return 503 when Sheets is unreachable
- Class: failure-visibility
- Status: validated
- Description: Both app health endpoints return structured JSON with sheets_ok, latency_ms, and queue_pending fields; both return 503 when Sheets is unreachable
- Why it matters: api_server.py health check returned {"status": "ok"} unconditionally
- Source: execution
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: validated

### R019 — docs/DEPLOY.md covers PythonAnywhere setup, required env vars, Sheets service account config, first-run migration steps, health check sequence, and known operational constraints
- Class: operability
- Status: validated
- Description: docs/DEPLOY.md covers PythonAnywhere setup, required env vars, Sheets service account config, first-run migration steps, health check sequence, and known operational constraints
- Why it matters: No runbook existed
- Source: execution
- Primary owning slice: M002/S05
- Supporting slices: none
- Validation: validated

### R020 — Arduino WiFi path routes physical card UIDs to /api/arduino/card-read and NFC phone tokens to /api/nfc/tap correctly
- Class: primary-user-loop
- Status: validated
- Description: Arduino WiFi path routes physical card UIDs to /api/arduino/card-read and NFC phone tokens to /api/nfc/tap correctly
- Why it matters: Firmware sent all WiFi POSTs to /api/nfc/tap; physical card taps silently failed without serial fallback
- Source: execution
- Primary owning slice: M003/S01
- Supporting slices: none
- Validation: validated

### R021 — Student can tap an Android HCE phone at the cashier to complete a payment
- Class: primary-user-loop
- Status: validated
- Description: Student can tap an Android HCE phone at the cashier to complete a payment
- Why it matters: nfc_payment socket event was emitted but unhandled in cashier UI
- Source: user
- Primary owning slice: M003/S02
- Supporting slices: none
- Validation: validated
- Notes: Superseded by R029/R030/R033 in M005 — QR payment replaces phone NFC entirely

### R022 — Cashier UI shows a WiFi status badge (green/red); Pay Now enables when Arduino is WiFi-connected even without a COM port selected
- Class: operability
- Status: validated
- Description: Cashier UI shows a WiFi status badge (green/red); Pay Now enables when Arduino is WiFi-connected even without a COM port selected
- Why it matters: arduinoConnected only went true via COM port selector; powerbank Arduino had checkout button permanently disabled
- Source: user
- Primary owning slice: M003/S03
- Supporting slices: none
- Validation: validated

### R023 — Arduino UNO R4 WiFi runs reliably for a full school day on a USB powerbank without auto-shutoff; WiFi reconnects automatically if the connection drops
- Class: continuity
- Status: validated
- Description: Arduino UNO R4 WiFi runs reliably for a full school day on a USB powerbank without auto-shutoff; WiFi reconnects automatically if the connection drops
- Why it matters: Many powerbanks cut power when current drops below ~100mA
- Source: user
- Primary owning slice: M003/S04
- Supporting slices: none
- Validation: validated

### R024 — arduino/README-wireless.md documents the complete standalone powerbank setup
- Class: operability
- Status: validated
- Description: arduino/README-wireless.md documents the complete standalone powerbank setup
- Why it matters: Without docs, whoever sets up the cashier counter has no guide for WiFi-only configuration
- Source: user
- Primary owning slice: M003/S04
- Supporting slices: none
- Validation: validated

### R025 — Arduino firmware retries the inDataExchange APDU call up to 3 times with 150ms between attempts
- Class: primary-user-loop
- Status: validated
- Description: Arduino firmware retries the inDataExchange APDU call up to 3 times with 150ms between attempts
- Why it matters: Single APDU attempt timed out on real phones causing 100% NFC payment failure
- Source: execution
- Primary owning slice: M004/S01
- Supporting slices: M004/S02
- Validation: validated
- Notes: Superseded by R026 in M005 — PN532 removed entirely, RC522 replaces it

### R053 — A standalone Flask app on port 5010 serves a cashier-only POS interface — login, product grid, order panel, and all three payment methods — without requiring the admin dashboard to be running
- Class: primary-user-loop
- Status: validated
- Description: A standalone Flask app on port 5010 serves a cashier-only POS interface — login, product grid, order panel, and all three payment methods — without requiring the admin dashboard to be running
- Why it matters: Cashiers need a dedicated URL with no admin clutter; process isolation means the cashier station can operate independently
- Source: user
- Primary owning slice: M006/S01
- Supporting slices: M006/S02, M006/S03, M006/S04, M006/S05
- Validation: validated via S05 final gate — `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` reports `overall.live_ready=true` with required flows (`products_live_data`, `arduino_heartbeat`, `card_read_sale_completion`, `student_qr_confirm`, `nfc_compatible_completion`) all `live_success` on `http://127.0.0.1:5010` and no `:5003` request-trace hits; closure narrative recorded in `.gsd/milestones/M006/M006-SUMMARY.md`
- Notes: S04 verifier artifacts (`.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.{json,md}`) remain prerequisite evidence, while S05 bundle artifacts (`.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.{json,md}`) are the closure gate outputs; evidence remains redacted (no raw JWT/API keys/full UID/unredacted student IDs).

### R054 — The cashier POS screen has a modern food-POS aesthetic: white background, left category sidebar with icons, center product grid with color-coded cards, right order panel, and a prominent coral Charge button
- Class: primary-user-loop
- Status: validated
- Description: The cashier POS screen has a modern food-POS aesthetic: white background, left category sidebar with icons, center product grid with color-coded cards, right order panel, and a prominent coral Charge button
- Why it matters: The current UI is generic and utilitarian; cashiers spend hours on it — a clean purpose-built interface reduces errors and fatigue
- Source: user
- Primary owning slice: M006/S02
- Supporting slices: none
- Validation: validated in M006/S02 runtime UAT (login to standalone POS, dynamic category sidebar, color-coded cards, interactive order panel, and Charge button total updates verified)
- Notes: Reference images provided; color-coded by category, no product photos needed; live Sheets was unavailable in this environment, so happy-path rendering was verified with mocked `/api/products` while real 500 failure visibility was also verified

### R063 — The final redesigned iOS build is ready for manual install and pass/fail acceptance by the user on a physical iOS 17+ phone across full app journey, including override checkpoints (dark-mode default launch, no-PIN login, and transactions filters `QR Pay`/`Card Pay`/`Load`)
- Class: launchability
- Status: validated
- Description: The final redesigned iOS build is ready for manual install and pass/fail acceptance by the user on a physical iOS 17+ phone across full app journey, including override checkpoints (dark-mode default launch, no-PIN login, and transactions filters `QR Pay`/`Card Pay`/`Load`)
- Why it matters: Final acceptance is human on-device, not simulator-only
- Source: user
- Primary owning slice: M007/S07
- Supporting slices: M007/S02, M007/S03, M007/S04, M007/S05, M007/S06
- Validation: validated
- Notes: Local Windows runtime proof remains fail at `apple_tooling` (`xcodebuild`/`xcrun` unavailable), but user-confirmed Apple-host physical-device execution completed and S09 UAT verdict is PASS.

### R073 — Budget limit and spend segments load from a stable backend contract backed by a dedicated `Student Budgets` sheet.
- Class: integration
- Status: validated
- Description: Budget limit and spend segments load from a stable backend contract backed by a dedicated `Student Budgets` sheet.
- Why it matters: Current iOS budget segments fail to load; reliability must be repaired at API/data boundary, not only in UI.
- Source: user
- Primary owning slice: M008-l1ngya/S01
- Supporting slices: M008-l1ngya/S05
- Validation: Validated in M008-l1ngya/S01 via backend+iOS contract proof: `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`, and phased verifier `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` (all phases passed).
- Notes: `/api/student/budget` GET/POST now persists month-scoped limits in dedicated `Student Budgets` sheet with upsert semantics; `/api/budget-summary` returns PH-month `monthly_spend` from `Transactions Log` with malformed-row skip+warn behavior.

### R074 — Budget load/save failures are surfaced with clear retryable UX and non-silent diagnostics.
- Class: failure-visibility
- Status: validated
- Description: Budget load/save failures are surfaced with clear retryable UX and non-silent diagnostics.
- Why it matters: Silent or stale fallbacks hide breakage and create false confidence during demo use.
- Source: inferred
- Primary owning slice: M008-l1ngya/S01
- Supporting slices: M008-l1ngya/S05
- Validation: Validated in M008-l1ngya/S01 via retry-visibility regressions and contract checks: `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"`, and `scripts/verify-m008-s01.sh` retry/static phases (pass via Git Bash invocation).
- Notes: Budget load/save failure channels remain explicit on iOS (`loadErrorMessage`, `saveErrorMessage`, retry actions/buttons) and backend returns explicit 401/404/503/500 envelopes instead of silent fallback.

## Deferred

### R064 — Personal info edit updates server-side student profile records
- Class: admin/support
- Status: deferred
- Description: Personal info edit updates server-side student profile records
- Why it matters: Useful for long-term account consistency, but unnecessary for current school demo scope
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred per explicit user instruction to keep personal info edit local-only

### R077 — Add an explicit in-app reduced-motion toggle in Settings.
- Class: quality-attribute
- Status: deferred
- Description: Add an explicit in-app reduced-motion toggle in Settings.
- Why it matters: Could improve accessibility control later, but user intentionally scoped appearance to theme + accent only for M008.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred by explicit scope choice during M008 planning.

## Out of Scope

### R050 — Parents top up student balances directly via GCash or Maya payment gateway
- Class: integration
- Status: out-of-scope
- Description: Parents top up student balances directly via GCash or Maya payment gateway
- Why it matters: Scope clarification — prevents scope creep toward payment gateway integration
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Requires merchant account setup; out of scope for current school deployment.

### R051 — Building a new iOS app from scratch
- Class: core-capability
- Status: out-of-scope
- Description: Building a new iOS app from scratch
- Why it matters: iOS app already exists at mobile/ios/BankongSetonStudent/ — M005 extends it, does not replace it
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R052 — R3 (registration terminal) displays QR codes for payment
- Class: primary-user-loop
- Status: out-of-scope
- Description: R3 (registration terminal) displays QR codes for payment
- Why it matters: Scope boundary — R3 is registration and lost-card only; all payment flows go through R4
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R065 — Any iOS UI for selecting/changing payment methods
- Class: anti-feature
- Status: out-of-scope
- Description: Any iOS UI for selecting/changing payment methods
- Why it matters: Product direction is QR-only payment for this app and demo; keeping method-switch UI conflicts with the intended flow
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: "default payment will always be QR pay"

### R066 — Receipt actions for downloading PDF or reporting an issue
- Class: constraint
- Status: out-of-scope
- Description: Receipt actions for downloading PDF or reporting an issue
- Why it matters: User explicitly asked to remove these actions from redesigned receipt flow
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R067 — Privacy & Security, Tuition Auto-Pay, and Campus Discounts settings groups from stitch references
- Class: constraint
- Status: out-of-scope
- Description: Privacy & Security, Tuition Auto-Pay, and Campus Discounts settings groups from stitch references
- Why it matters: These are not part of current product scope and would add misleading surface area in demo
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R078 — Search UI on the transactions screen.
- Class: anti-feature
- Status: out-of-scope
- Description: Search UI on the transactions screen.
- Why it matters: User explicitly wants filter-only transactions and no search bar in M008.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: If search returns later, it must be planned as a new requirement.

### R079 — Retaining the custom floating tab shell introduced in the stitch-era rework.
- Class: anti-feature
- Status: out-of-scope
- Description: Retaining the custom floating tab shell introduced in the stitch-era rework.
- Why it matters: User approved replacing it with native TabView as a speed-first UX direction.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R080 — Using stitch-parity as the primary design target for this milestone.
- Class: constraint
- Status: out-of-scope
- Description: Using stitch-parity as the primary design target for this milestone.
- Why it matters: M008 direction is explicit old-UX rollback + minimalist refresh, not stitch continuation.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | failure-visibility | validated | M001/S01 | none | validated |
| R002 | admin/support | validated | M001/S01 | none | validated |
| R003 | operability | validated | M001/S02 | none | validated |
| R004 | integration | validated | M001/S02 | none | validated |
| R005 | admin/support | validated | M001/S03 | none | validated |
| R006 | admin/support | validated | M001/S03 | none | validated |
| R007 | continuity | validated | M001/S04 | none | validated |
| R008 | primary-user-loop | validated | M001/S04 | none | validated |
| R009 | integration | validated | M001/S05 | none | validated |
| R010 | primary-user-loop | validated | M001/S05 | none | validated |
| R011 | primary-user-loop | validated | M001/S05 | none | validated |
| R012 | primary-user-loop | validated | M001/S05 | none | validated |
| R013 | integration | validated | M001/S06 | none | validated |
| R014 | operability | validated | M002/S01 | none | validated |
| R015 | quality-attribute | validated | M002/S02 | none | validated |
| R016 | failure-visibility | validated | M002/S03 | none | validated |
| R017 | quality-attribute | validated | M002/S04 | none | validated |
| R018 | failure-visibility | validated | M002/S03 | none | validated |
| R019 | operability | validated | M002/S05 | none | validated |
| R020 | primary-user-loop | validated | M003/S01 | none | validated |
| R021 | primary-user-loop | validated | M003/S02 | none | validated |
| R022 | operability | validated | M003/S03 | none | validated |
| R023 | continuity | validated | M003/S04 | none | validated |
| R024 | operability | validated | M003/S04 | none | validated |
| R025 | primary-user-loop | validated | M004/S01 | M004/S02 | validated |
| R026 | primary-user-loop | active | M005/S01 | none | contract verified (scripts/verify-m005-s01.sh exits 0); hardware integration (physical tap → POST 200) pending human verification |
| R027 | primary-user-loop | active | M005/S01 | M005/S02 | Adafruit SSD1306 driver activated in S02; oledShowReady() and renderQr() implemented; all 9 contract checks pass (scripts/verify-m005-s02.sh exits 0); hardware scan UAT pending |
| R028 | primary-user-loop | active | M005/S02 | none | httpGetBody() + parseQrUrl() + renderQr() + 500ms poll loop implemented in firmware; contract verified (scripts/verify-m005-s02.sh exits 0); live integration pending S03 backend |
| R029 | primary-user-loop | active | M005/S03 | none | contract verified — bash scripts/verify-m005-s03.sh exits 0 (14/14 checks pass); live Sheets debit closure is now traced via S04 evidence artifacts `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.{json,md}` (`qr_confirm` must be `live_success`). |
| R030 | primary-user-loop | active | M005/S04 | none | unmapped |
| R031 | operability | active | M005/S01 | none | contract verified — R3 firmware and README confirmed PN532-free (scripts/verify-m005-s01.sh check [9/9]); no firmware changes needed (was already MFRC522); README updated to document RC522 hardware accurately |
| R032 | operability | active | M005/S05 | none | unmapped |
| R033 | primary-user-loop | active | M005/S04 | none | unmapped |
| R050 | integration | out-of-scope | none | none | n/a |
| R051 | core-capability | out-of-scope | none | none | n/a |
| R052 | primary-user-loop | out-of-scope | none | none | n/a |
| R053 | primary-user-loop | validated | M006/S01 | M006/S02, M006/S03, M006/S04, M006/S05 | validated via S05 final gate — `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` reports `overall.live_ready=true` with required flows (`products_live_data`, `arduino_heartbeat`, `card_read_sale_completion`, `student_qr_confirm`, `nfc_compatible_completion`) all `live_success` on `http://127.0.0.1:5010` and no `:5003` request-trace hits; closure narrative recorded in `.gsd/milestones/M006/M006-SUMMARY.md` |
| R054 | primary-user-loop | validated | M006/S02 | none | validated in M006/S02 runtime UAT (login to standalone POS, dynamic category sidebar, color-coded cards, interactive order panel, and Charge button total updates verified) |
| R055 | primary-user-loop | active | M007/S01 | M007/S02, M007/S03, M007/S04, M007/S05 | mapped |
| R056 | quality-attribute | active | M007/S02 | M007/S03, M007/S04, M007/S05, M007/S07 | mapped |
| R057 | primary-user-loop | active | M007/S02 | M007/S05 | mapped |
| R058 | primary-user-loop | active | M007/S03 | M007/S07 | mapped |
| R059 | failure-visibility | active | M007/S03 | M007/S02, M007/S07 | mapped |
| R060 | continuity | active | M007/S05 | M007/S07 | mapped |
| R061 | constraint | active | M007/S05 | M007/S04, M007/S07 | mapped |
| R062 | quality-attribute | active | M007/S06 | M007/S07 | mapped |
| R063 | launchability | validated | M007/S07 | M007/S02, M007/S03, M007/S04, M007/S05, M007/S06 | validated |
| R064 | admin/support | deferred | none | none | unmapped |
| R065 | anti-feature | out-of-scope | none | none | n/a |
| R066 | constraint | out-of-scope | none | none | n/a |
| R067 | constraint | out-of-scope | none | none | n/a |
| R068 | primary-user-loop | active | M008-l1ngya/S02 | M008-l1ngya/S03, M008-l1ngya/S04, M008-l1ngya/S05 | mapped |
| R069 | quality-attribute | active | M008-l1ngya/S02 | M008-l1ngya/S05 | mapped |
| R070 | primary-user-loop | active | M008-l1ngya/S03 | M008-l1ngya/S05 | mapped |
| R071 | primary-user-loop | active | M008-l1ngya/S04 | M008-l1ngya/S05 | mapped |
| R072 | continuity | active | M008-l1ngya/S04 | M008-l1ngya/S05 | mapped |
| R073 | integration | validated | M008-l1ngya/S01 | M008-l1ngya/S05 | Validated in M008-l1ngya/S01 via backend+iOS contract proof: `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`, and phased verifier `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh` (all phases passed). |
| R074 | failure-visibility | validated | M008-l1ngya/S01 | M008-l1ngya/S05 | Validated in M008-l1ngya/S01 via retry-visibility regressions and contract checks: `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`, `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"`, and `scripts/verify-m008-s01.sh` retry/static phases (pass via Git Bash invocation). |
| R075 | launchability | active | M008-l1ngya/S06 | M008-l1ngya/S03, M008-l1ngya/S04, M008-l1ngya/S05 | mapped |
| R076 | constraint | active | M008-l1ngya/S03 | M008-l1ngya/S02, M008-l1ngya/S06 | mapped |
| R077 | quality-attribute | deferred | none | none | unmapped |
| R078 | anti-feature | out-of-scope | none | none | n/a |
| R079 | anti-feature | out-of-scope | none | none | n/a |
| R080 | constraint | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 23
- Mapped to slices: 23
- Validated: 30 (R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011, R012, R013, R014, R015, R016, R017, R018, R019, R020, R021, R022, R023, R024, R025, R053, R054, R063, R073, R074)
- Unmapped active requirements: 0
