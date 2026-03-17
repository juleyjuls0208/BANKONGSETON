# BANKONGSETON RFID Registration Reader — Arduino UNO R3 (RC522 over SPI)

Reads physical RFID cards via RC522 over SPI and emits `CARD|<UID-HEX>` over Serial for the Python `ArduinoBridge` to process card registrations.

> **Differences from the R4 WiFi sketch:** Serial-only delivery (no HTTP/WiFi), RC522 RFID module over SPI, UNO R3 pinout.

---

## Hardware Required

| Component | Notes |
|-----------|-------|
| Arduino UNO R3 | Any genuine or clone UNO R3 |
| RC522 RFID module | Any standard RC522 breakout board (3.3V) |
| 16x2 LCD with PCF8574 I2C backpack | Most "I2C LCD" modules use PCF8574 |
| Piezo buzzer | Passive or active (both work with `tone()`) |

---

## Wiring

### RC522 RFID Module → Arduino UNO R3

| RC522 Pin | Arduino UNO R3 |
|-----------|----------------|
| SDA/SS    | D10 (RC522_SS) |
| MOSI      | D11            |
| MISO      | D12            |
| SCK       | D13            |
| RST       | D8 (RC522_RST) |
| VCC       | 3.3V           |
| GND       | GND            |

### LCD 16x2 with PCF8574 I2C Backpack → Arduino UNO R3

> **Note:** Hardware I2C pins A4/A5 are **not used**. The LCD uses software (bit-bang) I2C on D6/D7, leaving A4/A5 free for sensors or other peripherals.

| LCD Backpack Pin | Arduino UNO R3 |
|-----------------|----------------|
| SDA             | D6 (software)  |
| SCL             | D7 (software)  |
| VCC             | 5V             |
| GND             | GND            |

### Piezo Buzzer → Arduino UNO R3

| Piezo Pin | Arduino UNO R3 |
|-----------|----------------|
| +         | D9             |
| −         | GND            |

---

## Required Libraries

Install via **Arduino IDE → Tools → Manage Libraries…**:

| Library | Author | Notes |
|---------|--------|-------|
| **MFRC522** | GithubCommunity (miguelbalboa/rfid) | RFID reader driver |

> **No extra library for LCD.** The sketch uses an inline bit-bang I2C + PCF8574 driver (~70 lines) — nothing to install.

---

## LCD I2C Address

The default PCF8574 backpack address is **`0x27`**.

If the LCD is not displaying anything:
1. Try changing `LCD_ADDR` in the sketch to `0x3F`
2. Or run an I2C scanner sketch to find the actual address

```cpp
// In bankongseton_nfc_r3.ino — change this line:
#define LCD_ADDR  0x27   // try 0x3F if LCD doesn't work
```

---

## Serial Output Format

The sketch sends one line per card tap over Serial at **9600 baud**:

```
CARD|AABBCCDD
```

- `AABBCCDD` is the card UID in **uppercase hexadecimal** (typically 8 hex chars for 4-byte MIFARE cards, up to 14 chars for 7-byte UIDs)
- This format is consumed by the Python `ArduinoBridge` class via its `_read_serial_line` regex

At startup, the sketch also prints:
```
BANKONGSETON NFC reader ready
```
This line is used by `ArduinoBridge` to detect that the Arduino has booted.

---

## Pin Summary

| Pin | Function |
|-----|----------|
| D6  | LCD SDA (software I2C) |
| D7  | LCD SCL (software I2C) |
| D8  | RC522 RST |
| D9  | Piezo buzzer |
| D10 | RC522 SDA/SS (SPI) |
| D11 | SPI MOSI (hardware, shared) |
| D12 | SPI MISO (hardware, shared) |
| D13 | SPI SCK (hardware, shared) |
| 3.3V | RC522 VCC |
| 5V  | LCD backpack VCC |
