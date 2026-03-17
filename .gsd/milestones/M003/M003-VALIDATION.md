---
verdict: needs-attention
remediation_round: 0
---

# Milestone Validation: M003

## Success Criteria Checklist

- [x] **Physical RFID card tapped at powerbank-powered Arduino completes a sale end-to-end (balance debited, cashier sees success modal, parent notified)** — evidence: S01 contract fully verified (verify-s01.sh 8/8 pass); `httpPostCard(uid)` → `POST /api/arduino/card-read {"uid":uid}`, `deliver()` dispatches by `prefix == "CARD"`, no bare `httpPost()` call sites remain; backend `/api/arduino/card-read` endpoint pre-existing and wired to `card_read` SocketIO event. **Gap: hardware UAT not completed** — flash + physical card tap → `POST /api/arduino/card-read 200` in Flask log is the remaining runtime gate (explicitly documented in S01-SUMMARY.md as the human/hardware verification step).

- [x] **Student Android phone tapped at same Arduino completes a sale end-to-end (via cashier flow)** — evidence: S02 contract fully verified (verify-s02.sh 9/9 pass, py_compile exit 0); `POST /cashier/api/complete-sale-nfc` endpoint resolves `virtual_card_token` via VirtualCards sheet, debits balance, returns same success payload as physical card tap; `socket.on('nfc_payment')` in cashier UI calls `completeNFCSale(token)`. D038 alignment applied (M004/S02): direct `str().strip()` comparison in Money Accounts loop, `normalized_money_card` removed. **Gap: hardware UAT not completed** — live phone tap at deployed Arduino is the remaining runtime gate.

- [x] **Cashier UI displays a WiFi status badge; badge green when Arduino heartbeating; "Pay Now" enables on WiFi alone (no COM port required)** — evidence: S03 contract fully verified (verify-m003-s03.sh 12/12 pass); `#wifiBadge` span with `.online`/`.offline` CSS classes in cashier header; `socket.on('arduino_wifi_status')` sets badge and `arduinoConnected`; `fetchArduinoWifiStatus()` primes badge on DOMContentLoaded; `checkout()` and `quickPay()` alert text updated to mention WiFi alongside COM port. **Gap: badge-goes-green runtime proof pending S04 firmware heartbeat flash** — badge stays red until Arduino sends its first heartbeat POST; documented as expected pre-flash state.

- [x] **Arduino recovers from WiFi drops automatically without manual intervention** — evidence: S04 contract verified (verify-m003-s04.sh 8/8 pass); `ensureWiFi()` called before every heartbeat POST in firmware; firmware reconnect logic is in place and structurally verified. **Gap: operational proof (simulated WiFi drop/reconnect cycle) requires physical hardware** — cannot be verified without flashing and disconnecting the access point.

- [x] **Wireless standalone deployment documented in `arduino/README-wireless.md`** — evidence: R024 fully validated; `test -f arduino/README-wireless.md` exits 0; 164-line README with 8 sections (Hardware Required, Wiring, Libraries, secrets.h field table naming port 5003 + ARDUINO_API_KEY explicitly, Flashing, Verification, Powerbank Selection, Troubleshooting); verify-m003-s04.sh checks (e–h) all pass. No hardware required to validate documentation completeness.

---

## Slice Delivery Audit

| Slice | Claimed | Delivered | Status |
|-------|---------|-----------|--------|
| S01 | `httpPostCard(uid)` → `/api/arduino/card-read`; `httpPostNFC(token)` → `/api/nfc/tap`; `deliver()` dispatches by prefix; serial fallback format unchanged; `HEARTBEAT_INTERVAL_MS` stub; `verify-s01.sh` 8/8 | All 7 items confirmed in S01-SUMMARY.md; verify-s01.sh 8/8 pass; py_compile not applicable (firmware) | **pass (contract)** |
| S02 | `POST /cashier/api/complete-sale-nfc`; `socket.on('nfc_payment')` → `completeNFCSale(token)`; VirtualCards token resolution; same debit/notify logic as `complete_sale()`; `verify-s02.sh` 9/9 | All items confirmed; verify-s02.sh 9/9 pass; py_compile exit 0; D038 alignment added by M004/S02 (direct string comparison, `normalized_money_card` removed) | **pass (contract)** |
| S03 | `POST /api/arduino/heartbeat` (API-key-authenticated); `GET /cashier/api/arduino-wifi-status` (JWT); `#wifiBadge` span; `updateWifiBadge()`; `fetchArduinoWifiStatus()`; `arduino_wifi_status` socket listener; `arduinoConnected` WiFi path; alert text updated | All items confirmed; verify-m003-s03.sh 12/12 pass; py_compile exit 0 on web_app.py and cashier_routes.py | **pass (contract)** |
| S04 | Firmware heartbeat loop (30s, `lastHeartbeatMs`, `ensureWiFi()` before POST, timer before `if (!found) return`); `arduino/README-wireless.md` (8 sections); `verify-m003-s04.sh` 8/8 | All items confirmed; verify-m003-s04.sh 8/8 pass; firmware spot-checks confirmed (`lastHeartbeatMs` at file scope, heartbeat block at lines 479–485 before early-exit at 530, stub text absent) | **pass (contract)** |

**All 37 contract assertions pass (8 S01 + 9 S02 + 12 S03 + 8 S04). `python -m py_compile` exits 0 on all modified Python files.**

---

## Cross-Slice Integration

All boundary map entries align with what was actually built.

**S01 → S02:** S01 produces `httpPostNFC(token)` routing to `/api/nfc/tap`; S02 correctly consumes the resulting `nfc_payment` SocketIO event (`socket.on('nfc_payment', function(data) { completeNFCSale(data.token); })`). Payload field `.token` matches what `dashboard_core.py` emits at the `nfc_payment` event. No mismatch.

**S01 → S03:** S01 proves the network path from Arduino to Flask backend (structural verification confirms `/api/arduino/card-read` POST is correctly routed). S03's heartbeat endpoint follows the identical API-key-auth pattern as `arduino_card_read()`. No dependency gap.

**S02 → S04:** S02 delivers `complete_sale_nfc()` endpoint and `nfc_payment` handler. S04's heartbeat work is orthogonal (firmware only, no backend changes). S04 correctly identifies S02 as a non-blocking dependency.

**S03 → S04:** S03 delivers `POST /api/arduino/heartbeat` backend endpoint and SocketIO `arduino_wifi_status` emit. S04 adds the firmware heartbeat POST loop that will call this endpoint. The timer placement (after `handleIncomingSerial()`, before `if (!found) return`) ensures heartbeats fire during idle — exactly what the badge and powerbank-keep-alive require.

**One note (not a gap):** S04 picks up `HEARTBEAT_INTERVAL_MS` from S01, where it was defined as a stub constant. The comment was updated in S04 to reflect actual purpose. The constant value (30000ms) is consistent across firmware, backend threshold (60s = 2 missed heartbeats before offline), and documentation.

---

## Requirement Coverage

| Requirement | Class | Assigned Slice | Contract Proof | Runtime Proof | Status |
|-------------|-------|---------------|----------------|--------------|--------|
| R020 — Correct WiFi Payment Routing | primary-user-loop | M003/S01 | verify-s01.sh 8/8 ✓ | Flash + card tap → `/api/arduino/card-read 200` in Flask log — **pending hardware** | active |
| R021 — Phone NFC Payment at Cashier | primary-user-loop | M003/S02 | verify-s02.sh 9/9, py_compile ✓ | Live phone tap at deployed Arduino — **pending hardware** | active |
| R022 — Arduino WiFi Status in Cashier UI | operability | M003/S03 | verify-m003-s03.sh 12/12, py_compile ✓ | Badge green on live heartbeat — **pending hardware flash** | active |
| R023 — Arduino Stable on Powerbank | continuity | M003/S04 | verify-m003-s04.sh 8/8 ✓ | 30-min powerbank soak + WiFi drop/reconnect cycle — **pending hardware** | active |
| R024 — Wireless Deployment Documentation | operability | M003/S04 | verify-m003-s04.sh checks (e–h) ✓; README-wireless.md 164 lines | Documentation completeness fully verifiable without hardware | **validated** |

All five requirements are covered by at least one slice. R024 is fully validated. R020–R023 are contract-verified with hardware UAT as the remaining validation gate.

---

## Verdict Rationale

**`needs-attention`** — All code deliverables are complete and structurally sound. No missing software, no implementation gaps, no architectural deviations. Every check, assertion, and compile-time verification passes. The sole gap is the hardware UAT layer: flashing the firmware to a physical Arduino UNO R4 WiFi on a powerbank, performing a real card tap and phone tap, confirming the 30-minute powerbank idle, and cycling WiFi to prove auto-reconnect.

**Why not `pass`:** The milestone's Definition of Done explicitly requires S01 to be "flashed and confirmed" and S04 to show "Arduino reconnects after WiFi drop; heartbeat sustains powerbank across 30-minute idle." These are runtime/operational conditions that no amount of grep assertions or py_compile calls can substitute for. The success criteria include end-to-end sale completion (criteria 1 and 2), which requires hardware. R020–R023 remain at `active` (not `validated`) status precisely because the hardware gate is uncleared.

**Why not `needs-remediation`:** There are no code gaps, regressions, or missing deliverables that a new slice could address. The remaining work is entirely a human/hardware dependency — access to the physical Arduino, a powerbank, and the school LAN. Adding a remediation slice would produce no additional code; the hardware gate can only be cleared by a human operator in the deployment environment. The PROJECT.md itself records M003 as "[x] complete" with "Hardware UAT gate remaining" — this is the anticipated exit state of the contract phase.

**Summary of attention items:**

1. **Hardware flash + card tap (R020):** Flash current `bankongseton_rfid.ino` to Arduino UNO R4 WiFi; confirm `POST /api/arduino/card-read 200` in Flask access log on physical RFID card tap; confirm `card_read` event fires in cashier UI.

2. **Hardware flash + phone tap (R021):** With same flashed Arduino, confirm Android phone NFC tap → `nfc_payment` event → `completeNFCSale()` → `POST /cashier/api/complete-sale-nfc 200` → success modal + Sheets balance debit.

3. **WiFi badge live test (R022):** Confirm `#wifiBadge` turns green in cashier UI within 30s of first heartbeat POST reaching backend; confirm badge turns red after Arduino powers off.

4. **Powerbank soak + WiFi drop recovery (R023):** Confirm Arduino stays online for 30-minute idle on standard USB powerbank; simulate WiFi drop (router off/on) and confirm Arduino reconnects and badge recovers without manual intervention.

Once all four hardware UAT items pass, R020–R023 can be marked `validated` and M003 sealed.

---

## Remediation Plan

_Not applicable — verdict is `needs-attention`. No new slices required. All gaps are hardware/operational gates, not software deliverables._
