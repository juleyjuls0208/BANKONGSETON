---
estimated_steps: 4
estimated_files: 2
---

# T02: Fix R3 README and Write Verify Script

**Slice:** S01 — RC522 Firmware Swap (R4 + R3)
**Milestone:** M005

## Description

Two independent deliverables that close out the slice:

1. Rewrite `arduino/bankongseton_nfc_r3/README.md` — the current README incorrectly describes a PN532 NFC module; the actual hardware is RC522 RFID. Update title, wiring table, library list, and pin summary.

2. Write `scripts/verify-m005-s01.sh` — the contract verification script that proves all S01 outputs are correct via grep/test assertions. This script is the objective stopping condition for the slice.

## Steps

1. **Rewrite `arduino/bankongseton_nfc_r3/README.md`** with the following changes:
   - Title: `BANKONGSETON RFID Registration Reader — Arduino UNO R3 (RC522 over SPI)`
   - Opening description: "Reads physical RFID cards via RC522 over SPI and emits `CARD|<UID-HEX>` over Serial for the Python `ArduinoBridge` to process card registrations."
   - Remove all PN532 references including: "PN532 NFC/RFID module", Adafruit PN532 shield/breakout, "SPI mode selection: set DIP switches SEL0=LOW SEL1=HIGH", "ISO14443A" and "HCE" mentions
   - Update Hardware Required table: replace PN532 row with `RC522 RFID module | Any standard RC522 breakout board (3.3V)`
   - Update Wiring section title to "RC522 RFID Module → Arduino UNO R3"; update table to show `SDA/SS → D10 (RC522_SS)`, `RST → D8 (RC522_RST)`, and SPI lines D11/D12/D13; remove "SPI mode selection" note
   - Update Required Libraries table: remove Adafruit PN532 and Adafruit BusIO rows; add `MFRC522 | GithubCommunity (miguelbalboa/rfid) | RFID reader driver`
   - Update Pin Summary table: replace PN532 D10 row with `D10 | RC522 SDA/SS (SPI)`; add `D8 | RC522 RST`; keep D6/D7/D9/D11/D12/D13 rows unchanged
   - Keep Serial Output Format section unchanged (format is still `CARD|AABBCCDD`, 9600 baud, `BANKONGSETON NFC reader ready` startup line)
   - Keep LCD I2C Address section unchanged

2. **Write `scripts/verify-m005-s01.sh`** as an executable bash script with the following checks (fail fast with `set -e`):

   ```bash
   #!/usr/bin/env bash
   set -euo pipefail

   # S01 contract verification: RC522 Firmware Swap (R4 + R3)
   # Run from project root: bash scripts/verify-m005-s01.sh

   echo "=== S01: RC522 Firmware Swap — contract verification ==="

   # Directory structure
   echo "[1/9] R4 firmware file exists..."
   test -f arduino/bankongseton_r4/bankongseton_r4.ino

   echo "[2/9] R4 secrets.h exists..."
   test -f arduino/bankongseton_r4/secrets.h

   echo "[3/9] Old bankongseton_rfid/ directory is gone..."
   ! test -d arduino/bankongseton_rfid

   # R4: correct reader library
   echo "[4/9] R4 uses MFRC522..."
   grep -q '#include <MFRC522.h>' arduino/bankongseton_r4/bankongseton_r4.ino

   # R4: no PN532 / LCD / APDU references
   echo "[5/9] R4 has no PN532/LCD/APDU code..."
   ! grep -qE 'PN532|pn532|Adafruit_PN532|lcd_|LCD_SDA|LCD_SCL|pcf8574|i2c_start|inDataExchange|SAMConfig|setRFField|httpPostNFC|NFC_TIMEOUT|APDU_MAX' arduino/bankongseton_r4/bankongseton_r4.ino

   # R4: WiFi path preserved
   echo "[6/9] R4 WiFi path preserved (httpPostCard, heartbeat, ensureWiFi)..."
   grep -q 'httpPostCard' arduino/bankongseton_r4/bankongseton_r4.ino
   grep -q 'heartbeat' arduino/bankongseton_r4/bankongseton_r4.ino
   grep -q 'ensureWiFi' arduino/bankongseton_r4/bankongseton_r4.ino

   # R4: OLED pin placeholder
   echo "[7/9] R4 OLED placeholder present (Wire.h, OLED_ADDR)..."
   grep -q '#include <Wire.h>' arduino/bankongseton_r4/bankongseton_r4.ino
   grep -qE 'OLED_ADDR|OLED_WIDTH' arduino/bankongseton_r4/bankongseton_r4.ino

   # R4: MFRC522 read pattern
   echo "[8/9] R4 MFRC522 read pattern present..."
   grep -qE 'PICC_IsNewCardPresent|PICC_ReadCardSerial' arduino/bankongseton_r4/bankongseton_r4.ino
   grep -qE 'PICC_HaltA|PCD_StopCrypto1' arduino/bankongseton_r4/bankongseton_r4.ino

   # R3: no PN532 references
   echo "[9/9] R3 README and firmware have no PN532 references..."
   ! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
   ! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/README.md

   echo ""
   echo "✓ All S01 contract checks passed."
   echo ""
   echo "NEXT: Flash arduino/bankongseton_r4/bankongseton_r4.ino to R4 WiFi hardware,"
   echo "      tap a physical RFID card, and confirm POST /api/arduino/card-read 200"
   echo "      in the Flask log to complete integration verification."
   ```

3. **Make the script executable**: `chmod +x scripts/verify-m005-s01.sh`

4. **Run the script** from project root: `bash scripts/verify-m005-s01.sh` — all 9 checks must pass.

## Must-Haves

- [ ] `arduino/bankongseton_nfc_r3/README.md` contains no PN532 or pn532 text
- [ ] README title is updated to reference RC522 not PN532
- [ ] README wiring table shows RC522 SS→D10, RST→D8
- [ ] README library table lists MFRC522 (not Adafruit PN532)
- [ ] `scripts/verify-m005-s01.sh` exists and is executable
- [ ] `bash scripts/verify-m005-s01.sh` exits 0

## Verification

- `! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/README.md`
- `bash scripts/verify-m005-s01.sh` (exits 0 — all 9 checks pass)

## Inputs

- `arduino/bankongseton_r4/bankongseton_r4.ino` — must exist (produced by T01) for verify script to pass
- `arduino/bankongseton_nfc_r3/README.md` — current stale README to replace
- S01-RESEARCH.md verification section — source of all grep patterns for the verify script

## Expected Output

- `arduino/bankongseton_nfc_r3/README.md` — rewritten to accurately describe RC522 hardware
- `scripts/verify-m005-s01.sh` — executable script that exits 0 when all S01 outputs are correct

## Observability Impact

**Signals introduced by this task:**
- `bash scripts/verify-m005-s01.sh` — the primary CI-able signal; exits 0 = all S01 contracts met, non-zero exit = specific failing check printed to stdout
- Each check prints `[N/9] <description>...` before the assertion, so a failure is pinpointed to a numbered step in the script output

**Inspection surfaces:**
- `scripts/verify-m005-s01.sh` stdout — run from project root to see all 9 check results in sequence
- `arduino/bankongseton_nfc_r3/README.md` — human-readable reference for actual R3 hardware wiring; no runtime signals but prevents future confusion about PN532 vs RC522

**Failure visibility:**
- Script fails at step N → stdout shows `[N/9] <description>...` then the `set -e` trap exits non-zero
- Common failure: check [9/9] fails → README or R3 firmware still contains `PN532`/`pn532` text
- Check [1/9] or [2/9] fail → T01 did not complete; firmware or secrets.h missing
- Check [3/9] fails → old `bankongseton_rfid/` directory was not deleted

**No runtime firmware signals** — this task only produces static files (README + verify script); all runtime signals for the slice come from T01's firmware.
