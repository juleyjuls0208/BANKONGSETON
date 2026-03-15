# M003: Wireless Cashier Payment Terminal — Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

## Project Description

Bangko ng Seton is an RFID-based school money management system. Students pay at the cashier by tapping an RFID card or an Android phone (NFC HCE virtual card). The Arduino UNO R4 WiFi reads cards and currently depends on a USB serial connection to a PC running the Python ArduinoBridge. M003 cuts that dependency: the Arduino runs standalone from a USB powerbank and delivers card/phone reads directly over school WiFi to the Flask backend.

## Why This Milestone

The cashier counter doesn't always have a PC with an active serial connection. A powerbank-powered Arduino is simpler to deploy and more reliable — no cable management, no dependency on a PC being awake and running the bridge process. This milestone makes that setup fully functional by fixing the firmware routing bug exposed when serial fallback is removed and wiring the complete cashier payment flow for both physical cards and phone taps.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Place the Arduino UNO R4 WiFi on the cashier counter, plug it into a powerbank, and process RFID card payments wirelessly — no PC, no USB cable to a computer
- Have a student tap their Android phone (HCE virtual card) at the cashier and see the payment complete — same success modal as a physical card
- See a green "WiFi" badge in the cashier UI confirming the Arduino is online, without needing to select a COM port
- Leave the Arduino running unattended for a school day; it reconnects automatically if WiFi drops

### Entry point / environment

- Entry point: Cashier browses to the cashier web UI; Arduino is powered by powerbank on the counter
- Environment: School LAN (WiFi + Flask server reachable); Arduino flashed with correct `secrets.h`
- Live dependencies involved: Arduino UNO R4 WiFi, PN532 NFC module, Flask dashboard (web_app.py on school LAN), Google Sheets (via backend), Android student app (for phone NFC taps)

## Completion Class

- Contract complete means: `arduino/bankongseton_rfid/bankongseton_rfid.ino` routes CARD UIDs to the correct endpoint; `complete_sale_nfc()` in cashier_routes.py resolves virtual card tokens and debits balance; heartbeat endpoint exists in web_app.py; `python -m py_compile` exits 0 on all modified Python files
- Integration complete means: Physical card tap over WiFi triggers `card_read` SocketIO event and completes a sale; phone NFC tap triggers `nfc_payment` and completes a sale; cashier UI shows WiFi status badge
- Operational complete means: Arduino stays online on a powerbank for a full school day; WiFi reconnects without manual intervention

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Student taps physical RFID card at standalone Arduino (powerbank, no PC) → `card_read` fires → cashier sees payment success modal → balance is debited in Sheets
- Student taps Android HCE phone at same standalone Arduino → `nfc_payment` fires → cashier sees same success modal → balance is debited via token resolution in Sheets
- Cashier UI shows green WiFi badge when Arduino is heartbeating; badge turns red when Arduino is offline
- `python -m py_compile` exits 0 on all modified Python files; firmware compiles cleanly in Arduino IDE

## Risks and Unknowns

- Firmware routing bug severity — the bug is in `deliver()` which routes all WiFi POSTs to `/api/nfc/tap`; the fix is surgical (two `httpPost` calls distinguished by prefix) but must not break the existing serial fallback path
- Token resolution at cashier — `complete_sale_nfc()` must replicate the token lookup from `api_server.py nfc_pay()` inside cashier_routes.py, which runs in a different process with its own Sheets client; needs careful testing against the VirtualCards sheet
- Powerbank auto-shutoff threshold — most powerbanks cut at ~50-100mA; the PN532 polling loop + WiFi active draw (~180-200mA) should keep the board above threshold, but heartbeat POST every 30s provides a guaranteed RF burst as additional mitigation

## Existing Codebase / Prior Art

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — R4 WiFi firmware; `deliver()` function is the routing bug target; `httpPost()` is the WiFi POST helper; `handleIncomingSerial()` is the PING/PONG handler
- `arduino/bankongseton_rfid/secrets.h` — WiFi credentials + Flask server IP + API key; gitignored; template must document new `HEARTBEAT_INTERVAL_MS` constant
- `backend/dashboard/web_app.py` — `/api/arduino/card-read` endpoint (emits `card_read`); `ARDUINO_API_KEY` loaded at module level; this is where `/api/arduino/heartbeat` should be added
- `backend/dashboard/dashboard_core.py` — `/api/nfc/tap` endpoint (emits `nfc_payment`); both files share the same `socketio` instance
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale()` endpoint; new `complete_sale_nfc()` follows the same pattern; both use `flask_session.get('pending_transaction')` for items/total
- `backend/dashboard/cashier/templates/cashier_index.html` — `arduinoConnected` flag gates checkout + Quick Pay; COM port selector + Connect button; needs WiFi status badge alongside existing serial UI
- `backend/api/api_server.py` — `nfc_pay()` reference implementation for virtual card token lookup (VirtualCards sheet, `IsActive`, `MoneyCardNumber` resolution)
- `arduino/bankongseton_nfc_r3/` — R3 registration-only reader; not modified by this milestone

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R020 — Correct WiFi payment routing (firmware routing bug fix)
- R021 — Phone NFC payment at cashier (new cashier endpoint + UI wiring)
- R022 — Arduino WiFi status in cashier UI (heartbeat + badge)
- R023 — Arduino stable on powerbank (keep-alive, reconnect hardening)
- R024 — Wireless deployment documentation

## Implementation Decisions

### Firmware Routing Fix
- `deliver()` takes a `prefix` parameter ("CARD" or "NFC"); the prefix determines which endpoint to POST to
- CARD → `POST /api/arduino/card-read` with `{"uid": value}`
- NFC → `POST /api/nfc/tap` with `{"token": value}`
- Both routes are already implemented in the backend; this is a firmware-only change
- Serial fallback line format remains identical (`CARD|UID` and `NFC|token`) — ArduinoBridge unchanged

### Heartbeat Mechanism
- Arduino POSTs `{"status": "ok"}` to `POST /api/arduino/heartbeat` every 30 seconds (configurable via `HEARTBEAT_INTERVAL_MS` constant)
- Backend stores `_arduino_last_heartbeat` timestamp in module scope (float, `time.time()`)
- Backend emits `arduino_wifi_status` SocketIO event: `{"online": bool, "last_seen_s": float}` on each heartbeat
- Cashier UI: `arduinoConnected` becomes true when EITHER serial is connected OR a heartbeat arrived within 60 seconds
- WiFi status badge: green with "WiFi" label when online; red with "WiFi?" when offline or never seen

### Phone NFC at Cashier (`complete_sale_nfc`)
- New endpoint: `POST /cashier/api/complete-sale-nfc` decorated with `@jwt_required`
- Request body: `{"virtual_card_token": "<48-char-token>"}` — token arrives from the `nfc_payment` socket event
- Lookup: VirtualCards sheet → `VirtualCardToken` match + `IsActive == TRUE` → extract `MoneyCardNumber`
- Payment processing: identical to `complete_sale()` (Money Accounts sheet → balance debit → Transactions Log append → FCM push → parent SMS)
- Cashier UI: `socket.on('nfc_payment', ...)` calls `completeNFCSale(data.token)` which calls this endpoint
- Items and total come from `flask_session.get('pending_transaction')` — same session key as `complete_sale`
- On token not found or inactive: return 401 with `{"error": "Virtual card not found or inactive"}` — cashier UI shows error in modal

### Cashier UI Dual-Mode
- Keep the existing COM port selector and Connect button unchanged (serial mode still works)
- Add a WiFi status badge to the right of the Connect button: `<span id="wifiStatusBadge" class="wifi-badge wifi-offline">WiFi?</span>`
- SocketIO listener: `socket.on('arduino_wifi_status', ...)` updates `arduinoConnected` and badge color
- On page load: fetch `GET /cashier/api/arduino-wifi-status` to set initial badge state (returns `{"online": bool, "last_seen_s": float}`)
- `arduinoConnected` is set to true on EITHER `updateArduinoStatus(true)` (serial) OR WiFi heartbeat online

### Powerbank Hardening
- Heartbeat POST itself provides the periodic RF burst that keeps powerbank alive — no separate keep-alive mechanism needed
- `HEARTBEAT_INTERVAL_MS = 30000` (30s) — configurable constant at top of .ino file
- `ensureWiFi()` is called before each heartbeat attempt (auto-reconnect on WiFi drop)
- Firmware does NOT use WiFi power-save mode (WiFiS3 default is active — leave it as-is)
- If heartbeat POST fails (no WiFi), firmware logs over Serial and retries on next interval (non-blocking)

## Scope

### In Scope

- Fix `deliver()` routing in `bankongseton_rfid.ino` to use two separate endpoints by prefix
- Add `POST /api/arduino/heartbeat` to `web_app.py`
- Add `GET /cashier/api/arduino-wifi-status` to cashier_routes.py
- Add `POST /cashier/api/complete-sale-nfc` to cashier_routes.py
- Wire `nfc_payment` socket event in `cashier_index.html`
- Add WiFi status badge to cashier header
- `arduino/README-wireless.md` — standalone powerbank setup guide

### Out of Scope

- ArduinoBridge changes (serial path is preserved as-is; ArduinoBridge unchanged)
- R3 registration reader (separate sketch, not involved in payment)
- Mobile API server (`api_server.py`) changes — cashier_routes.py does its own token lookup
- OTA firmware updates
- BLE connectivity
