---
id: S01
parent: M005
milestone: M005
provides:
  - arduino/bankongseton_r4/bankongseton_r4.ino — MFRC522 firmware for R4 WiFi board (RC522 read loop + WiFi delivery + heartbeat + OLED pin placeholder)
  - arduino/bankongseton_r4/secrets.h — credentials file, format unchanged from old bankongseton_rfid/
  - arduino/bankongseton_rfid/ — deleted
  - arduino/bankongseton_nfc_r3/README.md — rewritten with accurate RC522/MFRC522 hardware documentation
  - scripts/verify-m005-s01.sh — executable contract verification script (9 checks, exits 0)
requires: []
affects:
  - S02: consumes bankongseton_r4.ino base firmware (RC522 loop + WiFi working); OLED_ADDR/OLED_WIDTH/OLED_HEIGHT constants + Wire.begin() already present as placeholder
  - S05: R3 firmware already clean (no PN532 refs to scrub); S05 has no R3 firmware work
key_files:
  - arduino/bankongseton_r4/bankongseton_r4.ino
  - arduino/bankongseton_r4/secrets.h
  - arduino/bankongseton_nfc_r3/README.md
  - scripts/verify-m005-s01.sh
key_decisions:
  - D041: PN532 → RC522 on R4; phone NFC/HCE payment retired entirely (arch decision — recorded in DECISIONS.md)
  - D042: LCD → SSD1306 OLED on R4 (arch decision — recorded in DECISIONS.md; Wire.h placeholder committed in this slice)
  - deliver() kept CARD-only; the entire APDU/HCE path is gone from the firmware
  - OLED_ADDR/OLED_WIDTH/OLED_HEIGHT constants + Wire.begin() present but no Adafruit_SSD1306 include — intentional S02 placeholder with TODO comment
  - lcd_* calls in connectWiFi/handleIncomingSerial replaced with Serial.println equivalents (no LCD dependency)
  - ArduinoBridge startup string "BANKONGSETON NFC reader ready" preserved unchanged in R3 firmware — ArduinoBridge depends on this exact string
patterns_established:
  - SPI.begin() + rfid.PCD_Init() + VersionReg halt-check pattern for RC522 init (matches R3 reference firmware)
  - PICC_HaltA() + PCD_StopCrypto1() called unconditionally after every card read — prevents stuck card state
  - ERROR: RC522 not found + infinite halt on SPI fault — clear wiring diagnosis signal
observability_surfaces:
  - Serial at 9600 baud — "BANKONGSETON RFID reader ready" on startup; "SCAN: FOUND uidLen=N uid=XXXX" on card; "HTTP: delivered — CARD|<uid>" on success
  - "ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)" + halt on SPI fault
  - Flask log: POST /api/arduino/card-read 200 + POST /api/arduino/heartbeat 200
  - bash scripts/verify-m005-s01.sh — each step prints [N/9] so failures are immediately pinpointed
drill_down_paths:
  - .gsd/milestones/M005/slices/S01/tasks/T01-SUMMARY.md — firmware write + directory rename
  - .gsd/milestones/M005/slices/S01/tasks/T02-SUMMARY.md — R3 README rewrite + verify script
duration: ~40m
verification_result: passed
completed_at: 2026-03-17
---

# S01: RC522 Firmware Swap (R4 + R3)

**Replaced PN532+LCD+APDU firmware on R4 with a clean MFRC522 read loop preserving all WiFi/heartbeat behaviour; renamed `bankongseton_rfid/` to `bankongseton_r4/`; updated R3 README to accurately document RC522 hardware; wrote a 9-check verify script that exits 0.**

## What Happened

**T01 — Firmware + Directory Rename:** Read both source files — the existing R4 WiFi firmware (`bankongseton_rfid.ino`, WiFi helpers, constants, deliver, handleIncomingSerial, uidToHex) and the R3 reference firmware (RC522 VersionReg check, PICC_IsNewCardPresent/ReadCardSerial/HaltA/PCD_StopCrypto1 pattern). Wrote `bankongseton_r4.ino` fresh at 348 lines:

- **Removed:** all PN532_SPI/PN532 includes and `nfc.` calls; inline LCD driver (~180 lines of bit-bang I2C + PCF8574 + HD44780); APDU block (inDataExchange, SAMConfig, setRFField, httpPostNFC, NFC_TIMEOUT_MS, APDU_MAX_RETRIES, the NFC prefix branch in deliver())
- **Added:** `#include <MFRC522.h>`, `#include <Wire.h>`; RC522 pin defines + `MFRC522 rfid(RC522_SS, RC522_RST)`; OLED constants (OLED_WIDTH/HEIGHT/ADDR) + S02 TODO comment; VersionReg halt check in setup(); PICC_IsNewCardPresent/ReadCardSerial early-exit loop; PICC_HaltA + PCD_StopCrypto1 after every read
- **Preserved verbatim:** `uidToHex()`, `ensureWiFi()`, `httpPostJson()`, `httpPostCard()`, heartbeat timer, cooldown loop with handleIncomingSerial() during wait
- **Adapted:** `connectWiFi()` and `handleIncomingSerial()` lcd_* calls → Serial.println equivalents

Copied `secrets.h` verbatim to `arduino/bankongseton_r4/secrets.h`. Deleted `arduino/bankongseton_rfid/` with `rm -rf`.

**T02 — R3 README + Verify Script:** Rewrote R3 README replacing all PN532/Adafruit_PN532 content with accurate RC522/MFRC522 descriptions: title, opening description, hardware table, wiring table (RC522 SPI pinout D10/D11/D12/D13/RST=D8), libraries table (MFRC522 by GithubCommunity). Serial Output Format and LCD I2C Address sections kept unchanged — the `CARD|<UID>` serial format and `BANKONGSETON NFC reader ready` startup string are unchanged in the actual firmware and ArduinoBridge depends on the startup string. Wrote `scripts/verify-m005-s01.sh` with 9 numbered checks made executable.

## Verification

`bash scripts/verify-m005-s01.sh` exits 0 with all 9 checks passing:

```
[1/9] R4 firmware file exists...          PASS
[2/9] R4 secrets.h exists...              PASS
[3/9] Old bankongseton_rfid/ is gone...   PASS
[4/9] R4 uses MFRC522...                  PASS
[5/9] R4 has no PN532/LCD/APDU code...    PASS
[6/9] R4 WiFi path preserved...           PASS
[7/9] R4 OLED placeholder present...      PASS
[8/9] R4 MFRC522 read pattern present...  PASS
[9/9] R3 README/firmware no PN532 refs... PASS
✓ All S01 contract checks passed.
```

Manual integration verification (flash + physical card tap) is a separate hardware step — the verify script confirms the firmware contract; runtime confirmation requires flashing to R4 WiFi hardware and observing `POST /api/arduino/card-read 200` in the Flask log.

## Requirements Advanced

- **R026** (RC522 RFID on R4) — firmware contract verified; hardware integration step (flash + tap) still pending human verification
- **R027** (OLED replaces LCD on R4) — Wire.h include + OLED pin constants committed as S02 placeholder; primary OLED work in S02
- **R031** (RC522 RFID on R3, cleanup) — R3 README and firmware confirmed PN532-free; role clarification documented

## Requirements Validated

None validated in this slice. R026 and R031 require physical hardware flash to move from active → validated. R027 requires S02 completion.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

- During T01 initial verification, two checks appeared to FAIL (`display.begin` and `Adafruit_SSD1306`) — false positives because `grep -q` matched the TODO S02 comment text. Resolved by confirming with `grep -n '^#include.*Adafruit_SSD1306'` and `grep -n '^[^/]*display\.begin'` — no active code references those symbols. Verify script uses non-comment pattern matching to avoid this.
- R3 README retained the LCD hardware table entry (the R3 sketch still uses an LCD) and the PCF8574 bit-bang driver — these are accurate for R3 hardware. Only PN532 sections were replaced.

## Known Limitations

- **Hardware integration not yet proven:** `POST /api/arduino/card-read 200` from powerbank-powered R4 has not been confirmed in a Flask log — this is the manual hardware verification step that completes R026 validation. The firmware contract is proven; the SPI wiring of RC522 on R4 WiFi is unproven in this slice.
- **OLED is deactivated:** `Adafruit_SSD1306` is intentionally excluded from the firmware. Wire.begin() is called but the OLED does nothing — a blank display or no display. S02 completes this.
- **R3 README still documents LCD hardware:** The R3 sketch uses a 16×2 LCD with PCF8574; this is accurate. The LCD reference in README is not a mistake — it describes real hardware on R3.

## Follow-ups

- **S02:** Add `#include <Adafruit_SSD1306.h>`, `Adafruit_SSD1306 display(...)`, `display.begin()`, QR polling loop to `bankongseton_r4.ino`. The TODO comment and OLED_* constants mark exactly where to insert.
- **Hardware validation:** Flash `arduino/bankongseton_r4/bankongseton_r4.ino` to the R4 WiFi board, tap a physical RFID card, confirm `POST /api/arduino/card-read 200` in Flask log. This is the final step to validate R026.

## Files Created/Modified

- `arduino/bankongseton_r4/bankongseton_r4.ino` — new MFRC522 firmware (348 lines); replaces PN532+LCD+APDU firmware
- `arduino/bankongseton_r4/secrets.h` — verbatim copy of old `bankongseton_rfid/secrets.h`
- `arduino/bankongseton_rfid/` — **deleted**
- `arduino/bankongseton_nfc_r3/README.md` — fully rewritten; all PN532 references replaced with RC522/MFRC522 descriptions
- `scripts/verify-m005-s01.sh` — new executable S01 contract verification script (9 checks, exits 0)

## Forward Intelligence

### What the next slice should know

- **S02 insertion point is pre-marked:** In `bankongseton_r4.ino`, search for `// TODO S02` — this comment sits immediately after `Wire.begin()` and the OLED constant definitions. Insert `#include <Adafruit_SSD1306.h>`, the `Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1)` declaration (near the top with other globals), and `display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)` in setup() at this location.
- **RC522 SPI wiring on R4 WiFi is identical to R3:** SS=D10, RST=D8, SPI hardware lines D11/D12/D13. The R3 has proven this works on UNO-class hardware. The R4 WiFi uses the same SPI peripheral.
- **WiFi helpers are fully intact:** `ensureWiFi()`, `httpPostJson()`, `httpPostCard()`, heartbeat timer — all preserved verbatim. S02 can add the qr-pending poll loop alongside the heartbeat timer without touching these helpers.
- **ArduinoBridge startup string is "BANKONGSETON RFID reader ready"** (R4) and "BANKONGSETON NFC reader ready" (R3). Both are hardcoded. ArduinoBridge uses these to confirm boot — do not change them.
- **secrets.h format is unchanged:** `SECRET_SSID`, `SECRET_PASS`, `SECRET_API_KEY`, `FLASK_HOST` — same keys, same format. The file is gitignored; firmware never prints them to Serial.

### What's fragile

- **RC522 VersionReg halt-check is strict:** If SPI wiring is wrong, setup() never returns (infinite `while(true)` loop). This is intentional diagnostic behaviour but means a wiring error produces a completely silent board from the Python side (ArduinoBridge never sees the ready string, times out). Check the Serial Monitor first if the board appears unresponsive.
- **OLED_ADDR hardcoded to 0x3C:** Most SSD1306 breakouts ship at 0x3C but some are 0x3D. If the OLED doesn't respond in S02, check the address.
- **cooldown loop** (500ms between reads) calls `handleIncomingSerial()` for responsiveness during wait. If S02 adds a QR poll inside the cooldown, confirm it doesn't block long enough to break the 500ms card-read gate.

### Authoritative diagnostics

- **Arduino Serial Monitor at 9600 baud** — primary real-time observation; `BANKONGSETON RFID reader ready` = RC522 init OK; `ERROR: RC522 not found` = SPI fault
- **Flask log `POST /api/arduino/card-read 200`** — end-to-end proof that RC522 → WiFi → backend chain works
- **`bash scripts/verify-m005-s01.sh`** — authoritative contract proof for CI/pre-flash check; each `[N/9]` step pinpoints exactly which file or grep failed

### What assumptions changed

- **Original assumption:** R3 firmware might carry PN532 dead code. **Actual:** R3 firmware (`bankongseton_nfc_r3.ino`) already used MFRC522; no code changes were needed to the .ino file — only the README required updating.
- **Adafruit_SSD1306 grep false-positive:** Initial grep for `display.begin` and `Adafruit_SSD1306` matched comment text in the S02 TODO block. The verify script uses stricter line-start anchors (`^#include`) to avoid this in CI.
