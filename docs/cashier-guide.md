# Cashier Guide

## Overview

The cashier POS is a web application served on port 5003 (`http://<server-ip>:5003/cashier/`). A cashier opens it in a browser on the canteen PC, connects to the Arduino RFID reader via USB, selects the products a student has chosen, and completes the transaction by prompting the student to tap their RFID money card on the reader.

Payments are deducted instantly from the student's balance in Google Sheets and a transaction record is written to the Transactions Log sheet.

---

## Accessing the Cashier POS

**URL:** `http://localhost:5003/cashier/login`

**Credentials:**

| Field    | Value        |
|----------|--------------|
| Username | `cashier`    |
| Password | `cashier123` |

> ⚠️ **Security Warning:** These credentials are **hardcoded** in
> `backend/dashboard/cashier/cashier_routes.py` (line 69). They must be
> changed to a strong, unique password before deploying to production.
> Leaving the default credentials in place gives anyone on the network
> full access to the cashier POS and the ability to deduct student balances.

---

## Hardware Setup

### Required Hardware

- Arduino Uno (or compatible AVR-based board)
- RC522 RFID/NFC module (ISO 14443A, 13.56 MHz)
- USB cable — Type-A to Type-B (Arduino to PC)
- RFID cards/tags registered to students in the system

### Arduino Wiring

Wire the RC522 module to the Arduino using the SPI bus:

| RC522 Pin | Arduino Pin | Notes                                          |
|-----------|-------------|------------------------------------------------|
| SDA (SS)  | Pin 10      | Chip select                                    |
| SCK       | Pin 13      | SPI clock                                      |
| MOSI      | Pin 11      | SPI data out (Arduino → RC522)                 |
| MISO      | Pin 12      | SPI data in (RC522 → Arduino)                  |
| RST       | Pin 9       | Reset                                          |
| VCC       | **3.3V**    | ⚠️ **NOT 5V** — 5V will permanently damage the RC522 module |
| GND       | GND         |                                                |

> ⚠️ **Critical:** The RC522 is a **3.3V** device. Connecting VCC to the
> Arduino's 5 V pin will destroy the module.

### Arduino Firmware

The Arduino must be flashed with firmware that reads RC522 cards and writes
each scanned UID to the serial port in this exact format:

```
<CARD|ABCD1234>
```

- `ABCD1234` is the 8-character hexadecimal card UID (uppercase or lowercase).
- The angle brackets and pipe character are required delimiters.
- Serial settings: **9600 baud, 8N1**.

The `ArduinoBridge` in `backend/dashboard/arduino_bridge.py` parses this
format. Any deviation in the output format will cause card reads to fail.

---

## Connecting to the Arduino

1. Plug the Arduino into the computer running the dashboard server via USB.
2. Open the cashier POS in the browser and log in.
3. In the connection panel, click **Scan Ports** — this calls
   `GET /cashier/api/ports` and returns all available serial ports.
4. Select the correct COM port from the dropdown (e.g. `COM3` on Windows,
   `/dev/ttyUSB0` on Linux).
5. Click **Connect** — this calls `POST /cashier/api/connect-arduino` with
   `{"port": "COM3"}`.
6. The status indicator turns green when the Arduino is connected and ready.

---

## Processing a Sale

### Step-by-Step Transaction Flow

1. After login, the product grid loads automatically via `GET /cashier/api/products`.
2. Cashier clicks each product the student is purchasing; items are added to
   the cart and a running total is displayed.
3. When ready, cashier clicks **Charge**.
4. The browser calls `POST /cashier/api/process-sale` with the cart contents:
   ```json
   { "items": [{"name": "Rice", "price": 20, "qty": 1}], "total": 20.0 }
   ```
5. The server stores the pending transaction in the Flask session and emits
   the WebSocket event **`cashier_request_card`**.
6. The POS UI shows a **"Please tap card"** prompt to the cashier.
7. The student taps their RFID money card on the Arduino reader.
8. The Arduino sends `<CARD|ABCD1234>` over serial at **9600 baud**.
9. `ArduinoBridge` (background thread) reads the UID with a **5-second
   timeout** (hardcoded in `arduino_bridge.py`).
10. The UID is delivered to the browser via the WebSocket connection.
11. The browser calls `POST /cashier/api/complete-sale` with the card UID:
    ```json
    { "card_uid": "ABCD1234" }
    ```
12. The server:
    - Validates the UID format (`^[0-9A-Fa-f]{8}$`).
    - Looks up the card in the **Money Accounts** Google Sheet.
    - Checks the student has sufficient balance.
    - Deducts the sale total from the **Balance** column (column C).
    - Writes a transaction row to the **Transactions Log** sheet.
    - Sends an email receipt via `EmailService` (if configured).
13. The POS displays **"Sale Complete"** with the student's remaining balance.

### Transaction Record Written to Sheets

Each completed sale appends a 7-column row to the Transactions Log sheet
(note: no `BalanceBefore` in this write path — it is only present in the
admin Load Balance write path):

| Column | Field            | Example Value                     |
|--------|------------------|-----------------------------------|
| 1      | Timestamp        | `2026-02-28T10:30:00`             |
| 2      | MoneyCardNumber  | `ABCD1234`                        |
| 3      | TransactionType  | `Purchase`                        |
| 4      | Amount           | `-25.0` (negative = deduction)    |
| 5      | BalanceAfter     | `75.0`                            |
| 6      | Status           | `Success`                         |
| 7      | ItemsJson        | `[{"name":"Rice","price":20}]`    |

---

## Cashier API Endpoints

All endpoints are under the `/cashier/` prefix.

| Method | Path                            | Auth Required | Description                                      |
|--------|---------------------------------|---------------|--------------------------------------------------|
| GET    | `/cashier/login`                | No            | Renders the cashier login page                   |
| POST   | `/cashier/api/login`            | No            | Authenticates with hardcoded cashier credentials |
| POST   | `/cashier/api/logout`           | Session       | Logs out and clears the cashier session          |
| GET    | `/cashier/api/ports`            | Session       | Returns list of available serial COM ports       |
| POST   | `/cashier/api/connect-arduino`  | Session       | Connects to the specified serial port            |
| GET    | `/cashier/api/products`         | JWT + Session | Returns active products for the POS grid         |
| POST   | `/cashier/api/process-sale`     | Session       | Initiates a sale; triggers card-read request     |
| POST   | `/cashier/api/complete-sale`    | Session       | Finalises a sale using the scanned card UID      |

---

## Product Categories

Products in the POS grid are grouped by **Category**. Categories are defined
when products are added in the admin dashboard. Standard categories include
`Food`, `Drinks`, and `Snacks`, but any category name can be used. Only
products with `Active = TRUE` in the Products sheet appear in the grid.

---

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| **Product grid is empty** | Products sheet has no active rows, or the cashier session/JWT token has expired | Check the Products sheet has rows with `Active = TRUE`; log out and log back in |
| **Arduino not listed in ports** | USB cable not plugged in, or driver not installed | On Windows: check Device Manager → Ports (COM & LPT); on Linux: check for `/dev/ttyUSB0` or `/dev/ttyACM0` |
| **"No card read after 5 seconds" / card timeout** | Arduino not outputting data in the expected format, or physically disconnected | Confirm the Arduino firmware is running and the serial output matches `<CARD|XXXXXXXX>`; the 5-second timeout is hardcoded in `ArduinoBridge` |
| **"Card UID invalid" error** | Arduino sent a UID that is not exactly 8 hex characters | The firmware must output exactly 8 hex characters (e.g. `ABCD1234`); update the firmware if the UID length is different |
| **"Student not found" after card tap** | Card UID not registered in the Money Accounts sheet | Register the student's money card via the admin dashboard (Student Management → Link Money Card) |
| **"Insufficient balance"** | Student's balance is below the transaction total | Admin must top up the student's balance via Load Balance in the admin dashboard |
| **Login fails with correct credentials** | Credentials are hardcoded; if they were changed, the server must be restarted | Check `cashier_routes.py` line 69 for the current hardcoded values |

---

## Related Documentation

- [API Reference](api-reference.md) — Full REST API specification
- [Google Sheets Schema](google-sheets-schema.md) — Sheet column definitions
- [Admin Guide](admin-guide.md) — Student registration, product management, loading balance
