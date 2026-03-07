---
phase: quick-2
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
autonomous: true
requirements: [QUICK-2]
must_haves:
  truths:
    - "Arduino sketch compiles for UNO R3 (no WiFi, no WiFiS3.h dependency)"
    - "PN532 module read via SPI with correct pin assignments (NSS=D10, MOSI=D11, MISO=D12, SCK=D13)"
    - "Valid NFC card tap outputs CARD|{UID} over Serial at 9600 baud"
    - "Piezo buzzer on D9 beeps on successful scan"
    - "LCD shows card UID and status using software I2C on SCL=D7, SDA=D6"
  artifacts:
    - path: "arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino"
      provides: "UNO R3 NFC reader sketch using PN532 over SPI"
  key_links:
    - from: "PN532 SPI read"
      to: "Serial.print(CARD|{uid})"
      via: "deliverUID() function"
      pattern: "CARD\\|"
    - from: "SoftwareWire/software I2C"
      to: "LCD display"
      via: "LiquidCrystal_I2C initialized on SDA=6, SCL=7"
---

<objective>
Create a new Arduino sketch `bankongseton_nfc_r3.ino` for Arduino UNO R3 with PN532 NFC module over SPI. This replaces the existing R4 WiFi + MFRC522 sketch.

Purpose: UNO R3 has no WiFi — delivery is serial-only. The Python backend (ArduinoBridge) reads `CARD|{UID}` lines from serial to handle NFC card payments.
Output: A fully self-contained `.ino` sketch and companion `README.md` in a new `arduino/bankongseton_nfc_r3/` directory.
</objective>

<execution_context>
@C:/Users/admin/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@arduino/bankongseton_rfid/bankongseton_rfid.ino

Key decisions from STATE.md:
- [Phase 18-02]: CARD|UID serial fallback format matches ArduinoBridge._read_serial_line regex exactly
- [Phase 18-02]: HTTP/1.0 with Content-Length required for Flask (irrelevant here — R3 is serial-only)
- R3 has no WiFi; serial is the ONLY delivery path (no HTTP fallback logic needed)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write PN532 SPI + LCD sketch for UNO R3</name>
  <files>arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino</files>
  <action>
Create a NEW sketch at `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` from scratch.
Do NOT copy the R4 WiFi sketch — R3 is serial-only, no WiFiS3.h.

**Library requirements:**
- `Adafruit_PN532` (by Adafruit) for NFC — SPI mode
- `SPI.h` (built-in)
- `Wire.h` NOT used for hardware I2C (A4/A5 are occupied/unavailable)
- `SoftwareWire` library for software I2C to LCD (SCL=D7, SDA=D6)
  - OR use `SoftI2CMaster` / `TwoWire` on custom pins via `LiquidCrystal_I2C` with SoftwareWire
  - Recommended: use `SoftwareWire` library + `LiquidCrystal_I2C` ported to use SoftwareWire
  - Alternative (simpler, no extra lib): use `LiquidCrystal_PCF8574` with `SoftwareWire` wrapper
  - Best fit for Arduino IDE: Use `SoftwareWire` library by Testato (Arduino Library Manager) + `hd44780` with `hd44780_I2Cexp` backend using `SoftwareWire` — OR just bit-bang a simple `softI2C_write` helper inline

**Simplest correct approach for LCD with software I2C:**
Use `SoftI2CMaster.h` (part of `SoftI2CMaster` library) or implement a minimal inline bit-bang I2C + PCF8574 driver (20-30 lines). This avoids library compatibility issues.

Implement inline bit-bang I2C + LCD 16x2 with PCF8574 I2C backpack:
- `i2c_start()`, `i2c_write(byte)`, `i2c_stop()` functions using D6=SDA, D7=SCL
- `lcd_send(byte data, bool rs)` for PCF8574 expander (standard 4-bit HD44780 protocol)
- `lcd_init()`, `lcd_print(const char*)`, `lcd_set_cursor(col, row)`
- PCF8574 address: 0x27 (default for most LCD I2C backpacks; document this)

**Pin assignments (define at top, named constants):**
```cpp
#define PN532_SS   10   // SPI NSS/CS
#define PIEZO_PIN   9   // Buzzer
#define LCD_SDA     6   // Software I2C data
#define LCD_SCL     7   // Software I2C clock
// SPI bus: MOSI=11, MISO=12, SCK=13 (hardware SPI, no defines needed)
```

**PN532 SPI initialization:**
```cpp
Adafruit_PN532 nfc(PN532_SS);  // SPI mode: only SS pin passed
// In setup(): nfc.begin(); nfc.SAMConfig();
```

**UID reading (ISO14443A cards — MIFARE, NTAG, etc.):**
```cpp
uint8_t uid[7], uidLen;
bool found = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLen, 500);
```

**UID to hex string:**
Convert uid[0..uidLen-1] to uppercase hex string, e.g. "A3B2C1D0".

**Serial output (EXACT format — must match ArduinoBridge regex):**
```cpp
Serial.print("CARD|");
Serial.println(uidHex);
```
Baud rate: 9600 (match existing ArduinoBridge configuration).

**Piezo beep on successful scan:**
- `tone(PIEZO_PIN, 1000, 200)` — 1kHz, 200ms beep

**LCD behavior:**
- Line 0: "BANKONGSETON" (or "NFC READER")
- On card detected — Line 1: uid (first 8 chars if long)
- On idle — Line 1: "Waiting..." or "Tap card..."
- Clear and update on each scan

**Scan cooldown:** 1500ms delay after read to prevent double-scans.

**setup():**
1. Serial.begin(9600)
2. SPI.begin() — hardware SPI
3. nfc.begin() + nfc.SAMConfig()
4. Piezo test beep (brief, 100ms) to confirm hardware on startup
5. LCD init + show "BANKONGSETON" / "Ready..."
6. Serial.println("BANKONGSETON NFC reader ready") — for ArduinoBridge startup detection

**loop():**
1. Try readPassiveTargetID with 500ms timeout
2. If card found: convert UID, print CARD|{uid}, beep, update LCD, delay(1500)
3. If no card: continue loop (no delay needed, readPassiveTargetID blocks for timeout)

**Comments:** Add clear section headers, hardware wiring table in file header comment.
Include Arduino Library Manager names so user knows what to install.

**Do NOT include WiFi, HTTP, or secrets.h** — R3 is serial-only.
  </action>
  <verify>
    <automated>
      File exists: arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
      grep -c "CARD|" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
      grep -c "Adafruit_PN532" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
      grep -c "PN532_SS.*10\|10.*NSS\|SS.*10" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
      Confirm no WiFiS3.h or MFRC522.h includes
    </automated>
  </verify>
  <done>
    Sketch file exists with: correct pin defines (SS=10, PIEZO=9, SDA=6, SCL=7), Adafruit_PN532 SPI init, Serial output "CARD|{UID}" at 9600 baud, piezo beep, LCD output via software I2C bit-bang. No WiFi dependencies.
  </done>
</task>

<task type="auto">
  <name>Task 2: Write hardware README for R3 NFC setup</name>
  <files>arduino/bankongseton_nfc_r3/README.md</files>
  <action>
Create `arduino/bankongseton_nfc_r3/README.md` documenting:

1. **Hardware required:**
   - Arduino UNO R3
   - Adafruit PN532 NFC/RFID Shield or breakout board
   - 16x2 LCD with PCF8574 I2C backpack
   - Piezo buzzer (passive or active)

2. **Wiring table** (exact pin-to-pin):
   | PN532   | Arduino UNO R3 |
   |---------|----------------|
   | NSS/CS  | D10            |
   | MOSI    | D11            |
   | MISO    | D12            |
   | SCK     | D13            |
   | VCC     | 3.3V           |
   | GND     | GND            |

   | LCD I2C Backpack | Arduino UNO R3 |
   |-----------------|----------------|
   | SDA             | D6 (software)  |
   | SCL             | D7 (software)  |
   | VCC             | 5V             |
   | GND             | GND            |

   | Piezo | Arduino UNO R3 |
   |-------|----------------|
   | +     | D9             |
   | -     | GND            |

   **Note:** PN532 SPI mode selection — on Adafruit PN532 board, set switches: SEL0=LOW (0), SEL1=HIGH (1) for SPI mode.
   **Note:** Hardware I2C pins A4/A5 are NOT used (they are available but LCD uses software I2C on D6/D7 to free A4/A5).

3. **Required Arduino Libraries** (install via Library Manager):
   - `Adafruit PN532` by Adafruit
   - `Adafruit BusIO` by Adafruit (dependency of PN532)

   Note: LCD uses inline bit-bang I2C — no extra library needed.

4. **LCD I2C address:** Default is `0x27`. If LCD doesn't work, try `0x3F`. Change `LCD_ADDR` define in the sketch.

5. **Serial output format:** `CARD|AABBCCDD` at 9600 baud — consumed by Python `ArduinoBridge`.

6. **Differences from R4 WiFi sketch:** Serial-only (no HTTP/WiFi), PN532 NFC instead of MFRC522 RFID, UNO R3 pinout.
  </action>
  <verify>
    <automated>File exists: arduino/bankongseton_nfc_r3/README.md</automated>
  </verify>
  <done>README.md exists with wiring table, library list, LCD I2C address note, and serial format documentation.</done>
</task>

</tasks>

<verification>
- `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` exists and contains no WiFiS3.h, no MFRC522.h
- `grep "CARD|" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` returns a match
- `grep "Adafruit_PN532" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` returns a match  
- `grep "PN532_SS\b" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` shows value 10
- `grep "PIEZO_PIN\b" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` shows value 9
- `grep "LCD_SDA\b" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` shows value 6
- `grep "LCD_SCL\b" arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` shows value 7
- README.md exists with wiring table
</verification>

<success_criteria>
- New sketch at `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` targeting UNO R3 (no WiFi)
- PN532 initialized over SPI with NSS=D10
- On card tap: `CARD|{UPPERCASE_HEX_UID}` printed to Serial at 9600 baud
- Piezo beep on D9 confirms scan
- LCD on D6/D7 software I2C shows card UID
- README documents exact wiring and library install steps
</success_criteria>

<output>
After completion, create `.planning/quick/2-arduino-uno-r3-pn532-nfc-code-with-spi-p/2-SUMMARY.md` summarizing:
- Files created
- Key implementation decisions (e.g., inline bit-bang I2C for LCD, Adafruit_PN532 SPI mode)
- Any deviations from plan
</output>
