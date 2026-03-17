# S01: RC522 Firmware Swap (R4 + R3) — Research

**Date:** 2026-03-17
**Requirements:** R026 (RC522 on R4), R027 (OLED on R4 — pin reservation only), R031 (RC522 cleanup on R3)

## Summary

This slice rewrites the R4 payment terminal firmware (PN532 → RC522) and renames its directory. The R3 firmware is already RC522-based and functionally clean; only its README requires correction. No backend changes are needed — `POST /api/arduino/card-read` already exists and handles RC522 UIDs identically to PN532 UIDs.

The R4 rewrite is a targeted substitution: pull out PN532 + LCD + APDU logic, wire in MFRC522 + OLED pin placeholder + Wire.h, keep all WiFi/heartbeat/deliver infrastructure unchanged. The R3 pattern (MFRC522 init, PICC_IsNewCardPresent, PICC_ReadCardSerial, HaltA, StopCrypto1) is the exact template to port to R4.

This slice is low-risk in practice: RC522 on UNO-class SPI is proven by R3, the SPI pinout is identical between R3 and R4, and the backend endpoint is already live.

## Recommendation

Port the R3 MFRC522 read loop directly into the R4 firmware base, replacing the PN532 scan block. Preserve all WiFi helpers (ensureWiFi, httpPostJson, httpPostCard, deliver, heartbeat timer) verbatim. Remove the entire LCD bit-bang driver and all APDU/NFC code. Add Wire.h include and OLED constant defines as a pin-reservation placeholder for S02 — but no `display.begin()` or rendering calls. Status feedback goes to Serial only in S01.

## Implementation Landscape

### Key Files

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — R4 source being rewritten. Contains PN532 init, LCD bit-bang driver (~200 lines), APDU retry loop, dual-path deliver(), WiFi helpers, heartbeat timer. All WiFi/heartbeat code is **reusable verbatim**.
- `arduino/bankongseton_rfid/secrets.h` — WiFi credentials + FLASK_HOST + SECRET_API_KEY. Format unchanged; copy as-is to new directory.
- `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` — R3 firmware. Already uses MFRC522. No PN532 references in code. **MFRC522 read loop here is the reference implementation to port.** No code changes needed.
- `arduino/bankongseton_nfc_r3/README.md` — Stale: title says "PN532 over SPI", body refers to "PN532 NFC module". Must be updated to reflect RC522.
- `backend/dashboard/web_app.py` lines 260–292 — `arduino_card_read()` endpoint. Already live, already emits `card_read` SocketIO event. No changes needed.

### What to Remove from R4 Firmware

| Remove | Lines / symbols |
|--------|----------------|
| `#include <PN532_SPI.h>`, `#include <PN532.h>` | Top includes |
| `PN532_SPI pn532spi(...)`, `PN532 nfc(...)` | Global instances |
| `nfc.begin()`, `nfc.getFirmwareVersion()`, `nfc.SAMConfig()` | setup() |
| `nfc.readPassiveTargetID(...)` | loop() scan |
| Entire APDU block (SAK check, inDataExchange loop, response parsing) | ~80 lines in loop() |
| `nfc.setRFField(0,0)` / `nfc.setRFField(0,1)` RF reset calls | 3 places |
| `httpPostNFC()` function | WiFi helpers section |
| `NFC_TIMEOUT_MS`, `APDU_MAX_RETRIES`, `APDU_RETRY_DELAY_MS`, `ENABLE_RF_FIELD_CYCLE` | Tuning section |
| Entire LCD bit-bang I2C driver (pcf8574_write, lcd_*, i2c_*) | ~200 lines |
| `#define LCD_SDA`, `#define LCD_SCL`, `#define LCD_ADDR`, etc. | Pin/config defines |
| `lcd_init()` in setup(), all `lcd_clear()`/`lcd_set_cursor()`/`lcd_print()` calls | setup() + loop() |

### What to Add to R4 Firmware

```cpp
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>            // OLED I2C bus — driver code added in S02
#include <WiFiS3.h>
#include "secrets.h"

// RC522 SPI (identical pinout to R3)
#define RC522_SS   10
#define RC522_RST   8
MFRC522 rfid(RC522_SS, RC522_RST);

// OLED placeholder — Adafruit SSD1306 128×64 via hardware I2C
// Adafruit_SSD1306 and Adafruit_GFX includes + display object added in S02
#define OLED_WIDTH  128
#define OLED_HEIGHT  64
#define OLED_ADDR  0x3C
// Wire.begin() is called in setup(); display.begin() added in S02
```

### MFRC522 Read Loop Pattern (from R3)

```cpp
// setup():
SPI.begin();
rfid.PCD_Init();
byte ver = rfid.PCD_ReadRegister(MFRC522::VersionReg);
// halt if ver == 0x00 || ver == 0xFF

// loop():
if (!rfid.PICC_IsNewCardPresent()) return;
if (!rfid.PICC_ReadCardSerial())   return;
String uidHex = uidToHex(rfid.uid.uidByte, rfid.uid.size);
deliver(uidHex, "CARD");          // WiFi POST → serial fallback
rfid.PICC_HaltA();
rfid.PCD_StopCrypto1();
delay(SCAN_COOLDOWN_MS);
```

`PICC_HaltA()` + `PCD_StopCrypto1()` are mandatory after every read to reset the MFRC522 state machine for the next card.

### What to Keep Verbatim from R4 Firmware

- `connectWiFi()` — no changes
- `ensureWiFi()` — no changes
- `httpPostJson()` — no changes
- `httpPostCard()` — no changes
- `deliver(value, "CARD")` call — only CARD prefix now; NFC prefix gone
- Heartbeat timer block (lastHeartbeatMs, HEARTBEAT_INTERVAL_MS, httpPostJson("/api/arduino/heartbeat"))
- `handleIncomingSerial()` — no changes (PING still needed for dashboard serial test)
- `uidToHex()` — no changes
- `PIEZO_PIN`, `SCAN_COOLDOWN_MS`, `MAX_RETRIES`, `RETRY_DELAY_MS`, `HTTP_TIMEOUT_MS`, `HEARTBEAT_INTERVAL_MS`
- Cooldown loop with `handleIncomingSerial()` polling

### R3 README Changes

Change `arduino/bankongseton_nfc_r3/README.md`:
- Title: `BANKONGSETON NFC Reader — Arduino UNO R3 (PN532 over SPI)` → `BANKONGSETON RFID Registration Reader — Arduino UNO R3 (RC522 over SPI)`
- Body: remove all PN532 references, update hardware table to show RC522 (SS→D10, RST→D8), remove "Adafruit PN532 / Adafruit BusIO" library rows, replace with "MFRC522 by GithubCommunity"
- The `.ino` itself is already correct — **no code changes needed**

### Directory Operations

```
# Create new directory with renamed files
mkdir arduino/bankongseton_r4/
cp arduino/bankongseton_rfid/secrets.h arduino/bankongseton_r4/secrets.h
# Write new bankongseton_r4.ino (do not rename — write fresh)
# Delete old directory after new one is verified
rm -rf arduino/bankongseton_rfid/
```

### Build Order

1. Write `arduino/bankongseton_r4/bankongseton_r4.ino` (new R4 firmware)
2. Write `arduino/bankongseton_r4/secrets.h` (copy content, no changes)
3. Update `arduino/bankongseton_nfc_r3/README.md` (PN532 → RC522 text)
4. Delete `arduino/bankongseton_rfid/` directory

Items 1–4 are independent. No backend work needed.

### Verification Approach

Contract verification (CI-able grep checks for `scripts/verify-m005-s01.sh`):

```bash
# Directory structure
test -f arduino/bankongseton_r4/bankongseton_r4.ino
test -f arduino/bankongseton_r4/secrets.h
! test -d arduino/bankongseton_rfid

# R4: correct reader library
grep -q '#include <MFRC522.h>' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: no PN532 references
! grep -qE 'PN532|pn532|Adafruit_PN532' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: WiFi path preserved
grep -q 'httpPostCard' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'heartbeat' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'ensureWiFi' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: OLED pin placeholder
grep -q '#include <Wire.h>' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'OLED_ADDR\|OLED_WIDTH\|SSD1306\|oled' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: APDU/NFC code gone
! grep -qE 'inDataExchange|SAMConfig|setRFField|httpPostNFC|NFC_TIMEOUT' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: MFRC522 read pattern present
grep -q 'PICC_IsNewCardPresent\|PICC_ReadCardSerial' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'PICC_HaltA\|PCD_StopCrypto1' arduino/bankongseton_r4/bankongseton_r4.ino

# R3: no PN532 references
! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/README.md
```

Integration verification (requires hardware): flash `bankongseton_r4.ino` to R4 WiFi, tap a physical RFID card → observe `POST /api/arduino/card-read 200` in Flask log. This confirms RC522 SPI on R4 WiFi hardware.

## Constraints

- `WiFiS3.h` is the correct WiFi library for UNO R4 WiFi (not `WiFi.h` or `WiFiNINA.h`). Already in use — keep as-is.
- `MFRC522` library requires SPI to be started before `PCD_Init()` — call `SPI.begin()` first in setup() (R3 already shows this pattern).
- `PICC_HaltA()` + `PCD_StopCrypto1()` must be called after every card read. Omitting these causes the next `PICC_IsNewCardPresent()` to always return true (card stuck in active state).
- `Wire.begin()` must be called in setup() even though no OLED driver code runs in S01 — it initializes the I2C bus so S02 can call `display.begin()` without re-initializing.
- OLED I2C address 0x3C is the standard SSD1306 address. Not in conflict with anything (old LCD was at 0x27 on bit-bang D6/D7 pins, now unused).
- R4 WiFi hardware I2C: SDA and SCL are on the dedicated I2C header (or A4/A5) — not D6/D7. The freed D6/D7 pins have no role in S01.
- `deliver()` function retains the `prefix` parameter signature but only ever called with `"CARD"` in the new firmware. The `"NFC"` branch in `deliver()` should be removed entirely (or `deliver` simplified — planner's call).

## Common Pitfalls

- **Forgetting `PICC_HaltA()` + `PCD_StopCrypto1()`** — results in the scan loop reading the same card forever. Pattern already in R3; copy exactly.
- **Keeping LCD calls without LCD driver** — removing the driver but leaving `lcd_clear()` / `lcd_print()` calls will fail to compile. All LCD calls must be removed or replaced with Serial equivalents.
- **Wire.begin() vs display.begin()** — S01 calls `Wire.begin()` in setup(); `display.begin()` is intentionally deferred to S02. The firmware must compile and run without Adafruit SSD1306/GFX libraries installed if S01 does not include those headers. Safest approach: include Wire.h and define OLED constants only; do not include Adafruit_SSD1306.h in S01 (that would require the library to be installed). Add a comment `// TODO S02: add Adafruit_SSD1306.h and display.begin() here`.
- **Stale verify script references** — the existing `verify-m003-s04.sh` checks `arduino/bankongseton_rfid/bankongseton_rfid.ino`. The new verify script must check `arduino/bankongseton_r4/bankongseton_r4.ino`.
