# S01: Firmware WiFi Routing Fix — Research

**Date:** 2026-03-15

## Summary

The routing bug is exactly where the context says it is and is straightforward to fix. `deliver()` calls a single `httpPost(value)` helper for both CARD and NFC prefixes. That helper always POSTs `{"token": value}` to `/api/nfc/tap`. When a physical RFID card is tapped over WiFi, the UID lands on the wrong endpoint as a bogus NFC token, emits `nfc_payment` (unhandled in cashier UI today), and `/api/arduino/card-read` is never called — so `card_read` never fires.

The fix is firmware-only: split `httpPost()` into two targeted helpers (`httpPostCard`, `httpPostNFC`) and have `deliver()` dispatch by prefix. The backend already has both endpoints fully implemented and auth-ready. No Python changes for S01.

The serial fallback path in `deliver()` is already correct — it emits `prefix + "|" + value`, which `ArduinoBridge._parse_line()` parses correctly. That path stays untouched.

One mismatch to note: M003-CONTEXT.md references `handleIncomingSerial()` as a PING/PONG handler, but this function does not exist in the current firmware. The firmware is strictly one-directional (Arduino → Serial output). This doesn't affect S01 — no bidirectional serial needed.

## Recommendation

Refactor `httpPost()` into a shared `httpPostJson(path, body)` internal helper (handles host parsing, TCP connect, header write, status read), then wrap it with `httpPostCard(uid)` and `httpPostNFC(token)` that supply the correct path and payload shape. Update `deliver()` to branch on prefix. Add `HEARTBEAT_INTERVAL_MS = 30000` constant at top of file as a stub (no heartbeat POST logic — that's S04). Update `secrets.h` template to document the new constant.

This approach avoids duplicating the TCP connect logic across two helpers while staying legible for embedded C++. No clever abstraction — just one private helper and two public wrappers.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| HTTP POST to Flask from Arduino | `WiFiClient` (WiFiS3, built-in) | Already used in `httpPost()` — keep same pattern |
| UID hex encoding | `uidToHex()` already in firmware | Call it exactly as today |
| Card-read event delivery | `/api/arduino/card-read` in `web_app.py` | Fully implemented, auth-gated, tested at startup |
| NFC token delivery | `/api/nfc/tap` in `dashboard_core.py` | Fully implemented, identical auth |

## Existing Code and Patterns

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — Bug is at line 295 (`httpPost`) and line 351 (`deliver` calls it). `deliver()` at line 341 already has the `prefix` parameter — it's just not used to route. Serial fallback at lines 363-367 already uses `prefix + "|" + value` correctly.
- `arduino/bankongseton_rfid/secrets.h` — Template file (gitignored real version). Has `FLASK_HOST`, `SECRET_PASS`, `SECRET_SSID`, `SECRET_API_KEY`. Port 5003 serves both target endpoints — no host change needed. Needs `HEARTBEAT_INTERVAL_MS` stub added.
- `backend/dashboard/web_app.py:244` — `arduino_card_read()` at `/api/arduino/card-read`. Validates `X-API-Key` header against `ARDUINO_API_KEY` env var. Validates UID against `UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")`. Emits `socketio.emit("card_read", {"success": True, "uid": uid})`. Returns 200 on success, 401 on bad key, 400 on bad UID.
- `backend/dashboard/dashboard_core.py:2026` — `arduino_nfc_tap()` at `/api/nfc/tap`. Validates `X-API-Key` (reads fresh from env each call). Requires non-empty `token` in body. Emits `socketio.emit("nfc_payment", {"token": token})`. Returns 200 / 401 / 400.
- `backend/dashboard/arduino_bridge.py:91` — `_parse_line()` shows wire format: `CARD|uid` → `card_read` event + callback; `NFC|token` → `nfc_payment` event + POST. Serial fallback path in `deliver()` must continue producing exactly this format.
- `.env` line 24 — `ARDUINO_API_KEY=testkey123` (dev value, matches `secrets.h`).

## Constraints

- UID_PATTERN accepts only 8 or 14 hex chars. `uidToHex()` produces uppercase hex — the regex is case-insensitive (`[0-9A-Fa-f]`), so uppercase UIDs pass validation. 4-byte cards → 8 hex chars; 7-byte cards → 14 hex chars. Both cases covered.
- `httpPostCard` must send `{"uid": uid}` (not `{"token": uid}`) — the key name difference is what the backend validates and what `card_read` event consumers expect.
- `httpPostNFC` must send `{"token": token}` — the existing payload shape unchanged.
- Both helpers must include the `X-API-Key: SECRET_API_KEY` header — same as the current `httpPost()`.
- Serial fallback format must remain `CARD|uid` and `NFC|token` — ArduinoBridge unchanged.
- FLASK_HOST at port 5003 serves both `/api/arduino/card-read` (web_app.py) and `/api/nfc/tap` (dashboard_core.py) — same server, no routing change.
- The firmware has no Arduino IDE CI; compile verification is manual (Arduino IDE or arduino-cli).
- `secrets.h` is gitignored; the template in the repo must be updated to document `HEARTBEAT_INTERVAL_MS`.

## Common Pitfalls

- **Wrong payload key for card reads** — sending `{"token": uid}` instead of `{"uid": uid}` will pass through the NFC endpoint but emit `nfc_payment` with a garbage UID-shaped token, which is the exact bug being fixed. Double-check the body string in `httpPostCard`.
- **4-byte UID cards going through APDU path** — MIFARE Classic 1K has a 4-byte UID. These cards enter the `uidLen == 4` branch, attempt APDU (fails), RF field reset, then fall back to `deliver(uidHex, "CARD")` with an 8-char UID. This already works today; the fix doesn't change that path. Just verify 8-char UIDs pass `UID_PATTERN`.
- **`httpPost()` function name collision** — if the existing `httpPost` is renamed to `httpPostNFC` and a new `httpPostCard` is added, any forward declarations or external references must be updated. The firmware has no header file for this sketch, so only the call site in `deliver()` needs updating.
- **`handleIncomingSerial` doesn't exist** — the M003-CONTEXT.md mentions it, but it is not in the firmware. Don't add it in S01; it was likely a stale reference to a planned feature.
- **Empty ARDUINO_API_KEY open-door bug** — backend explicitly rejects empty API key even if header matches. In development, `testkey123` is set in both `.env` and `secrets.h` — keep them in sync. With an empty `ARDUINO_API_KEY` env var, every POST returns 401 regardless of header value.
- **WiFiS3 HTTP/1.0 vs HTTP/1.1** — current `httpPost` uses `HTTP/1.0` which closes the connection after response. Keep this in both new helpers to avoid keep-alive state management complexity on the Arduino.

## Open Risks

- **UID_PATTERN error message is stale** — backend returns `"Invalid UID format — expected 8 hex chars"` but the regex also accepts 14 chars. Not a bug (validation still works), but a misleading message if a 14-char UID is ever rejected for another reason. Low priority, not blocking S01.
- **NFC simulate endpoint behavior during S01 testing** — dashboard_core.py also has an `/api/nfc/simulate` endpoint that tests can hit. Unrelated to S01 but may appear in logs during integration testing and cause confusion.
- **`secrets.h` real file has different IP/key** — the repo has the template; the real `secrets.h` on the developer machine has the actual school LAN IP and real API key. Any firmware build must use the real `secrets.h`, not the template. Document this clearly in README-wireless.md (S04).
- **Arduino IDE compile not automated** — no CI for firmware. Integration verification (card tap → server log check) is the primary proof for S01. Plan a manual flash + tap test on real hardware before marking S01 done.
- **4-byte MIFARE Classic at the school** — if student cards are MIFARE Classic 1K (4-byte UID), they go through APDU attempt + failure + UID fallback on every tap. This works but adds ~1-2 seconds latency per tap (APDU timeout). Not a bug introduced by S01, but worth noting if latency complaints arise.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Arduino C++ / WiFiS3 | (none found) | none found |
| Flask SocketIO | (none found) | none found |

No relevant installed skills found. The work is pure C++ firmware editing + grep-and-verify for backend — no library research needed beyond what's already in the codebase.

## Sources

- Bug location confirmed: `bankongseton_rfid.ino` line 295 (`httpPost`), line 351 (`deliver` call site) (source: direct code read)
- Backend endpoints confirmed working: `web_app.py:244` (`/api/arduino/card-read`), `dashboard_core.py:2026` (`/api/nfc/tap`) (source: direct code read)
- Serial wire format confirmed: `arduino_bridge.py:91` `_parse_line()` (source: direct code read)
- UID validation pattern confirmed: `web_app.py:103` `UID_PATTERN` (source: direct code read)
- `ARDUINO_API_KEY=testkey123` in `.env` matches `secrets.h` template value (source: direct read)
