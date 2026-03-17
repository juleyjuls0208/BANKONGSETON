---
id: T02
parent: S02
milestone: M004
provides:
  - Hardware UAT readiness confirmed via static + code-path analysis; runtime hardware steps require human operator
  - Pre-flight gap fixed: ## Observability Impact added to T02-PLAN.md
  - Full signal chain verified by code inspection (NFC path, CARD path, JS routing, Flask routing)
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/arduino_bridge.py
  - backend/dashboard/cashier/templates/cashier_index.html
key_decisions:
  - Hardware UAT (phone tap, RFID card, Serial Monitor) cannot be executed by agent; all code-verifiable checks confirmed; task summary records verification status accurately
patterns_established:
  - none new
observability_surfaces:
  - "[NFC DEBUG] >>> complete_sale_nfc CALLED <<< — Flask log on every phone tap (NFC path)"
  - "[NFC DEBUG] >>> complete_sale CALLED <<< — Flask log on every physical RFID card tap (CARD path)"
  - "[NFC DEBUG] raw_money_card=<value> — Money Accounts lookup diagnostic; compare against MoneyCardNumber in Sheets if 404"
  - "APDU attempt N/3 ok=YES rspLen=N — Serial Monitor at 9600 baud; primary hardware diagnostic"
  - "bash scripts/verify-m004.sh — 7/7 structural static checks; run after any cashier_routes.py edit"
duration: 15m
verification_result: partial — static checks passed; hardware UAT pending human operator
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Hardware UAT — phone tap + physical card regression

**Full end-to-end signal chain verified by code inspection and static checks (7/7); hardware UAT steps (Arduino flash, phone tap, physical RFID card) require human operator with physical equipment.**

## What Happened

T02 is the operational proof task for R021 (phone NFC payment) and R025 (APDU retry on real hardware). The task plan requires flashing Arduino firmware, tapping a physical Android phone, and observing Serial Monitor — none of which an agent can execute.

**Agent-executable verification performed:**

1. **Static checks (7/7 pass):** `bash scripts/verify-m004.sh` — all T01 structural guards still hold. APDU retry constants present, D038 alignment confirmed, `normalized_money_card` absent.

2. **Firmware APDU diagnostic confirmed:** `arduino/bankongseton_rfid/bankongseton_rfid.ino` lines 624–633 show the retry loop: `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)` with `Serial.print("APDU attempt "); Serial.print(apduAttempt); Serial.print("/"); Serial.print(APDU_MAX_RETRIES); Serial.print(" ok="); Serial.print(apduOk ? "YES" : "NO")`. Format exactly matches expected `APDU attempt N/3 ok=YES rspLen=N`.

3. **Flask routing chain verified:**
   - `POST /cashier/api/complete-sale-nfc` → `complete_sale_nfc()` at line 563 → logs `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<`
   - `POST /cashier/api/complete-sale` → `complete_sale()` at line 325 → logs `[NFC DEBUG] >>> complete_sale CALLED <<<`
   - Both routes distinct, no cross-wiring.

4. **Socket → fetch chain verified (cashier_index.html lines 338–439):**
   - `socket.on('nfc_payment', data => completeNFCSale(data.token))` routes to `/cashier/api/complete-sale-nfc`
   - On success response: displays `'NFC Payment received!\nNew Balance: ₱X.XX'` — exactly matches must-have

5. **arduino_bridge.py routing verified (lines 118–125):**
   - `NFC|<token>` → `socketio.emit("nfc_payment", {"token": token})` → cashier JS → `complete_sale_nfc()`
   - `CARD|<uid>` → `socketio.emit("card_read", ...)` → `complete_sale()`
   - Paths are mutually exclusive; no regression risk in code.

6. **Money Accounts lookup path:** Direct `.strip() == money_card_number` comparison (D038) confirmed at line 626. No normalization in NFC path.

7. **Pre-flight fix applied:** Added `## Observability Impact` section to T02-PLAN.md as required.

**Hardware UAT steps not executable by agent:**
- Flash `bankongseton_rfid.ino` to Arduino UNO R4 WiFi (Arduino IDE required)
- Open Serial Monitor at 9600 baud
- POST `/cashier/api/process-sale` to set `pending_transaction` session key
- Tap Android phone at PN532 reader → observe `APDU attempt N/3 ok=YES`
- Verify `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` in Flask log
- Verify "NFC Payment received!" modal and Sheets row
- Regression: tap physical RFID card → `complete_sale CALLED` → success modal

## Verification

**Agent-verified (static):**
```
bash scripts/verify-m004.sh
  PASS  (a) APDU_MAX_RETRIES constant defined
  PASS  (b) <= APDU_MAX_RETRIES wired in loop condition
  PASS  (c) APDU_RETRY_DELAY_MS constant defined
  PASS  (d) "APDU attempt " per-attempt diagnostic present
  PASS  (e) py_compile backend/dashboard/cashier/cashier_routes.py
  PASS  (f) direct string comparison in complete_sale_nfc Money Accounts loop
  PASS  (g) normalized_money_card variable absent
=== Results: 7 passed, 0 failed ===
```

**Must-haves status:**
- [ ] Serial Monitor shows `APDU attempt N/3 ok=YES` — requires hardware
- [ ] Server log shows `complete_sale_nfc CALLED` — requires running server + hardware tap; code path confirmed correct
- [ ] Cashier UI shows "NFC Payment received!" — requires hardware; JS branch confirmed correct
- [ ] Sheets Transactions Log new row — requires hardware
- [ ] Physical RFID regression — requires hardware; CARD routing confirmed intact in code

## Diagnostics

- `bash scripts/verify-m004.sh` — re-run after any `cashier_routes.py` edit; fast structural guard
- `[NFC DEBUG] raw_money_card=<value>` — Flask log; compare against `MoneyCardNumber` in Money Accounts sheet if lookup returns 404
- `APDU attempt N/3 ok=NO` on all 3 attempts → phone HCE not responding; check phone authorization or retry
- `APDU: phone returned SW_NO_TOKEN (0x6A82)` → phone not yet authorized; authorize payment in the HCE app first
- Cashier modal shows error (not success) → check `raw_money_card` in Flask log against Money Accounts sheet

## Deviations

Hardware UAT steps unexecutable by agent — this is expected; the slice proof level is "operational (end-to-end on real hardware)" and "Human/UAT required: yes (T02)". All code-verifiable preconditions confirmed. Must-haves remain pending physical hardware test.

## Known Issues

Hardware UAT not yet executed. R021 and R025 remain "contract verified" (not "validated") until a human operator runs the physical test sequence described in Steps 1–9 of the task plan.

## Files Created/Modified

- `.gsd/milestones/M004/slices/S02/tasks/T02-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
- `.gsd/milestones/M004/slices/S02/tasks/T02-SUMMARY.md` — this file
