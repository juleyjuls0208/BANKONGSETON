---
id: T01
parent: S04
milestone: M003
provides:
  - File-scope lastHeartbeatMs variable at line 427 (before setup())
  - 4-line timer block in loop() at lines 479-485: millis() check → ensureWiFi() → httpPostJson("/api/arduino/heartbeat", {"status":"ok"})
  - Updated HEARTBEAT_INTERVAL_MS comment — stub text removed
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
key_decisions:
  - Heartbeat block placed immediately after handleIncomingSerial() and before the NFC uid[] declaration — ensures it fires during idle periods and is not gated by the if (!found) return at line 530
  - lastHeartbeatMs declared static at file scope (not inside loop()) so it accumulates across iterations; plain local would reset to 0 each call and fire every iteration
patterns_established:
  - Powerbank keep-alive pattern: periodic POST to a live endpoint during idle avoids current-starve shutoff without any dedicated hardware change
observability_surfaces:
  - Serial Monitor: "HTTP: POST /api/arduino/heartbeat" printed by httpPostJson every 30s during idle — confirms timer fires
  - Flask access log: "POST /api/arduino/heartbeat 200" on each interval — confirms network path
  - Cashier UI #wifiBadge turns green within 30s of first heartbeat via arduino_wifi_status Socket.IO event
  - Failure: badge stays red → check Serial Monitor for gap >30s between heartbeat prints; 401 in access log → SECRET_API_KEY/ARDUINO_API_KEY mismatch
  - grep -n "lastHeartbeatMs" arduino/bankongseton_rfid/bankongseton_rfid.ino — shows declaration at line 427 and use at lines 481-482
duration: 15m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add firmware heartbeat POST loop

**30-second POST heartbeat loop added to bankongseton_rfid.ino — keeps powerbank alive during idle and drives the cashier WiFi badge green.**

## What Happened

Three surgical edits to `arduino/bankongseton_rfid/bankongseton_rfid.ino`:

1. **File-scope variable** — `static unsigned long lastHeartbeatMs = 0;` inserted at line 427, immediately before `void setup()`. This is the only placement that survives across `loop()` calls; a plain local would reset to 0 every iteration, triggering the POST on every loop pass instead of every 30 s.

2. **Timer block in loop()** — 4-line block inserted at lines 479-485, immediately after `handleIncomingSerial()` and before the NFC `uid[]` declaration and all NFC scan code. Placement before the `if (!found) return;` early exit (line 530) is the critical constraint: the heartbeat must fire during idle periods when no card is in range. The comparison uses `unsigned long` arithmetic to handle millis() rollover correctly.

3. **Constant comment updated** — `HEARTBEAT_INTERVAL_MS` comment at line 71 changed from "S04: heartbeat stub — POST not yet implemented" to the authoritative description. No stub text remains anywhere in the file.

Also fixed the two S04-PLAN.md observability gaps flagged in pre-flight: added `## Observability / Diagnostics` section and a failure-path diagnostic check in `## Verification`.

## Verification

```
grep -n "lastHeartbeatMs" arduino/bankongseton_rfid/bankongseton_rfid.ino
# → 427: static unsigned long lastHeartbeatMs = 0; (file-scope, before setup() at 429)
# → 481: if (now - lastHeartbeatMs >= ...)
# → 482: lastHeartbeatMs = now;

grep -n "httpPostJson.*heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino
# → 484: httpPostJson("/api/arduino/heartbeat", "{\"status\":\"ok\"}");

grep -n "HEARTBEAT_INTERVAL_MS" arduino/bankongseton_rfid/bankongseton_rfid.ino
# → 71: static const int HEARTBEAT_INTERVAL_MS = 30000;  // 30s heartbeat interval...
# → 481: if (now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS)

grep -n "ensureWiFi" arduino/bankongseton_rfid/bankongseton_rfid.ino
# → 483: ensureWiFi();  (inside heartbeat block, adjacent to httpPostJson at 484)

grep "stub\|not yet implemented" arduino/bankongseton_rfid/bankongseton_rfid.ino
# → (no output) — CLEAN

grep -n "if (!found) return" arduino/bankongseton_rfid/bankongseton_rfid.ino
# → 530: if (!found) return;  — heartbeat block (479-485) is safely before this
```

All must-haves confirmed. Slice-level script (`verify-m003-s04.sh`) does not exist yet — that is created in T02.

## Diagnostics

- `grep -n "heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino` — shows constant (line 71), timer check (line 481), and POST call (line 484)
- Serial Monitor during idle: `HTTP: POST /api/arduino/heartbeat` line every 30 s confirms the timer is firing and WiFi is up
- Flask access log `POST /api/arduino/heartbeat 200` confirms server receives the request
- 401 response → `SECRET_API_KEY` in `secrets.h` does not match `ARDUINO_API_KEY` in Flask `.env`
- Badge stays red after >30 s → heartbeat not reaching server; check Serial Monitor for WiFi reconnect failures from `ensureWiFi()`

## Deviations

none — implemented exactly as specified in the task plan

## Known Issues

none

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — added lastHeartbeatMs file-scope variable and 4-line heartbeat timer block in loop(); updated HEARTBEAT_INTERVAL_MS comment
- `.gsd/milestones/M003/slices/S04/S04-PLAN.md` — added Observability/Diagnostics section and failure-path diagnostic check in Verification (pre-flight fixes)
