# S03: WiFi Status Indicator — Research

**Date:** 2026-03-15

## Summary

S03 adds three things: a heartbeat receiver in `web_app.py`, a status query endpoint in `cashier_routes.py`, and a WiFi badge + socket listener in `cashier_index.html`. The backend work is small and follows exact existing patterns. The frontend work is also straightforward — the only non-obvious part is that `arduinoConnected` must be set from two independent code paths (serial and WiFi) without letting the WiFi path clobber the serial status indicator dot, and one alert message string needs updating to be WiFi-aware.

No new libraries needed. No schema migrations. No firmware changes beyond the `HEARTBEAT_INTERVAL_MS` constant already stubbed in S01. The slice is genuinely low-risk.

Key finding: state sharing between the heartbeat handler in `web_app.py` and the status-query route in `cashier_routes.py` is solved by storing `arduino_last_heartbeat` as an attribute on the `app` object — the same pattern already used for `app.arduino`, `app.arduino_port`, `app.arduino_bridge` (cashier_routes.py lines 176–219).

## Recommendation

Follow the existing `arduino_card_read()` + `current_app.arduino_*` patterns exactly. No abstractions needed. Three touch points, each surgical:

1. **`web_app.py`** — add `import time`, initialize `app.arduino_last_heartbeat = 0.0` after app creation, add `POST /api/arduino/heartbeat` route.
2. **`cashier_routes.py`** — add `GET /cashier/api/arduino-wifi-status` route reading `getattr(current_app, 'arduino_last_heartbeat', 0.0)`.
3. **`cashier_index.html`** — add CSS for `.wifi-badge`, add badge `<span>` to header, add `fetchArduinoWifiStatus()` on DOMContentLoaded, add `socket.on('arduino_wifi_status', ...)`, update two alert strings.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| API key auth on heartbeat endpoint | `ARDUINO_API_KEY` + `X-API-Key` header check (lines 264–271 of `web_app.py`) | Exact same guard used in `arduino_card_read`; copy verbatim |
| JWT auth on cashier GET endpoint | `@jwt_required(roles=['cashier', 'admin'])` decorator | Every cashier API route uses this |
| Accessing app state from blueprint | `getattr(current_app, 'arduino_last_heartbeat', 0.0)` | Pattern established for `arduino`, `arduino_port`, `arduino_bridge` |
| SocketIO emit from app-level handler | Module-scope `socketio.emit(...)` in `web_app.py` | Same as `arduino_card_read` line 284 |

## Existing Code and Patterns

- `backend/dashboard/web_app.py:256–287` — `arduino_card_read()` is the exact template for the heartbeat endpoint: API key check, JSON parse, `socketio.emit()`, log, return 200
- `backend/dashboard/web_app.py:104–106` — `ARDUINO_API_KEY = os.environ.get("ARDUINO_API_KEY", "")` — module-scope, already there; reuse in heartbeat without redeclaring
- `backend/dashboard/web_app.py:118–121` — `socketio = SocketIO(...)` then `app.socketio = socketio` — this is how blueprint accesses socketio via `current_app.socketio`
- `backend/dashboard/cashier/cashier_routes.py:14` — `import time` already present; no addition needed there
- `backend/dashboard/cashier/cashier_routes.py:176–219` — `getattr(current_app, 'arduino', None)` / `current_app.arduino = arduino` — established pattern for sharing state between blueprint and app module; heartbeat timestamp follows same pattern
- `backend/dashboard/cashier/cashier_routes.py:817–828` — `queue_status()` is a clean minimal GET endpoint template (no body parsing, just a read and return)
- `backend/dashboard/cashier/templates/cashier_index.html:56–62` — `.arduino-status` div holds the serial status dot, port selector, and Connect button; WiFi badge goes inside this same div to the right of Connect
- `backend/dashboard/cashier/templates/cashier_index.html:104,157–161` — `arduinoConnected` flag and `updateArduinoStatus(connected)` function; WiFi path must set `arduinoConnected` directly WITHOUT calling `updateArduinoStatus()` (that function also touches the serial indicator dot)
- `backend/dashboard/cashier/templates/cashier_index.html:287–307` — `initWebSocket()` — already has `nfc_payment` listener (S02); `arduino_wifi_status` listener goes here
- `backend/dashboard/cashier/templates/cashier_index.html:311–315, 430–434` — `checkout()` and `quickPay()` both gate on `arduinoConnected` with the message "Arduino not connected! Please connect to a COM port first." — this text must be updated; with WiFi mode, a cashier who has no COM port but has WiFi online will never hit the gate (because `arduinoConnected = true`), but the error message is still wrong if WiFi drops

## Constraints

- `import time` is NOT in `web_app.py` top-level imports (only used inline as `import datetime as _dt` inside functions) — must add it
- `_arduino_last_heartbeat` cannot live as a raw module-scope float AND be accessible from `cashier_routes.py` without a circular import (web_app.py imports cashier_bp from cashier_routes.py at line 33) — use `app.arduino_last_heartbeat` instead
- `app.arduino_last_heartbeat = 0.0` must be initialized after `app = Flask(...)` but before the first request; line 121 (`app.socketio = socketio`) is the right insertion point — add it immediately after
- Heartbeat endpoint lives in `web_app.py` (not `dashboard_core.py`) for the same reason `arduino_card_read` does: it requires `ARDUINO_API_KEY` and `socketio` which are both module-scope in `web_app.py`
- The cashier GET endpoint must use `@jwt_required(roles=['cashier', 'admin'])` — no anonymous access, same as every other cashier API route
- Online threshold: 60 seconds (configurable via `ARDUINO_WIFI_OFFLINE_S = 60` constant, add near top of web_app.py ARDUINO section)
- `socketio.emit('arduino_wifi_status', ...)` payload: `{"online": bool, "last_seen_s": float}` where `last_seen_s` is `time.time() - last_heartbeat` (0.0 when never seen)
- `GET /cashier/api/arduino-wifi-status` returns `{"online": bool, "last_seen_s": float}` — identical shape to socket payload so frontend can share one update function

## Common Pitfalls

- **Calling `updateArduinoStatus(data.online)` from WiFi path** — this sets the serial status dot to green/red, which is wrong for WiFi-only cashiers; the serial dot should only reflect serial connection state; WiFi path must directly set `arduinoConnected = data.online` and update only the WiFi badge
- **Not initializing `app.arduino_last_heartbeat`** — if the attribute is only set on first heartbeat, `getattr(current_app, 'arduino_last_heartbeat', 0.0)` will return 0.0 which means `last_seen_s = now - 0 ≈ 1.7T` seconds → `online = False` — which is correct behavior, but the `last_seen_s` value in the response will be enormous/meaningless; return `null` or `-1` when never seen to distinguish from genuinely old heartbeat; OR simply initialize to 0.0 at startup and let the UI show offline badge until first heartbeat arrives (simpler, acceptable)
- **Forgetting the `python -m py_compile` gate** — both `web_app.py` and `cashier_routes.py` must compile cleanly; verify before declaring done
- **`last_seen_s` arithmetic**: `time.time() - 0.0` on first load gives a huge number but `online = (last_seen_s < 60)` still returns False correctly; just make sure the UI doesn't display the raw float to the cashier
- **Alert text in `quickPay()` and `checkout()`** — update both alert strings from "Arduino not connected! Please connect to a COM port first." to "Arduino not connected — check COM port or WiFi." The gate condition `!arduinoConnected` itself is correct; only the message needs updating

## Open Risks

- **SocketIO broadcast scope**: `socketio.emit('arduino_wifi_status', ...)` broadcasts to ALL connected SocketIO clients (not just the cashier). This is fine for this deployment (one cashier session), but if multiple browser tabs are open, all will receive the event. Acceptable — no security concern, just cosmetic.
- **Heartbeat not yet implemented in firmware**: S01 added `HEARTBEAT_INTERVAL_MS = 30000` as a constant stub but no actual POST logic. S03's backend endpoints will exist and be correct, but the WiFi badge will stay red until S04 adds the firmware heartbeat POST. This is by design (S03 wires the UI side; S04 fires the firmware side). The badge showing red is the correct initial state.
- **Page-load race**: `fetchArduinoWifiStatus()` hits `GET /cashier/api/arduino-wifi-status` immediately on load. If the Flask server is slow to respond, the badge stays at its initial "offline" state for a moment. Not a real risk — just a cosmetic blink on load.
- **Multiple cashier tabs**: If two browser tabs are open, both receive `arduino_wifi_status` events. Both will update their `arduinoConnected` flag. This is correct behavior — no conflict.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Flask / SocketIO / HTML | No dedicated skill needed | — |
| Flask-SocketIO | Standard library, well-documented | — |

## Sources

- Existing `arduino_card_read()` implementation (web_app.py:256–287) — template for heartbeat endpoint
- Existing `connect_arduino()` implementation (cashier_routes.py:153–237) — confirms `current_app.*` attribute pattern
- `cashier_index.html` full read — confirms `arduinoConnected` flag, `updateArduinoStatus()`, and where badge/listener go
- DECISIONS.md: D029 (heartbeat as dual keep-alive), D031 (arduinoConnected honors both serial and WiFi)
- M003-CONTEXT.md: Implementation Decisions → Cashier UI Dual-Mode, Heartbeat Mechanism
