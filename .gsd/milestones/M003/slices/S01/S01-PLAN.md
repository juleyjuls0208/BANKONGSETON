# S01: Firmware WiFi Routing Fix

**Goal:** Fix `deliver()` in the Arduino firmware so physical RFID card taps over WiFi POST `{"uid": uid}` to `/api/arduino/card-read` (triggering `card_read`) instead of incorrectly POSTing to `/api/nfc/tap`.

**Demo:** `bash scripts/verify-s01.sh` passes all checks; manual flash + physical card tap → server log shows `POST /api/arduino/card-read 200` → cashier UI fires `card_read` event → sale completes — no serial cable, no PC.

## Must-Haves

- `httpPost(value)` monolithic helper replaced by `httpPostJson(path, body)` (shared TCP connect/header/response logic) + `httpPostCard(uid)` + `httpPostNFC(token)` wrappers
- `httpPostCard(uid)` sends `{"uid": uid}` to `/api/arduino/card-read` with `X-API-Key` header; returns bool
- `httpPostNFC(token)` sends `{"token": token}` to `/api/nfc/tap` with `X-API-Key` header; returns bool
- `deliver()` calls `httpPostCard(value)` when `prefix == "CARD"`, `httpPostNFC(value)` otherwise
- Serial fallback format unchanged: `CARD|uid` and `NFC|token` (lines 363–367 untouched in logic)
- `HEARTBEAT_INTERVAL_MS 30000` constant added to firmware (stub for S04 — no heartbeat POST logic)
- `secrets.h` template documents `HEARTBEAT_INTERVAL_MS`
- `scripts/verify-s01.sh` passes all grep assertions on the firmware

## Proof Level

- This slice proves: contract (grep assertions) + integration (hardware UAT)
- Real runtime required: yes — manual flash + card tap on actual hardware before marking done
- Human/UAT required: yes — cashier tests physical card tap and confirms sale completes

## Verification

- `bash scripts/verify-s01.sh` — all checks pass (no `httpPost(` call site in deliver, both routing paths present, `{"uid":` in card helper, `{"token":` in NFC helper, heartbeat constant present)
- Manual: `arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi arduino/bankongseton_rfid` exits 0
- Manual: flash firmware to Arduino, tap physical RFID card at terminal, check Flask server log for `POST /api/arduino/card-read 200`
- Manual: confirm cashier UI fires `card_read` event and shows sale completion modal

## Observability / Diagnostics

- Runtime signals: Arduino Serial logs `"HTTP attempt X/Y"` and `"HTTP: delivered — CARD|uid"` on success, `"HTTP: non-200 response: ..."` on failure
- Inspection surfaces: Flask server log (`POST /api/arduino/card-read 200` vs `POST /api/nfc/tap`); cashier UI SocketIO event log; `bash scripts/verify-s01.sh` for structural check
- Failure visibility: non-200 response line printed to Arduino Serial; serial fallback triggers if all retries fail (fallback line format `CARD|uid` visible on Serial monitor)
- Redaction constraints: `SECRET_API_KEY` must not appear in log output — existing Serial.print statements don't log the key value

## Integration Closure

- Upstream surfaces consumed: `web_app.py` `/api/arduino/card-read` (pre-existing, auth-gated, emits `card_read`); `dashboard_core.py` `/api/nfc/tap` (pre-existing, emits `nfc_payment`)
- New wiring introduced: `deliver("CARD")` → `httpPostCard()` → `POST /api/arduino/card-read` (was: `httpPost()` → `POST /api/nfc/tap`)
- What remains before milestone is truly usable end-to-end: S02 (phone NFC cashier payment), S03 (WiFi status badge), S04 (powerbank hardening + docs)

## Tasks

- [x] **T01: Refactor firmware HTTP helpers and fix deliver() routing** `est:45m`
  - Why: The single `httpPost()` always hits `/api/nfc/tap`; splitting into typed helpers and dispatching by prefix in `deliver()` is the entire bug fix
  - Files: `arduino/bankongseton_rfid/bankongseton_rfid.ino`, `arduino/bankongseton_rfid/secrets.h`, `scripts/verify-s01.sh`
  - Do: Add `HEARTBEAT_INTERVAL_MS 30000` constant to the HTTP tuning section; rename `httpPost` to `httpPostJson(path, body)` updating its body to take `path` and `body` as params; add `httpPostCard(uid)` and `httpPostNFC(token)` wrappers; update `deliver()` to dispatch by prefix (`prefix == "CARD"` → `httpPostCard`, else `httpPostNFC`); update `secrets.h` template to document `HEARTBEAT_INTERVAL_MS`; write `scripts/verify-s01.sh` with grep assertions
  - Verify: `bash scripts/verify-s01.sh` exits 0 with all checks green
  - Done when: verify script passes; no call to old `httpPost(` remains; both endpoint paths and payload shapes confirmed present in firmware source

## Files Likely Touched

- `arduino/bankongseton_rfid/bankongseton_rfid.ino`
- `arduino/bankongseton_rfid/secrets.h`
- `scripts/verify-s01.sh`
