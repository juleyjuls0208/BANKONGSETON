---
estimated_steps: 3
estimated_files: 1
---

# T01: Add firmware heartbeat POST loop

**Slice:** S04 — Powerbank Hardening + Wireless Docs
**Milestone:** M003

## Description

`HEARTBEAT_INTERVAL_MS = 30000` is currently a constant with no associated code — the comment explicitly says "POST not yet implemented". This task adds the actual heartbeat POST loop: a file-scope `static unsigned long lastHeartbeatMs` variable and a 4-line timer check at the top of `loop()` that calls `ensureWiFi()` + `httpPostJson("/api/arduino/heartbeat", ...)` every 30 seconds.

This single change satisfies R023 on two fronts: (1) the periodic POST provides an RF burst that keeps powerbank current above auto-shutoff threshold during idle periods between card taps; (2) the heartbeat reaches the already-live `POST /api/arduino/heartbeat` endpoint (web_app.py), which emits `arduino_wifi_status {online: True}` to the cashier UI, making the WiFi badge go green.

No backend changes. No Python changes. Firmware-only.

## Steps

1. Declare `static unsigned long lastHeartbeatMs = 0;` at file scope — place it immediately before the `setup()` function so it survives across `loop()` calls. A plain local variable inside `loop()` would reset to 0 on every call, causing the heartbeat to fire every iteration instead of every 30s.

2. Inside `loop()`, immediately after the `handleIncomingSerial()` call (line ~474) and before the LCD display code, insert:
   ```cpp
   // ── Heartbeat: keep powerbank alive + drive WiFi badge in cashier UI ──
   unsigned long now = millis();
   if (now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS) {
     lastHeartbeatMs = now;
     ensureWiFi();
     httpPostJson("/api/arduino/heartbeat", "{\"status\":\"ok\"}");
   }
   ```
   The check MUST be placed before the `if (!found) return;` early exit at line ~519 — otherwise the heartbeat never fires during idle periods (no card in range).

3. Update the `HEARTBEAT_INTERVAL_MS` constant comment (line ~71):
   - From: `// S04: heartbeat stub — POST not yet implemented`
   - To: `// 30s heartbeat interval — POST to /api/arduino/heartbeat keeps powerbank alive and drives WiFi badge in cashier UI`

## Must-Haves

- [ ] `lastHeartbeatMs` declared at file scope (not inside `loop()` — must be `static` or global)
- [ ] Timer check placed immediately after `handleIncomingSerial()`, before any NFC scan code and before `if (!found) return;`
- [ ] Timer comparison uses unsigned long: `now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS`
- [ ] `ensureWiFi()` called inside the heartbeat block (handles WiFi reconnect before POST)
- [ ] `httpPostJson("/api/arduino/heartbeat", ...)` body is `{"status":"ok"}` — no sensitive data logged
- [ ] `HEARTBEAT_INTERVAL_MS` constant comment updated; no remaining "stub" or "not yet implemented" text

## Verification

- `grep -n "lastHeartbeatMs" arduino/bankongseton_rfid/bankongseton_rfid.ino` — must show a file-scope line (before `void setup()` or `void loop()`)
- `grep -n "httpPostJson.*heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino` — must return a match
- `grep -n "HEARTBEAT_INTERVAL_MS" arduino/bankongseton_rfid/bankongseton_rfid.ino` — comment must not contain "stub" or "not yet implemented"
- `grep -n "ensureWiFi" arduino/bankongseton_rfid/bankongseton_rfid.ino` — heartbeat call site must appear in proximity to the httpPostJson heartbeat line

## Observability Impact

- Signals added/changed: Arduino Serial will print `HTTP: POST /api/arduino/heartbeat` (via existing `httpPostJson` Serial logging) every 30s during idle — visible in Serial Monitor as proof of heartbeat firing
- How a future agent inspects this: `grep -n "heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino` shows the call site; Flask access log `POST /api/arduino/heartbeat 200` confirms server receives it; cashier UI WiFi badge turns green within 30s of flashing
- Failure state exposed: 401 in access log → `SECRET_API_KEY` in `secrets.h` doesn't match `ARDUINO_API_KEY` in Flask `.env`; badge stays red → heartbeat never posted (check Serial Monitor for timer firing)

## Inputs

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — `HEARTBEAT_INTERVAL_MS = 30000` constant at line 71 (stub comment); `ensureWiFi()` at ~line 280; `httpPostJson(path, body)` at ~line 306; `loop()` at line 472 with `handleIncomingSerial()` as first call; `if (!found) return;` at line ~519
- S01 summary: `httpPostJson(path, body)` and `ensureWiFi()` are fully implemented and tested via S01 — heartbeat just needs a one-liner call into each
- S03 summary: `POST /api/arduino/heartbeat` live in `web_app.py`; `#wifiBadge` and `arduino_wifi_status` socket listener fully wired in `cashier_index.html` — badge goes green the moment first heartbeat lands

## Expected Output

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — `lastHeartbeatMs` file-scope variable; 4-line timer check at top of `loop()` calling `ensureWiFi()` + `httpPostJson("/api/arduino/heartbeat", ...)`; updated constant comment
