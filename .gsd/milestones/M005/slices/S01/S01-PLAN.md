# S01: RC522 Firmware Swap (R4 + R3)

**Goal:** Replace the PN532 NFC reader firmware on R4 with an RC522 MFRC522 firmware that preserves all WiFi/heartbeat behaviour, adds Wire.h + OLED pin constants as an S02 placeholder, and renames the directory to `arduino/bankongseton_r4/`. Update the R3 README to reflect its actual RC522 hardware.

**Demo:** `bash scripts/verify-m005-s01.sh` exits 0 — old `bankongseton_rfid/` directory is gone, new `bankongseton_r4/` directory has a clean MFRC522 firmware with no PN532 or LCD references, R3 README has no PN532 text. Physical card tap at powerbank-powered R4 → `POST /api/arduino/card-read 200` in Flask log (hardware integration step, human-verified).

## Must-Haves

- `arduino/bankongseton_r4/bankongseton_r4.ino` exists with MFRC522 read loop (`PICC_IsNewCardPresent`, `PICC_ReadCardSerial`, `PICC_HaltA`, `PCD_StopCrypto1`), `Wire.h` include + OLED constants placeholder, all WiFi/heartbeat helpers preserved, no PN532 / LCD / APDU symbols
- `arduino/bankongseton_r4/secrets.h` exists (copy of old file, format unchanged)
- `arduino/bankongseton_rfid/` directory deleted
- `arduino/bankongseton_nfc_r3/README.md` updated — no PN532 references, correct RC522 wiring table and library entry
- `scripts/verify-m005-s01.sh` exists and exits 0

## Proof Level

- This slice proves: contract
- Real runtime required: yes (hardware flash to confirm RC522 SPI on R4 WiFi — separate manual step after script passes)
- Human/UAT required: yes (flash + tap physical card, confirm POST 200 in Flask log)

## Verification

- `bash scripts/verify-m005-s01.sh` — all grep/test assertions exit 0
- Manual integration: flash `bankongseton_r4.ino` to R4 WiFi hardware, tap a physical RFID card, observe `POST /api/arduino/card-read 200` in Flask log

## Integration Closure

- Upstream surfaces consumed: none (first slice — no dependencies)
- New wiring introduced in this slice: `arduino/bankongseton_r4/` directory with new firmware; old `bankongseton_rfid/` removed
- What remains before the milestone is truly usable end-to-end: S02 (OLED driver + QR polling), S03 (backend QR payment flow), S04 (apps), S05 (NFC cleanup)

## Tasks

- [ ] **T01: Write R4 RC522 firmware and rename directory** `est:45m`
  - Why: Core of the slice — replace PN532+LCD+APDU with MFRC522 read loop; rename directory to bankongseton_r4/; copy secrets.h; delete old bankongseton_rfid/
  - Files: `arduino/bankongseton_r4/bankongseton_r4.ino` (new), `arduino/bankongseton_r4/secrets.h` (copy), `arduino/bankongseton_rfid/` (delete)
  - Do: Write the full firmware per the task plan. Copy `arduino/bankongseton_rfid/secrets.h` to `arduino/bankongseton_r4/secrets.h` unchanged. Delete `arduino/bankongseton_rfid/`.
  - Verify: `test -f arduino/bankongseton_r4/bankongseton_r4.ino && ! test -d arduino/bankongseton_rfid && ! grep -qE 'PN532|pn532|lcd_|LCD_SDA|httpPostNFC|inDataExchange' arduino/bankongseton_r4/bankongseton_r4.ino`
  - Done when: File exists, old directory gone, no PN532/LCD/APDU symbols in new firmware

- [ ] **T02: Fix R3 README and write verify script** `est:20m`
  - Why: R3 README still documents PN532 hardware; verify script provides CI-able proof of the entire slice's contract
  - Files: `arduino/bankongseton_nfc_r3/README.md`, `scripts/verify-m005-s01.sh`
  - Do: Rewrite R3 README to reflect actual RC522 hardware and MFRC522 library. Write verify script with all grep/test checks per the task plan.
  - Verify: `bash scripts/verify-m005-s01.sh` exits 0
  - Done when: Script exits 0 with all checks passing

## Files Likely Touched

- `arduino/bankongseton_r4/bankongseton_r4.ino` (new)
- `arduino/bankongseton_r4/secrets.h` (copied from bankongseton_rfid/)
- `arduino/bankongseton_rfid/` (deleted)
- `arduino/bankongseton_nfc_r3/README.md` (updated)
- `scripts/verify-m005-s01.sh` (new)
