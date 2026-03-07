# BANKONGSETON NFC Reader — Arduino UNO R3 (PN532 over SPI)

This sketch runs on an **Arduino UNO R3** with a **PN532 NFC module** connected via SPI. It reads NFC card UIDs and sends them over Serial for the Python `ArduinoBridge` to process payments.

> **Differences from the R4 WiFi sketch:** Serial-only delivery (no HTTP/WiFi), PN532 NFC module instead of MFRC522 RFID, UNO R3 pinout.

---

## Hardware Required

| Component | Notes |
|-----------|-------|
| Arduino UNO R3 | Any genuine or clone UNO R3 |
| PN532 NFC/RFID module | Adafruit PN532 shield/breakout, or compatible |
| 16x2 LCD with PCF8574 I2C backpack | Most "I2C LCD" modules use PCF8574 |
| Piezo buzzer | Passive or active (both work with `tone()`) |

---

## Wiring

### PN532 NFC Module → Arduino UNO R3

> **SPI mode selection:** On the Adafruit PN532 board, set the DIP switches to **SEL0 = LOW (0), SEL1 = HIGH (1)** before wiring.

| PN532 Pin | Arduino UNO R3 |
|-----------|----------------|
| NSS / CS  | D10            |
| MOSI      | D11            |
| MISO      | D12            |
| SCK       | D13            |
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
| **Adafruit PN532** | Adafruit | NFC reader driver |
| **Adafruit BusIO** | Adafruit | Required dependency of Adafruit PN532 |

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
| D9  | Piezo buzzer |
| D10 | PN532 NSS/CS (SPI) |
| D11 | SPI MOSI (hardware, shared) |
| D12 | SPI MISO (hardware, shared) |
| D13 | SPI SCK (hardware, shared) |
| 3.3V | PN532 VCC |
| 5V  | LCD backpack VCC |
