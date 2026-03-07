---
phase: quick-2
plan: 01
subsystem: arduino-hardware
tags: [arduino, nfc, pn532, spi, serial, uno-r3]
dependency_graph:
  requires: []
  provides: [arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino]
  affects: [ArduinoBridge serial reader]
tech_stack:
  added: [Adafruit_PN532, Adafruit BusIO, inline-bit-bang-I2C]
  patterns: [SPI hardware, software I2C bit-bang, PCF8574 LCD driver]
key_files:
  created:
    - arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
    - arduino/bankongseton_nfc_r3/README.md
  modified: []
decisions:
  - Inline bit-bang I2C used for LCD (no SoftwareWire library required — avoids compatibility issues)
  - PCF8574 default address 0x27 with 0x3F documented as fallback
  - Adafruit_PN532 SPI mode via single-pin constructor nfc(PN532_SS)
  - No WiFi, no HTTP, no secrets.h — UNO R3 is serial-only by design
metrics:
  duration: 2min
  completed: 2026-03-07
  tasks: 2
  files: 2
---

# Phase quick-2 Plan 01: Arduino UNO R3 PN532 NFC Reader Summary

**One-liner:** PN532 SPI NFC reader for Arduino UNO R3 with inline bit-bang I2C LCD driver and serial-only `CARD|UID` output for ArduinoBridge.

---

## What Was Built

New `arduino/bankongseton_nfc_r3/` directory with two files targeting Arduino UNO R3 — replacing the R4 WiFi+MFRC522 sketch with a serial-only PN532 variant.

---

## Files Created

| File | Purpose |
|------|---------|
| `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` | Main Arduino sketch — PN532 SPI reader, Serial output, LCD, piezo |
| `arduino/bankongseton_nfc_r3/README.md` | Hardware wiring guide, library install, serial format docs |

---

## Key Implementation Decisions

### 1. Inline bit-bang I2C for LCD

The plan offered several options for software I2C (SoftwareWire library, SoftI2CMaster, or inline bit-bang). **Chose inline bit-bang** (~70 lines):
- `i2c_start()`, `i2c_write_byte()`, `i2c_stop()` using open-drain pattern on D6/D7
- `pcf8574_write()` targets the 8-bit PCF8574 expander at address `0x27`
- `lcd_send()` implements HD44780 4-bit mode via PCF8574 bit layout
- Zero extra libraries required — avoids Arduino Library Manager version conflicts

### 2. Adafruit_PN532 SPI constructor

```cpp
Adafruit_PN532 nfc(PN532_SS);  // SPI mode: pass only SS pin
```
`readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLen, 500)` used for ISO14443A (MIFARE, NTAG, etc.) cards with 500ms timeout — blocks during wait, so no extra delay is needed in loop.

### 3. Serial output format

```cpp
Serial.print("CARD|");
Serial.println(uidHex);  // uppercase hex e.g. "A3B2C1D0"
```
Matches `ArduinoBridge._read_serial_line` regex exactly (per STATE.md decision [Phase 18-02]).

### 4. No WiFi / No secrets.h

R3 has no WiFi hardware. Sketch includes only `SPI.h` and `Adafruit_PN532.h`. No `WiFiS3.h`, no `MFRC522.h`, no `secrets.h`.

---

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 — .ino sketch | `4057bcd` | feat(quick-2-01): add PN532 SPI NFC sketch for Arduino UNO R3 |
| Task 2 — README | `dac7eea` | docs(quick-2-01): add hardware README for UNO R3 PN532 NFC setup |

---

## Deviations from Plan

None — plan executed exactly as written. Chose inline bit-bang I2C (the "simplest correct approach" recommended in the plan) over external SoftwareWire library.

---

## Self-Check

- [x] `arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` — FOUND
- [x] `arduino/bankongseton_nfc_r3/README.md` — FOUND
- [x] `4057bcd` commit — FOUND
- [x] `dac7eea` commit — FOUND
- [x] No `#include <WiFiS3.h>` in sketch
- [x] No `#include <MFRC522.h>` in sketch
- [x] `CARD|` serial output present
- [x] Pin defines: PN532_SS=10, PIEZO_PIN=9, LCD_SDA=6, LCD_SCL=7

## Self-Check: PASSED
