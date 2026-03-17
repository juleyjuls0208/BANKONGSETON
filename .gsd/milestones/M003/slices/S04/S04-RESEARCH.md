# S04: Powerbank Hardening + Wireless Docs — Research

**Date:** 2026-03-15

## Summary

S04 is the lightest slice in M003 — the backend is fully wired (heartbeat endpoint from S03), the firmware has the constant stubbed (S01), and the cashier badge is ready and waiting (S03). The only missing pieces are: (1) the firmware heartbeat POST loop, and (2) `arduino/README-wireless.md`. No Python files change; no backend changes needed.

The firmware change is surgical: add a `static unsigned long lastHeartbeatMs = 0;` variable and a 4-line timer check at the top of `loop()`. The timer check calls `ensureWiFi()` then `httpPostJson("/api/arduino/heartbeat", ...)` every 30 seconds, regardless of whether any card was tapped. This single change satisfies both R023 (powerbank keep-alive via guaranteed current draw) and makes R022 runtime-validatable (badge goes green for the first time in production).

The README documents hardware, wiring, secrets.h, flashing, and verification — using the existing `arduino/bankongseton_nfc_r3/README.md` as the format template.

## Recommendation

Two tasks in sequence:
1. **T01** — Firmware heartbeat POST (add loop timer + POST call, update constant comment)
2. **T02** — Write `arduino/README-wireless.md` + verify script `scripts/verify-m003-s04.sh`

No backend work. No Python changes. Run `verify-m003-s04.sh` + `verify-m003-s03.sh` to confirm nothing regressed.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| WiFi reconnect on drop | `ensureWiFi()` already implemented | Tested, non-blocking with 8s timeout, already called from `deliver()` |
| HTTP POST to backend | `httpPostJson(path, body)` already implemented | Shared TCP/header/response logic; heartbeat just needs a one-liner call |
| WiFi status badge UI | S03 fully wired `#wifiBadge`, socket listener, REST endpoint | Badge goes green the moment first heartbeat lands — no UI changes needed |
| Heartbeat backend endpoint | `POST /api/arduino/heartbeat` live in `web_app.py` | Exists, API-key authenticated, emits `arduino_wifi_status` socket event |

## Existing Code and Patterns

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — `HEARTBEAT_INTERVAL_MS = 30000` constant at line 71; comment says "S04: heartbeat stub — POST not yet implemented". `ensureWiFi()` at ~line 280. `httpPostJson(path, body)` at ~line 301. `loop()` starts at line 472 — `handleIncomingSerial()` is first call; heartbeat check goes immediately after.
- `arduino/bankongseton_rfid/secrets.h` — Has `HEARTBEAT_INTERVAL_MS` orientation comment pointing to the `.ino`. No changes needed.
- `backend/dashboard/web_app.py` — `POST /api/arduino/heartbeat` (lines 293–313): API-key guard, updates `app.arduino_last_heartbeat`, emits `arduino_wifi_status {online: True, last_seen_s: 0.0}`. Ready to receive.
- `backend/dashboard/cashier/cashier_routes.py` — `GET /cashier/api/arduino-wifi-status` (line 833): JWT-protected, reads `app.arduino_last_heartbeat`, returns `{online, last_seen_s}`. Badge primed via this on page load.
- `backend/dashboard/cashier/templates/cashier_index.html` — `#wifiBadge` span at line 65; `arduino_wifi_status` socket listener at line 342; `fetchArduinoWifiStatus()` called at line 114. All wired and waiting.
- `arduino/bankongseton_nfc_r3/README.md` — Formatting model for the wireless README. Same section structure (Hardware Required table, Wiring table, libraries, flashing steps). Adopt format verbatim.

## Constraints

- `lastHeartbeatMs` MUST be `static` (file-scope inside loop is fine) or a global — a plain local variable resets to 0 every loop() call and the timer never fires.
- `millis()` unsigned long overflow at ~49.7 days: `now - lastHeartbeatMs` with unsigned subtraction handles this correctly without any guards. Do NOT use `>=` with signed int.
- `HEARTBEAT_INTERVAL_MS` is declared `static const int` (not `unsigned long`) — cast to `(unsigned long)` in the comparison: `now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS`. Avoids sign-comparison warning from gcc.
- `ensureWiFi()` blocks up to 8000ms on reconnect. Placing heartbeat check at top of loop() (before NFC scan) means a reconnect adds ~8s before the NFC field activates — acceptable because reconnects are rare, and no card is in range during the check.
- No HEARTBEAT_INTERVAL_MS in secrets.h — it is a compile-time constant in the .ino; users adjust it there before flashing. The secrets.h orientation comment already says this — leave it.
- Loop iteration cadence on idle: `readPassiveTargetID(NFC_TIMEOUT_MS=1000ms)` + ~110ms overhead ≈ 1.1s per loop. With `HEARTBEAT_INTERVAL_MS = 30000`, the heartbeat fires every ~27-28 idle iterations. This is correct.
- `if (!found) return;` early exit at line ~519: this exits `loop()`, which immediately restarts from the top. Because the heartbeat check is at the TOP of loop(), it runs on every iteration including those with no card — this is the correct placement.
- Powerbank draw: UNO R4 WiFi + PN532 polling ≈ 180–200mA active; WiFi in active client mode (not power-save) holds ~150mA between POSTs. This is well above the 50–100mA powerbank auto-shutoff threshold. The 30s heartbeat burst adds extra margin. Firmware does NOT enable WiFi power-save (WiFiS3 default is active mode — leave as-is).

## Common Pitfalls

- **`static` omitted on `lastHeartbeatMs`** — declared as plain `unsigned long lastHeartbeatMs = 0;` inside `loop()`. Resets to 0 on every call. Heartbeat fires every loop iteration instead of every 30s. Declare as file-scope (before `setup()`/`loop()`) or inside loop() with `static`.
- **Heartbeat check placed AFTER `if (!found) return;`** — the early return means the heartbeat never fires during idle periods (only fires after a card tap). Heartbeat must be at the TOP of loop() before the NFC scan.
- **Logging the token in heartbeat Serial output** — `httpPostJson()` itself doesn't log body, but don't add body to the Serial.print. The heartbeat body is just `{"status":"ok"}` so it's harmless, but establish the pattern of not logging POST bodies.
- **Forgetting to update the HEARTBEAT_INTERVAL_MS constant comment** — comment currently says "S04: heartbeat stub — POST not yet implemented". Must update to "30s heartbeat interval — POST to /api/arduino/heartbeat keeps powerbank alive and drives WiFi badge in cashier UI".
- **README-wireless.md documenting wrong Flask port** — `secrets.h` shows `FLASK_HOST "100.120.2.48:5003"` (port 5003 = dashboard, which has both `/api/arduino/card-read` and `/api/arduino/heartbeat`). README must document port 5003, not 5000 (api_server.py). This is a live credential file so treat these as examples only; document that users must set their own values.
- **Missing `X-API-Key` mention in README** — The heartbeat endpoint requires `X-API-Key` header matching `ARDUINO_API_KEY` in Flask `.env`. If `SECRET_API_KEY` in secrets.h doesn't match the server env var, heartbeats return 401 and badge stays red. Must be called out explicitly in the README.

## Open Risks

- Arduino compile not verifiable in this environment (arduino-cli not installed) — verify-m003-s04.sh uses grep assertions only; actual compilation must be done in Arduino IDE before flashing. Document this limitation in S04-SUMMARY.
- `ensureWiFi()` blocking up to 8s during reconnect may cause NFC to miss a tap that arrives during that window (card approaches just as WiFi is reconnecting). Acceptable tradeoff — reconnects are rare; the cooldown period after the previous tap (1500ms) provides natural spacing.
- Powerbank variation: some low-end powerbanks cut at higher current thresholds (150mA+) regardless of spec; the 180-200mA baseline draw should be safe for name-brand banks. README should recommend 2A output port and >10,000mAh capacity for a full school day.
- R022 runtime validation (badge going green on live heartbeat) depends on the Arduino being flashed — cannot verify in this dev environment. This is the human UAT gate for both R022 and R023.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Arduino C++ / WiFiS3 | — | none found (standard Arduino patterns sufficient) |
| Markdown documentation | — | not applicable (hand-written) |

## Sources

- `HEARTBEAT_INTERVAL_MS` constant stub and comment (source: `arduino/bankongseton_rfid/bankongseton_rfid.ino` line 71)
- `ensureWiFi()` implementation and 8s reconnect timeout (source: firmware lines ~280–292)
- `httpPostJson()` shared TCP/header/response helper (source: firmware lines ~301–340)
- Loop iteration structure and `if (!found) return;` early exit placement (source: firmware lines 472–652)
- Heartbeat backend endpoint fully implemented (source: `backend/dashboard/web_app.py` lines 293–313)
- Cashier WiFi badge fully wired (source: `cashier_index.html` lines 19–21, 65, 114, 169–182, 342)
- R3 README format template (source: `arduino/bankongseton_nfc_r3/README.md`)
- Decisions D029 (heartbeat as dual-purpose keep-alive), D034 (0.0 float sentinel), D035 (WiFi offline doesn't fight serial) confirm all design choices are already locked
