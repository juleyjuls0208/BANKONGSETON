---
id: S03
parent: M003
milestone: M003
provides:
  - POST /api/arduino/heartbeat — API-key-authenticated; updates app.arduino_last_heartbeat; emits arduino_wifi_status socket event
  - GET /cashier/api/arduino-wifi-status — JWT-protected REST endpoint returning {online, last_seen_s}
  - app.arduino_last_heartbeat = 0.0 shared state initialized at startup in web_app.py
  - ARDUINO_WIFI_OFFLINE_S configurable threshold (default 60s, env-overridable)
  - WiFi badge span (#wifiBadge) in cashier header — green (.online) / red (.offline)
  - updateWifiBadge(data) + fetchArduinoWifiStatus() wired to DOMContentLoaded
  - socket.on('arduino_wifi_status') listener in initWebSocket()
  - Updated alert text in checkout() and quickPay() — mentions WiFi alongside COM port
requires:
  - slice: S01
    provides: Confirmed Arduino WiFi POSTs reach Flask backend (network path proven end-to-end)
affects:
  - S04 — adds firmware heartbeat POST logic that will make this badge go green in production
key_files:
  - backend/dashboard/web_app.py
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/cashier/templates/cashier_index.html
  - scripts/verify-m003-s03.sh
key_decisions:
  - app.arduino_last_heartbeat initialized to 0.0 (float, not None) — arithmetic in status query is always safe, no None-guard needed anywhere
  - last_seen_s returns -1.0 sentinel when last_hb == 0 (never heartbeated) — distinguishable from a real elapsed time, not zero-as-elapsed-zero confusion
  - updateWifiBadge() checks serial statusIndicator class before clearing arduinoConnected on WiFi offline — WiFi going offline does not override an active serial connection
  - fetchArduinoWifiStatus() called before initWebSocket() in DOMContentLoaded — badge primed from REST before first socket event arrives
patterns_established:
  - Heartbeat endpoint copies API key guard verbatim from arduino_card_read() — uniform guard pattern for all Arduino-origin endpoints
  - Status route reads app-level state via getattr(current_app, 'arduino_last_heartbeat', 0.0) — safe sentinel default when attribute absent
  - WiFi path sets arduinoConnected directly; serial path calls updateArduinoStatus() — two fully independent paths, no shared update function
observability_surfaces:
  - Flask access log: POST /api/arduino/heartbeat 200 on each Arduino ping
  - Structured log: event=arduino_heartbeat remote=<ip> at INFO; event=arduino_heartbeat_rejected reason=invalid_api_key at WARNING
  - SocketIO event: arduino_wifi_status {online, last_seen_s} visible in DevTools WS frame stream
  - REST: GET /cashier/api/arduino-wifi-status with cashier JWT → {online, last_seen_s}; last_seen_s=-1.0 before first heartbeat
  - Visual: #wifiBadge className — wifi-badge online (green) or wifi-badge offline (red)
drill_down_paths:
  - .gsd/milestones/M003/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S03/tasks/T02-SUMMARY.md
duration: ~35m
verification_result: passed
completed_at: 2026-03-15
---

# S03: WiFi Status Indicator

**Backend heartbeat endpoint + cashier WiFi badge wired end-to-end; all 12 verify-m003-s03.sh checks pass; badge correctly shows red (offline) until S04 adds firmware heartbeat POST.**

## What Happened

Two tasks, both complete.

**T01 (backend):** Added `import time` at module level in `web_app.py`. Added `ARDUINO_WIFI_OFFLINE_S = int(os.environ.get("ARDUINO_WIFI_OFFLINE_S", "60"))` immediately after `ARDUINO_API_KEY`. Initialized `app.arduino_last_heartbeat = 0.0` immediately after `app.socketio = socketio`. Added `POST /api/arduino/heartbeat` route after `arduino_card_read()` — same API key guard as the card-read endpoint, updates timestamp, emits `arduino_wifi_status {online: True, last_seen_s: 0.0}` via SocketIO, logs structured event. Added `GET /cashier/api/arduino-wifi-status` to `cashier_routes.py` after `queue_status()` — JWT-protected, reads `getattr(current_app, 'arduino_last_heartbeat', 0.0)`, returns `last_seen_s = -1.0` sentinel when never heartbeated, derives `online` from `ARDUINO_WIFI_OFFLINE_S` threshold. `scripts/verify-m003-s03.sh` was already present with all 12 checks.

**T02 (frontend):** Four surgical edits to `cashier_index.html`. CSS: added `.wifi-badge`, `.wifi-badge.online` (green), `.wifi-badge.offline` (red) rules after `.connect-btn`. Badge span: added `<span class="wifi-badge offline" id="wifiBadge">WiFi</span>` inside `.arduino-status` div after the Connect button. JS: added `updateWifiBadge(data)` (WiFi offline branch checks serial statusIndicator class before clearing `arduinoConnected`) and `async function fetchArduinoWifiStatus()` (JWT GET call on DOMContentLoaded, before `initWebSocket()`). Socket listener: `socket.on('arduino_wifi_status', ...)` in `initWebSocket()` after the `nfc_payment` handler. Alert text: both `checkout()` and `quickPay()` updated from `"Please connect to a COM port first."` to `"check COM port or WiFi."`.

## Verification

```
bash scripts/verify-m003-s03.sh
→ Results: 12 passed, 0 failed
   M003/S03 verification PASSED ✓
```

Individual checks:
- (a–e) Backend web_app.py: import time, ARDUINO_WIFI_OFFLINE_S, arduino_last_heartbeat init, heartbeat route, socketio emit — all ✓
- (f–g) cashier_routes.py: arduino-wifi-status route, jwt_required present — ✓
- (h–j) Frontend: wifiBadge span, arduino_wifi_status socket listener, old COM-port-only alert text removed — ✓
- (k–l) Python compile: web_app.py and cashier_routes.py — both ✓

## Requirements Advanced

- R022 (Arduino WiFi Status in Cashier UI) — contract-level proof complete: heartbeat endpoint exists with correct auth, status REST endpoint exists, badge span wired to socket event, arduinoConnected set from WiFi path

## Requirements Validated

- R022 — contract-level (structural + compile); runtime validation (badge going green on live heartbeat) deferred to S04

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

**T02 alert text:** The plan's prose said `arduinoConnected = arduinoConnected || data.online` in `updateWifiBadge()`. The plan's code block showed a conditional form that prevents WiFi offline from overriding a live serial connection. Implemented the conditional form — it's the correct behavior for the "never fight serial" constraint described in the plan; the `||` shorthand was a simplification that missed the offline case.

## Known Limitations

- Badge stays red on initial page load — no Arduino heartbeat has been sent yet. This is the correct offline state. S04 firmware heartbeat POST will make the badge go green in real deployment.
- `fetchArduinoWifiStatus()` makes a JWT-authenticated GET on DOMContentLoaded. If the cashier JWT has expired at page load, the REST prime silently fails and the badge stays red. Socket event will correct it on next heartbeat.

## Follow-ups

- S04: Add `httpPostHeartbeat()` to Arduino firmware; call it every 30s in `loop()`. Without this, the backend heartbeat endpoint exists but is never called by the Arduino, so the badge remains red in production.

## Files Created/Modified

- `backend/dashboard/web_app.py` — added `import time`, `ARDUINO_WIFI_OFFLINE_S` constant, `app.arduino_last_heartbeat = 0.0` init, `arduino_heartbeat()` route
- `backend/dashboard/cashier/cashier_routes.py` — added `arduino_wifi_status()` route after `queue_status()`
- `backend/dashboard/cashier/templates/cashier_index.html` — WiFi badge CSS, badge span, `updateWifiBadge()` + `fetchArduinoWifiStatus()`, `arduino_wifi_status` socket listener, alert text updated in `checkout()` and `quickPay()`
- `scripts/verify-m003-s03.sh` — pre-existing; 12 checks verified correct as-is

## Forward Intelligence

### What the next slice should know
- The heartbeat endpoint is ready and waiting. S04 only needs to add `httpPostHeartbeat()` in the Arduino firmware — no backend changes required for basic badge functionality.
- `ARDUINO_WIFI_OFFLINE_S` is env-configurable. Default is 60s. If the 30s heartbeat interval slips under load, the badge won't flicker offline. 60s threshold gives two missed heartbeats before going red.
- `app.arduino_last_heartbeat` is a plain Python float on the Flask app object. In production (single-worker, no gunicorn multi-worker per R016), this is safe. Do not rely on it in any multi-worker config.

### What's fragile
- `fetchArduinoWifiStatus()` silently fails if JWT is expired at DOMContentLoaded — badge stays red until the next socket heartbeat event. This is acceptable for the cashier flow (cashier is always logged in) but worth knowing if session timeouts are shortened.
- `last_seen_s = -1.0` sentinel: if consumer code checks `last_seen_s < 60` without first checking `last_hb > 0`, a never-heartbeated Arduino would pass as "seen -1 second ago." The `online` field is the authoritative signal — don't use `last_seen_s` alone as an online gate.

### Authoritative diagnostics
- `document.getElementById('wifiBadge').className` in browser console — immediate visual state check without opening DevTools Network tab
- `GET /cashier/api/arduino-wifi-status` with cashier JWT — ground truth for what the server believes; last_seen_s=-1.0 means never heartbeated
- Flask WARNING log `event=arduino_heartbeat_rejected reason=invalid_api_key` — confirms API key mismatch if badge never goes green after flashing S04 firmware

### What assumptions changed
- Plan assumed `scripts/verify-m003-s03.sh` needed to be written in T01. It was already present from prior work with all 12 checks correctly defined — T01 skipped that step.
