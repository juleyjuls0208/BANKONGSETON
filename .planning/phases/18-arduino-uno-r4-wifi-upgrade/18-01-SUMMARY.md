---
phase: 18-arduino-uno-r4-wifi-upgrade
plan: "01"
subsystem: api

tags: [arduino, wifi, flask, socketio, rfid, api-key]

requires:
  - phase: 07.1-web-deployable-dashboard
    provides: web_app.py Flask app with SocketIO, UID_PATTERN, card_reader_state

provides:
  - POST /api/arduino/card-read route in web_app.py with X-API-Key auth
  - ARDUINO_API_KEY env var documented in both .env.example files
  - WiFi card-read path that emits identical card_read SocketIO event to serial path

affects: [cashier-frontend, arduino-firmware, 18-arduino-uno-r4-wifi-upgrade]

tech-stack:
  added: []
  patterns:
    - "Empty-string guard: `if not ARDUINO_API_KEY` prevents open-door bug when env var unset"
    - "Module-level env var read after load_dotenv() (safe per wsgi.py import order)"
    - "SocketIO emission shape matches ArduinoBridge._read_card_thread exactly for zero frontend changes"

key-files:
  created: []
  modified:
    - backend/dashboard/web_app.py
    - .env.example
    - config/.env.example

key-decisions:
  - "No normalize_card_uid() call in arduino_card_read — Arduino firmware sends uppercase hex, UID_PATTERN accepts both cases, normalisation happens downstream"
  - "No card_reader_state guard before emit — serial path doesn't guard either; cashier JS handles events gracefully"
  - "ARDUINO_API_KEY read at module import time via os.environ.get — load_dotenv() called before web_app import in wsgi.py"

patterns-established:
  - "WiFi card-read: POST /api/arduino/card-read + X-API-Key header + empty-key guard"

requirements-completed:
  - ARDW-02
  - ARDW-03

duration: 5min
completed: 2026-03-06
---

# Phase 18 Plan 01: Arduino UNO R4 WiFi Card-Read Endpoint Summary

**POST /api/arduino/card-read added to web_app.py with X-API-Key auth and UID_PATTERN validation, emitting card_read SocketIO event identical to the serial path**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-06T00:00:00Z
- **Completed:** 2026-03-06T00:05:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `POST /api/arduino/card-read` route to `web_app.py` — Arduino UNO R4 WiFi can now deliver card UIDs over LAN without USB serial
- Implemented X-API-Key authentication with empty-key guard (Pitfall 4 prevention — no open-door vulnerability)
- Route emits `socketio.emit('card_read', {'success': True, 'uid': uid})` identical to `ArduinoBridge._read_card_thread` — zero frontend changes required
- Documented `ARDUINO_API_KEY` in both `.env.example` files with comment linking to arduino firmware `secrets.h`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ARDUINO_API_KEY to env examples** - `50c281d` (feat)
2. **Task 2: Add POST /api/arduino/card-read endpoint to web_app.py** - `8c4b3bf` (feat)

**Plan metadata:** _(docs commit hash — added below)_

## Files Created/Modified

- `backend/dashboard/web_app.py` — Added `ARDUINO_API_KEY` module-level constant and `arduino_card_read()` route handler
- `.env.example` — Added `ARDUINO_API_KEY=` entry with comment in Arduino serial section
- `config/.env.example` — Added `ARDUINO_API_KEY=` entry with comment in Arduino serial section

## Decisions Made

- No `normalize_card_uid()` call in the new route — Arduino firmware sends uppercase hex (`%02X`), `UID_PATTERN` accepts both cases, and normalisation happens downstream in existing transaction handlers
- No `card_reader_state` guard before `socketio.emit` — the existing serial path in `ArduinoBridge._read_card_thread` doesn't guard either; cashier JS handles unexpected events gracefully
- `ARDUINO_API_KEY` read at module import time via `os.environ.get` — confirmed safe because `load_dotenv()` is called before `web_app` is imported in `wsgi.py` (per Phase 07.1 decision)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

**External configuration required:**

To enable WiFi card-read:
1. Generate a secure key: `python -c "import secrets; print(secrets.token_urlsafe(16))"`
2. Set `ARDUINO_API_KEY=<key>` in your `.env` file
3. Set `SECRET_API_KEY "<key>"` in `arduino/bankongseton_rfid/secrets.h`

If `ARDUINO_API_KEY` is left empty (default), the endpoint returns 401 for all requests (safe default — serial path still works normally).

## Next Phase Readiness

- WiFi card-read backend is complete and ready for Arduino firmware implementation
- Serial path unchanged — existing deployments unaffected
- Cashier frontend unchanged — `card_read` SocketIO event arrives identically from both paths

---
*Phase: 18-arduino-uno-r4-wifi-upgrade*
*Completed: 2026-03-06*
