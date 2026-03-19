---
verdict: needs-attention
remediation_round: 0
---

# Milestone Validation: M005

## Success Criteria Checklist

- [x] **Physical RFID card tapped at powerbank-powered R4 completes a sale end-to-end** — `arduino/bankongseton_r4/bankongseton_r4.ino` confirmed on master branch: MFRC522 read loop, WiFi delivery via `httpPostCard()`, heartbeat preserved, 9/9 S01 verify checks pass. **Attention:** firmware contract proven; physical hardware tap → `POST /api/arduino/card-read 200` in Flask log has not been confirmed by a human operator (S01-SUMMARY "Known Limitations"). This is a UAT step, not a code gap.

- [x] **R4 OLED renders a QR code within ~1s of cashier hitting Pay Now; returns to idle on completion or cancel** — `bankongseton_r4.ino` confirmed on master: Adafruit SSD1306 + qrcode.h included, `renderQr()`, `httpGetBody()`, `parseQrUrl()`, `oledShowReady()` all present, 500ms poll loop in main loop and cooldown loop, 9/9 S02 verify checks pass. **Attention:** hardware OLED QR-scannable confirmation has not been performed (S02-SUMMARY "Known Limitations"). Deferred to human operator.

- [x] **Student scans OLED QR in Android app → sees cart → Confirm → balance debited → cashier success modal** — `QRPayActivity.kt` with CameraX+ML Kit confirmed on master; 12/12 S04 checks pass; S03 backend QR endpoints confirmed on master (14/14 S03 checks pass). **Attention:** live Sheets balance debit with real device has not been confirmed end-to-end. Deferred to human operator.

- [x] **Student scans OLED QR in iOS app → sees cart → Confirm → balance debited → cashier success modal** — `QRPayView.swift`, `QRScannerView.swift` (AVFoundation), `QRPayViewModel.swift` confirmed on master; HomeView "Pay with QR" button present; `project.pbxproj` registered; all 12/12 S04 iOS checks pass. **Attention:** same hardware/e2e caveat as Android above.

- [x] **All HCE/NFC code gone: BankoHceService, NfcManager, NfcPayOverlayActivity, nfc_payments.py, /api/nfc/\* routes, complete_sale_nfc, socket.on('nfc_payment')** — S05 18/18 verify checks pass on milestone/M005 branch: `nfc_payments.py` deleted, four `/api/nfc/*` routes removed, `complete_sale_nfc` gone, `socket.on('nfc_payment')` gone, all 5 Android NFC/HCE files deleted, NFC manifest entries removed, iOS display-label cases consolidated. **Attention:** S05 was applied to the pre-S01-S04 baseline on the milestone/M005 worktree branch; master still carries the old NFC files. When milestone/M005 merges into master, conflicts in ~8 source files will need resolution (NFC deletions from S05 + QR additions from S01–S04 are logically non-overlapping but textually adjacent). Post-merge re-run of `bash scripts/verify-m005-s05.sh` is required.

- [x] **Both apps build without NFC/HCE references; `python -m py_compile` exits 0 on all modified Python files** — `python -m py_compile` exits 0 on `api_server.py`, `web_app.py`, `cashier_routes.py` confirmed against master state. **Attention:** Android Gradle build and iOS `xcodebuild` have not been executed — no build toolchain available in this validation environment. Contract-level checks (manifest/strings/layout integrity) pass.

- [x] **`arduino/bankongseton_r4/` exists; `arduino/bankongseton_rfid/` is gone** — confirmed on master branch: `arduino/bankongseton_r4/bankongseton_r4.ino` exists; `arduino/bankongseton_rfid/` is absent. On the milestone/M005 worktree branch the old directory still exists (S01–S04 commits landed on master, not the milestone branch); the merge will resolve this correctly.

---

## Slice Delivery Audit

| Slice | Claimed | Delivered | Status |
|-------|---------|-----------|--------|
| S01 | RC522 firmware for R4 + secrets.h + R3 README PN532-free + verify script (9 checks, exits 0) | `arduino/bankongseton_r4/bankongseton_r4.ino` + `secrets.h` on master; `bankongseton_rfid/` deleted; R3 README rewritten; `scripts/verify-m005-s01.sh` — 9/9 pass confirmed against master | pass |
| S02 | Adafruit SSD1306 driver + `renderQr()` + `httpGetBody()` + `parseQrUrl()` + 500ms QR poll loop + verify script (9 checks) | All 5 functions present on master; poll in main loop and cooldown loop; TODO S02 comment removed; `scripts/verify-m005-s02.sh` — 9/9 pass confirmed against master | pass |
| S03 | 4 QR endpoints + `app.pending_qr_token` state machine + `socket.on('qr_payment')` in cashier UI + `jwt_token` in login response + verify script (14 checks) + `.env.example`/`DEPLOY.md` updated | All endpoints confirmed on master; `SERVER_URL` in `.env.example` and `docs/DEPLOY.md` on master; `scripts/verify-m005-s03.sh` — 14/14 pass confirmed (run against master files in temp dir) | pass |
| S04 | `QRPayActivity.kt` + Android `qrPayButton` wiring + iOS `QRPayView.swift` + `QRScannerView.swift` + HomeView "Pay with QR" + `scripts/verify-m005-s04.sh` (12 checks) | All confirmed on master via T01–T04 task summaries (each `verification_result: passed`); `verify-m005-s04.sh` — 12/12 pass; S04-SUMMARY.md and S04-UAT.md are doctor-created placeholders but underlying T01–T04 summaries document real deliverables | pass (attention: S04-SUMMARY.md is a placeholder — see A5 below) |
| S05 | NFC/HCE files deleted from backend + Android + iOS; 18-check verify script exits 0 | `scripts/verify-m005-s05.sh` exits 0 with 18/18 on milestone/M005 branch; `nfc_payments.py` absent; 5 Android NFC files absent; NFC manifest entries gone; iOS labels consolidated | pass (attention: applied to pre-S01-S04 baseline; post-merge re-verification required — see A1) |

---

## Cross-Slice Integration

**S01 → S02 (OLED placeholder hand-off):** Aligned. S01 committed `OLED_ADDR/OLED_WIDTH/OLED_HEIGHT` constants and `Wire.begin()` with `// TODO S02`. S02 check [9/9] confirms the TODO comment is removed and all OLED symbols are present. ✓

**S03 → S02 (qr-pending endpoint):** Aligned. S03's `GET /api/arduino/qr-pending` returns `{"token","url"}` or `{"token":null}`. S02's `httpGetBody()` + `parseQrUrl()` expect exactly this format; poll interval and X-API-Key auth pattern match. ✓

**S03 → S04 (QR API for apps):** Aligned. S03 added `jwt_token` to login response; S04 T01 stores it in Android (EncryptedSharedPreferences) and iOS (Keychain) and wires `getQrCart()`/`confirmQrPayment()` using it. Cart response shape and error codes (402/404/410) are consistent. ✓

**S04 → S05 (apps clean before NFC removal):** Aligned. S04 retained NFC dead code (no active call sites) per plan for S05 to clean. S05 confirmed BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml all deleted; NFC imports removed from HomeActivity; `nfc_cancel` string preserved (used by `activity_qr_pay.xml`). ✓

**Branch integration gap (S01–S04 on master / S05 on milestone/M005):** S01–S04 source code committed to master. S05 ran on milestone/M005 branch against pre-M005 baseline. The `git merge` of `milestone/M005` into `master` will produce conflicts in ~8 source files. Resolution is mechanical: keep QR additions (master) + keep NFC deletions (milestone/M005) in each file. `bash scripts/verify-m005-s05.sh` must be re-run post-merge. This is a process gap, not a code gap.

---

## Requirement Coverage

| Req | Status | Evidence | Remaining |
|-----|--------|----------|-----------|
| R026 | active | S01 firmware contract 9/9 on master | Hardware tap → Flask log (human UAT) |
| R027 | active | S01 placeholder + S02 full SSD1306 driver 9/9 on master | Hardware OLED scan (human UAT) |
| R028 | active | S02 500ms poll loop + S03 qr-pending endpoint; contracts verified | Live integration + hardware UAT |
| R029 | active | S03 all 4 endpoints + socket handler; 14/14 verified on master | Live Sheets debit (human UAT) |
| R030 | active | S04 QRPayActivity + CameraX + ML Kit; 12/12 verified on master | Real-device e2e + Gradle build |
| R031 | active | S01 R3 README rewritten; R3 firmware already used MFRC522 | Hardware flash confirmation |
| R032 | validated | S05 18/18 verify checks; py_compile exits 0 | Post-merge re-verification (A1) |
| R033 | active | S04 QRPayView + QRScannerView + HomeView wiring; 12/12 verified | Real-device e2e + xcodebuild |

All 7 active requirements have substantive code deliverables committed to git. None are missing code — all remaining items are hardware validation or build execution steps.

---

## Verdict Rationale

**All code deliverables are present and contractually verified.** The milestone achieves "contract complete" per its own verification class definition:

- `python -m py_compile` exits 0 on all modified Python files ✓  
- All five slice verify scripts (`verify-m005-s01.sh` through `verify-m005-s05.sh`) exit 0 on their respective targets ✓  
- `arduino/bankongseton_r4/` exists and `arduino/bankongseton_rfid/` is gone (on master) ✓  
- QR backend, Android QRPayActivity, iOS QRPayView, firmware OLED driver — all committed to git ✓

The gaps are not code gaps. They fall into three categories:

1. **Hardware UAT** — physical RFID tap, OLED scan, real-device app e2e. Explicitly classified as "UAT / human verification" in the Roadmap. No automated substitute exists; no new slice can replace hardware.

2. **Branch merge resolution** — S05 on milestone/M005 + S01–S04 on master diverged. The merge is needed to produce the final unified codebase. ~8 file conflicts are expected; all are mechanically resolvable (logically non-overlapping changes). This is a process step, not an engineering gap.

3. **S04 placeholder artifacts** — `S04-SUMMARY.md` and `S04-UAT.md` are doctor-created placeholders. Real work is documented in T01–T04 task summaries (all `verification_result: passed`). No code gap.

**Verdict is `needs-attention` rather than `pass`** because: (a) the branch merge has not been executed and post-merge verify-m005-s05.sh has not been re-run, and (b) the Roadmap Definition of Done explicitly requires physical hardware confirmation (`POST /api/arduino/card-read 200 in Flask log from powerbank-powered R4`) which has not been logged. These are legitimate open items that the milestone owner must close before sealing.

---

## Attention Items (no new slices required)

### A1 — Merge milestone/M005 into master and re-verify S05 *(HIGH — required before sealing)*
1. `git checkout master && git merge milestone/M005`
2. Resolve conflicts: in each conflicted file keep QR additions from master AND NFC deletions from milestone/M005
3. `bash scripts/verify-m005-s05.sh` — must exit 0 (18/18) after merge
4. `python -m py_compile backend/api/api_server.py backend/dashboard/web_app.py backend/dashboard/cashier/cashier_routes.py` — must all exit 0

### A2 — Hardware UAT: Physical RFID card tap at R4 *(HIGH — Milestone DoD requires this)*
Flash `arduino/bankongseton_r4/bankongseton_r4.ino` to the R4 WiFi board. Tap a physical RFID card. Confirm `POST /api/arduino/card-read 200` in Flask log. Validates R026; satisfies DoD item S01.

### A3 — Hardware UAT: OLED QR scannable by phone camera *(HIGH — Milestone DoD requires this)*
With firmware flashed and `POST /cashier/api/qr-generate` triggered, confirm Serial Monitor shows "QR: rendering v\<N\>", OLED shows QR pattern, and a phone camera can scan it. Validates R027/R028; satisfies DoD item S02.

### A4 — End-to-end QR payment on real devices (Android + iOS) *(HIGH — Milestone DoD requires this)*
Cashier hits Pay Now → OLED shows QR → student app "Scan QR" → scan OLED → see cart → Confirm → Sheets balance debited → cashier success modal. Run on both Android and iOS. Validates R030/R033; satisfies DoD item S04.

### A5 — Regenerate S04-SUMMARY.md from task summaries *(LOW — documentation cleanup)*
`S04-SUMMARY.md` is a doctor-created placeholder with `verification_result: unknown`. Replace with a real summary compiled from T01–T04 task summaries. No code change required.

### A6 — Android and iOS build verification *(MEDIUM — DoD "both apps build clean")*
On a machine with Android SDK: `cd mobile/student_app_v2 && ./gradlew assembleDebug` — must exit 0.  
On a Mac with Xcode: `xcodebuild -project BankongSetonStudent.xcodeproj -scheme BankongSetonStudent build` — must exit 0.

---

## Remediation Plan

None. Verdict is `needs-attention` — no new slices are required. All attention items are hardware tasks (A2/A3/A4), a merge process step (A1), a build verification step (A6), and a documentation update (A5). No missing code was identified.
