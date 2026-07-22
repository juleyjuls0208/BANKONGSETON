# BANKONGSETON RFID Registration Reader — Arduino UNO R3

Serial-only RC522 reader for the on-prem registration panel. The same firmware
also works as a cashier fallback when the UNO R4 WiFi reader is unavailable.
It emits physical card UIDs over USB serial; it does not use WiFi or an LCD.

## Hardware

| Component | Notes |
|---|---|
| Arduino UNO R3 | Genuine or compatible clone |
| RC522 RFID module | Power from **3.3V**, not 5V |
| Piezo buzzer | Optional; both active and passive buzzers work |

## Wiring

### RC522 → UNO R3

| RC522 pin | UNO R3 |
|---|---|
| SDA/SS | D10 |
| RST | D2 |
| SCK | D13 |
| MOSI | D11 |
| MISO | D12 |
| 3.3V | 3.3V |
| GND | GND |
| IRQ | Not connected |

### Piezo → UNO R3

| Piezo pin | UNO R3 |
|---|---|
| + | D7 |
| − | GND |

## Required library

Install **MFRC522 by GithubCommunity** from Arduino IDE → Library Manager.
`SPI` is included with the UNO board package.

## Serial protocol

The sketch uses **9600 baud**, with newline-terminated commands and events.

### UNO R3 → panel

```text
BANKONGSETON RFID reader ready
CARD|AABBCCDD
PONG
```

`CARD|` contains uppercase hex: 8 characters for a 4-byte UID or 14 for a
7-byte UID. The panel accepts only those two lengths.

### Panel → UNO R3

```text
PING
<DISPLAY|Line 1|Line 2>
<SUCCESS|message>
<ERROR|message>
```

`PING` replies with `PONG` and a connect beep. The R3 has no display, so
`DISPLAY` is accepted and ignored; `SUCCESS` and `ERROR` still trigger audio
feedback. This keeps the R3 compatible with the registration panel and the
shared cashier serial bridge.

## Upload and test

1. Select **Arduino UNO** in Arduino IDE.
2. Select the board's COM port.
3. Install MFRC522 and upload `bankongseton_nfc_r3.ino`.
4. Open Serial Monitor at **9600 baud** only when the panel is disconnected.
5. With the panel connected, select the same COM port and click **Connect**.
6. A successful connection produces `PONG`; tapping a card produces `CARD|...`.

Do not leave Arduino IDE Serial Monitor open while the registration or cashier
app is connected; Windows allows only one process to own the COM port.
