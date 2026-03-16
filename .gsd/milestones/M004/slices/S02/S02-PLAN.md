# S02: End-to-End Validation + Backend Cleanup

**Goal:** Fix the `complete_sale_nfc()` Money Accounts lookup to use direct string comparison (D038 alignment), extend `verify-m004.sh` to assert the alignment, then validate the full end-to-end NFC phone payment path on real hardware.
**Demo:** Student taps Android phone at payment terminal → `APDU attempt N/3 ok=YES` in Serial Monitor → `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` in server log → cashier UI shows "NFC Payment received! New Balance: ₱X.XX" → Sheets Transactions Log has a new "NFC Purchase" row.

## Must-Haves

- `complete_sale_nfc()` Money Accounts loop uses `str(...).strip() == money_card_number` (direct comparison, not `normalize_card_uid`)
- `normalized_money_card` intermediate variable and its two debug prints absent from `cashier_routes.py`
- `normalize_card_uid` import **not** removed (still used by `complete_sale()`)
- `verify-m004.sh` extended with checks (f) and (g); `bash scripts/verify-m004.sh` exits 0 with 7/7 passing
- Phone tap → `complete_sale_nfc CALLED` in server log (not `complete_sale CALLED`)
- Physical RFID card tap → `complete_sale CALLED` → cashier success (no regression)

## Proof Level

- This slice proves: operational (end-to-end on real hardware)
- Real runtime required: yes (T02)
- Human/UAT required: yes (T02)

## Verification

- `bash scripts/verify-m004.sh` exits 0 — 7/7 pass (T01 gate)
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0 (included in script)
- `grep -c "normalized_money_card" backend/dashboard/cashier/cashier_routes.py` outputs `0` (D038 gone)
- Serial Monitor shows `APDU attempt N/3 ok=YES` on phone tap (T02 gate)
- Server log shows `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` (not `complete_sale CALLED`) on phone tap
- Cashier UI shows "NFC Payment received! New Balance: ₱X.XX" success modal
- Physical card tap shows `complete_sale CALLED` → success (regression check)

## Observability / Diagnostics

- Runtime signals: `[NFC DEBUG] raw_money_card=...` and `[NFC DEBUG] money_accounts count=...` prints in `complete_sale_nfc()` — primary diagnostic if Money Accounts lookup misses
- Inspection surfaces: Serial Monitor at 9600 baud (APDU attempt lines); Flask server log (complete_sale_nfc CALLED); cashier UI success/error modal
- Failure visibility: if lookup misses → 404 "Card not found" in cashier modal + `raw_money_card` print reveals the token value; check VirtualCards and Money Accounts rows in Sheets for alignment
- Redaction constraints: none — token values in debug prints are ephemeral NFC session tokens, not credentials

## Integration Closure

- Upstream surfaces consumed: `bankongseton_rfid.ino` delivers `NFC|<token>` → `/api/nfc/tap` → `nfc_payment` socket → `completeNFCSale()` JS → `/cashier/api/complete-sale-nfc` → `complete_sale_nfc(token)` (S01 firmware wired; cashier JS wired in M003)
- New wiring introduced: none — T01 is a lookup correction inside an already-wired function
- What remains before milestone is truly usable end-to-end: nothing after T02 passes

## Tasks

- [x] **T01: Align Money Accounts lookup to D032/D038 + extend verify script** `est:20m`
  - Why: `complete_sale_nfc()` uses `normalize_card_uid()` for the Money Accounts comparison, deviating from D032 which mandates direct string comparison; this will cause mismatches for every student whose VirtualCards `MoneyCardNumber` doesn't round-trip through normalization
  - Files: `backend/dashboard/cashier/cashier_routes.py`, `scripts/verify-m004.sh`
  - Do:
    1. In `cashier_routes.py` inside `complete_sale_nfc()`, replace the block starting at `normalized_money_card = normalize_card_uid(...)` through the two per-record debug prints with: `print(f"[NFC DEBUG] raw_money_card={money_card_number!r}", flush=True)` (single line, no normalized variable)
    2. In the Money Accounts `for` loop condition, change `normalize_card_uid(str(record.get('MoneyCardNumber', ''))) == normalized_money_card` to `str(record.get('MoneyCardNumber', '')).strip() == money_card_number`
    3. Do NOT remove the `normalize_card_uid` import — `complete_sale()` still uses it
    4. In `scripts/verify-m004.sh`, append checks (f) and (g) after check(e) and before the results echo:
       - `check "(f) direct string comparison in complete_sale_nfc Money Accounts loop" "\.strip() == money_card_number" "backend/dashboard/cashier/cashier_routes.py"`
       - `check_absent "(g) normalized_money_card variable absent (normalize removed from NFC lookup)" "normalized_money_card" "backend/dashboard/cashier/cashier_routes.py"`
    5. Update the banner echo at top of results block to: `=== M004 verify: APDU retry firmware + py_compile + D038 alignment ===`
  - Verify: `bash scripts/verify-m004.sh` — must show 7 passed, 0 failed; `grep -c "normalized_money_card" backend/dashboard/cashier/cashier_routes.py` must output `0`
  - Done when: `bash scripts/verify-m004.sh` exits 0 with 7/7 pass output visible

- [x] **T02: Hardware UAT — phone tap + physical card regression** `est:30m`
  - Why: Proves R021 (phone NFC payment) and R025 (APDU retry) on real hardware for the first time; T01 is contract-level only; this is the operational proof that advances both requirements to validated
  - Files: `arduino/bankongseton_rfid/bankongseton_rfid.ino` (flash only — no edits)
  - Do:
    1. Flash `bankongseton_rfid.ino` to Arduino UNO R4 WiFi (S01 firmware — no changes since S01)
    2. Open Serial Monitor at 9600 baud
    3. On cashier UI: log in, load products, select a product, click Checkout to initiate `process-sale` (sets `pending_transaction` session key — required before NFC tap)
    4. Tap Android phone at Arduino — observe Serial Monitor for `APDU attempt N/3 ok=YES`
    5. Observe Flask server log for `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<`
    6. Observe cashier UI for "NFC Payment received! New Balance: ₱X.XX" success modal
    7. Verify new "NFC Purchase" row in Sheets Transactions Log
    8. Regression check: tap a physical RFID card → Serial Monitor shows `CARD|<uid>` delivery → server log shows `complete_sale CALLED` → cashier UI shows success modal
  - Verify: All 4 diagnostic surfaces confirmed (Serial Monitor APDU ok=YES, server log complete_sale_nfc CALLED, cashier UI success modal, Sheets row); physical card tap does not regress
  - Done when: Both phone tap and physical card tap produce success in cashier UI; `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` confirmed in server log on phone tap

## Files Likely Touched

- `backend/dashboard/cashier/cashier_routes.py`
- `scripts/verify-m004.sh`
