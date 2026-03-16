---
estimated_steps: 5
estimated_files: 2
---

# T01: Align Money Accounts lookup to D032/D038 + extend verify script

**Slice:** S02 — End-to-End Validation + Backend Cleanup
**Milestone:** M004

## Description

`complete_sale_nfc()` in `cashier_routes.py` currently calls `normalize_card_uid()` when comparing the `MoneyCardNumber` from the Money Accounts sheet against the value retrieved from VirtualCards. This deviates from D032 (which mandates direct string comparison for canonical card numbers stored in Sheets) and from the reference implementation in `api_server.py:790`. Replace the normalize-based comparison with a direct `str(...).strip() == money_card_number` comparison, remove the intermediate `normalized_money_card` variable and its two associated debug prints, then wire two new checks into `verify-m004.sh` to assert the alignment structurally.

## Steps

1. Open `backend/dashboard/cashier/cashier_routes.py`. Inside `complete_sale_nfc()`, locate the block that sets `normalized_money_card` (line ~614). Remove this block and the two debug prints that reference `normalized_money_card`. Replace with a single print: `print(f"[NFC DEBUG] raw_money_card={money_card_number!r}", flush=True)`.
2. Locate the Money Accounts `for` loop condition that calls `normalize_card_uid(str(record.get('MoneyCardNumber', ''))) == normalized_money_card`. Replace with: `str(record.get('MoneyCardNumber', '')).strip() == money_card_number`.
3. Confirm `normalize_card_uid` import is still present in the file (used by `complete_sale()` — do not remove it).
4. In `scripts/verify-m004.sh`, append two new checks after check(e) and before the results echo block:
   ```bash
   # (f) direct string comparison used for Money Accounts lookup (D032/D038)
   check \
     "(f) direct string comparison in complete_sale_nfc Money Accounts loop" \
     "\.strip() == money_card_number" \
     "backend/dashboard/cashier/cashier_routes.py"

   # (g) normalized_money_card intermediate variable absent — normalize_card_uid removed from NFC lookup
   check_absent \
     "(g) normalized_money_card variable absent (normalize removed from NFC lookup)" \
     "normalized_money_card" \
     "backend/dashboard/cashier/cashier_routes.py"
   ```
5. Update the banner echo from `=== M004 verify: APDU retry firmware + py_compile ===` to `=== M004 verify: APDU retry firmware + py_compile + D038 alignment ===`. Run `bash scripts/verify-m004.sh` and confirm 7/7 pass.

## Must-Haves

- [ ] `normalized_money_card` variable absent from `cashier_routes.py` — `grep -c "normalized_money_card" backend/dashboard/cashier/cashier_routes.py` outputs `0`
- [ ] Money Accounts loop uses `str(record.get('MoneyCardNumber', '')).strip() == money_card_number`
- [ ] `normalize_card_uid` import still present in file (not removed)
- [ ] `[NFC DEBUG] raw_money_card=...` debug print still present (single line, no normalized variable)
- [ ] `verify-m004.sh` outputs 7 passed, 0 failed

## Verification

- `bash scripts/verify-m004.sh` — exits 0, output shows `7 passed, 0 failed` with all 7 PASS lines visible
- `grep -c "normalized_money_card" backend/dashboard/cashier/cashier_routes.py` → `0`
- `grep "normalize_card_uid" backend/dashboard/cashier/cashier_routes.py` → import line still present (confirm at least 1 match, but not inside `complete_sale_nfc`'s loop)

## Inputs

- `backend/dashboard/cashier/cashier_routes.py:614–630` — the D038-deviating block to replace (confirmed in research)
- `scripts/verify-m004.sh` — existing 5-check script; append (f) and (g) inline after check(e)
- `backend/api/api_server.py:790` — reference pattern: `str(r.get("MoneyCardNumber", "")).strip() == money_card_number` (copy verbatim)

## Observability Impact

**Signals changed:**
- `[NFC DEBUG] raw_money_card=...` — still emitted; now a single line (no `normalized=` suffix). Primary diagnostic when a Money Accounts lookup misses: confirms the token value being compared.
- `[NFC DEBUG] money_accounts count=...` — unchanged; confirms the sheet was reached and how many rows were loaded.
- Removed: `[NFC DEBUG] sheet card raw=... normalized=...` loop (was 0–10 lines per request); now absent from logs.

**How a future agent inspects this:**
- `grep "\[NFC DEBUG\] raw_money_card" <server-log>` — finds the lookup value on every NFC payment attempt.
- If lookup misses (404 "Card not found" in cashier modal), compare `raw_money_card=` value against `MoneyCardNumber` column in the Money Accounts sheet — they must match as plain stripped strings.
- `bash scripts/verify-m004.sh` — checks (f) and (g) structurally assert D038 alignment; re-run after any merge that touches the NFC path.

**Failure visibility:**
- Lookup miss → `raw_money_card=` print reveals the token; check VirtualCards row's `MoneyCardNumber` matches the Money Accounts sheet entry exactly (whitespace stripped).
- Accidental re-introduction of `normalize_card_uid` in the NFC loop → check (g) fails immediately.


- `backend/dashboard/cashier/cashier_routes.py` — Money Accounts loop uses direct string comparison; `normalized_money_card` variable and associated prints removed; `normalize_card_uid` import untouched
- `scripts/verify-m004.sh` — 7 checks, exits 0; checks (f) and (g) assert D038 alignment structurally
