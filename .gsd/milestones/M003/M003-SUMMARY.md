---
id: M003
provides:
  - httpPostCard(uid) — routes CARD prefix to POST /api/arduino/card-read with {"uid":uid}
  - httpPostNFC(token) — routes NFC prefix to POST /api/nfc/tap with {"token":token}
  - deliver() dispatch by prefix ("CARD" vs "NFC") — firmware-only fix, no backend changes
  - HEARTBEAT_INTERVAL_MS = 30000 + lastHeartbeatMs file-scope variable + 4-line timer block in loop()
  - POST /api/arduino/heartbeat — API-key-authenticated; updates arduino_last_heartbeat; emits arduino_wifi_status socket event
  - GET /cashier/api/arduino-wifi-status — JWT-protected; returns {online, last_seen_s}
  - POST /cashier/api/complete-sale-nfc — VirtualCards token → MoneyCardNumber → balance debit; same retry/rollback/offline-queue as complete_sale()
  - socket.on('nfc_payment') + completeNFCSale(token) in cashier UI — inbound handler, no arduinoConnected gate
  - WiFi badge (#wifiBadge) in cashier header — green (.online) / red (.offline) driven by arduino_wifi_status socket event
  - arduino/README-wireless.md — complete standalone wireless deployment guide (8 sections)
  - scripts/verify-s01.sh — 8-check grep assertion script
  - scripts/verify-s02.sh — 9-check structural grep assertion script
  - scripts/verify-m003-s03.sh — 12-check assertion script
  - scripts/verify-m003-s04.sh — 8-check assertion script
key_decisions:
  - D028: Two separate HTTP helpers dispatched by prefix in deliver() — firmware-only fix, no backend changes required
  - D029: Arduino heartbeat is dual-purpose — WiFi status signal for cashier badge + RF burst to keep powerbank above auto-shutoff threshold
  - D030: Phone NFC token resolution runs inside cashier_routes.py — direct VirtualCards sheet lookup, no cross-process call to api_server.py
  - D031: arduinoConnected honors both serial and WiFi states — two independent paths, serial path unchanged
  - D032: VirtualCards MoneyCardNumber matched by direct string — no normalize_card_uid(); normalization would be wrong for virtual tokens
  - D033: Inbound socket event handlers do not gate on arduinoConnected — connection state is irrelevant when the event already arrived
  - D034: arduino_last_heartbeat initialized to 0.0 float; last_seen_s = -1.0 sentinel when never heartbeated
  - D035: WiFi offline does not fight serial connection in updateWifiBadge() — serial is the stronger signal
  - D036: Heartbeat timer block placed before NFC early-exit in loop() — must fire during idle, not gated by if (!found) return
patterns_established:
  - Thin wrapper pattern: shared TCP connect/header/read logic in httpPostJson; domain wrappers supply path+payload only
  - Firmware idle keep-alive: periodic POST during NFC scan idle avoids powerbank current-starve shutoff without dedicated hardware
  - Inbound socket event handlers delegate immediately to async fetch functions; no connection-state gating on inbound paths
  - VirtualCards token → MoneyCardNumber → Money Accounts debit: three-step chain, identical retry/rollback/offline-queue logic as physical card path
  - Deployment README pattern: hardware table → wiring tables → libraries → secrets.h field table → flashing steps → verification → powerbank selection → troubleshooting
observability_surfaces:
  - bash scripts/verify-s01.sh — 8 firmware routing checks; exit 0 is structural proof
  - bash scripts/verify-s02.sh — 9 NFC cashier endpoint + UI checks; exit 0 is structural proof
  - bash scripts/verify-m003-s03.sh — 12 heartbeat backend + badge checks; exit 0 is structural proof
  - bash scripts/verify-m003-s04.sh — 8 firmware heartbeat + README checks; exit 0 is structural proof
  - Arduino Serial "HTTP: delivered — CARD|uid" vs "HTTP: delivered — NFC|token" — distinguishes routing paths
  - Flask access log "POST /api/arduino/card-read 200" — definitive card WiFi routing proof
  - Flask access log "POST /api/arduino/heartbeat 200" every 30s — heartbeat timer firing confirmed
  - Flask WARNING "event=arduino_heartbeat_rejected reason=invalid_api_key" — API key mismatch diagnosis
  - SocketIO frame stream "arduino_wifi_status {online, last_seen_s}" — visible in DevTools WS tab
  - Browser console "document.getElementById('wifiBadge').className" — immediate badge state check
  - grep "event=nfc_sale_complete\|event=nfc_sale_no_pending" server.log — NFC sale success/fail diagnosis
  - Browser DevTools Network filter "/complete-sale-nfc" — exact request/response for each phone tap
requirement_outcomes:
  - id: R020
    from_status: active
    to_status: active
    proof: "Contract verified — bash scripts/verify-s01.sh 8/8 pass; firmware routes CARD prefix to /api/arduino/card-read with {uid} payload, NFC prefix to /api/nfc/tap with {token} payload; python -m py_compile not applicable (C++ firmware); runtime validation (flash + physical card tap → POST /api/arduino/card-read 200 in Flask log) requires physical hardware UAT"
  - id: R021
    from_status: active
    to_status: active
    proof: "Contract verified — python -m py_compile cashier_routes.py exits 0; bash scripts/verify-s02.sh 9/9 pass; complete_sale_nfc() defined, /cashier/api/complete-sale-nfc route registered, VirtualCardToken/IsActive/MoneyCardNumber fields present, flask_session.pop present, socket.on('nfc_payment') wired, completeNFCSale() defined; runtime validation (live phone tap at deployed Arduino → sale complete → Sheets debit) requires physical hardware UAT"
  - id: R022
    from_status: active
    to_status: active
    proof: "Contract verified — python -m py_compile web_app.py + cashier_routes.py both exit 0; bash scripts/verify-m003-s03.sh 12/12 pass; POST /api/arduino/heartbeat exists with API key auth, arduino_wifi_status socket emit confirmed, GET /cashier/api/arduino-wifi-status with JWT confirmed, #wifiBadge span in cashier UI, arduinoConnected set from WiFi path; badge going green on live Arduino heartbeat requires physical hardware flash + UAT"
  - id: R023
    from_status: active
    to_status: active
    proof: "Contract verified — bash scripts/verify-m003-s04.sh 8/8 pass; lastHeartbeatMs file-scope variable confirmed, httpPostJson heartbeat call in loop() before if (!found) return confirmed, ensureWiFi() called before each heartbeat POST confirmed, HEARTBEAT_INTERVAL_MS not a stub; operational proof (30-minute powerbank idle without shutoff, WiFi drop + auto-reconnect) requires physical hardware UAT"
  - id: R024
    from_status: active
    to_status: validated
    proof: "arduino/README-wireless.md exists (164 lines, 8 sections); bash scripts/verify-m003-s04.sh checks (e–h) all pass — README covers hardware, wiring, secrets.h with explicit port 5003 + ARDUINO_API_KEY, flashing, powerbank selection (≥2A/≥10,000mAh/name-brand), verification (Serial Monitor + badge), troubleshooting; no hardware required to validate documentation completeness"
duration: ~2h 05m total (S01: ~15m, S02: ~40m, S03: ~35m, S04: ~35m)
verification_result: contract_verified
completed_at: 2026-03-15
---

# M003: Wireless Cashier Payment Terminal

**All M003 code work complete and structurally verified across 37 assertions — Arduino firmware routes CARD/NFC correctly, phone NFC payment wired end-to-end at cashier, WiFi badge and heartbeat backend fully wired, powerbank keep-alive in firmware, wireless deployment documented; hardware UAT (flash → real tap → badge green → 30-min powerbank soak) is the sole remaining gate.**

## What Happened

M003 attacked a single root problem from four angles: the Arduino was broken as a standalone unit.

**S01 (Firmware WiFi Routing Fix)** killed the root bug in `deliver()` — it had been sending every WiFi POST to `/api/nfc/tap` with `{"token": value}`, so physical RFID card taps over WiFi fired `nfc_payment` instead of `card_read`. The fix replaced the monolithic `httpPost(value)` with a routed dispatch: `httpPostCard(uid)` → `POST /api/arduino/card-read {"uid":uid}` for CARD prefix, `httpPostNFC(token)` → `POST /api/nfc/tap {"token":token}` for NFC prefix. The shared TCP/HTTP logic moved to `httpPostJson(path, body)`. Serial fallback format (`CARD|uid`, `NFC|token`) untouched — ArduinoBridge continues unchanged. `HEARTBEAT_INTERVAL_MS = 30000` constant stubbed as a S04 hook.

**S02 (Phone NFC Cashier Payment)** wired the phone tap path from socket event to balance debit. Backend: `complete_sale_nfc()` added to `cashier_routes.py` — a direct clone of `complete_sale()` with one difference: it first resolves `virtual_card_token` through the VirtualCards worksheet (VirtualCardToken → IsActive → MoneyCardNumber), then passes the resolved card number through the identical three-step retry loop, rollback-on-exhaustion, offline-queue fallback, session-pop replay-prevention, and email/SMS/FCM notification tail. Frontend: `socket.on('nfc_payment', ...)` added inside `initWebSocket()` calling `completeNFCSale(data.token)`, which opens the payment modal proactively (phone tap can arrive before cashier initiates checkout) and never checks `arduinoConnected` (inbound event — the tap already arrived).

**S03 (WiFi Status Indicator)** added the backend heartbeat infrastructure and the cashier badge. `POST /api/arduino/heartbeat` in `web_app.py` — API-key-authenticated, updates `app.arduino_last_heartbeat`, emits `arduino_wifi_status {online, last_seen_s}` via SocketIO. `GET /cashier/api/arduino-wifi-status` in `cashier_routes.py` — JWT-protected, returns `{online, last_seen_s}`, with `last_seen_s = -1.0` sentinel when never heartbeated. Cashier UI: `#wifiBadge` span (green `.online` / red `.offline`) driven by socket event; `updateWifiBadge()` checks serial `statusIndicator` class before clearing `arduinoConnected` on WiFi offline (serial is the stronger signal); `fetchArduinoWifiStatus()` called at DOMContentLoaded to prime badge before first socket event; both `checkout()` and `quickPay()` alert text updated to mention WiFi alongside COM port.

**S04 (Powerbank Hardening + Wireless Docs)** closed the loop on the hardware deployment. Three surgical edits to the firmware: `static unsigned long lastHeartbeatMs = 0;` at file scope (the only placement that persists across `loop()` iterations), 4-line timer block inserted after `handleIncomingSerial()` and before `if (!found) return` at line 530 (heartbeat must fire during idle — after the early-exit it never would), and `HEARTBEAT_INTERVAL_MS` comment updated from stub text to authoritative description. The heartbeat POST is dual-purpose: RF burst keeps powerbank above auto-shutoff threshold; `/api/arduino/heartbeat` handler emits `arduino_wifi_status` to drive the cashier badge green. `arduino/README-wireless.md` written with 8 sections (hardware table, wiring, libraries, secrets.h field table, flashing steps, verification, powerbank selection, troubleshooting).

## Cross-Slice Verification

**S01 — bash scripts/verify-s01.sh: 8/8 PASS**
- No bare `httpPost(` call sites remain in firmware
- `httpPostCard` and `httpPostNFC` functions defined
- `prefix == "CARD"` dispatch in `deliver()`
- `/api/arduino/card-read` path present, `{"uid":` payload present
- `HEARTBEAT_INTERVAL_MS` constant in firmware; `secrets.h` references it

**S02 — python -m py_compile cashier_routes.py: exit 0; bash scripts/verify-s02.sh: 9/9 PASS**
- `complete_sale_nfc` function defined; `/api/complete-sale-nfc` route registered
- `VirtualCardToken` field name, `IsActive` guard, `NFC Purchase` transaction label present
- `flask_session.pop('pending_transaction')` present (replay prevention)
- `socket.on('nfc_payment')` in cashier UI; `completeNFCSale` function defined; correct endpoint URL in JS

**S03 — python -m py_compile web_app.py + cashier_routes.py: both exit 0; bash scripts/verify-m003-s03.sh: 12/12 PASS**
- `import time`, `ARDUINO_WIFI_OFFLINE_S`, `app.arduino_last_heartbeat`, heartbeat route, socketio emit — all confirmed in web_app.py
- `arduino-wifi-status` route with `jwt_required` confirmed in cashier_routes.py
- `#wifiBadge` span, `arduino_wifi_status` socket listener, old COM-port-only alert removed — all confirmed in cashier_index.html

**S04 — bash scripts/verify-m003-s04.sh: 8/8 PASS; bash scripts/verify-m003-s03.sh re-run: 12/12 PASS**
- `lastHeartbeatMs` declared at file scope; `httpPostJson` heartbeat call in loop(); `HEARTBEAT_INTERVAL_MS` not a stub; `ensureWiFi` present
- `arduino/README-wireless.md` exists; port 5003 named; `ARDUINO_API_KEY` named; powerbank guidance present

**Milestone definition of done — item-by-item:**

| Item | Status | Evidence |
|------|--------|----------|
| `arduino/README-wireless.md` exists with complete instructions | ✅ | `test -f` exits 0; 164-line file; 8/8 verify checks cover README content |
| `python -m py_compile` exits 0 on all modified Python files | ✅ | web_app.py: OK; cashier_routes.py: OK |
| S01 firmware fix is flashed and confirmed (physical card WiFi POST → `/api/arduino/card-read`) | ⏳ | Contract verified (8/8 grep assertions); flash + live tap → Flask log requires physical hardware UAT |
| S02 phone NFC payment works end-to-end (tap → Sheets debit) | ⏳ | Contract verified (9/9 assertions, py_compile); live phone tap at deployed Arduino requires physical hardware UAT |
| S03 WiFi badge shows correct state (green/red) | ⏳ | Contract verified (12/12 assertions); badge going green requires S04 firmware flashed to real hardware |
| S04 hardening confirmed (WiFi reconnect, 30-min powerbank soak) | ⏳ | Contract verified (8/8 assertions); operational proof requires physical hardware UAT |

All code work is complete. The remaining gate is hardware UAT: flash the firmware, confirm `POST /api/arduino/card-read 200` in Flask log on card tap, confirm badge goes green within 30s, confirm 30-minute powerbank idle, confirm WiFi drop/reconnect. These require the physical Arduino on the school LAN.

## Requirement Changes

- R020: active → active (contract verified: verify-s01.sh 8/8; runtime hardware UAT pending — flash + card tap → `/api/arduino/card-read 200` in Flask log)
- R021: active → active (contract verified: py_compile + verify-s02.sh 9/9; live phone tap at deployed hardware pending)
- R022: active → active (contract verified: py_compile + verify-m003-s03.sh 12/12; badge going green on live heartbeat pending hardware flash)
- R023: active → active (contract verified: verify-m003-s04.sh 8/8 including lastHeartbeatMs + ensureWiFi; 30-min powerbank soak + WiFi drop recovery pending hardware)
- R024: active → **validated** — `arduino/README-wireless.md` exists (164 lines); verify-m003-s04.sh checks (e–h) all pass; README covers all required topics (hardware, wiring, secrets.h with explicit port 5003 + ARDUINO_API_KEY, flashing, powerbank selection, verification, troubleshooting); no hardware required to validate documentation completeness

## Forward Intelligence

### What the next milestone should know
- The firmware is structurally correct but must be flashed to the hardware and tested before M003 is fully done. The human UAT gate is: (1) Serial Monitor shows `HTTP: POST /api/arduino/card-read` on card tap, (2) Flask log shows `POST /api/arduino/card-read 200`, (3) cashier UI shows `card_read` event and sale success modal, (4) badge goes green within 30s of boot.
- `complete_sale_nfc()` and `api_server.py:nfc_pay()` both resolve VirtualCards by `VirtualCardToken` / `IsActive` / `MoneyCardNumber` — these field names are duplicated. Any Sheets schema change must update both files together; there is no shared constant.
- The heartbeat endpoint is at `POST /api/arduino/heartbeat` with `X-API-Key` header — same guard pattern as `POST /api/arduino/card-read`. Both require `ARDUINO_API_KEY` in Flask `.env` to match `SECRET_API_KEY` in `secrets.h`. A 401 on heartbeat means the API key doesn't match.
- `ARDUINO_WIFI_OFFLINE_S` defaults to 60s (two missed 30s heartbeats before badge goes red). This is env-configurable — useful if the heartbeat interval is tuned.
- `app.arduino_last_heartbeat` is a plain Python float on the Flask app object. Safe for single-worker (R016 constraint). Do not use in any multi-worker config.

### What's fragile
- `httpPostJson` body is raw string concatenation — works for RFID UIDs (hex digits) and UUID tokens (alphanumeric + dashes) but will break if either ever contains `"` or `\`; no JSON library in firmware
- VirtualCards field names duplicated in `cashier_routes.py:complete_sale_nfc` and `api_server.py:nfc_pay` — single point of breakage if Sheets schema changes
- Powerbank keep-alive relies on RF burst from POST, not a dedicated hardware signal — cheap powerbanks with sub-100mA auto-shutoff thresholds may still cut power despite the 30s heartbeat; PN532 polling loop baseline draw (~180–200mA) is the real current buffer
- `fetchArduinoWifiStatus()` silently fails if JWT is expired at DOMContentLoaded — badge stays red until next socket heartbeat event; acceptable for cashier flow (always logged in) but worth knowing if session timeouts are shortened
- `completeNFCSale` opens the payment modal proactively if not visible — correct behavior when phone tap arrives before cashier initiates checkout; do not add an `arduinoConnected` guard here (D033)

### Authoritative diagnostics
- `bash scripts/verify-s01.sh` — first check after any firmware edit; exits 0 = routing structure correct
- Flask access log `POST /api/arduino/card-read 200` — definitive proof card WiFi POST reached the right endpoint
- Flask access log `POST /api/arduino/heartbeat 200` every 30s — heartbeat timer confirmed firing; `401` → API key mismatch between `secrets.h` and Flask `.env`
- `document.getElementById('wifiBadge').className` in browser console — immediate badge state (no DevTools Network needed)
- `GET /cashier/api/arduino-wifi-status` with cashier JWT — ground truth: `last_seen_s: -1.0` = never heartbeated; `online: false` = more than 60s since last heartbeat
- `grep "event=nfc_sale" server.log` — finds both `nfc_sale_complete` (success) and `nfc_sale_no_pending` (missing session); fastest first-look for NFC payment issues

### What assumptions changed
- Original plan assumed `scripts/verify-m003-s03.sh` needed to be written in S03/T01. It was already present from prior work with all 12 checks correctly defined — T01 skipped that write step.
- Original plan assumed `updateWifiBadge()` would use `arduinoConnected = arduinoConnected || data.online`. Implemented conditional form instead — WiFi going offline does not override an active serial connection. The `||` shorthand missed the offline case.
- Original plan assumed the payment modal would always be open when a phone NFC tap arrives. Actual: phone tap can arrive before cashier initiates checkout — `completeNFCSale` must open the modal proactively via the `display !== 'flex'` guard.

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — replaced `httpPost` with `httpPostJson`/`httpPostCard`/`httpPostNFC`; updated `deliver()` dispatch; added `HEARTBEAT_INTERVAL_MS` constant; added `lastHeartbeatMs` file-scope variable + 4-line heartbeat timer block in `loop()`; updated `HEARTBEAT_INTERVAL_MS` comment from stub to authoritative description
- `arduino/bankongseton_rfid/secrets.h` — added `HEARTBEAT_INTERVAL_MS` orientation comment
- `arduino/README-wireless.md` — new; complete standalone wireless deployment guide (164 lines, 8 sections)
- `backend/dashboard/web_app.py` — added `import time`, `ARDUINO_WIFI_OFFLINE_S` constant, `app.arduino_last_heartbeat = 0.0` init, `POST /api/arduino/heartbeat` route
- `backend/dashboard/cashier/cashier_routes.py` — added `complete_sale_nfc()` (~235 lines) after `complete_sale()`; added `GET /cashier/api/arduino-wifi-status` route after `queue_status()`
- `backend/dashboard/cashier/templates/cashier_index.html` — WiFi badge CSS, `#wifiBadge` span, `updateWifiBadge()` + `fetchArduinoWifiStatus()`, `arduino_wifi_status` socket listener, `socket.on('nfc_payment')` handler, `completeNFCSale(token)` function, alert text in `checkout()` and `quickPay()` updated
- `scripts/verify-s01.sh` — new; 8-check firmware routing grep assertions
- `scripts/verify-s02.sh` — new; 9-check NFC cashier endpoint + UI structural assertions
- `scripts/verify-m003-s03.sh` — pre-existing; 12 checks verified correct as-is
- `scripts/verify-m003-s04.sh` — new; 8-check firmware heartbeat + README assertions
