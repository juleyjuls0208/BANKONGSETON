# S04: Powerbank Hardening + Wireless Docs — UAT

**Milestone:** M003
**Written:** 2026-03-15

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime + human-experience)
- Why this mode is sufficient: Firmware structure and README completeness can be contract-verified by grep assertions (artifact-driven); badge going green and powerbank behavior require a flashed Arduino and physical hardware (live-runtime + human-experience)

## Preconditions

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` updated firmware is compiled and flashed to the Arduino UNO R4 WiFi
- `secrets.h` has correct SSID, FLASK_HOST (IP:5003), and SECRET_API_KEY matching `ARDUINO_API_KEY` in Flask `.env`
- Flask web app (`web_app.py`) is running on port 5003 and reachable from the Arduino's network segment
- Cashier UI (`cashier_index.html`) is open in a browser and connected via Socket.IO
- USB powerbank (≥10,000mAh, ≥2A output port) available and charged
- Arduino IDE (or equivalent serial terminal) available for Serial Monitor at 115200 baud
- `bash` available in repo root for running verify scripts

## Smoke Test

Run `bash scripts/verify-m003-s04.sh` from repo root. It must print "8 passed, 0 failed" and exit 0. If this fails, do not proceed to hardware testing — fix the structural issue first.

## Test Cases

### 1. Contract: Firmware structure passes all 8 grep assertions

1. From repo root: `bash scripts/verify-m003-s04.sh`
2. Observe per-line output — expect ✓ for each of the 8 checks
3. **Expected:** `8 passed, 0 failed — verify-m003-s04: all 8 checks passed ✓`; exit code 0

### 2. Contract: No stub text remains in firmware

1. Run: `grep -n "stub\|not yet implemented" arduino/bankongseton_rfid/bankongseton_rfid.ino`
2. **Expected:** No output (0 matches). Any output means the constant comment was not fully updated.

### 3. Contract: S03 regression clean

1. From repo root: `bash scripts/verify-m003-s03.sh`
2. **Expected:** `12 passed, 0 failed — M003/S03 verification PASSED ✓`; exit code 0

### 4. Contract: README is complete and human-readable

1. Open `arduino/README-wireless.md` in a text editor
2. Confirm eight sections are present: Hardware Required, Wiring, Required Libraries, secrets.h Configuration, Flashing, Verification, Powerbank Selection, Troubleshooting
3. In secrets.h Configuration section, confirm: FLASK_HOST row mentions port `5003` explicitly; SECRET_API_KEY row names `ARDUINO_API_KEY` as the matching Flask env var
4. In Powerbank Selection section, confirm: minimum 2A output port and 10,000mAh guidance is stated
5. In Troubleshooting section, confirm: at least one row covers badge-stays-red symptom with API key mismatch as a cause
6. **Expected:** All five confirmations pass; no placeholder text (`TODO`, `TBD`, `{{...}}`) anywhere in the file

### 5. Live: WiFi badge turns green on first heartbeat

1. Flash updated firmware to Arduino UNO R4 WiFi
2. Power Arduino from USB powerbank (≥2A port)
3. Open Serial Monitor at 115200 baud
4. Open cashier UI in browser — observe `#wifiBadge` (should be red/offline initially)
5. Wait up to 60 seconds
6. **Expected:** Serial Monitor prints `HTTP: POST /api/arduino/heartbeat` within 30s of boot; Flask access log shows `POST /api/arduino/heartbeat 200`; `#wifiBadge` turns green within 30s of first successful heartbeat

### 6. Live: Heartbeat fires consistently during idle (no card taps)

1. With Arduino running and badge green, leave idle for 90 seconds — no card taps
2. Watch Serial Monitor
3. **Expected:** `HTTP: POST /api/arduino/heartbeat` appears approximately every 30 seconds (±5s); badge stays green throughout; no red flash

### 7. Live: Pay Now button enables without COM port selection

1. With badge green and no COM port selected in the cashier UI port selector
2. Observe the Pay Now / checkout button state
3. **Expected:** Pay Now is enabled (not grayed out); checkout can be initiated from WiFi connection alone — S03 arduinoConnected behavior confirmed with S04 heartbeat active

### 8. Live: WiFi drop and auto-reconnect

1. With badge green and Arduino running on powerbank, disable the WiFi AP or move Arduino out of range
2. Wait 45 seconds (1–2 missed heartbeat intervals)
3. **Expected:** Badge turns red within ~30–45s of losing WiFi; Serial Monitor shows WiFi reconnect attempts from `ensureWiFi()`
4. Re-enable the AP or move Arduino back in range
5. Wait up to 60 seconds
6. **Expected:** Arduino reconnects automatically; badge turns green within 30s of reconnect; no manual intervention (no reboot, no re-flash)

### 9. Live: Physical card tap still works after heartbeat loop added

1. With badge green, tap a physical RFID card at the PN532 reader
2. **Expected:** Cashier UI receives `card_read` event; student name and balance populate; Pay Now completes a sale; balance is debited in Google Sheets; no regression from S01 behavior

### 10. Live: 30-minute powerbank soak

1. Power Arduino from powerbank; confirm badge green
2. Leave completely idle (no card taps) for 30 minutes
3. At the end, check Serial Monitor and badge
4. **Expected:** Arduino is still powered; badge is still green; Serial Monitor shows regular heartbeat lines throughout (one every ~30s); powerbank did not auto-shutoff during idle

## Edge Cases

### Badge red — wrong API key

1. Configure `secrets.h` with an incorrect `SECRET_API_KEY` (e.g., append "X" to the real value)
2. Flash and power Arduino; wait 30s
3. **Expected:** Badge stays red; Flask access log shows `POST /api/arduino/heartbeat 401`; Serial Monitor still shows the POST attempt (timer fires correctly; server rejects it)

### Badge red — wrong Flask port

1. With correct secrets.h but Flask running on a different port than `FLASK_HOST` specifies
2. Flash and power Arduino; wait 30s
3. **Expected:** Badge stays red; Serial Monitor shows connection error or timeout on heartbeat POST; no 200 in Flask log

### Heartbeat fires during active NFC scan hold

1. Hold a card within PN532 range so loop() is busy with NFC processing
2. Wait 30+ seconds (one full heartbeat interval)
3. **Expected:** Heartbeat timer fires between scan iterations — the timer check is at the top of loop(), before the NFC scan code; heartbeat may be delayed by one loop cycle but is not permanently blocked

## Failure Signals

- Badge stays red after 30s with firmware flashed → heartbeat not reaching server; check Serial Monitor for POST attempt; check Flask access log; check API key match and port 5003
- Serial Monitor shows no heartbeat lines at all → firmware not flashed correctly or loop() is hanging; verify timer block is before `if (!found) return;` at line 530
- `POST /api/arduino/heartbeat 401` in Flask log → `SECRET_API_KEY` in `secrets.h` does not match `ARDUINO_API_KEY` in Flask `.env`
- `bash scripts/verify-m003-s04.sh` fails on checks (a–d) → T01 heartbeat edits not applied; inspect the `.ino` with `grep -n "lastHeartbeatMs"` and `grep -n "httpPostJson.*heartbeat"`
- `bash scripts/verify-m003-s04.sh` fails on checks (e–h) → README absent or missing required content; check file exists and sections are present
- Powerbank shuts off during 30-minute idle → powerbank's auto-shutoff threshold is below heartbeat current burst; try a different (name-brand, ≥2A) powerbank; PN532 polling baseline (~180–200mA) is the main current draw

## Requirements Proved By This UAT

- R023 (Arduino Stable on Powerbank) — Tests 6, 8, 10: heartbeat fires consistently during idle, Arduino reconnects after WiFi drop without intervention, powerbank stays on for 30-minute idle
- R024 (Wireless Deployment Documentation) — Tests 4 (README content), 5 (live badge green): README is complete and human-readable; explicit port/key callouts verified

## Not Proven By This UAT

- Full-day (8-hour) powerbank endurance — 30-minute soak is the practical gate; 8-hour endurance depends on powerbank capacity and is not time-feasible in a single test session
- Multi-drop WiFi recovery — only a single drop/reconnect cycle is tested; extended repeated outage behavior is untested
- Complete M003 end-to-end simultaneously — card tap + phone tap + badge green + powerbank idle all on the same live session; each slice was verified independently

## Notes for Tester

- Always run the verify script first. Hardware testing is wasted if contract checks fail.
- Serial Monitor at exactly 115200 baud. Garbage output means wrong baud rate.
- For the WiFi drop test, toggling the router is the simplest approach. Alternatively, temporarily change secrets.h SSID to a nonexistent network and re-flash — but that requires two flash cycles.
- The 30-minute powerbank soak can run unattended — leave Serial Monitor open and check at the end.
- `#wifiBadge` state: class `online` = green, class `offline` = red. Use browser DevTools → Elements if the visual state is ambiguous.
- If badge stays red but Flask log shows 200: check the Socket.IO connection in the browser console — the cashier page may not be connected to the right server instance.
