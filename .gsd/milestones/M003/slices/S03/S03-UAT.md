# S03: WiFi Status Indicator — UAT

**Milestone:** M003
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S03 is contract-level proof — the heartbeat endpoint, status REST endpoint, and badge DOM/JS wiring are all verifiable structurally and via Python compile. Runtime badge color change (green) requires S04 firmware heartbeat POST to exist; that runtime validation is explicitly deferred to S04. The verify script covers all 12 structural checks.

## Preconditions

1. `bash scripts/verify-m003-s03.sh` exits 0 (12/12 checks) — this is the canonical pre-check
2. Python 3.x available in PATH
3. `backend/dashboard/web_app.py` and `backend/dashboard/cashier/cashier_routes.py` accessible

## Smoke Test

Run `bash scripts/verify-m003-s03.sh` and confirm output ends with:
```
Results: 12 passed, 0 failed
M003/S03 verification PASSED ✓
```

## Test Cases

### 1. Heartbeat endpoint has correct auth guard

1. Grep `web_app.py` for `api_key` check pattern inside the heartbeat route:
   ```
   grep -A 10 "arduino/heartbeat" backend/dashboard/web_app.py
   ```
2. Confirm the API key guard is present — same pattern as `arduino_card_read()`.
3. **Expected:** The route contains a check against `ARDUINO_API_KEY` and returns a 401/error response when the key is missing or wrong. No route handler skips the guard.

### 2. ARDUINO_WIFI_OFFLINE_S is env-configurable

1. Grep `web_app.py` for the constant definition:
   ```
   grep "ARDUINO_WIFI_OFFLINE_S" backend/dashboard/web_app.py
   ```
2. **Expected:** Line reads `ARDUINO_WIFI_OFFLINE_S = int(os.environ.get("ARDUINO_WIFI_OFFLINE_S", "60"))` — default 60, overridable via env var. Not a bare literal.

### 3. arduino_last_heartbeat initialized to float at startup

1. Grep `web_app.py` for the initialization:
   ```
   grep "arduino_last_heartbeat" backend/dashboard/web_app.py
   ```
2. **Expected:** `app.arduino_last_heartbeat = 0.0` appears after `app.socketio = socketio` in the app startup block. Value is `0.0` (float), not `None` or `0` (int).

### 4. Heartbeat emits correct SocketIO event

1. Grep `web_app.py` for the socketio emit in the heartbeat route:
   ```
   grep "arduino_wifi_status" backend/dashboard/web_app.py
   ```
2. **Expected:** `socketio.emit("arduino_wifi_status", ...)` present. Payload includes `online` and `last_seen_s` keys.

### 5. Status REST endpoint is JWT-protected

1. Grep `cashier_routes.py` for the status route and its decorator:
   ```
   grep -B 2 "arduino-wifi-status" backend/dashboard/cashier/cashier_routes.py
   ```
2. **Expected:** `@jwt_required` (or `@jwt_required(roles=[...])`) appears immediately above the route decorator. No unprotected path to the handler.

### 6. Status endpoint returns -1.0 sentinel when never heartbeated

1. Read the `arduino_wifi_status()` function body in `cashier_routes.py`.
2. **Expected:** When `last_hb == 0` (never heartbeated), `last_seen_s` is set to `-1.0` (explicit sentinel) rather than computing `time.time() - 0.0` (which would be a large positive number and could be misread as "seen recently").

### 7. WiFi badge span exists in cashier header DOM

1. Grep `cashier_index.html` for the badge span:
   ```
   grep "wifiBadge" backend/dashboard/cashier/templates/cashier_index.html
   ```
2. **Expected:** At minimum two hits — the span definition (`id="wifiBadge"`) and at least one JS reference (`wifiBadge`). The span carries class `wifi-badge offline` as its initial state.

### 8. arduino_wifi_status socket listener wired in initWebSocket()

1. Grep `cashier_index.html` for the socket listener:
   ```
   grep "arduino_wifi_status" backend/dashboard/cashier/templates/cashier_index.html
   ```
2. **Expected:** `socket.on('arduino_wifi_status', ...)` present inside or near `initWebSocket()`. Handler calls `updateWifiBadge(data)` and sets `arduinoConnected`.

### 9. Old COM-port-only alert text is gone

1. Check that neither `checkout()` nor `quickPay()` still has the old message:
   ```
   grep "COM port first" backend/dashboard/cashier/templates/cashier_index.html
   ```
2. **Expected:** No output — zero matches. The old string `"Please connect to a COM port first."` (or any variant ending in "first") is fully replaced.

3. Confirm the replacement text is present:
   ```
   grep "check COM port or WiFi" backend/dashboard/cashier/templates/cashier_index.html
   ```
4. **Expected:** Two matches — one in `checkout()` and one in `quickPay()`.

### 10. Both Python files compile cleanly

1. Run:
   ```
   python -m py_compile backend/dashboard/web_app.py && echo "web_app OK"
   python -m py_compile backend/dashboard/cashier/cashier_routes.py && echo "cashier_routes OK"
   ```
2. **Expected:** Both print OK, exit code 0. No syntax errors, no import errors at compile time.

## Edge Cases

### WiFi offline does not disable Pay Now when serial is connected

1. In a running cashier UI session, open browser DevTools console.
2. Manually simulate serial connect: call `updateArduinoStatus('connected')` (or connect a real COM port).
3. Confirm `window.arduinoConnected === true`.
4. Now simulate a WiFi offline event: run `updateWifiBadge({online: false, last_seen_s: 120})`.
5. **Expected:** `window.arduinoConnected` remains `true`. The badge turns red (WiFi offline), but the Pay Now button stays enabled. Serial connection wins.

### Badge starts red (correct offline initial state)

1. Load the cashier UI fresh (no Arduino heartbeat POSTed).
2. Check `document.getElementById('wifiBadge').className`.
3. **Expected:** `"wifi-badge offline"` — badge is red. This is the correct initial state; no Arduino has checked in yet.

### Never-heartbeated status endpoint returns online: false

1. Call the status REST endpoint before any Arduino heartbeat has been sent:
   ```
   curl -s http://localhost:5000/cashier/api/arduino-wifi-status \
     -H "Authorization: Bearer <cashier-jwt>"
   ```
2. **Expected:** `{"online": false, "last_seen_s": -1.0}`. The `-1.0` sentinel clearly distinguishes "never heartbeated" from "heartbeated 120 seconds ago (timed out)".

### Unauthorized heartbeat POST returns 401

1. POST to the heartbeat endpoint without a valid API key:
   ```
   curl -s -X POST http://localhost:5000/api/arduino/heartbeat
   ```
2. **Expected:** HTTP 401, body `{"error": "Unauthorized"}`. Flask WARNING log: `event=arduino_heartbeat_rejected reason=invalid_api_key`.

## Failure Signals

- `bash scripts/verify-m003-s03.sh` shows any FAIL — specific check letter tells you which file and what's missing
- `python -m py_compile` exits non-zero — syntax error introduced during edits
- `grep "COM port first" cashier_index.html` returns output — old alert text not replaced in one or both functions
- `grep "wifiBadge" cashier_index.html` returns no output — badge span was not added or was removed
- `grep "arduino_wifi_status" cashier_index.html` returns no output — socket listener missing
- `document.getElementById('wifiBadge')` returns null in browser console — span not in rendered DOM

## Requirements Proved By This UAT

- R022 (Arduino WiFi Status in Cashier UI) — contract-level: heartbeat endpoint with API key auth confirmed, status REST endpoint with JWT confirmed, badge span in DOM confirmed, socket listener wired, arduinoConnected set from WiFi path, old COM-port-only alert text replaced

## Not Proven By This UAT

- Badge turning green (requires live Arduino heartbeat POST — S04 firmware work)
- Badge toggling green → red after 60s silence (requires real-time observation with live Arduino)
- `fetchArduinoWifiStatus()` REST prime actually updating the badge on page load (requires running Flask server + valid cashier JWT)
- Pay Now button becoming enabled purely via WiFi heartbeat with no COM port selected (requires live cashier session + live Arduino)
- All runtime operational behavior — deferred to S04 human UAT which covers powerbank hardening + full wireless standalone validation

## Notes for Tester

The badge will be red in any test environment without a live Arduino POSTing to `/api/arduino/heartbeat`. This is correct and expected — it is not a bug. The slice proves the wiring exists; S04 proves the full runtime path. Do not report "badge is red" as a failure unless you have confirmed a heartbeat POST was sent and received (check Flask access log for `POST /api/arduino/heartbeat 200`).

When testing the status REST endpoint, use a freshly-issued cashier JWT (`/cashier/login`). Expired JWTs return 401 which looks similar to "endpoint missing" — check the HTTP status code first.
