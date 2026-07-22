# BANKONGSETON NFC Reader — Arduino UNO R4 WiFi (Standalone / Powerbank)

This guide covers running the **UNO R4 WiFi** sketch (`arduino/bankongseton_r4/bankongseton_r4.ino`) without a USB cable to a PC — powered by a USB powerbank and delivering RFID taps over WiFi to the standalone cashier app.

> **Differences from the R3 sketch:** WiFi HTTP delivery instead of Serial, UNO R4 WiFi board (RA4M1 + ESP32-S3 coprocessor), 30-second heartbeat POST that keeps the powerbank alive and drives the cashier WiFi badge green.

---

## Hardware Required

| Component | Notes |
|-----------|-------|
| Arduino UNO R4 WiFi | Genuine Renesas RA4M1 + ESP32-S3 coprocessor board |
| RC522 RFID module | MFRC522-compatible SPI module |
| 128×64 OLED | SSD1306 I2C module, address `0x3C` |
| Piezo buzzer | Passive or active (both work with `tone()`) |
| USB powerbank | ≥10,000 mAh, ≥2 A USB-A output port, name-brand recommended (Anker, Xiaomi, Baseus) |

---

## Wiring

### RC522 RFID Module → Arduino UNO R4 WiFi

| RC522 Pin | Arduino UNO R4 WiFi |
|-----------|---------------------|
| NSS / CS  | D10                 |
| MOSI      | D11                 |
| MISO      | D12                 |
| SCK       | D13                 |
| VCC       | 3.3V                |
| GND       | GND                 |

### SSD1306 OLED → Arduino UNO R4 WiFi

| OLED Pin | Arduino UNO R4 WiFi |
|-----------------|---------------------|
| SDA             | SDA (hardware I2C)  |
| SCL             | SCL (hardware I2C)  |
| VCC             | 3.3V or 5V          |
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
| **MFRC522** | GithubCommunity | RFID reader driver |
| **Adafruit SSD1306** | Adafruit | OLED driver |
| **Adafruit GFX Library** | Adafruit | OLED graphics dependency |
| **QRCode** | Richard Moore | OLED QR rendering |
| **WiFiS3** | Arduino | Included with the Arduino UNO R4 board package — no separate install needed |

> `WiFiS3`, `Wire`, and `SPI` are included with the UNO R4 board package.

---

## secrets.h Configuration

Copy `arduino/bankongseton_r4/secrets.example.h` to `arduino/bankongseton_r4/secrets.h` and fill in each field:

| Field | Value | Notes |
|-------|-------|-------|
| `SECRET_SSID` | Your school WiFi SSID | 2.4 GHz network recommended; UNO R4 WiFi supports 2.4 GHz only |
| `SECRET_PASS` | WiFi password | |
| `FLASK_HOST` | `<cashier-pc-lan-ip>:5010` | Use the cashier PC's LAN IP and standalone cashier port. Never use `localhost`. |
| `SECRET_API_KEY` | API key string | **Must match `ARDUINO_API_KEY` in the Flask `.env` file exactly** — any mismatch returns HTTP 401 and the WiFi badge stays red |

**`HEARTBEAT_INTERVAL_MS`** is defined as a constant directly in `bankongseton_r4.ino` (not in `secrets.h`). If you need to change the heartbeat interval, edit the constant there and reflash.

> **`secrets.h` is gitignored** — never commit real credentials. The `.example` file is safe to commit.

---

## Flashing

1. Open **Arduino IDE**.
2. File → Open → navigate to `arduino/bankongseton_r4/bankongseton_r4.ino`.
3. Copy `secrets.example.h` to `secrets.h` in the same directory and fill in all fields (see [secrets.h Configuration](#secretsh-configuration) above).
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
   WiFi connected. IP: 192.168.x.x
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
| WiFi badge stays red — no heartbeat in server logs | Heartbeat not reaching server; WiFi may not be connected | Check SSID/password, verify `FLASK_HOST`, and look for `WiFi connected` at boot |
| WiFi badge stays red — wrong port | `FLASK_HOST` uses the wrong listener | Change to `<cashier-pc-lan-ip>:5010` in `secrets.h` and reflash |
| WiFi never connects | Wrong SSID or password, or 5 GHz network | Verify credentials; ensure network is 2.4 GHz |
| OLED blank | Wrong I2C address or wiring | Confirm SDA/SCL wiring and address `0x3C`; run an I2C scanner if needed |
| Powerbank shuts off within minutes | Bank has aggressive auto-shutoff | Use a name-brand bank; verify the 30-second heartbeat is firing in Serial Monitor |
| RFID tap not delivered to server | WiFi connected but wrong Flask host or API key | Confirm `FLASK_HOST` is the cashier PC's LAN IP on port 5010, not localhost, and verify the API key |

---

## Pin Summary

| Pin | Function |
|-----|----------|
| D8  | Piezo buzzer |
| D9  | RC522 reset |
| D10 | RC522 NSS/CS (SPI) |
| D11 | SPI MOSI (hardware, shared) |
| D12 | SPI MISO (hardware, shared) |
| D13 | SPI SCK (hardware, shared) |
| SDA | SSD1306 OLED SDA |
| SCL | SSD1306 OLED SCL |
| 3.3V | RC522 VCC / OLED VCC |
