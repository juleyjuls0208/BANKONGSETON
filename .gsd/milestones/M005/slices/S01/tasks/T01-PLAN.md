---
estimated_steps: 7
estimated_files: 3
---

# T01: Write R4 RC522 Firmware and Rename Directory

**Slice:** S01 — RC522 Firmware Swap (R4 + R3)
**Milestone:** M005

## Description

Write the full `bankongseton_r4.ino` firmware from scratch (do not rename the old file — write fresh). The firmware is a targeted substitution: pull out PN532 + LCD + APDU logic from the old `bankongseton_rfid.ino`, wire in MFRC522 + Wire.h OLED placeholder, and keep all WiFi/heartbeat helpers verbatim. Then copy `secrets.h` to the new directory and delete `arduino/bankongseton_rfid/`.

The MFRC522 read loop pattern comes directly from the R3 firmware (`arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino`) — use it as the reference implementation to port.

## Steps

1. **Read the R3 firmware** `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` to extract the exact MFRC522 setup and read loop (SPI.begin, PCD_Init, VersionReg halt check, PICC_IsNewCardPresent, PICC_ReadCardSerial, PICC_HaltA, PCD_StopCrypto1).

2. **Write `arduino/bankongseton_r4/bankongseton_r4.ino`** with the following structure (in order):
   - Header comment block: role, hardware wiring table (RC522 SPI on D10/D13 + RST D8; OLED on SDA/SCL hardware I2C; piezo D9), required libraries
   - Includes: `<SPI.h>`, `<MFRC522.h>`, `<Wire.h>`, `<WiFiS3.h>`, `"secrets.h"`
   - RC522 pin defines: `RC522_SS 10`, `RC522_RST 8`; global `MFRC522 rfid(RC522_SS, RC522_RST);`
   - OLED placeholder constants: `OLED_WIDTH 128`, `OLED_HEIGHT 64`, `OLED_ADDR 0x3C`; comment `// TODO S02: add #include <Adafruit_SSD1306.h>, Adafruit_SSD1306 display(...), and display.begin() here`
   - Other defines/constants: `PIEZO_PIN 9`, `SCAN_COOLDOWN_MS 1500`, `MAX_RETRIES 3`, `RETRY_DELAY_MS 2000`, `HTTP_TIMEOUT_MS 5000`, `HEARTBEAT_INTERVAL_MS 30000`
   - `uidToHex()` — copy verbatim from old firmware
   - `connectWiFi()` — copy verbatim; replace all `lcd_*` calls with `Serial.println(...)` equivalents
   - `ensureWiFi()` — copy verbatim (no LCD calls in this function)
   - `httpPostJson()` — copy verbatim
   - `httpPostCard()` — copy verbatim
   - `deliver()` — simplified version: only "CARD" prefix, remove the `httpPostNFC` branch; keep WiFi retry loop and serial fallback
   - `handleIncomingSerial()` — copy verbatim; replace `lcd_*` calls with `Serial.println(...)` equivalents
   - `lastHeartbeatMs` static variable
   - `setup()`: Serial.begin(9600), pinMode PIEZO_PIN, SPI.begin(), rfid.PCD_Init(), VersionReg halt check (halt if ver==0x00 || ver==0xFF with Serial error + infinite loop), Wire.begin(), connectWiFi(), startup beep, `Serial.println("BANKONGSETON RFID reader ready")`
   - `loop()`: handleIncomingSerial(), heartbeat timer block, PICC_IsNewCardPresent early-exit, PICC_ReadCardSerial early-exit, uidToHex(), detect beep, deliver(uidHex, "CARD"), success beep, PICC_HaltA(), PCD_StopCrypto1(), cooldown loop with handleIncomingSerial()

3. **Constraints to enforce while writing:**
   - No `#include <PN532*.h>`, no `PN532`, no `nfc.` references anywhere
   - No `lcd_*` function calls, no `pcf8574_*`, no LCD inline driver (~200 lines from old firmware)
   - No APDU block: no `inDataExchange`, no `SAMConfig`, no `setRFField`, no `httpPostNFC`, no `NFC_TIMEOUT_MS`, no `APDU_MAX_RETRIES`
   - `deliver()` must NOT contain the `(prefix == "NFC")` branch — CARD only
   - `Wire.begin()` called in setup(); NO `display.begin()` call (deferred to S02)
   - Do NOT include `<Adafruit_SSD1306.h>` — that library is not installed in S01; only `Wire.h` header is safe
   - `PICC_HaltA()` + `PCD_StopCrypto1()` MUST be called after every card read (prevents stuck card state)
   - `SPI.begin()` MUST be called before `rfid.PCD_Init()`
   - WiFiS3.h (not WiFi.h or WiFiNINA.h)

4. **Copy secrets.h**: copy `arduino/bankongseton_rfid/secrets.h` contents exactly to `arduino/bankongseton_r4/secrets.h` — do not modify the format.

5. **Delete old directory**: remove `arduino/bankongseton_rfid/` and all its contents.

6. **Spot-check** the new firmware file:
   - `grep -c 'MFRC522\|PICC_IsNewCardPresent\|PICC_HaltA' arduino/bankongseton_r4/bankongseton_r4.ino` should be > 0
   - `grep -c 'PN532\|lcd_\|inDataExchange\|httpPostNFC' arduino/bankongseton_r4/bankongseton_r4.ino` should be 0
   - `test -f arduino/bankongseton_r4/secrets.h` should pass
   - `! test -d arduino/bankongseton_rfid` should pass

## Must-Haves

- [ ] `arduino/bankongseton_r4/bankongseton_r4.ino` exists
- [ ] `arduino/bankongseton_r4/secrets.h` exists (identical content to old secrets.h)
- [ ] `arduino/bankongseton_rfid/` directory does not exist
- [ ] No PN532/PN532_SPI includes or symbols in new firmware
- [ ] No LCD driver code (`lcd_init`, `lcd_clear`, `lcd_set_cursor`, `lcd_print`, `pcf8574_write`, `i2c_start`, `LCD_SDA`, `LCD_SCL`, `LCD_ADDR`) in new firmware
- [ ] No APDU/NFC code (`inDataExchange`, `SAMConfig`, `setRFField`, `httpPostNFC`, `NFC_TIMEOUT_MS`, `APDU_MAX_RETRIES`) in new firmware
- [ ] MFRC522 read loop present: `PICC_IsNewCardPresent`, `PICC_ReadCardSerial`, `PICC_HaltA`, `PCD_StopCrypto1`
- [ ] Wire.h included, `OLED_ADDR` constant defined, no `display.begin()` call
- [ ] All WiFi helpers preserved: `connectWiFi`, `ensureWiFi`, `httpPostJson`, `httpPostCard`, `deliver`, `handleIncomingSerial`, heartbeat timer

## Verification

- `test -f arduino/bankongseton_r4/bankongseton_r4.ino`
- `test -f arduino/bankongseton_r4/secrets.h`
- `! test -d arduino/bankongseton_rfid`
- `! grep -qE 'PN532|pn532|lcd_|LCD_SDA|LCD_SCL|pcf8574|inDataExchange|SAMConfig|setRFField|httpPostNFC|NFC_TIMEOUT|APDU_MAX' arduino/bankongseton_r4/bankongseton_r4.ino`
- `grep -q '#include <MFRC522.h>' arduino/bankongseton_r4/bankongseton_r4.ino`
- `grep -q 'PICC_IsNewCardPresent\|PICC_ReadCardSerial' arduino/bankongseton_r4/bankongseton_r4.ino`
- `grep -q 'PICC_HaltA\|PCD_StopCrypto1' arduino/bankongseton_r4/bankongseton_r4.ino`
- `grep -q '#include <Wire.h>' arduino/bankongseton_r4/bankongseton_r4.ino`
- `grep -q 'OLED_ADDR\|OLED_WIDTH' arduino/bankongseton_r4/bankongseton_r4.ino`
- `grep -q 'httpPostCard\|heartbeat\|ensureWiFi' arduino/bankongseton_r4/bankongseton_r4.ino`

## Inputs

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — source of WiFi helpers, deliver(), handleIncomingSerial(), uidToHex(), tuning constants to preserve
- `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` — reference implementation for MFRC522 setup and read loop
- `arduino/bankongseton_rfid/secrets.h` — copy contents verbatim to new location

## Expected Output

- `arduino/bankongseton_r4/bankongseton_r4.ino` — complete RC522 firmware, ~250 lines, no PN532/LCD/APDU code
- `arduino/bankongseton_r4/secrets.h` — identical copy of old secrets.h
- `arduino/bankongseton_rfid/` — deleted

## Observability Impact

**What signals change after this task:**
- `Serial.println("BANKONGSETON RFID reader ready")` replaces the old `"BANKONGSETON NFC reader ready"` — ArduinoBridge startup detection string must be updated if it matches on this exact line (check `arduino_bridge.py` / any subprocess watcher)
- VersionReg halt check in `setup()` replaces `nfc.getFirmwareVersion()` — failure now prints `ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)` and halts; agent inspecting a non-starting reader should look for this line at Serial Monitor startup
- No APDU diagnostic lines (`APDU attempt N/5`, `APDU: inDataExchange failed`, etc.) — those are gone; an agent monitoring for APDU output will see nothing

**How a future agent inspects this task:**
1. Open Arduino Serial Monitor at 9600 baud after flashing `bankongseton_r4.ino`
2. Observe: `BANKONGSETON RFID reader ready` → RC522 SPI OK
3. Tap RFID card → observe `SCAN: FOUND uidLen=N uid=XXXX` + `HTTP: delivered — CARD|<uid>` → end-to-end confirmed
4. Check Flask log for `POST /api/arduino/card-read 200` as final delivery proof
5. Run `bash scripts/verify-m005-s01.sh` → all exits 0 confirms static contract

**Failure state visibility:**
- RC522 SPI fault: `ERROR: RC522 not found` + halt; no subsequent output
- WiFi disabled (no `SECRET_SSID`): `WiFi disabled — serial-only mode` then `CARD|<uid>` fallback lines
- HTTP failure: `HTTP: non-200 response: ...` then serial fallback
