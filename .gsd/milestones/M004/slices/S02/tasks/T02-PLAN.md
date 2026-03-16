---
estimated_steps: 8
estimated_files: 1
---

# T02: Hardware UAT — phone tap + physical card regression

**Slice:** S02 — End-to-End Validation + Backend Cleanup
**Milestone:** M004

## Description

This is the operational proof task. Flash the S01 firmware (no code changes — just flash what's in the repo), run through the full NFC phone payment flow at the cashier terminal, and confirm all four diagnostic surfaces agree. Then tap a physical RFID card to confirm no regression. This task advances R021 and R025 from "contract verified" to "validated."

Note: `pending_transaction` session key must be set before the NFC tap arrives — cashier must click Checkout to POST `/cashier/api/process-sale` first. If the tap arrives before that, `complete_sale_nfc` returns 400. This is expected behavior; the fix is operational (sequence matters).

## Steps

1. Flash `arduino/bankongseton_rfid/bankongseton_rfid.ino` to Arduino UNO R4 WiFi via Arduino IDE. No edits needed — S01 firmware is already in place.
2. Open Serial Monitor at 9600 baud.
3. In cashier UI: log in, load products from Sheets, add a product to cart, click Checkout → confirm `POST /cashier/api/process-sale` 200 in Flask log (sets `pending_transaction`).
4. Tap Android phone (with HCE virtual card app) at the Arduino PN532 reader.
5. Watch Serial Monitor for `APDU attempt N/3 ok=YES` — confirms retry loop is working and NFC token was exchanged.
6. Watch Flask server log for `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` (not `complete_sale CALLED`) — confirms correct routing.
7. Confirm cashier UI shows "NFC Payment received! New Balance: ₱X.XX" success modal.
8. Verify new "NFC Purchase" row in Google Sheets Transactions Log.
9. Regression check: tap a physical RFID card → Serial Monitor shows `CARD|<uid>` → server log shows `complete_sale CALLED` → cashier UI shows success modal.

## Must-Haves

- [ ] Serial Monitor shows `APDU attempt N/3 ok=YES` on phone tap (N ≥ 1, ≤ 3)
- [ ] Server log shows `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` (not `complete_sale CALLED`)
- [ ] Cashier UI shows "NFC Payment received! New Balance: ₱X.XX"
- [ ] Sheets Transactions Log has new "NFC Purchase" row after phone tap
- [ ] Physical RFID card tap produces `complete_sale CALLED` in server log → cashier success modal (no regression)

## Verification

- Serial Monitor output: `APDU attempt N/3 ok=YES rspLen=N` visible (runtime)
- Flask log: `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` visible after phone tap
- Cashier modal: "NFC Payment received!" visible in UI
- Sheets: Transactions Log new row with type "NFC Purchase"
- Flask log on physical card tap: `complete_sale CALLED` visible (not `complete_sale_nfc`)

## Inputs

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — S01 firmware; flash as-is
- T01 must be complete first — `complete_sale_nfc()` must use direct string comparison before this test, otherwise Money Accounts lookup may fail silently with 404 even if APDU succeeds

## Observability Impact

This task produces no code changes — it is operational proof only. The signals below are the observable surfaces that confirm correct end-to-end behavior at runtime.

**New signals introduced:** none — all signals were wired in prior milestones/slices.

**Active signals to inspect:**
- **Serial Monitor (9600 baud):** `APDU attempt N/3 ok=YES rspLen=N` — one line per attempt, up to 3. If `ok=NO` on all 3, phone HCE is not responding; check VirtualCards row or phone authorization state.
- **Flask server log:** `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` — confirms NFC routing, not CARD. `[NFC DEBUG] raw_money_card=<value>` — emitted immediately after; compare against `MoneyCardNumber` in Money Accounts sheet if lookup misses.
- **Cashier UI:** "NFC Payment received! New Balance: ₱X.XX" success modal (happy path) or "Card not found" / 400 error modal (failure path — check `raw_money_card` value in Flask log).
- **Google Sheets Transactions Log:** new row with `type = NFC Purchase` after successful phone tap.

**Failure visibility:**
- `complete_sale_nfc CALLED` missing → APDU never succeeded, check `APDU attempt N/3 ok=NO` lines in Serial Monitor.
- `raw_money_card` print shows wrong value → token mismatch; verify VirtualCards sheet `MoneyCardNumber` column.
- Modal shows "Card not found" (404) despite correct routing → Money Accounts sheet `MoneyCardNumber` doesn't match `raw_money_card` value; check D038 alignment in sheets.
- Physical RFID card tap produces `complete_sale_nfc CALLED` instead of `complete_sale CALLED` → routing regression; check `arduino_bridge.py` and cashier route wiring.

**What a future agent can inspect after this task:**
- `bash scripts/verify-m004.sh` — 7/7 structural checks; fast re-confirmation that D038 alignment is intact.
- `grep "complete_sale_nfc\|complete_sale CALLED" backend/dashboard/cashier/cashier_routes.py` — confirm both log lines are present and distinct.

## Expected Output

- R021 advances to validated: phone tap completes a real payment at cashier terminal
- R025 advances to validated: `APDU attempt N/3 ok=YES` confirmed on real phone hardware
- R020, R022, R023 regression: physical card tap confirms CARD routing still works (these remain "active" — their full hardware UAT is a separate gate)
