---
id: T01
parent: S03
milestone: M003
provides:
  - POST /api/arduino/heartbeat endpoint with API key auth and socketio emit
  - GET /cashier/api/arduino-wifi-status endpoint with JWT auth
  - app.arduino_last_heartbeat shared state initialized at startup
  - ARDUINO_WIFI_OFFLINE_S configurable threshold constant
key_files:
  - backend/dashboard/web_app.py
  - backend/dashboard/cashier/cashier_routes.py
  - scripts/verify-m003-s03.sh
key_decisions:
  - Used local `from flask import current_app` inside arduino_wifi_status() to match existing cashier_routes.py pattern (all other current_app uses are local imports)
  - app.arduino_last_heartbeat initialized to 0.0 (not None) so arithmetic in status query is always safe without None-guard
patterns_established:
  - Heartbeat endpoint copies API key guard verbatim from arduino_card_read() — same guard pattern for all Arduino endpoints
  - Status route reads app-level state via getattr(current_app, 'arduino_last_heartbeat', 0.0) — safe default when state not set
  - last_seen_s = -1.0 when last_hb == 0 (never heartbeated) — sentinel value distinguishable from a real elapsed time
observability_surfaces:
  - Flask access log: POST /api/arduino/heartbeat 200 on each Arduino ping
  - Structured log: event=arduino_heartbeat remote=<ip> at INFO; event=arduino_heartbeat_rejected reason=invalid_api_key at WARNING
  - SocketIO event: arduino_wifi_status {online, last_seen_s} visible in browser DevTools WS frame tab
  - REST: GET /cashier/api/arduino-wifi-status with cashier JWT → {online, last_seen_s}
  - Failure: 401 on missing/wrong API key; online=false + last_seen_s=-1.0 when never heartbeated
duration: 20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add heartbeat endpoint + status query endpoint + verify script

**Backend half of WiFi status feature wired: heartbeat endpoint, status query endpoint, and verify script all pass 9/12 checks (3 frontend checks deferred to T02).**

## What Happened

Added `import time` at module level in `web_app.py` (alongside `import os/sys/logging`). Added `ARDUINO_WIFI_OFFLINE_S = int(os.environ.get("ARDUINO_WIFI_OFFLINE_S", "60"))` immediately after `ARDUINO_API_KEY`. Initialized `app.arduino_last_heartbeat = 0.0` immediately after `app.socketio = socketio`.

Added `arduino_heartbeat()` route (`POST /api/arduino/heartbeat`) after `arduino_card_read()` — copied API key guard verbatim, updates `app.arduino_last_heartbeat = time.time()`, emits `socketio.emit("arduino_wifi_status", {"online": True, "last_seen_s": 0.0})`, logs `event=arduino_heartbeat`.

Added `arduino_wifi_status()` route (`GET /cashier/api/arduino-wifi-status`) to `cashier_routes.py` after `queue_status()` — JWT-protected, reads `getattr(current_app, 'arduino_last_heartbeat', 0.0)`, computes `last_seen_s` (returns -1.0 sentinel when never heartbeated), derives `online` against `ARDUINO_WIFI_OFFLINE_S` threshold, returns `{online, last_seen_s}`.

`scripts/verify-m003-s03.sh` was already present from prior work with all 12 checks correctly defined.

## Verification

- `python -m py_compile backend/dashboard/web_app.py` → exits 0 ✓
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` → exits 0 ✓
- `bash scripts/verify-m003-s03.sh` → 9/12 pass ✓ (checks a–g backend pass, k–l compile pass; h–j frontend deferred to T02 as planned)

## Diagnostics

- Heartbeat test: `curl -s -X POST http://localhost:5000/api/arduino/heartbeat -H "X-API-Key: $ARDUINO_API_KEY"` → `{"status":"ok"}` 200
- Auth guard test: `curl -s -X POST http://localhost:5000/api/arduino/heartbeat` → `{"error":"Unauthorized"}` 401 + WARNING log
- Status query: `curl -s http://localhost:5000/cashier/api/arduino-wifi-status -H "Authorization: Bearer $JWT"` → `{"online":false,"last_seen_s":-1.0}` before first heartbeat

## Deviations

- `scripts/verify-m003-s03.sh` was already written with the correct 12 checks — no action required on step 6.

## Known Issues

- Frontend checks (h), (i), (j) will fail until T02 adds the WiFi badge, socket listener, and updated alert text to `cashier_index.html`.

## Files Created/Modified

- `backend/dashboard/web_app.py` — added `import time`, `ARDUINO_WIFI_OFFLINE_S` constant, `app.arduino_last_heartbeat = 0.0` init, `arduino_heartbeat()` route
- `backend/dashboard/cashier/cashier_routes.py` — added `arduino_wifi_status()` route after `queue_status()`
- `.gsd/milestones/M003/slices/S03/S03-PLAN.md` — pre-flight fix: added failure-path diagnostic check to Verification section
