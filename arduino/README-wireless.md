# BANKONGSETON NFC Reader — Arduino UNO R4 WiFi (Standalone / Powerbank)

This guide covers running the **UNO R4 WiFi** sketch (`arduino/bankongseton_rfid/bankongseton_rfid.ino`) without a USB cable to a PC — powered by a USB powerbank and delivering NFC taps over WiFi to the Flask dashboard server.

> **Differences from the R3 sketch:** WiFi HTTP delivery instead of Serial, UNO R4 WiFi board (RA4M1 + ESP32-S3 coprocessor), 30-second heartbeat POST that keeps the powerbank alive and drives the cashier WiFi badge green.

---

## Hardware Required

| Component | Notes |
|-----------|-------|
| Arduino UNO R4 WiFi | Genuine Renesas RA4M1 + ESP32-S3 coprocessor board |
| PN532 NFC/RFID module | Adafruit PN532 shield/breakout, or compatible SPI module |
| 16×2 LCD with PCF8574 I2C backpack | Most "I2C LCD" modules use PCF8574 |
| Piezo buzzer | Passive or active (both work with `tone()`) |
| USB powerbank | ≥10,000 mAh, ≥2 A USB-A output port, name-brand recommended (Anker, Xiaomi, Baseus) |

---

## Wiring

### PN532 NFC Module → Arduino UNO R4 WiFi

> **SPI mode selection:** On the Adafruit PN532 board, set the DIP switches to **SEL0 = LOW (0), SEL1 = HIGH (1)** before wiring.

| PN532 Pin | Arduino UNO R4 WiFi |
|-----------|---------------------|
| NSS / CS  | D10                 |
| MOSI      | D11                 |
| MISO      | D12                 |
| SCK       | D13                 |
| VCC       | 3.3V                |
| GND       | GND                 |

### LCD 16×2 with PCF8574 I2C Backpack → Arduino UNO R4 WiFi

> **Note:** The LCD uses software (bit-bang) I2C on D6/D7, leaving the hardware I2C pins free for other peripherals.

| LCD Backpack Pin | Arduino UNO R4 WiFi |
|-----------------|---------------------|
| SDA             | D6 (software I2C)   |
| SCL             | D7 (software I2C)   |
| VCC             | 5V                  |
| GND             | GND                 |

### Piezo Buzzer → Arduino UNO R4 WiFi

| Piezo Pin | Arduino UNO R4 WiFi |
|-----------|---------------------|
| +         | D9                  |
| −         | GND                 |

---

## Required Libraries

Install via **Arduino IDE → Tools → Manage Libraries…**:

| Library | Author | Notes |
|---------|--------|-------|
| **Adafruit PN532** | Adafruit | NFC reader driver |
| **Adafruit BusIO** | Adafruit | Required dependency of Adafruit PN532 |
| **WiFiS3** | Arduino | Included with the Arduino UNO R4 board package — no separate install needed |

> **No extra library for LCD.** The sketch uses an inline bit-bang I2C + PCF8574 driver — nothing to install.

---

## secrets.h Configuration

Copy `arduino/bankongseton_rfid/secrets.h.example` to `arduino/bankongseton_rfid/secrets.h` and fill in each field:

| Field | Value | Notes |
|-------|-------|-------|
| `SECRET_SSID` | Your school WiFi SSID | 2.4 GHz network recommended; UNO R4 WiFi supports 2.4 GHz only |
| `SECRET_PASS` | WiFi password | |
| `FLASK_HOST` | `<server-ip>:5003` | **Must use port 5003** — the dashboard server listens on 5003 and hosts both `/api/arduino/card-read` and `/api/arduino/heartbeat`. Port 5000 is wrong. |
| `SECRET_API_KEY` | API key string | **Must match `ARDUINO_API_KEY` in the Flask `.env` file exactly** — any mismatch returns HTTP 401 and the WiFi badge stays red |

**`HEARTBEAT_INTERVAL_MS`** is defined as a constant directly in `bankongseton_rfid.ino` (not in `secrets.h`). If you need to change the heartbeat interval, edit the constant there and reflash.

> **`secrets.h` is gitignored** — never commit real credentials. The `.example` file is safe to commit.

---

## Flashing

1. Open **Arduino IDE**.
2. File → Open → navigate to `arduino/bankongseton_rfid/bankongseton_rfid.ino`.
3. Copy `secrets.h.example` to `secrets.h` in the same directory and fill in all fields (see [secrets.h Configuration](#secretsh-configuration) above).
4. Connect the Arduino UNO R4 WiFi to your PC via USB.
5. Tools → Board → select **"Arduino UNO R4 WiFi"**.
6. Tools → Port → select the correct COM port.
7. Sketch → Upload. Wait for "Done uploading."
8. Disconnect the USB cable and connect the powerbank.

---

## Verification

After powering on from the powerbank:

1. **Open Serial Monitor** at **9600 baud** (while USB cable is connected during initial test — remove it once confirmed working).
2. Expect within a few seconds:
   ```
   WiFi connected — IP: 100.120.x.x
   ```
3. Every 30 seconds during idle, expect:
   ```
   HTTP: POST /api/arduino/heartbeat
   ```
   (logged by `httpPostJson` on each heartbeat attempt)
4. **Open the cashier UI** in a browser — the **WiFi badge** (top-right of the page) should turn **green** within 30 seconds of the first heartbeat reaching the server.

If the badge stays red after 30 seconds, see [Troubleshooting](#troubleshooting).

---

## Powerbank Selection

| Spec | Minimum | Recommended |
|------|---------|-------------|
| Capacity | 10,000 mAh | 20,000 mAh for all-day use |
| USB-A output current | 2 A | 2.4 A or higher |
| Brand | Name-brand only | Anker, Xiaomi, Baseus |

**Why these specs matter:**

- **2 A minimum:** Some no-name banks advertise 2 A but cut out at <1 A under load. The Arduino UNO R4 WiFi draws ~180–200 mA at baseline; the PN532 and LCD add ~50–80 mA. A weak port may brownout on the WiFi burst.
- **10,000 mAh minimum:** Provides ≈8 hours at 200 mA average draw — enough for a full school day.
- **Name-brand:** Off-brand banks with aggressive auto-shutoff circuitry interpret the Arduino's normal idle current as "no device" and cut power after 30–60 seconds. The 30-second heartbeat POST adds a current burst (~300 mA for the WiFi transmit) that keeps quality banks alive, but cannot overcome a bank with a fundamentally broken keep-alive threshold.
- **Avoid:** No-name "10000mAh" banks sold without a brand name, banks with a single USB-A port rated at 1 A, and power-delivery-only banks with no USB-A port.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| WiFi badge stays red after 30+ seconds | `SECRET_API_KEY` in `secrets.h` doesn't match `ARDUINO_API_KEY` in Flask `.env` | Re-check both values; reflash after fixing `secrets.h` |
| WiFi badge stays red — Serial Monitor shows HTTP 401 | API key mismatch (same as above) | Same fix |
| WiFi badge stays red — no `HTTP: POST` line in Serial Monitor | Heartbeat not reaching server; WiFi may not be connected | Check SSID/password, check Arduino is on school LAN, look for `WiFi connected` at boot |
| WiFi badge stays red — wrong port | `FLASK_HOST` uses port 5000 instead of 5003 | Change to `<ip>:5003` in `secrets.h` and reflash |
| WiFi never connects | Wrong SSID or password, or 5 GHz network | Verify credentials; ensure network is 2.4 GHz |
| LCD blank | Wrong I2C address | Change `LCD_ADDR` in sketch to `0x3F` (default is `0x27`); or run an I2C scanner sketch |
| Powerbank shuts off within minutes | Bank has aggressive auto-shutoff | Use a name-brand bank; verify the 30-second heartbeat is firing in Serial Monitor |
| NFC tap not delivered to server | WiFi connected but wrong Flask host | Confirm `FLASK_HOST` IP is the server machine's LAN IP, not localhost |

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
