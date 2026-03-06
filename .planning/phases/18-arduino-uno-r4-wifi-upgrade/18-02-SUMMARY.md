---
phase: 18-arduino-uno-r4-wifi-upgrade
plan: "02"
subsystem: infra
tags: [arduino, wifi, rfid, mfrc522, wifis3, http-post, serial-fallback]

# Dependency graph
requires:
  - phase: 18-arduino-uno-r4-wifi-upgrade
    provides: "Flask POST /api/arduino/card-read endpoint with X-API-Key auth (Plan 01)"
provides:
  - "Arduino UNO R4 WiFi firmware with WiFiS3 + MFRC522 + HTTP POST delivery"
  - "3-retry HTTP loop with CARD|UID serial fallback"
  - "secrets.h.example template for credential management"
  - ".gitignore updated to exclude secrets.h"
affects: [arduino, rfid, card-reading, wifis3]

# Tech tracking
tech-stack:
  added: [WiFiS3 (Arduino UNO R4 WiFi built-in), MFRC522 by miguelbalboa]
  patterns:
    - "Arduino HTTP/1.0 raw POST with Content-Length header for Flask compatibility"
    - "secrets.h gitignore pattern for Arduino credential management"
    - "3-retry loop with RETRY_DELAY_MS between attempts before serial fallback"

key-files:
  created:
    - arduino/bankongseton_rfid/bankongseton_rfid.ino
    - arduino/bankongseton_rfid/secrets.h.example
  modified:
    - .gitignore

key-decisions:
  - "Used WiFiS3.h (not WiFi.h) — UNO R4 WiFi specific library; WiFi.h is for older shields"
  - "HTTP/1.0 with explicit Content-Length header — Werkzeug/Flask hangs on chunked transfer without it"
  - "WL_NO_MODULE guard halts sketch with clear error — prevents confusing silent failure if shield missing"
  - "Serial fallback format CARD|UID matches ArduinoBridge._read_serial_line regex exactly"
  - "SCAN_COOLDOWN_MS=1000 debounce after each read prevents same card triggering multiple POSTs"

patterns-established:
  - "Arduino credential isolation: secrets.h gitignored, secrets.h.example committed as template"
  - "deliverUID() separation: HTTP delivery logic decoupled from loop() scan logic"

requirements-completed: [ARDW-01, ARDW-04]

# Metrics
duration: 2min
completed: 2026-03-06
---

# Phase 18 Plan 02: Arduino UNO R4 WiFi RFID Firmware Summary

**WiFiS3-based Arduino sketch that reads MFRC522 UIDs, POSTs JSON to Flask with 3-retry loop, falls back to CARD|UID serial format, with gitignored secrets.h credential isolation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-06T09:20:10Z
- **Completed:** 2026-03-06T09:22:28Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Complete Arduino UNO R4 WiFi firmware using WiFiS3.h (not WiFi.h) — UNO R4 specific
- HTTP POST to Flask `/api/arduino/card-read` with X-API-Key header and Content-Length (Flask/Werkzeug compatible)
- 3-retry delivery loop with RETRY_DELAY_MS=2000 between attempts, ensureWiFi() on each retry
- Serial fallback `CARD|{uid}` format exactly matching ArduinoBridge regex after all retries exhausted
- secrets.h gitignored; secrets.h.example committed as operator template

## Task Commits

Each task was committed atomically:

1. **Task 1: Update .gitignore to exclude secrets.h** - `6e8ce8b` (chore)
2. **Task 2: Create Arduino firmware and secrets template** - `3e28f11` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — Main sketch: WiFiS3 + MFRC522 + HTTP POST with retry/fallback logic
- `arduino/bankongseton_rfid/secrets.h.example` — Credential template with SECRET_SSID, SECRET_PASS, FLASK_HOST, SECRET_API_KEY
- `.gitignore` — Added `arduino/bankongseton_rfid/secrets.h` exclusion rule

## Decisions Made
- Used `WiFiS3.h` not `WiFi.h` — UNO R4 WiFi requires this specific library (ARDW-01)
- HTTP/1.0 with explicit `Content-Length` header — Flask/Werkzeug hangs on chunked bodies without it
- `WL_NO_MODULE` guard halts with clear serial error — avoids silent failure if WiFi shield is missing
- `CARD|UID` fallback format exactly matches `ArduinoBridge._read_serial_line` parsing regex
- `SCAN_COOLDOWN_MS=1000` debounce prevents double-reads of the same card tap

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
**Arduino hardware setup required before deployment:**

1. Copy `arduino/bankongseton_rfid/secrets.h.example` → `arduino/bankongseton_rfid/secrets.h`
2. Fill in:
   - `SECRET_SSID` — school WiFi network name
   - `SECRET_PASS` — school WiFi password
   - `FLASK_HOST` — Flask server IP and port (e.g. `192.168.1.50:5000`)
   - `SECRET_API_KEY` — must match `ARDUINO_API_KEY` in Flask `.env`
3. Install libraries in Arduino IDE:
   - MFRC522 by miguelbalboa (Library Manager)
   - WiFiS3 is built-in (no install needed)
4. Upload `bankongseton_rfid.ino` to Arduino UNO R4 WiFi board

## Next Phase Readiness
- Arduino firmware complete and ready for hardware testing
- Connects WiFi on boot, reads MFRC522 cards, POSTs UIDs to Flask endpoint from Plan 01
- Serial fallback ensures no scan is silently lost even without WiFi/HTTP connectivity
- Phase 18 now has both Plan 01 (Flask endpoint) and Plan 02 (Arduino firmware) complete

---
*Phase: 18-arduino-uno-r4-wifi-upgrade*
*Completed: 2026-03-06*
