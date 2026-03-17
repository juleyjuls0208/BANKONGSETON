# S01: Firmware WiFi Routing Fix — UAT

**Milestone:** M003
**Written:** 2026-03-15

## UAT Type

- UAT mode: mixed (artifact-driven contract verification + live-runtime hardware verification)
- Why this mode is sufficient: The routing bug is a firmware-source-level issue — grep assertions confirm the fix at the source level. Runtime hardware verification (flash + card tap → server log) is the definitive integration proof and must be done on physical hardware before R020 is marked validated.

## Preconditions

- `bash scripts/verify-s01.sh` exits 0 (all 8 checks pass) — run this first; if any check fails, stop and fix before hardware testing
- Arduino UNO R4 WiFi flashed with the updated `bankongseton_rfid.ino`
- `secrets.h` filled in with real values: `WIFI_SSID`, `WIFI_PASSWORD`, `SERVER_IP` (Flask server LAN IP), `SERVER_PORT` (default 5000), `SECRET_API_KEY` (matching `ARDUINO_API_KEY` env var in the Flask server)
- Flask server (`web_app.py` / `admin_dashboard.py`) running and reachable at the configured `SERVER_IP:SERVER_PORT`
- Cashier UI open in browser, logged in, connected to the Flask server via SocketIO
- Physical RFID card available (the kind issued to students — any UID works for routing test)
- Arduino serial monitor open (Arduino IDE or `arduino-cli monitor`) to observe Serial output
- Flask server access log visible (tail -f or console output from `python web_app.py`)

## Smoke Test

Open the Arduino serial monitor. Power-cycle the Arduino. Within ~10 seconds, confirm `"WiFi connected"` and the assigned IP address appear in the Serial output. This confirms the Arduino is on the school LAN and can reach the Flask server before any card tap is attempted.

## Test Cases

### 1. Contract verification — verify-s01.sh passes

1. In the project root, run: `bash scripts/verify-s01.sh`
2. **Expected:** Output shows `8 passed, 0 failed` with all checks marked `PASS`. Exit code 0.

### 2. Firmware compilation check

1. With `arduino-cli` installed, run:
   `arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi arduino/bankongseton_rfid`
2. **Expected:** Exits 0. No compilation errors. Warnings about deprecated APIs are acceptable.

### 3. Physical RFID card tap — server routing

1. Ensure Arduino is powered and WiFi-connected (Serial shows IP).
2. Tap a physical RFID card against the PN532 reader.
3. **Expected (Arduino Serial):** Line appears: `HTTP: delivered — CARD|<hex_uid>` (where `<hex_uid>` is the card's UID in hex).
4. **Expected (Flask server access log):** Line appears: `POST /api/arduino/card-read 200`
5. **Not expected:** `POST /api/nfc/tap` — if this appears instead, the firmware is not updated correctly.

### 4. card_read SocketIO event fires in cashier UI

1. Perform the card tap from Test 3 with the cashier UI open in the browser.
2. **Expected:** Cashier UI reacts to the card tap — either the sale completion modal appears (if a student is matched to the UID and a product is in cart/Quick Pay), or the UI shows a card-detected state waiting for product selection.
3. **Expected (browser console or SocketIO debug):** `card_read` event received (not `nfc_payment`).
4. **Not expected:** No UI reaction at all (would indicate the event name mismatch bug is still present or SocketIO is not connected).

### 5. End-to-end sale completion via WiFi card tap

1. In the cashier UI, add a product to the cart (or use Quick Pay on a product).
2. Tap the student's physical RFID card at the Arduino.
3. **Expected (Arduino Serial):** `HTTP: delivered — CARD|<uid>`
4. **Expected (Flask server log):** `POST /api/arduino/card-read 200`
5. **Expected (cashier UI):** Sale completion modal appears showing student name, product, and new balance.
6. **Expected (Google Sheets Transactions Log):** New transaction row appended with correct student, product, amount, and new balance.
7. **Expected (parent SMS/FCM if configured):** Parent notification sent.
8. **Not expected:** ArduinoBridge running — this test must be performed with no serial cable connected to a PC (powerbank-powered standalone mode).

### 6. Serial fallback unchanged (regression check)

1. Connect the Arduino via USB to the PC with ArduinoBridge running.
2. Tap a physical RFID card.
3. **Expected (Arduino Serial):** Line `CARD|<uid>` printed (the fallback line format is unchanged).
4. **Expected:** ArduinoBridge picks up the line and routes it as before — cashier UI fires `card_read` via the serial path.
5. **Confirms:** The serial fallback block was not accidentally modified by the firmware refactor.

## Edge Cases

### WiFi drop before card tap

1. Disable the WiFi access point (or move Arduino out of range) briefly, then re-enable.
2. Tap a physical RFID card within 10 seconds of WiFi being restored.
3. **Expected:** Arduino calls `ensureWiFi()` before the HTTP attempt, reconnects, then successfully POSTs `{"uid":uid}` to `/api/arduino/card-read`.
4. **Expected (Serial):** May show `"WiFi reconnecting..."` followed by `"HTTP: delivered — CARD|<uid>"` after reconnect.
5. The tap may be slower than normal (~3-5s for reconnect) but must succeed without rebooting the Arduino.

### Non-200 response from server

1. Temporarily stop the Flask server (or misconfigure `SERVER_IP`).
2. Tap a physical RFID card.
3. **Expected (Arduino Serial):** `HTTP: non-200 response:` line or connection failure message; retries up to configured `HTTP_MAX_RETRIES`; then falls back to Serial print (`CARD|<uid>`).
4. **Confirms:** Error visibility is intact; serial fallback activates on network failure.

### NFC phone tap (routing regression check for S02)

1. Tap an Android HCE phone (with the student app open) at the Arduino.
2. **Expected (Arduino Serial):** `HTTP: delivered — NFC|<token>`
3. **Expected (Flask server log):** `POST /api/nfc/tap 200`
4. **Not expected:** `POST /api/arduino/card-read` — phone tokens must not go to the card-read endpoint.
5. Note: The cashier UI `nfc_payment` handler is built in S02; this test only verifies the server-side routing is correct.

## Failure Signals

- `bash scripts/verify-s01.sh` exits non-zero → firmware source was not saved correctly; re-edit and re-run before flashing
- Flask log shows `POST /api/nfc/tap` for a physical card tap → old firmware is flashed; re-flash with updated `.ino`
- Flask log shows `POST /api/arduino/card-read 401` → `SECRET_API_KEY` in `secrets.h` does not match `ARDUINO_API_KEY` env var in Flask
- Cashier UI shows no reaction to card tap but Flask log shows `200` → SocketIO event name mismatch or cashier UI not connected to correct Flask server
- Arduino Serial shows no `"WiFi connected"` after power-up → `WIFI_SSID`/`WIFI_PASSWORD` incorrect in `secrets.h` or school LAN is unreachable
- Arduino Serial shows `HTTP attempt 1/3` then `HTTP attempt 2/3` then serial fallback → Flask server unreachable at `SERVER_IP:SERVER_PORT`; check `secrets.h` IP and that Flask is running

## Requirements Proved By This UAT

- R020 (Correct WiFi Payment Routing) — Test Cases 1–5 together prove that physical card UIDs hit `/api/arduino/card-read` and fire `card_read`; NFC edge case confirms NFC tokens still hit `/api/nfc/tap`

## Not Proven By This UAT

- R021 (Phone NFC Payment at Cashier) — phone tap fires `nfc_payment` but cashier UI handler is S02 work; phone tap routing is checked as an edge case here but end-to-end sale is not tested
- R022 (WiFi Status Badge) — heartbeat and badge are S03 work; no heartbeat POST exists in S01 firmware
- R023 (Arduino Stable on Powerbank) — 30-minute idle powerbank test is S04 operational verification
- R024 (Wireless Deployment Docs) — `arduino/README-wireless.md` is S04 deliverable
- arduino-cli compile step (Test 2) requires arduino-cli to be installed; if not available, compilation must be verified in Arduino IDE before flashing

## Notes for Tester

- **Powerbank mode is required for Test 5** — the whole point of S01 is proving the bug is fixed when there is no serial cable. Test with USB cable only for the regression check (Test 6).
- If the sale doesn't complete in Test 5 but the server log shows `POST /api/arduino/card-read 200`, the problem is in the cashier UI or the backend card-read handler — not the firmware fix. Check that the student's UID is registered in the Users sheet and that a product is selected.
- `SECRET_API_KEY` in `secrets.h` is sensitive — never paste it into Serial monitor commands or paste the Arduino log output containing it. The firmware is written to not log the key value.
- Test 3 (routing check) is the minimum bar for calling S01 done. Tests 4 and 5 (cashier UI + full sale) are the full integration proof needed for R020 to be marked validated.
