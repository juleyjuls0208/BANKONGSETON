# S02: End-to-End Validation + Backend Cleanup — Research

**Date:** 2026-03-16

## Summary

S02 has two deliverables: (1) a surgical code fix in `complete_sale_nfc()` to align its Money Accounts lookup with D032/D038 — four lines change, nothing else moves, and (2) two new structural checks added to `verify-m004.sh` to assert the alignment. The end-to-end hardware validation is a UAT gate, not a code task — it proves R021 and R025 on real hardware after the firmware from S01 is flashed.

The code change is low-risk and confined entirely to `cashier_routes.py` lines 614–630. The rest of `complete_sale_nfc()` — VirtualCards lookup, balance deduction with retry/rollback, offline queue, email/SMS/FCM paths — is already correct and unchanged. The `normalize_card_uid` import stays (used by `complete_sale()`); only its usage in the Money Accounts comparison loop is removed.

The hardware path from Arduino → `/api/nfc/tap` → `nfc_payment` socket → `completeNFCSale()` JS → `/cashier/api/complete-sale-nfc` is fully wired and working at the contract level. No changes to `web_app.py`, `dashboard_core.py`, or `cashier_index.html` are needed.

## Recommendation

Two tasks:
- **T01**: Apply D038 fix to `cashier_routes.py` + add two checks to `verify-m004.sh` + run `bash scripts/verify-m004.sh` (now 7 checks).
- **T02**: Hardware validation — flash S01 firmware, tap Android phone, confirm Serial Monitor + server log + cashier UI, then physical card regression tap.

T01 is pure contract work (automated verification). T02 is the UAT that advances R021 and R025 to validated.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Direct MoneyCardNumber comparison | `api_server.py nfc_pay()` line 790: `str(r.get("MoneyCardNumber", "")).strip() == money_card_number` | Exact pattern D032 mandates; copy verbatim |
| Structural contract script | `scripts/verify-m004.sh` (existing, 5 checks) | Same check()/check_absent() scaffold; add (f) and (g) inline |

## Existing Code and Patterns

- `backend/dashboard/cashier/cashier_routes.py:563` — `complete_sale_nfc()`: the function to fix. Lines 614–630 contain the D038 deviation. Lines 742 (Users sheet lookup) and all post-deduction paths are already using direct string comparison correctly — only the Money Accounts loop deviates.
- `backend/api/api_server.py:790` — `nfc_pay()` reference: `str(r.get("MoneyCardNumber", "")).strip() == money_card_number` is the authoritative D032 pattern to replicate exactly.
- `backend/dashboard/cashier/templates/cashier_index.html:417` — `completeNFCSale(token)`: JS already calls `/cashier/api/complete-sale-nfc` and shows "NFC Payment received!\nNew Balance: ₱X.XX" on success. No changes needed.
- `backend/dashboard/dashboard_core.py:2026` — `/api/nfc/tap` endpoint: receives Arduino WiFi POST, emits `nfc_payment` socket event. Unchanged.
- `scripts/verify-m004.sh` — 5 checks currently passing; extend with 2 more (see Constraints below).

## What Changes (T01 — surgical)

**`backend/dashboard/cashier/cashier_routes.py`** — inside `complete_sale_nfc()`, replace this block (lines 614–630):

```python
# BEFORE (D038 deviation — uses normalize_card_uid):
normalized_money_card = normalize_card_uid(money_card_number)
print(f"[NFC DEBUG] raw_money_card={money_card_number!r} normalized={normalized_money_card!r}", flush=True)

# Find money account
money_sheet = db.worksheet('Money Accounts')
money_records = money_sheet.get_all_records()

print(f"[NFC DEBUG] money_accounts count={len(money_records)}", flush=True)
for r in money_records[:10]:
    raw = str(r.get('MoneyCardNumber', ''))
    print(f"[NFC DEBUG]   sheet card raw={raw!r} normalized={normalize_card_uid(raw)!r}", flush=True)

# ... in the loop:
if normalize_card_uid(str(record.get('MoneyCardNumber', ''))) == normalized_money_card:
```

With:
```python
# AFTER (D032/D038 aligned — direct string comparison):
print(f"[NFC DEBUG] raw_money_card={money_card_number!r}", flush=True)

# Find money account
money_sheet = db.worksheet('Money Accounts')
money_records = money_sheet.get_all_records()

print(f"[NFC DEBUG] money_accounts count={len(money_records)}", flush=True)

# ... in the loop:
if str(record.get('MoneyCardNumber', '')).strip() == money_card_number:
```

**`scripts/verify-m004.sh`** — append two checks after check(e):

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

Update the echo at the bottom: `=== M004 verify: APDU retry firmware + py_compile + D038 alignment ===` and `=== Results: $PASS passed, $FAIL failed ===` (no count change needed, it's dynamic).

## Constraints

- `normalize_card_uid` import line in `cashier_routes.py` must **not** be removed — it is still used by `complete_sale()` for physical RFID card lookup (where byte-order normalization is correct for raw hardware UIDs).
- The `[NFC DEBUG]` prints inside `complete_sale_nfc()` should be **kept** through S02 hardware validation — they are the primary diagnostic surface if the end-to-end tap fails. Cleanup is a follow-up after R021 advances to validated.
- `pending_transaction` session key must be set before the NFC tap arrives: cashier must click "Checkout" → POST `/cashier/api/process-sale` before the tap. If the tap arrives first, `complete_sale_nfc` returns 400 and the modal shows the error. This is existing behavior; not in scope to change.
- D032 assumes VirtualCards `MoneyCardNumber` values are canonical (match Money Accounts exactly after `.strip()`). Normalization would be wrong here (confirmed by D032 rationale: normalization is only correct for raw hardware UIDs that may have byte-order variants).

## Common Pitfalls

- **Removing normalize_card_uid import** — Don't. `complete_sale()` (physical card path) still uses it. Only remove the usage inside `complete_sale_nfc`'s Money Accounts loop.
- **Moving the 150ms pre-delay inside the APDU retry loop** — Don't touch the firmware (S01 note: pre-delay is a one-time RF settle outside the loop, intentional). S02 firmware is flash-only; no `.ino` edits.
- **Forgetting `responseLength` reset** — Not relevant for S02; S01 already handled this in the firmware.
- **grep(f) pattern ambiguity** — `\.strip() == money_card_number` as a grep pattern will match both the loop line and the Users sheet lookup line 742. That's fine — both should be direct comparisons. The check_absent on `normalized_money_card` is the clean "D038 deviation is gone" signal.

## Open Risks

- **Data alignment in real Sheets**: D032 assumes VirtualCards `MoneyCardNumber` exactly matches Money Accounts `MoneyCardNumber` after `.strip()`. If a student was registered with a normalized form in VirtualCards but the canonical form in Money Accounts (or vice versa), the direct comparison will miss and return 404 "Card not found." The `[NFC DEBUG]` prints (`raw_money_card=...` and `money_accounts count=...`) will surface this immediately during hardware validation. Mitigation: check both sheets in Sheets UI before the first live test.
- **pending_transaction timing**: If the NFC tap event arrives at the cashier socket before the cashier initiates checkout (process-sale not yet called), `complete_sale_nfc` returns 400. The modal opens and shows the error. The fix is operational (cashier must initiate checkout first), not a code bug.
- **R025 hardware proof still pending**: S01 firmware is flashed in T02. If a phone consistently hits `APDU attempt 3/3 ok=NO` (all retries exhaust), the 450ms budget may not be enough for that device. Watching for this in Serial Monitor during T02 validation.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Python / Flask | none needed | n/a — standard Flask; no unfamiliar library |
| Google Sheets (gspread) | none needed | n/a — existing patterns in codebase |

## Sources

- `backend/api/api_server.py:790` — reference implementation of D032 direct comparison pattern (confirmed in codebase)
- `backend/dashboard/cashier/cashier_routes.py:563–827` — full `complete_sale_nfc()` body (read directly)
- `backend/dashboard/cashier/templates/cashier_index.html:417` — `completeNFCSale()` JS (confirmed wired correctly, no changes needed)
- `backend/dashboard/dashboard_core.py:2026` — `/api/nfc/tap` Arduino endpoint (confirmed emits `nfc_payment`, no changes needed)
- `scripts/verify-m004.sh` — existing 5-check script (read directly; adding 2 checks in T01)
- `.gsd/DECISIONS.md:D032, D038` — canonical decisions driving the lookup alignment
