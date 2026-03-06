# Phase 18: Arduino UNO R4 WiFi Upgrade - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a WiFi path so the Arduino UNO R4 WiFi can POST card UIDs directly to the Flask dashboard server over the school network. This eliminates the USB serial dependency for card reading. Serial/USB stays as a fallback — no code is removed. The cashier order-entry UI is unchanged; only the card-read transport layer changes.

</domain>

<decisions>
## Implementation Decisions

### Flask Endpoint Placement
- New endpoint lives in `web_app.py` (dashboard server, ~port 5003) — where SocketIO already lives
- Endpoint path: `POST /api/arduino/card-read`
- Arduino POSTs anytime it scans a card; Flask handles whether the cashier is in an active state
- When valid UID received, Flask emits the same `card_read` SocketIO event as the serial path — cashier UI sees no difference between WiFi and serial card reads

### Arduino Credential Management
- All credentials hardcoded in a `secrets.h` file (gitignored, not committed to repo)
- `secrets.h` must be created locally before flashing — document this clearly in a `secrets.h.example` template
- API key delivered as `X-API-Key: <secret>` HTTP header in every POST
- Flask validates the header against an env var (e.g., `ARDUINO_API_KEY`) — reject with 401 if missing or wrong
- Security implications documented: binary contains WiFi credentials and API key, acceptable for school environment
- Server address/port format in secrets.h: Claude's discretion (IP vs hostname)

### Retry & Fallback Behavior
- 3 retries per card scan (on HTTP failure or timeout), ~2 seconds apart, then give up on that scan
- If all 3 retries fail: Arduino automatically outputs the card UID over serial (silent fallback) so the existing serial path can still pick it up if a computer is connected
- WiFi reconnection: auto-reconnect in background if connection drops between scans
- Startup WiFi timeout: Claude's discretion (recommend ~30s, then enter serial-only mode)

### Claude's Discretion
- Startup WiFi timeout value
- Server address format in secrets.h (IP recommended for reliability on school LAN)
- Heartbeat / keepalive behavior (whether Arduino periodically pings Flask)
- How "Connect Arduino" button in cashier UI changes (if at all) for WiFi mode
- What Flask returns when a card is POSTed outside an active transaction (recommend: log + 200 OK, discard gracefully)
- Any status badge or indicator in the cashier UI for WiFi vs serial mode

</decisions>

<specifics>
## Specific Ideas

- The roadmap explicitly names `WiFiS3.h` as the library for Arduino UNO R4 WiFi — firmware must use this, not ESP8266WiFi or WiFi.h
- Serial fallback is a preservation requirement: no serial code is removed, only a new WiFi path is added
- The existing `ArduinoBridge` class reads serial in a background thread and emits `card_read` — the WiFi endpoint should trigger the same SocketIO emission to stay consistent

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/dashboard/arduino_bridge.py` — `ArduinoBridge` class manages serial reading and emits `card_read` / `card_error` / `card_timeout` SocketIO events; WiFi endpoint should emit the same events
- `backend/dashboard/web_app.py` — `card_reader_state` dict manages Arduino state; new WiFi endpoint should integrate here
- `backend/dashboard/cashier/cashier_routes.py` — existing serial connect/read flow; WiFi path sits alongside, not replacing

### Established Patterns
- SocketIO events used for card reads: `card_read` (success), `card_error`, `card_timeout` — WiFi path must emit same events
- Serial card read format expected: `<CARD|ABCD1234>` (8-char hex UID) — WiFi JSON body: `{"uid": "ABCD1234"}`
- Env var pattern: `SERIAL_PORT`, `BAUD_RATE` etc. in `.env` — new `ARDUINO_API_KEY` follows same pattern
- No existing API key auth mechanism in `web_app.py` — needs to be added fresh (simple header check)

### Integration Points
- `web_app.py` registers the cashier blueprint and manages SocketIO — new `/api/arduino/card-read` route added here
- `.env` / `.env.example` — add `ARDUINO_API_KEY` env var
- Arduino firmware: new file(s) in a new `arduino/` directory (no existing firmware in repo)
- `secrets.h.example` template needed alongside the `.ino` sketch

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-arduino-uno-r4-wifi-upgrade*
*Context gathered: 2026-03-06*
