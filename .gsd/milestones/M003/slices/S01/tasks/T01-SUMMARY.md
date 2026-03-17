---
id: T01
parent: S01
milestone: M003
provides:
  - httpPostJson(path, body) — shared TCP/HTTP helper replacing httpPost
  - httpPostCard(uid) — routes CARD prefix to /api/arduino/card-read with {"uid":uid}
  - httpPostNFC(token) — routes NFC prefix to /api/nfc/tap with {"token":token}
  - deliver() dispatches by prefix == "CARD" instead of always calling old httpPost
  - HEARTBEAT_INTERVAL_MS = 30000 constant (S04 stub)
  - scripts/verify-s01.sh — 8-check grep assertion script
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
  - arduino/bankongseton_rfid/secrets.h
  - scripts/verify-s01.sh
key_decisions:
  - httpPostJson takes path+body params rather than being a method-on-wrapper; keeps all TCP logic in one place and wrappers are thin one-liners
  - Serial fallback format (prefix + "|" + value) preserved exactly — ArduinoBridge downstream depends on it
patterns_established:
  - HTTP routing: thin wrapper pattern — shared connect/header/read in httpPostJson, domain wrappers supply path+payload
observability_surfaces:
  - Serial log now prints "HTTP: delivered — CARD|uid" vs "HTTP: delivered — NFC|token" distinguishing routing paths
  - bash scripts/verify-s01.sh — structural grep assertions (8 checks)
  - Flask access log: "POST /api/arduino/card-read 200" vs "POST /api/nfc/tap" shows correct routing
duration: ~15 min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Refactor firmware HTTP helpers and fix deliver() routing

**Replaced single-endpoint `httpPost()` with routed `httpPostCard()`/`httpPostNFC()` wrappers; `deliver()` now dispatches by prefix so physical RFID card taps POST `{"uid":uid}` to `/api/arduino/card-read` instead of `/api/nfc/tap`.**

## What Happened

`httpPost(value)` hardcoded both the path (`/api/nfc/tap`) and payload shape (`{"token":value}`), causing all card taps — regardless of prefix — to fire `nfc_payment` on the backend instead of `card_read`.

Renamed/refactored to `httpPostJson(path, body)`: same TCP connect, headers, and response-read logic, but `path` and `body` are now parameters. Added `httpPostCard(uid)` (POSTs `{"uid":uid}` to `/api/arduino/card-read`) and `httpPostNFC(token)` (POSTs `{"token":token}` to `/api/nfc/tap`). `deliver()` now does:

```cpp
bool ok = (prefix == "CARD") ? httpPostCard(value) : httpPostNFC(value);
```

The serial fallback block (prefix + "|" + value) is logically unchanged.

Added `HEARTBEAT_INTERVAL_MS = 30000` constant in the HTTP tuning section as a S04 stub (no POST logic — constant only).

Updated `secrets.h` template with a comment pointing developers to the `HEARTBEAT_INTERVAL_MS` constant location in the `.ino`.

Wrote `scripts/verify-s01.sh` with 8 grep assertions covering all structural requirements.

## Verification

`bash scripts/verify-s01.sh` — all 8 checks passed:
- (a) no bare `httpPost(` call site in firmware — PASS
- (b) `httpPostCard` function defined — PASS
- (b2) `httpPostNFC` function defined — PASS
- (c) `prefix == "CARD"` dispatch in `deliver()` — PASS
- (d) `/api/arduino/card-read` path present — PASS
- (e) `{"uid":` payload present — PASS
- (f) `HEARTBEAT_INTERVAL_MS` constant in `.ino` — PASS
- (g) `secrets.h` mentions `HEARTBEAT_INTERVAL_MS` — PASS

Manual slice-level checks remaining (require hardware/live server):
- `arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi arduino/bankongseton_rfid` — not run (arduino-cli not in this environment)
- Flash + physical card tap → Flask log `POST /api/arduino/card-read 200` — hardware required
- Cashier UI `card_read` event — live server required

## Diagnostics

- `bash scripts/verify-s01.sh` — quick structural check, exits 0 on success
- Arduino Serial monitor: watch for `"HTTP: delivered — CARD|<uid>"` vs `"HTTP: delivered — NFC|<token>"` to confirm routing
- Flask access log: `POST /api/arduino/card-read` confirms card path, `POST /api/nfc/tap` confirms NFC path
- Mismatch signal: Serial says `"HTTP: delivered — CARD|..."` but Flask shows `POST /api/nfc/tap` → mis-routing (should not occur after this fix)

## Deviations

none — implementation followed the plan exactly

## Known Issues

none — `arduino-cli compile` not verified locally (tool not installed in this environment); compilation verification is the next manual slice-level check before flashing

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — replaced `httpPost` with `httpPostJson`/`httpPostCard`/`httpPostNFC`; updated `deliver()` dispatch; added `HEARTBEAT_INTERVAL_MS` constant
- `arduino/bankongseton_rfid/secrets.h` — added `HEARTBEAT_INTERVAL_MS` orientation comment
- `scripts/verify-s01.sh` — new 8-check grep assertion script (exits 0 on pass)
