---
estimated_steps: 6
estimated_files: 3
---

# T01: Add heartbeat endpoint + status query endpoint + verify script

**Slice:** S03 — WiFi Status Indicator
**Milestone:** M003

## Description

Wire the backend half of the WiFi status feature: a `POST /api/arduino/heartbeat` endpoint in `web_app.py` that receives Arduino pings, updates shared timestamp state, and emits the `arduino_wifi_status` socket event; a `GET /cashier/api/arduino-wifi-status` endpoint in `cashier_routes.py` that lets the cashier page prime its badge state on load; and a verify script with 10 structural grep checks.

Both routes follow the exact patterns already established in the codebase: API key auth matches `arduino_card_read()`; app attribute state matches the `current_app.arduino_*` pattern; JWT auth matches every other cashier API route.

## Steps

1. **`web_app.py` — add `import time`**: Insert `import time` alongside the existing top-level imports (near `import datetime`). Do not add it inline — it must be module-level.

2. **`web_app.py` — add constants**: Immediately after the `ARDUINO_API_KEY = ...` line, add:
   ```python
   ARDUINO_WIFI_OFFLINE_S = int(os.environ.get("ARDUINO_WIFI_OFFLINE_S", "60"))
   ```

3. **`web_app.py` — initialize `app.arduino_last_heartbeat`**: Immediately after `app.socketio = socketio`, add:
   ```python
   app.arduino_last_heartbeat = 0.0
   ```

4. **`web_app.py` — add heartbeat route**: After the closing `return jsonify({"status": "ok"}), 200` of `arduino_card_read()`, add:
   ```python
   @app.route("/api/arduino/heartbeat", methods=["POST"])
   def arduino_heartbeat():
       """
       WiFi keep-alive / status heartbeat endpoint for Arduino UNO R4 WiFi.
       Arduino POSTs every HEARTBEAT_INTERVAL_MS ms with X-API-Key header.
       Emits arduino_wifi_status SocketIO event to cashier UI.
       """
       api_key = request.headers.get("X-API-Key", "")
       if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
           logger.warning(
               "event=arduino_heartbeat_rejected reason=invalid_api_key remote=%s",
               request.remote_addr,
           )
           return jsonify({"error": "Unauthorized"}), 401

       app.arduino_last_heartbeat = time.time()
       last_seen_s = 0.0  # just updated
       socketio.emit("arduino_wifi_status", {"online": True, "last_seen_s": last_seen_s})
       logger.info("event=arduino_heartbeat remote=%s", request.remote_addr)
       return jsonify({"status": "ok"}), 200
   ```

5. **`cashier_routes.py` — add status query route**: After the closing `except Exception` block of `queue_status()`, add:
   ```python
   @cashier_bp.route('/api/arduino-wifi-status', methods=['GET'])
   @jwt_required(roles=['cashier', 'admin'])
   def arduino_wifi_status():
       """GET /cashier/api/arduino-wifi-status — returns {online, last_seen_s}."""
       try:
           last_hb = getattr(current_app, 'arduino_last_heartbeat', 0.0)
           now = time.time()
           last_seen_s = now - last_hb if last_hb > 0 else -1.0
           offline_threshold = getattr(current_app, 'config', {}).get('ARDUINO_WIFI_OFFLINE_S', 60)
           online = (last_hb > 0) and (last_seen_s < offline_threshold)
           return jsonify({'online': online, 'last_seen_s': round(last_seen_s, 1)})
       except Exception as e:
           logger.error(f"arduino_wifi_status error: {e}", exc_info=True)
           return jsonify({'error': 'An unexpected error occurred'}), 500
   ```
   Note: `time` is already imported in `cashier_routes.py` (line 14). `current_app` is already imported.

6. **Write `scripts/verify-m003-s03.sh`**: 10 structural grep checks covering both Python files and the HTML (the HTML checks pass once T02 is done; include them here so the script is the single stopping condition for the whole slice).

## Must-Haves

- [ ] `import time` present at module level in `web_app.py` (not only inside functions)
- [ ] `ARDUINO_WIFI_OFFLINE_S` constant defined in `web_app.py`
- [ ] `app.arduino_last_heartbeat = 0.0` initialization present in `web_app.py` after `app.socketio`
- [ ] `POST /api/arduino/heartbeat` route present in `web_app.py`
- [ ] `socketio.emit("arduino_wifi_status", ...)` call present in heartbeat handler
- [ ] API key guard in heartbeat handler identical pattern to `arduino_card_read`
- [ ] `GET /cashier/api/arduino-wifi-status` route registered on `cashier_bp`
- [ ] Route is `@jwt_required(roles=['cashier', 'admin'])` protected
- [ ] `python -m py_compile backend/dashboard/web_app.py` exits 0
- [ ] `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0

## Verification

- `python -m py_compile backend/dashboard/web_app.py` exits 0
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0
- `bash scripts/verify-m003-s03.sh` — checks (a)–(e) pass (backend checks); (f)–(j) will pass after T02; (k)–(l) compile checks

## Observability Impact

- Signals added/changed: Flask access log `POST /api/arduino/heartbeat 200` on each Arduino ping; `event=arduino_heartbeat remote=<ip>` structured log entry; SocketIO `arduino_wifi_status` event visible in browser DevTools Network / WS frame tab
- How a future agent inspects this: `curl -X POST http://localhost:5000/api/arduino/heartbeat -H "X-API-Key: $ARDUINO_API_KEY"` → 200; `GET /cashier/api/arduino-wifi-status` with cashier JWT → `{online, last_seen_s}`
- Failure state exposed: 401 on missing/wrong API key logged at WARNING; `online: false` when `arduino_last_heartbeat = 0.0` (never seen) or stale

## Inputs

- `backend/dashboard/web_app.py` — `arduino_card_read()` (lines 256–287) is the template; copy API key guard and socketio.emit pattern verbatim
- `backend/dashboard/cashier/cashier_routes.py` — `queue_status()` (lines 818–828) is the insert point; `getattr(current_app, 'arduino', None)` pattern confirms how to read app-level state from blueprint
- S03-RESEARCH.md — constraint list for import time, initialization order, and circular import avoidance

## Expected Output

- `backend/dashboard/web_app.py` — `import time` added; `ARDUINO_WIFI_OFFLINE_S` constant; `app.arduino_last_heartbeat = 0.0`; `arduino_heartbeat()` route
- `backend/dashboard/cashier/cashier_routes.py` — `arduino_wifi_status()` route after `queue_status()`
- `scripts/verify-m003-s03.sh` — 10-check grep assertion script (exits 0 when all structural requirements met)
