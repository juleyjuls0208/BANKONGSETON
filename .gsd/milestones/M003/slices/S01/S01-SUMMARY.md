---
id: S01
parent: M003
milestone: M003
provides:
  - httpPostJson(path, body) — shared TCP/HTTP helper replacing monolithic httpPost
  - httpPostCard(uid) — routes CARD prefix to /api/arduino/card-read with {"uid":uid}
  - httpPostNFC(token) — routes NFC prefix to /api/nfc/tap with {"token":token}
  - deliver() dispatches by prefix == "CARD" instead of always calling old httpPost
  - HEARTBEAT_INTERVAL_MS = 30000 constant in firmware (S04 stub)
  - scripts/verify-s01.sh — 8-check grep assertion script (exits 0)
requires:
  - slice: none
    provides: first slice
affects:
  - S02: httpPostNFC(token) → /api/nfc/tap → nfc_payment event — phone tap flow depends on NFC path working correctly
  - S03: WiFi badge depends on POST /api/arduino/card-read being confirmed reachable from Arduino
  - S04: HEARTBEAT_INTERVAL_MS constant stubbed here; S04 adds the actual POST logic
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
  - arduino/bankongseton_rfid/secrets.h
  - scripts/verify-s01.sh
key_decisions:
  - D028: Two separate HTTP helpers (httpPostCard, httpPostNFC) dispatched by prefix in deliver() — firmware-only fix, no backend changes required
  - Serial fallback format (prefix + "|" + value) preserved exactly — ArduinoBridge downstream depends on it
patterns_established:
  - Thin wrapper pattern: shared TCP connect/header/read logic in httpPostJson; domain wrappers (httpPostCard, httpPostNFC) supply path+payload only
observability_surfaces:
  - bash scripts/verify-s01.sh — structural grep assertions (8 checks, exits 0)
  - Arduino Serial: "HTTP: delivered — CARD|uid" vs "HTTP: delivered — NFC|token" distinguishes routing paths
  - Flask access log: "POST /api/arduino/card-read 200" vs "POST /api/nfc/tap" confirms correct routing at server side
drill_down_paths:
  - .gsd/milestones/M003/slices/S01/tasks/T01-SUMMARY.md
duration: ~15 min (T01 only)
verification_result: passed
completed_at: 2026-03-15
---

# S01: Firmware WiFi Routing Fix

**Replaced single-endpoint `httpPost()` with routed `httpPostCard()`/`httpPostNFC()` wrappers; `deliver()` now dispatches by prefix so physical RFID card taps POST `{"uid":uid}` to `/api/arduino/card-read` (not `/api/nfc/tap`), firing `card_read` instead of `nfc_payment`.**

## What Happened

The root bug: `httpPost(value)` hardcoded both path (`/api/nfc/tap`) and payload shape (`{"token":value}`), so all WiFi POSTs — regardless of whether the read was a physical card UID or a phone NFC token — hit the same endpoint and emitted `nfc_payment`. With ArduinoBridge (serial path) running, this was masked because ArduinoBridge correctly routed by prefix. With a standalone powerbank Arduino (no USB serial to PC), every physical card tap silently failed.

**T01** refactored in a single pass:

- `httpPost(value)` replaced by `httpPostJson(path, body)`: same TCP connect, headers, retry loop, and response-read logic — `path` and `body` are now parameters
- `httpPostCard(uid)` added: calls `httpPostJson("/api/arduino/card-read", '{"uid":"' + uid + '"}')` with `X-API-Key` header
- `httpPostNFC(token)` added: calls `httpPostJson("/api/nfc/tap", '{"token":"' + token + '"}')` with `X-API-Key` header
- `deliver()` updated: `bool ok = (prefix == "CARD") ? httpPostCard(value) : httpPostNFC(value);`
- Serial fallback block (prefix + "|" + value) logically unchanged — ArduinoBridge depends on exact format
- `HEARTBEAT_INTERVAL_MS 30000` constant added to HTTP tuning section (S04 stub — no POST logic)
- `secrets.h` template updated with orientation comment pointing to the constant location in the `.ino`
- `scripts/verify-s01.sh` written: 8 grep assertions covering all structural requirements

## Verification

`bash scripts/verify-s01.sh` — all 8 checks passed:
- (a) no bare `httpPost(` call site in firmware — PASS
- (b) `httpPostCard` function defined — PASS
- (b2) `httpPostNFC` function defined — PASS
- (c) `prefix == "CARD"` dispatch in `deliver()` — PASS
- (d) `/api/arduino/card-read` path present — PASS
- (e) `{"uid":` payload present in firmware — PASS
- (f) `HEARTBEAT_INTERVAL_MS` constant present — PASS
- (g) `secrets.h` mentions `HEARTBEAT_INTERVAL_MS` — PASS

Manual/hardware checks (require physical hardware — documented in S01-UAT.md):
- `arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi arduino/bankongseton_rfid` — not run in this environment (arduino-cli not installed); must be run before flashing
- Flash + physical RFID card tap → Flask server log must show `POST /api/arduino/card-read 200`
- Cashier UI must fire `card_read` event and show sale completion modal

## Requirements Advanced

- R020 (Correct WiFi Payment Routing) — contract verification complete (all grep assertions pass); integration verification (flash + card tap) is the remaining hardware UAT gate

## Requirements Validated

- none — R020 moves to validated only after hardware UAT (flash + card tap → `POST /api/arduino/card-read 200` in server log)

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none — implementation followed the plan exactly

## Known Limitations

- `arduino-cli compile` not verified locally (tool not installed in CI/dev environment); compilation must be confirmed before flashing
- Hardware UAT (actual card tap → Flask log) is required before R020 can be marked validated; this is a human/hardware gate
- No heartbeat POST logic — HEARTBEAT_INTERVAL_MS is a constant stub only; actual heartbeat behavior (powerbank keep-alive + cashier WiFi badge) is S04 work

## Follow-ups

- S02: `httpPostNFC(token)` path confirmed structurally — phone tap flow can be built assuming `/api/nfc/tap` is wired (it is, pre-existing)
- S04: Add `POST /api/arduino/heartbeat` every `HEARTBEAT_INTERVAL_MS` ms in firmware; call `ensureWiFi()` before each heartbeat POST

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — replaced `httpPost` with `httpPostJson`/`httpPostCard`/`httpPostNFC`; updated `deliver()` dispatch; added `HEARTBEAT_INTERVAL_MS` constant
- `arduino/bankongseton_rfid/secrets.h` — added `HEARTBEAT_INTERVAL_MS` orientation comment
- `scripts/verify-s01.sh` — new 8-check grep assertion script (exits 0 on pass)

## Forward Intelligence

### What the next slice should know
- `/api/nfc/tap` is pre-existing in `dashboard_core.py` and already emits `nfc_payment` — S02 can build the cashier handler for that event immediately without any backend changes
- `/api/arduino/card-read` is pre-existing in `web_app.py` — the card-read path is fully wired backend-side; only the firmware bug was broken
- The serial fallback format (`CARD|uid`, `NFC|token`) is unchanged — ArduinoBridge continues to work as-is for USB-connected Arduinos

### What's fragile
- `httpPostJson` body is a raw string concatenated in each wrapper (not a JSON library) — works for simple scalar values but will break if uid or token ever contains `"` or `\`; acceptable for RFID UIDs (hex digits only) and UUID tokens (alphanumeric + dashes) but worth noting
- Arduino WiFi reconnect is via `ensureWiFi()` called before each HTTP attempt — if WiFi drops mid-session, the first post-drop card tap will trigger reconnect and may feel slow; subsequent taps are fast

### Authoritative diagnostics
- `bash scripts/verify-s01.sh` — first check, exits 0 means all structural routing is correct
- Flask access log line `POST /api/arduino/card-read 200` — definitive proof the card read reached the right endpoint
- Arduino Serial `HTTP: delivered — CARD|<uid>` — confirms Arduino-side routing; pair with Flask log to confirm end-to-end

### What assumptions changed
- Original assumption: `httpPost()` was a simple function; actual: it had retry loop, response-read, and Serial logging — all preserved in `httpPostJson()` without change
