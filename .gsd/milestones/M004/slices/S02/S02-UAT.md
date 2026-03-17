# S02: End-to-End Validation + Backend Cleanup — UAT

**Milestone:** M004
**Written:** 2026-03-16

## UAT Type

- UAT mode: mixed (artifact-driven static checks + live-runtime hardware)
- Why this mode is sufficient: Static checks (7/7) confirm all code-level preconditions; live hardware test is the operational proof that R021 and R025 advance to validated

## Preconditions

1. Arduino UNO R4 WiFi flashed with `arduino/bankongseton_rfid/bankongseton_rfid.ino` (S01 firmware — current HEAD)
2. PN532 NFC reader connected to Arduino over SPI
3. Arduino powered and connected to school LAN (or connected via USB serial to the PC running the Flask server)
4. Flask dashboard server running (the process that handles `/cashier/api/complete-sale-nfc`)
5. Android phone with Bangko ng Seton HCE app installed and configured with a student account that has a registered virtual card
6. That student's `MoneyCardNumber` in the VirtualCards sheet matches a row in the Money Accounts sheet (column `MoneyCardNumber`)
7. That student's Money Accounts balance is sufficient to cover the product price being tested
8. Cashier is logged in to the cashier UI; at least one product is loaded
9. Serial Monitor open at 9600 baud (Arduino IDE or equivalent)
10. Flask server log visible in a terminal

## Smoke Test

Run `bash scripts/verify-m004.sh` from the project root. Must print `7 passed, 0 failed` before any hardware test begins. If this fails, stop — the backend or firmware has a structural problem.

---

## Test Cases

### 1. Contract verification (static — no hardware required)

1. From project root: `bash scripts/verify-m004.sh`
2. Confirm all 7 lines read `PASS` and the final line reads `=== Results: 7 passed, 0 failed ===`
3. Run: `grep -c "normalized_money_card" backend/dashboard/cashier/cashier_routes.py`
4. **Expected:** output is `0` — no normalization in NFC lookup path
5. Run: `grep "normalize_card_uid" backend/dashboard/cashier/cashier_routes.py` and check line numbers
6. **Expected:** all matches are in the `complete_sale()` function body (lines ~333, 353, 364, 471, 583), none inside `complete_sale_nfc()`

### 2. Phone NFC payment — happy path

1. In cashier UI: click a product tile, then click "Checkout" to initiate `process-sale`. This sets the `pending_transaction` session key required for `complete_sale_nfc()` to find the sale.
2. Open Serial Monitor at 9600 baud.
3. Tap the registered Android phone (HCE enabled, authorized) against the PN532 reader.
4. Watch Serial Monitor.
5. **Expected (Serial Monitor):** One or more lines of the form `APDU attempt N/3 ok=YES rspLen=N` (N ≤ 3). The first `ok=YES` line should be followed by `HTTP: delivered — NFC|<token>`.
6. **Expected (Flask log):** Within ~1 second: `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` appears. Also expect `[NFC DEBUG] raw_money_card=<token_value>` and `[NFC DEBUG] money_accounts count=<n>`.
7. **Expected (cashier UI):** Success modal appears: "NFC Payment received! New Balance: ₱X.XX" where X.XX is the student's old balance minus the product price.
8. **Expected (Sheets):** A new row appears in the Transactions Log with type "NFC Purchase", the student's ID, the product name, the deducted amount, and today's date.

### 3. Phone NFC payment — retry path (APDU attempt > 1)

This case confirms the retry loop works when HCE initialization is slow.

1. Same setup as Test Case 2.
2. Tap phone slightly earlier than normal (before HCE service is fully initialized, if observable).
3. **Expected (Serial Monitor):** One or more `APDU attempt N/3 ok=NO rspLen=60` lines before the final `APDU attempt N/3 ok=YES` line. Total attempts ≤ 3.
4. **Expected (Flask log + cashier UI):** Same success outcome as Test Case 2 — retry does not degrade the end result.
5. **Note:** This case may not be reliably reproducible on demand; observing it once on any tap confirms the retry diagnostic output format is correct.

### 4. Physical RFID card tap — regression check

1. After the phone tap in Test Case 2 succeeds, initiate a new checkout for a different product (or same product with sufficient balance).
2. Tap a physical RFID card (not a phone) at the PN532 reader.
3. **Expected (Serial Monitor):** No `APDU attempt` lines. Instead: `CARD|<uid>` delivery line.
4. **Expected (Flask log):** `[NFC DEBUG] >>> complete_sale CALLED <<<` (not `complete_sale_nfc CALLED`).
5. **Expected (cashier UI):** Standard card payment success modal (not "NFC Payment received!" — the message differs).
6. **Expected (Sheets):** New row in Transactions Log with type "Purchase" (not "NFC Purchase").

### 5. Backend cleanup — normalize_card_uid import present

1. Run: `grep "from.*import.*normalize_card_uid\|import.*normalize_card_uid" backend/dashboard/cashier/cashier_routes.py`
2. **Expected:** At least one match — the import line must still exist (used by `complete_sale()`).
3. Run: `python -m py_compile backend/dashboard/cashier/cashier_routes.py`
4. **Expected:** Exit code 0, no output — file is syntactically valid.

---

## Edge Cases

### APDU all-retries fail (phone not authorized or HCE not responding)

1. Tap a phone that has NOT authorized a payment in the HCE app (or tap a non-HCE phone).
2. **Expected (Serial Monitor):** Three lines of `APDU attempt N/3 ok=NO rspLen=60` (N = 1, 2, 3), then `APDU: all retries failed`.
3. **Expected:** Arduino falls back to CARD delivery path with the phone's hardware UID.
4. **Expected (Flask log):** `complete_sale CALLED` (not `complete_sale_nfc CALLED`) — fallback to physical card path.
5. **Expected (cashier UI):** "Card not found" error modal (phone UID is not in Money Accounts). This is expected and correct behavior — not a bug.

### Token lookup miss (MoneyCardNumber mismatch)

1. If `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` appears in Flask log but the cashier UI shows "Card not found":
2. Check `[NFC DEBUG] raw_money_card=<value>` in Flask log — this is the exact token value being looked up.
3. Open the Money Accounts sheet and search for that value in the `MoneyCardNumber` column.
4. **Expected:** The value matches exactly (after whitespace strip) if the account is registered correctly.
5. **If mismatch:** The VirtualCards or Money Accounts sheet has an inconsistent entry — correct the Sheets row. No code change needed.

### Insufficient balance

1. Tap phone for a purchase that exceeds the student's current balance.
2. **Expected (cashier UI):** Error modal showing "Insufficient balance" (same behavior as physical card).
3. **Expected (Sheets):** No new Transactions Log row written.

---

## Failure Signals

- `bash scripts/verify-m004.sh` shows any `FAIL` — backend structural regression; fix before hardware test
- Serial Monitor shows `APDU attempt N/3 ok=NO` on all 3 attempts — phone HCE not responding; check phone HCE app authorization
- Flask log shows `complete_sale CALLED` after phone tap (not `complete_sale_nfc CALLED`) — APDU failed and Arduino fell back to CARD path; check Serial Monitor for `ok=NO` pattern
- Flask log shows `complete_sale_nfc CALLED` but cashier UI shows "Card not found" — token lookup miss; check `raw_money_card` value against Money Accounts sheet
- `[NFC DEBUG] money_accounts count=0` in Flask log — Sheets read failed or Money Accounts sheet is empty; check Sheets credentials and connectivity
- Cashier UI shows no response after tap — socket event not firing; check SocketIO connection and `arduino_bridge.py` serial reader or WiFi POST

## Requirements Proved By This UAT

- R025 (APDU Retry) — `APDU attempt N/3 ok=YES` in Serial Monitor proves the retry loop fires and succeeds on real phone hardware; advances R025 from "contract verified" to "validated"
- R021 (Phone NFC Payment at Cashier) — `complete_sale_nfc CALLED` in Flask log + success modal in cashier UI proves the full NFC payment path works end-to-end; advances R021 from "contract verified" to "validated"

## Not Proven By This UAT

- R020 (Correct WiFi routing for physical card) — requires standalone powerbank Arduino (no USB); still pending hardware UAT from M003
- R022 (Arduino WiFi status badge) — requires live heartbeat from running Arduino; still pending hardware UAT from M003
- R023 (Arduino stable on powerbank) — requires 30-min powerbank soak test; still pending hardware UAT from M003
- Multi-phone compatibility — APDU retry budget (3 × 150ms) tested on available phones only; very slow HCE implementations on other phone models unverified

## Notes for Tester

- The cashier UI must have an active checkout (after clicking "Checkout" on a product) before tapping the phone — `pending_transaction` must be in the Flask session or `complete_sale_nfc()` will return an error. Do not tap the phone from the idle cashier home screen.
- "NFC Payment received!" and the standard card success message are visually distinct — confirm the NFC modal text specifically.
- If the phone tap triggers the fallback path (CARD delivery, `complete_sale CALLED`), the APDU retry loop fired but all 3 attempts failed — this is a phone/HCE issue, not a code bug. Check that the HCE app is running and the student is authorized in the app before retrying.
- The Transactions Log row type should be "NFC Purchase" for phone taps and "Purchase" for physical card taps — verify these are distinct to confirm the correct code path ran.
