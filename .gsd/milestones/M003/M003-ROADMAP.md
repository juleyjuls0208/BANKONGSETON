# M003: Wireless Cashier Payment Terminal

**Vision:** Make the Arduino UNO R4 WiFi a fully standalone cashier payment terminal — powered by a USB powerbank, connected wirelessly to the school LAN, processing both physical RFID card taps and Android phone NFC taps without any USB cable to a PC or ArduinoBridge process running.

## Success Criteria

- A physical RFID card tapped at a powerbank-powered Arduino completes a sale end-to-end: balance debited in Sheets, cashier sees success modal, parent notified
- A student Android phone tapped at the same Arduino completes a sale end-to-end via the same cashier flow
- Cashier UI displays a WiFi status badge; badge is green when Arduino is heartbeating; "Pay Now" button enables on WiFi connection alone (no COM port required)
- Arduino recovers from WiFi drops automatically without manual intervention
- Wireless standalone deployment is documented in `arduino/README-wireless.md`

## Key Risks / Unknowns

- Firmware routing bug — `deliver()` sends CARD UIDs to `/api/nfc/tap` instead of `/api/arduino/card-read`; exposed only when serial fallback (ArduinoBridge) is absent
- NFC token resolution at cashier — `complete_sale_nfc()` must replicate `nfc_pay()` token lookup in a different process (cashier_routes.py vs api_server.py); must not introduce double-spend or stale cache window

## Proof Strategy

- Firmware routing bug → retire in S01 by confirming CARD POST hits `/api/arduino/card-read` (check server log) and triggers `card_read` event in cashier UI
- NFC token resolution → retire in S02 by confirming phone tap completes a sale with correct balance debit in Sheets

## Verification Classes

- Contract verification: `python -m py_compile` exits 0 on all modified Python files; firmware compiles in Arduino IDE; endpoint existence checks via grep
- Integration verification: card tap over WiFi → `card_read` event → sale complete; phone tap → `nfc_payment` event → sale complete; heartbeat → WiFi badge green
- Operational verification: Arduino stays connected through a 30-minute idle period on powerbank; auto-reconnects after WiFi simulated drop (WiFi router off/on)
- UAT / human verification: cashier tests physical card and phone tap payment on actual hardware before calling milestone done

## Milestone Definition of Done

This milestone is complete only when all are true:

- S01 firmware fix is flashed and confirmed: physical card WiFi POST reaches `/api/arduino/card-read` and completes a real sale
- S02 phone NFC payment works end-to-end: phone tap at Arduino → sale complete → balance debited in Sheets
- S03 WiFi badge shows correct state: green when Arduino heartbeating, red when offline; "Pay Now" enables without COM port
- S04 hardening confirmed: Arduino reconnects after WiFi drop; heartbeat sustains powerbank across 30-minute idle
- `arduino/README-wireless.md` exists with complete standalone setup instructions
- `python -m py_compile` exits 0 on all modified Python files

## Requirement Coverage

- Covers: R020, R021, R022, R023, R024
- Partially covers: none
- Leaves for later: none
- Orphan risks: none

## Slices

- [x] **S01: Firmware WiFi Routing Fix** `risk:high` `depends:[]`
  > After this: Physical RFID card tapped at a powerbank-powered Arduino posts to `/api/arduino/card-read` over WiFi, fires `card_read` in the cashier UI, and completes a real sale — no serial cable, no PC.

- [ ] **S02: Phone NFC Cashier Payment** `risk:medium` `depends:[S01]`
  > After this: Student taps Android phone at the Arduino → `nfc_payment` socket event fires → cashier UI calls `complete-sale-nfc` → sale completes with balance debited — same success modal as a card tap.

- [ ] **S03: WiFi Status Indicator** `risk:low` `depends:[S01]`
  > After this: Cashier UI shows a green "WiFi" badge when Arduino is heartbeating; badge turns red when Arduino goes offline; "Pay Now" enables without selecting a COM port.

- [ ] **S04: Powerbank Hardening + Wireless Docs** `risk:low` `depends:[S01]`
  > After this: Arduino reconnects automatically after a WiFi drop; stays powered for a full school day on a standard USB powerbank; `arduino/README-wireless.md` documents the complete standalone setup.

## Boundary Map

### S01 → S02

Produces:
- `bankongseton_rfid.ino` — `deliver(value, prefix)` routes `"NFC"` prefix to `POST /api/nfc/tap {"token": value}` and `"CARD"` prefix to `POST /api/arduino/card-read {"uid": value}`
- `httpPostCard(uid)` helper — POSTs `{"uid": uid}` to `/api/arduino/card-read` with `X-API-Key` header
- `httpPostNFC(token)` helper — POSTs `{"token": token}` to `/api/nfc/tap` with `X-API-Key` header

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- Same firmware with `HEARTBEAT_INTERVAL_MS` constant stubbed (heartbeat POST can be added in S04)
- `POST /api/arduino/card-read` confirmed working end-to-end (pre-existing backend endpoint, S01 proves it)

Consumes:
- nothing (first slice)

### S02 → S04

Produces:
- `POST /cashier/api/complete-sale-nfc` — takes `virtual_card_token`, resolves to `MoneyCardNumber`, debits balance, returns `{new_balance, offline}`
- `socket.on('nfc_payment', ...)` handler in `cashier_index.html` calls `completeNFCSale(token)`

Consumes from S01:
- `bankongseton_rfid.ino` — `"NFC"` prefix correctly hits `/api/nfc/tap` which emits `nfc_payment` SocketIO event to cashier

### S03 → S04

Produces:
- `POST /api/arduino/heartbeat` in `web_app.py` — updates `_arduino_last_heartbeat`, emits `arduino_wifi_status {online, last_seen_s}`
- `GET /cashier/api/arduino-wifi-status` in `cashier_routes.py` — returns `{online, last_seen_s}`
- WiFi status badge in `cashier_index.html` — green/red based on `arduino_wifi_status` socket event
- `arduinoConnected` logic updated to honor WiFi state

Consumes from S01:
- Confirmed that Arduino POSTs arrive at the backend (S01 end-to-end proves network path)
