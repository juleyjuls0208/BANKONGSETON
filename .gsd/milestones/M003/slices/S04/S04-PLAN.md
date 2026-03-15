# S04: Powerbank Hardening + Wireless Docs

**Goal:** Arduino heartbeats every 30 seconds — keeping the powerbank alive and driving the WiFi badge green in the cashier UI — and `arduino/README-wireless.md` documents the complete standalone wireless setup so anyone can deploy without a USB cable.

**Demo:** `bash scripts/verify-m003-s04.sh` exits 0 (firmware loop + README structure); `arduino/README-wireless.md` exists and covers hardware, wiring, `secrets.h`, flashing, and verification; first live heartbeat makes the WiFi badge turn green (hardware UAT gate).

## Must-Haves

- `lastHeartbeatMs` declared at file scope (not a plain local — it must survive across loop() calls)
- Heartbeat check placed at top of `loop()` immediately after `handleIncomingSerial()`, before the NFC scan and `if (!found) return;`
- Timer comparison uses unsigned long arithmetic: `now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS`
- `HEARTBEAT_INTERVAL_MS` constant comment updated to reflect actual purpose (no longer "stub")
- `arduino/README-wireless.md` exists with: hardware list, wiring, required libraries, `secrets.h` field-by-field explanation (SSID, FLASK_HOST port 5003, SECRET_API_KEY matching `ARDUINO_API_KEY` in Flask `.env`), flashing steps, powerbank selection guidance, and WiFi badge verification
- `scripts/verify-m003-s04.sh` exits 0 with ≥8 grep assertions covering firmware structure and README content

## Proof Level

- This slice proves: contract (grep assertions on firmware structure + README content)
- Real runtime required: yes — badge going green on live heartbeat requires physical hardware flash
- Human/UAT required: yes — flash Arduino → observe WiFi badge turns green within 30s

## Verification

- `bash scripts/verify-m003-s04.sh` — exits 0; covers firmware heartbeat loop, variable declaration, constant comment, README existence and required sections
- `bash scripts/verify-m003-s03.sh` — regression check; exits 0 confirms S03 contracts unchanged
- **Failure diagnostic:** `grep -n "stub\|not yet implemented" arduino/bankongseton_rfid/bankongseton_rfid.ino` — must return 0 matches (confirms stub comment removed); `grep -c "lastHeartbeatMs" arduino/bankongseton_rfid/bankongseton_rfid.ino` — must be ≥2 (declaration + use); badge stays red after flash → check Serial Monitor for `HTTP: POST /api/arduino/heartbeat` every 30s; 401 in Flask access log → `SECRET_API_KEY` in `secrets.h` doesn't match `ARDUINO_API_KEY` in Flask `.env`

## Observability / Diagnostics

- **Runtime signal:** Arduino Serial prints `HTTP: POST /api/arduino/heartbeat` (via existing `httpPostJson` Serial logging) every 30 s during idle — visible in Serial Monitor as proof the timer fires
- **Server-side signal:** Flask access log shows `POST /api/arduino/heartbeat 200` on each heartbeat; absence means Arduino never reached server (check WiFi, API key, port 5003)
- **UI signal:** `#wifiBadge` in cashier UI turns green within 30 s of first heartbeat — `arduino_wifi_status {online: True}` emitted via Socket.IO; badge stays red → heartbeat not reaching server
- **Failure state persisted:** `lastHeartbeatMs` stays 0 until first successful timer trip — Serial Monitor gap of >30 s between heartbeat prints signals WiFi or POST failure; `httpPostJson` logs HTTP status code on each attempt
- **Inspection command:** `grep -n "heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino` shows both declaration context and call site; `grep -n "lastHeartbeatMs" arduino/bankongseton_rfid/bankongseton_rfid.ino` confirms file-scope placement
- **Redaction:** `httpPostJson` body is `{"status":"ok"}` — no secrets, no UID, no transaction data logged

## Tasks

- [x] **T01: Add firmware heartbeat POST loop** `est:20m`
  - Why: Satisfies R023 — without the actual POST call, the powerbank gets no keep-alive burst and the WiFi badge stays red forever (HEARTBEAT_INTERVAL_MS is currently a stub constant with no associated code)
  - Files: `arduino/bankongseton_rfid/bankongseton_rfid.ino`
  - Do: (1) Declare `static unsigned long lastHeartbeatMs = 0;` at file scope before `setup()`. (2) Immediately after the `handleIncomingSerial()` call at the top of `loop()`, insert a 4-line timer check: `unsigned long now = millis(); if (now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS) { lastHeartbeatMs = now; ensureWiFi(); httpPostJson("/api/arduino/heartbeat", "{\"status\":\"ok\"}"); }`. (3) Update the `HEARTBEAT_INTERVAL_MS` constant comment from "S04: heartbeat stub — POST not yet implemented" to "30s heartbeat interval — POST to /api/arduino/heartbeat keeps powerbank alive and drives WiFi badge in cashier UI".
  - Verify: `grep -n "lastHeartbeatMs" arduino/bankongseton_rfid/bankongseton_rfid.ino` shows file-scope declaration; `grep -n "httpPostJson.*heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino` shows the call; `grep -n "HEARTBEAT_INTERVAL_MS" arduino/bankongseton_rfid/bankongseton_rfid.ino` shows updated comment with no "stub"
  - Done when: All three greps return matches; constant comment contains no "stub" or "not yet implemented"

- [x] **T02: Write README-wireless.md and verify script** `est:25m`
  - Why: Satisfies R024 — without docs whoever sets up the cashier counter has no guide for WiFi-only mode; the verify script gives a single exit-0 command to confirm both T01 and T02 are structurally complete
  - Files: `arduino/README-wireless.md`, `scripts/verify-m003-s04.sh`
  - Do: (1) Write `arduino/README-wireless.md` following the section structure of `arduino/bankongseton_nfc_r3/README.md`: Hardware Required table (UNO R4 WiFi, PN532 SPI, LCD, buzzer, USB powerbank ≥10,000mAh 2A port), Wiring table (same SPI pinout as R3), Required Libraries, `secrets.h` field-by-field guide (note FLASK_HOST must use port 5003, SECRET_API_KEY must match `ARDUINO_API_KEY` in Flask `.env`, HEARTBEAT_INTERVAL_MS is in the `.ino` not in `secrets.h`), Flashing steps (Arduino IDE, select UNO R4 WiFi board, upload), Verification section (what Serial Monitor shows at boot and on heartbeat, how to confirm WiFi badge goes green in cashier UI within 30s), Powerbank selection notes (≥2A output port, ≥10,000mAh for full school day, name-brand recommended), and Troubleshooting (badge stays red → check API key match and Flask port). (2) Write `scripts/verify-m003-s04.sh`: check `lastHeartbeatMs` in firmware, check `httpPostJson.*heartbeat` call, check HEARTBEAT_INTERVAL_MS comment no longer contains "stub", check `README-wireless.md` exists, check README contains FLASK_HOST/5003, X-API-Key/ARDUINO_API_KEY, powerbank, and at least one section header for Flashing.
  - Verify: `bash scripts/verify-m003-s04.sh` exits 0; `test -f arduino/README-wireless.md` exits 0
  - Done when: Verify script exits 0 with ≥8 passing checks; README is human-readable standalone setup guide

## Files Likely Touched

- `arduino/bankongseton_rfid/bankongseton_rfid.ino`
- `arduino/README-wireless.md`
- `scripts/verify-m003-s04.sh`
