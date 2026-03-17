# S01: RC522 Firmware Swap (R4 + R3) — UAT

**Milestone:** M005
**Written:** 2026-03-17

## UAT Type

- UAT mode: artifact-driven (contract verification) + human-experience (hardware flash + tap)
- Why this mode is sufficient: The firmware is a `.ino` file — it cannot be executed without hardware. The artifact-driven checks (verify script) prove all structural contracts: correct library, no dead symbols, WiFi path intact, OLED placeholder present, R3 README accurate. The human-experience step proves the one thing only hardware can prove: RC522 SPI actually communicates with the R4 WiFi board and the WiFi POST reaches the Flask backend.

## Preconditions

**For artifact-driven checks (CI-able):**
- Project cloned at project root
- bash available (Git Bash or WSL on Windows)
- No hardware required

**For hardware integration check:**
- Arduino UNO R4 WiFi board with RC522 wired: SDA/SS→D10, RST→D8, SPI D11/D12/D13, VCC→3.3V, GND→GND
- Arduino IDE (or arduino-cli) with MFRC522 library installed (Library Manager → "MFRC522 by GithubCommunity")
- `arduino/bankongseton_r4/secrets.h` populated with correct SSID, password, API key, Flask host
- Flask backend running (PythonAnywhere or local) and reachable from the Arduino's LAN
- USB cable to flash; USB powerbank to run standalone after flash

## Smoke Test

```bash
bash scripts/verify-m005-s01.sh
```

Expected output ending with:
```
✓ All S01 contract checks passed.
```

Exit code 0 = all contracts met.

---

## Test Cases

### 1. Verify Script — All 9 Checks Pass

1. From the project root, run: `bash scripts/verify-m005-s01.sh`
2. Observe each numbered step prints without error
3. **Expected:** Script prints `✓ All S01 contract checks passed.` and exits with code 0
4. **Failure signal:** Any `[N/9]` line is the last output before exit — that step's assertion failed

---

### 2. R4 Firmware: No PN532/LCD/APDU Symbols

1. Open `arduino/bankongseton_r4/bankongseton_r4.ino` in any text editor or IDE
2. Search (Ctrl+F) for: `PN532`, `pn532`, `Adafruit_PN532`, `lcd_`, `LCD_SDA`, `LCD_SCL`, `pcf8574`, `i2c_start`, `inDataExchange`, `SAMConfig`, `setRFField`, `httpPostNFC`, `NFC_TIMEOUT`, `APDU_MAX`
3. **Expected:** Zero matches for all search terms (only valid hit: `# TODO S02` comment which does not contain any of these strings)

---

### 3. R4 Firmware: MFRC522 Read Loop and WiFi Path Present

1. Open `arduino/bankongseton_r4/bankongseton_r4.ino`
2. Verify the following are present as active code (not comments):
   - `#include <MFRC522.h>` near top
   - `#include <Wire.h>` near top
   - `PICC_IsNewCardPresent` and `PICC_ReadCardSerial` in loop()
   - `PICC_HaltA` and `PCD_StopCrypto1` after card read
   - `httpPostCard` function definition
   - `ensureWiFi` function definition
   - `heartbeat` variable used in loop()
3. **Expected:** All items found as uncommented code

---

### 4. R4 Firmware: OLED S02 Placeholder

1. Open `arduino/bankongseton_r4/bankongseton_r4.ino`
2. Search for `OLED_ADDR` and `OLED_WIDTH`
3. Verify `#include <Wire.h>` is present (not commented)
4. Verify `Wire.begin()` is called in setup()
5. Verify `Adafruit_SSD1306` does NOT appear as an active `#include` (may appear in a comment)
6. **Expected:** OLED constants defined, Wire initialized, no active SSD1306 include — this is the correct S02 placeholder state

---

### 5. Old Directory Gone, New Directory Present

1. Check directory listing: `ls arduino/`
2. **Expected:**
   - `bankongseton_r4/` directory exists
   - `bankongseton_rfid/` directory does NOT exist
   - `bankongseton_nfc_r3/` directory still exists

---

### 6. R3 README: No PN532 References

1. Open `arduino/bankongseton_nfc_r3/README.md`
2. Search for: `PN532`, `pn532`, `Adafruit_PN532`
3. **Expected:** Zero matches — document describes RC522 hardware only
4. Verify wiring table shows `SDA/SS → D10` and `RST → D8` for the RC522

---

### 7. Hardware Flash — RC522 Init on R4

1. Open `arduino/bankongseton_r4/bankongseton_r4.ino` in Arduino IDE
2. Verify `secrets.h` has correct SSID/password/API key/FLASK_HOST
3. Connect R4 WiFi via USB, select board "Arduino UNO R4 WiFi" and correct port
4. Verify RC522 is physically wired: SDA/SS→D10, RST→D8, SPI D11/D12/D13, VCC→3.3V
5. Upload sketch
6. Open Serial Monitor at 9600 baud
7. **Expected:** `BANKONGSETON RFID reader ready` printed within ~5 seconds of boot
8. **Failure signal:** `ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)` followed by halt — indicates SPI wiring problem

---

### 8. Hardware Integration — Physical Card Tap → Flask Log

1. With Serial Monitor open (from Test 7), tap a physical RFID/MIFARE card to the RC522 reader
2. **Expected in Serial Monitor:**
   ```
   SCAN: FOUND uidLen=4 uid=AABBCCDD
   HTTP attempt 1/3
   HTTP: delivered — CARD|AABBCCDD
   ```
3. **Expected in Flask log (PythonAnywhere or local):**
   ```
   POST /api/arduino/card-read 200
   ```
4. **Expected in cashier UI:** `card_read` socket event fires; if cashier has a cart open with Pay Now active, payment flow initiates
5. **Failure signal:** `HTTP attempt 1/3` ... `HTTP attempt 2/3` ... `HTTP attempt 3/3` then `WARNING: WiFi deliver failed — sending serial fallback` — indicates WiFi/network issue, not RC522 issue

---

### 9. Hardware — Heartbeat on Powerbank

1. After successful flash, unplug USB cable and connect R4 WiFi to USB powerbank
2. Wait 35 seconds
3. Check Flask log
4. **Expected:** `POST /api/arduino/heartbeat 200` appears approximately every 30 seconds
5. **Expected in cashier UI:** WiFi status badge turns green within one heartbeat cycle

---

## Edge Cases

### WiFi Not Configured (blank SECRET_SSID in secrets.h)

1. Flash with `SECRET_SSID` left blank
2. Open Serial Monitor
3. **Expected:** `WiFi disabled — serial-only mode` printed; no HTTP attempts; on card tap, `CARD|<UID>` is printed to Serial without any WiFi POST

### RC522 SPI Wiring Wrong

1. Flash with any SPI pin disconnected (simulate by removing SDA/SS wire)
2. Open Serial Monitor
3. **Expected:** `ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)` followed by infinite halt — no further output, no card reads

### WiFi Drops During Operation

1. After successful flash, power-cycle the WiFi router or move R4 out of range
2. Tap a card while WiFi is down
3. **Expected:** `HTTP attempt 1/3`, `HTTP attempt 2/3`, `HTTP attempt 3/3` then `WARNING: WiFi deliver failed — sending serial fallback` then `CARD|<UID>` emitted to Serial; ArduinoBridge processes the serial fallback
4. When WiFi recovers, **Expected:** next card tap or heartbeat uses WiFi successfully (`ensureWiFi` reconnects)

---

## Failure Signals

- `ERROR: RC522 not found` in Serial Monitor → SPI wiring fault (check D10/D8 connections, VCC at 3.3V)
- `WiFi disabled — serial-only mode` → `SECRET_SSID` is blank in secrets.h
- No `BANKONGSETON RFID reader ready` after 10 seconds → sketch not uploaded or board frozen
- `scripts/verify-m005-s01.sh` exits non-zero at step N → specific contract failure at that numbered check
- `POST /api/arduino/card-read` missing from Flask log after tap → WiFi connectivity issue or wrong FLASK_HOST in secrets.h
- Card tap produces no Serial output after `BANKONGSETON RFID reader ready` → RC522 is not detecting card (check antenna, card compatibility)

---

## Requirements Proved By This UAT

- **R026** (RC522 RFID on R4) — Test Cases 7 and 8 prove RC522 SPI works on R4 WiFi and card taps reach the Flask backend
- **R031** (RC522 RFID on R3, cleanup) — Test Case 6 proves R3 README and firmware have no PN532 references

## Not Proven By This UAT

- **R027** (OLED replaces LCD) — OLED placeholder is present (Test Case 4) but OLED display is non-functional until S02; full R027 proof requires S02 completion
- **R026 fully validated** — artifact check confirms firmware contract; only Tests 7–8 with real hardware provide complete validation. Test Cases 7–9 require physical hardware and manual execution — they cannot be automated in CI.
- WiFi heartbeat keeping a powerbank alive across a full school day — confirmed in M003/S04 (R023); this slice preserves that behaviour but does not re-prove it

## Notes for Tester

- The verify script (`scripts/verify-m005-s01.sh`) is the definitive artifact check. Run it first; if it exits 0, the firmware contract is solid.
- Tests 7–9 require physical hardware. The most important is Test 8 — the `POST /api/arduino/card-read 200` in the Flask log is the milestone-level proof for R026.
- The R3 firmware (`bankongseton_nfc_r3.ino`) was NOT modified in this slice — it already used MFRC522 correctly. Only the README was updated. If testing R3, it should behave identically to before this slice.
- `secrets.h` is gitignored. Before flashing, verify it contains real credentials — the template file shows the format but has empty values.
- If the OLED appears to do nothing after flash — that is correct. OLED is intentionally deferred to S02. Wire.begin() is called but nothing is drawn.
