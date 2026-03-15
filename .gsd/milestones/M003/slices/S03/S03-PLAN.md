# S03: WiFi Status Indicator

**Goal:** Cashier UI shows a green WiFi badge when the Arduino is heartbeating and red when offline; `arduinoConnected` is set via the WiFi heartbeat path so "Pay Now" enables without a COM port.

**Demo:** POST to `/api/arduino/heartbeat` with valid API key → `arduino_wifi_status {online: true, last_seen_s: <float>}` socket event fires → cashier badge turns green, checkout button enables. 60 seconds pass without heartbeat → `GET /cashier/api/arduino-wifi-status` returns `online: false` → badge red. Serial connect path unchanged.

## Must-Haves

- `POST /api/arduino/heartbeat` in `web_app.py`: validates API key, updates `app.arduino_last_heartbeat`, emits `arduino_wifi_status {online, last_seen_s}` socket event
- `ARDUINO_WIFI_OFFLINE_S = 60` constant in `web_app.py` (configurable threshold)
- `app.arduino_last_heartbeat = 0.0` initialized after `app.socketio = socketio` in `web_app.py`
- `GET /cashier/api/arduino-wifi-status` in `cashier_routes.py`: JWT-protected, returns `{online, last_seen_s}`
- WiFi badge in `cashier_index.html` header (`.wifi-badge` span), CSS green/red states
- `socket.on('arduino_wifi_status', ...)` in `initWebSocket()` sets `arduinoConnected = data.online` directly (NOT via `updateArduinoStatus()`) and updates badge
- `fetchArduinoWifiStatus()` called on DOMContentLoaded to prime badge state from REST endpoint
- Alert text in `checkout()` and `quickPay()` updated from "connect to a COM port first" to "check COM port or WiFi"
- `python -m py_compile` exits 0 on `web_app.py` and `cashier_routes.py`
- `bash scripts/verify-m003-s03.sh` exits 0

## Proof Level

- This slice proves: contract-level (structural grepping + compile checks)
- Real runtime required: no — badge will stay red until S04 adds firmware heartbeat POST; correct initial state
- Human/UAT required: no — runtime validation deferred to S04

## Verification

- `python -m py_compile backend/dashboard/web_app.py` exits 0
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0
- `bash scripts/verify-m003-s03.sh` exits 0 (12 checks: 10 grep + 2 compile)
- Failure path (diagnostic): `curl -s -X POST http://localhost:5000/api/arduino/heartbeat` (no key) → `{"error":"Unauthorized"}` 401 — confirms auth guard active; 401 logged at WARNING in Flask output

## Observability / Diagnostics

- Runtime signals: Flask access log `POST /api/arduino/heartbeat 200` on each heartbeat; SocketIO `arduino_wifi_status` event visible in browser DevTools console
- Inspection surfaces: `GET /cashier/api/arduino-wifi-status` — returns `{online, last_seen_s}` readable by curl; cashier badge color (green/red) visual signal
- Failure visibility: `last_seen_s` in both socket payload and REST response shows age of last heartbeat; `online=false` when never heartbeated or > 60s since last
- Redaction constraints: no secrets in payloads; `X-API-Key` validated server-side, not echoed

## Integration Closure

- Upstream surfaces consumed: `ARDUINO_API_KEY` (module-scope in `web_app.py`), `app.socketio` (attached at startup), `@jwt_required` decorator pattern, `getattr(current_app, ...)` pattern
- New wiring introduced: `app.arduino_last_heartbeat` as shared state; `arduino_wifi_status` socket event; `/cashier/api/arduino-wifi-status` REST endpoint; `arduinoConnected` set from WiFi path without touching serial indicator
- What remains before milestone is usable end-to-end: S04 must add firmware heartbeat POST logic — until then badge stays red (correct offline state)

## Tasks

- [x] **T01: Add heartbeat endpoint + status query endpoint + verify script** `est:30m`
  - Why: The WiFi badge needs a backend to receive heartbeats (`web_app.py`) and to serve initial badge state on page load (`cashier_routes.py`); the verify script is the slice's objective stopping condition
  - Files: `backend/dashboard/web_app.py`, `backend/dashboard/cashier/cashier_routes.py`, `scripts/verify-m003-s03.sh`
  - Do: In `web_app.py`: add `import time` to top-level imports; add `ARDUINO_WIFI_OFFLINE_S = 60` constant immediately after `ARDUINO_API_KEY` line; add `app.arduino_last_heartbeat = 0.0` immediately after `app.socketio = socketio`; add `POST /api/arduino/heartbeat` route after `arduino_card_read()` — copy API key guard verbatim, update `app.arduino_last_heartbeat = time.time()`, compute `last_seen_s = time.time() - app.arduino_last_heartbeat`, emit `socketio.emit("arduino_wifi_status", {"online": True, "last_seen_s": last_seen_s})`, log `event=arduino_heartbeat`, return 200. In `cashier_routes.py`: add `GET /cashier/api/arduino-wifi-status` route after `queue_status()` — `@jwt_required(roles=['cashier','admin'])`, read `last_hb = getattr(current_app, 'arduino_last_heartbeat', 0.0)`, compute `last_seen_s = time.time() - last_hb`, `online = (last_hb > 0) and (last_seen_s < current_app.config.get('ARDUINO_WIFI_OFFLINE_S', 60))`, return `jsonify({online, last_seen_s})`. Write `scripts/verify-m003-s03.sh` with 10 grep checks (see task plan).
  - Verify: `python -m py_compile backend/dashboard/web_app.py` exits 0; `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0; `bash scripts/verify-m003-s03.sh` exits 0
  - Done when: both files compile; verify script 10/10 pass

- [x] **T02: Add WiFi badge, socket listener, and alert text to cashier UI** `est:20m`
  - Why: The backend is useless without a UI element to display badge state; `arduinoConnected` must be set from the WiFi path so checkout enables without a COM port
  - Files: `backend/dashboard/cashier/templates/cashier_index.html`
  - Do: In `<style>`: add `.wifi-badge` CSS class with green/red states (`.wifi-badge.online` / `.wifi-badge.offline`). In the `.arduino-status` div (after `<button class="connect-btn">`): add `<span class="wifi-badge offline" id="wifiBadge">WiFi</span>`. Add `async function fetchArduinoWifiStatus()` that GETs `/cashier/api/arduino-wifi-status` with JWT header and calls `updateWifiBadge(data)`. Add `function updateWifiBadge(data)` that sets `arduinoConnected = arduinoConnected || data.online` (WiFi sets to true; doesn't override serial true to false) and toggles `wifiBadge` class between `online`/`offline`. Call `fetchArduinoWifiStatus()` in the `DOMContentLoaded` block. In `initWebSocket()`: add `socket.on('arduino_wifi_status', function(data) { arduinoConnected = arduinoConnected || data.online; updateWifiBadge(data); });` after the `nfc_payment` handler. Update alert text in `checkout()` and `quickPay()` from `"Arduino not connected! Please connect to a COM port first."` to `"Arduino not connected — check COM port or WiFi."`.
  - Verify: `bash scripts/verify-m003-s03.sh` exits 0 (checks badge and listener presence + alert text); open `cashier_index.html` source and confirm no old alert text remains
  - Done when: verify script still passes; both alert strings updated; badge span in DOM; socket listener wired

## Files Likely Touched

- `backend/dashboard/web_app.py`
- `backend/dashboard/cashier/cashier_routes.py`
- `backend/dashboard/cashier/templates/cashier_index.html`
- `scripts/verify-m003-s03.sh`
