---
estimated_steps: 7
estimated_files: 3
---

# T01: Refactor firmware HTTP helpers and fix deliver() routing

**Slice:** S01 — Firmware WiFi Routing Fix
**Milestone:** M003

## Description

`deliver()` currently calls a single `httpPost(value)` helper for both CARD and NFC prefixes. That helper always POSTs `{"token": value}` to `/api/nfc/tap`. When a physical RFID card is tapped over WiFi, the UID lands on the wrong endpoint and fires `nfc_payment` instead of `card_read` — the exact bug masked by serial fallback today.

The fix: rename `httpPost` to `httpPostJson(path, body)` (shared TCP connect/header/response logic), add `httpPostCard(uid)` and `httpPostNFC(token)` wrappers that supply the correct path and payload for each prefix, and update `deliver()` to dispatch by prefix. Add `HEARTBEAT_INTERVAL_MS 30000` constant as a stub for S04. Update `secrets.h` template. Write a grep-based verify script.

No Python files are touched in this task — the backend already has both endpoints fully implemented.

## Steps

1. Read `arduino/bankongseton_rfid/bankongseton_rfid.ino` in full to confirm exact line positions of `httpPost`, the HTTP tuning section, and `deliver()`.
2. In the HTTP tuning section (after `HTTP_TIMEOUT_MS`), add: `static const int HEARTBEAT_INTERVAL_MS = 30000;  // S04: heartbeat stub — POST not yet implemented`
3. Replace the `httpPost(const String &value)` function with `httpPostJson(const String &path, const String &body)` — same TCP connect/header/read logic, but `path` replaces the hardcoded `/api/nfc/tap` and `body` replaces the hardcoded `{"token":...}` string.
4. Add `httpPostCard(const String &uid)` after `httpPostJson`: calls `httpPostJson("/api/arduino/card-read", "{\"uid\":\"" + uid + "\"}")`. Sends `X-API-Key` via `httpPostJson`.
5. Add `httpPostNFC(const String &token)` after `httpPostCard`: calls `httpPostJson("/api/nfc/tap", "{\"token\":\"" + token + "\"}")`.
6. In `deliver()`, change the single `if (httpPost(value))` call to: `bool ok = (prefix == "CARD") ? httpPostCard(value) : httpPostNFC(value); if (ok) {`. Serial fallback lines (the `Serial.print(prefix)` block) remain untouched.
7. Update `arduino/bankongseton_rfid/secrets.h` template to add a comment documenting `HEARTBEAT_INTERVAL_MS` (note that this constant lives in the `.ino` file, not in `secrets.h` — the update is a comment pointing to it for the developer's orientation).
8. Write `scripts/verify-s01.sh`: grep assertions confirming (a) `httpPost(` is not called in `deliver()`, (b) `httpPostCard` and `httpPostNFC` functions exist, (c) `prefix == "CARD"` dispatch exists in `deliver()`, (d) `/api/arduino/card-read` appears, (e) `{"uid":` appears, (f) `HEARTBEAT_INTERVAL_MS` appears in the `.ino`, (g) `secrets.h` template mentions `HEARTBEAT_INTERVAL_MS`.

## Must-Haves

- [ ] `httpPostJson(path, body)` replaces the old `httpPost` — same HTTP/1.0 pattern, no keep-alive state
- [ ] `httpPostCard(uid)` POSTs `{"uid": uid}` (not `{"token": uid}`) to `/api/arduino/card-read`
- [ ] `httpPostNFC(token)` POSTs `{"token": token}` to `/api/nfc/tap`
- [ ] Both wrappers include the `X-API-Key: SECRET_API_KEY` header via `httpPostJson`
- [ ] `deliver()` dispatches by `prefix == "CARD"` — no other deliver() logic changes
- [ ] `HEARTBEAT_INTERVAL_MS 30000` constant present in `.ino` (no heartbeat POST logic — stub only)
- [ ] Serial fallback lines 363–367 logically unchanged (prefix + "|" + value format preserved)
- [ ] `bash scripts/verify-s01.sh` exits 0 with all grep checks passing

## Verification

- `bash scripts/verify-s01.sh` — all checks exit 0
- Confirm no `httpPost(` string remains as a call site in the deliver() body (the definition `httpPostJson` is fine)
- Confirm `{"uid":` appears in the card helper and `{"token":` appears in the NFC helper

## Observability Impact

- Signals added/changed: Serial log now prints `"HTTP: delivered — CARD|uid"` vs `"HTTP: delivered — NFC|token"` (was always NFC before); non-200 responses still printed
- How a future agent inspects this: `bash scripts/verify-s01.sh`; Arduino Serial monitor during hardware test; Flask access log for endpoint hit confirmation
- Failure state exposed: if wrong endpoint is still hit, Serial log will show `"HTTP: delivered — CARD|..."` but Flask log will show `POST /api/nfc/tap` — mismatch immediately reveals mis-routing

## Inputs

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — current firmware with `httpPost()` bug at line 295 and `deliver()` at line 341
- `arduino/bankongseton_rfid/secrets.h` — template file to update with heartbeat constant note
- S01-RESEARCH.md — confirms payload shapes (`{"uid": uid}` for card, `{"token": token}` for NFC), both endpoint paths, and UID_PATTERN constraints

## Expected Output

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — `httpPost` replaced by three functions; `deliver()` dispatches by prefix; `HEARTBEAT_INTERVAL_MS` constant present
- `arduino/bankongseton_rfid/secrets.h` — template updated with `HEARTBEAT_INTERVAL_MS` documentation comment
- `scripts/verify-s01.sh` — executable verify script that passes all grep assertions on the firmware
