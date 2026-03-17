---
id: T01
parent: S01
milestone: M005
provides:
  - arduino/bankongseton_r4/bankongseton_r4.ino — MFRC522 firmware for R4 WiFi board
  - arduino/bankongseton_r4/secrets.h — credentials copy
  - arduino/bankongseton_rfid/ — deleted
key_files:
  - arduino/bankongseton_r4/bankongseton_r4.ino
  - arduino/bankongseton_r4/secrets.h
key_decisions:
  - deliver() kept CARD-only (no NFC prefix branch); the entire APDU/HCE path is gone
  - OLED_ADDR/OLED_WIDTH/OLED_HEIGHT constants defined and Wire.begin() called; no Adafruit_SSD1306 include (S02 placeholder)
  - TODO comment kept in firmware to guide S02 implementer: "add #include <Adafruit_SSD1306.h>, Adafruit_SSD1306 display(...), and display.begin() here"
  - lcd_* calls in connectWiFi/handleIncomingSerial replaced with Serial.println equivalents
patterns_established:
  - SPI.begin() + rfid.PCD_Init() + VersionReg halt-check pattern for RC522 init (matches R3 reference)
  - PICC_HaltA() + PCD_StopCrypto1() called unconditionally after every card read (prevents stuck card state)
observability_surfaces:
  - Serial at 9600 baud — "BANKONGSETON RFID reader ready" on startup; "SCAN: FOUND uidLen=N uid=XXXX" on card; "HTTP: delivered — CARD|<uid>" on success
  - "ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)" + halt on SPI fault
  - Flask log: POST /api/arduino/card-read 200 + POST /api/arduino/heartbeat 200
duration: ~30m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T01: Write R4 RC522 Firmware and Rename Directory

**Wrote `arduino/bankongseton_r4/bankongseton_r4.ino` — clean MFRC522 firmware replacing PN532+LCD+APDU with RC522 SPI read loop and WiFi delivery; deleted `arduino/bankongseton_rfid/`.**

## What Happened

Read both source files: `bankongseton_rfid.ino` (WiFi helpers, constants, deliver, handleIncomingSerial, uidToHex) and `bankongseton_nfc_r3.ino` (RC522 VersionReg check, PICC_IsNewCardPresent/ReadCardSerial/HaltA/PCD_StopCrypto1 pattern).

Wrote `bankongseton_r4.ino` fresh (348 lines):
- **Removed:** all PN532_SPI/PN532 includes and `nfc.` calls; entire inline LCD driver (~180 lines of bit-bang I2C + pcf8574 + HD44780); APDU block (inDataExchange, SAMConfig, setRFField, httpPostNFC, NFC_TIMEOUT_MS, APDU_MAX_RETRIES, the NFC prefix branch in deliver())
- **Added:** `#include <MFRC522.h>`, `#include <Wire.h>`; RC522 pin defines + `MFRC522 rfid(RC522_SS, RC522_RST)`; OLED constants (OLED_WIDTH/HEIGHT/ADDR) + TODO S02 comment; VersionReg halt check in setup(); PICC_IsNewCardPresent/ReadCardSerial early-exit loop; PICC_HaltA + PCD_StopCrypto1 after every read
- **Preserved verbatim:** `uidToHex()`, `ensureWiFi()`, `httpPostJson()`, `httpPostCard()`, heartbeat timer, cooldown loop with handleIncomingSerial() during wait
- **lcd_* → Serial.println:** `connectWiFi()` and `handleIncomingSerial()` had their LCD calls replaced with serial equivalents

Copied `secrets.h` verbatim to `arduino/bankongseton_r4/secrets.h`. Deleted `arduino/bankongseton_rfid/` with `rm -rf`.

Also added `## Observability / Diagnostics` to `S01-PLAN.md` and `## Observability Impact` to `T01-PLAN.md` as required by the pre-flight fixes.

## Verification

All checks passed:

```
test -f arduino/bankongseton_r4/bankongseton_r4.ino         → PASS
test -f arduino/bankongseton_r4/secrets.h                   → PASS
! test -d arduino/bankongseton_rfid                         → PASS
! grep -qE 'PN532|pn532|lcd_|LCD_SDA|...' bankongseton_r4.ino → PASS (no forbidden symbols)
grep -q '#include <MFRC522.h>'                              → PASS
grep -q 'PICC_IsNewCardPresent|PICC_ReadCardSerial'         → PASS
grep -q 'PICC_HaltA|PCD_StopCrypto1'                       → PASS
grep -q '#include <Wire.h>'                                 → PASS
grep -q 'OLED_ADDR|OLED_WIDTH'                              → PASS
grep -q 'httpPostCard|heartbeat|ensureWiFi'                 → PASS
no active #include <Adafruit_SSD1306.h> (comment only)     → PASS
no active display.begin() call (comment only)              → PASS
SPI.begin() before rfid.PCD_Init() (lines 282-283)         → PASS
```

## Diagnostics

- Arduino Serial Monitor at 9600 baud: `BANKONGSETON RFID reader ready` confirms RC522 init OK
- RC522 SPI fault: `ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)` + infinite halt
- Card read: `SCAN: FOUND uidLen=N uid=XXXX` then `HTTP: delivered — CARD|<uid>` or serial fallback `CARD|<uid>`
- Heartbeat: `POST /api/arduino/heartbeat 200` in Flask log every 30 s
- WiFi issues: `WiFi lost — reconnecting...` / `WARNING: WiFi connect failed`

## Deviations

The two "FAIL" results during initial verification (`display.begin` and `Adafruit_SSD1306`) were false positives — `grep -q` matched comment text in the TODO S02 line. No active code references those symbols. Verified with `grep -n '^#include.*Adafruit_SSD1306'` and `grep -n '^[^/]*display\.begin'` — both confirmed PASS.

## Known Issues

None.

## Files Created/Modified

- `arduino/bankongseton_r4/bankongseton_r4.ino` — new MFRC522 firmware (348 lines); replaces PN532+LCD+APDU firmware
- `arduino/bankongseton_r4/secrets.h` — verbatim copy of old `bankongseton_rfid/secrets.h`
- `arduino/bankongseton_rfid/` — **deleted**
- `.gsd/milestones/M005/slices/S01/S01-PLAN.md` — added `## Observability / Diagnostics` section
- `.gsd/milestones/M005/slices/S01/tasks/T01-PLAN.md` — added `## Observability Impact` section
