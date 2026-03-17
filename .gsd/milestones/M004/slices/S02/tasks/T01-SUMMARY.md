---
id: T01
parent: S02
milestone: M004
provides:
  - D038-aligned Money Accounts lookup in complete_sale_nfc()
  - verify-m004.sh extended to 7 checks asserting D038 alignment structurally
key_files:
  - backend/dashboard/cashier/cashier_routes.py
  - scripts/verify-m004.sh
key_decisions:
  - Direct str().strip() comparison matches api_server.py reference pattern (D032/D038); normalize_card_uid stays for complete_sale() only
patterns_established:
  - NFC lookup path uses no normalization — plain stripped string equality only
observability_surfaces:
  - "[NFC DEBUG] raw_money_card=<value> — emitted on every complete_sale_nfc() call; primary diagnostic for lookup misses"
  - "[NFC DEBUG] money_accounts count=<n> — confirms sheet was reached"
  - "bash scripts/verify-m004.sh — check (g) fails immediately if normalized_money_card re-introduced"
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Align Money Accounts lookup to D032/D038 + extend verify script

**Replaced `normalize_card_uid()` call in `complete_sale_nfc()` Money Accounts loop with direct `str().strip() == money_card_number` comparison; extended `verify-m004.sh` to 7/7 structural checks.**

## What Happened

`complete_sale_nfc()` had an intermediate `normalized_money_card = normalize_card_uid(money_card_number)` variable that was then used in the Money Accounts `for` loop condition. This deviated from D032/D038 (direct string comparison for canonical card numbers stored in Sheets) and from the reference pattern in `api_server.py:790`.

Changes made:
1. Removed the `normalized_money_card` assignment and the two debug prints that referenced normalization (the `normalized=` suffix on the raw_money_card print, and the 10-item per-card debug loop using `normalize_card_uid(raw)`).
2. Replaced with a single `print(f"[NFC DEBUG] raw_money_card={money_card_number!r}", flush=True)`.
3. Changed loop condition from `normalize_card_uid(str(record.get('MoneyCardNumber', ''))) == normalized_money_card` to `str(record.get('MoneyCardNumber', '')).strip() == money_card_number`.
4. Confirmed `normalize_card_uid` import untouched — still used by `complete_sale()` (lines 333, 353, 364, 471, 583).
5. Appended checks (f) and (g) to `verify-m004.sh`; updated banner to include `+ D038 alignment`.

## Verification

```
bash scripts/verify-m004.sh
  PASS  (a) APDU_MAX_RETRIES constant defined
  PASS  (b) <= APDU_MAX_RETRIES wired in loop condition
  PASS  (c) APDU_RETRY_DELAY_MS constant defined
  PASS  (d) "APDU attempt " per-attempt diagnostic present
  PASS  (e) py_compile backend/dashboard/cashier/cashier_routes.py
  PASS  (f) direct string comparison in complete_sale_nfc Money Accounts loop
  PASS  (g) normalized_money_card variable absent (normalize removed from NFC lookup)
=== Results: 7 passed, 0 failed ===

grep -c "normalized_money_card" backend/dashboard/cashier/cashier_routes.py → 0
grep "normalize_card_uid" backend/dashboard/cashier/cashier_routes.py → 5 matches, all in complete_sale() path (lines 333, 353, 364, 471, 583), none in complete_sale_nfc()
```

## Diagnostics

- `[NFC DEBUG] raw_money_card=<value>` — single line per NFC attempt; compare against `MoneyCardNumber` column in Money Accounts sheet if lookup returns 404.
- `[NFC DEBUG] money_accounts count=<n>` — still present; confirms sheet read succeeded.
- `bash scripts/verify-m004.sh` — check (g) is a structural guard; re-run after any future edit to cashier_routes.py that touches the NFC path.

## Deviations

None — plan executed as written.

## Known Issues

None.

## Files Created/Modified

- `backend/dashboard/cashier/cashier_routes.py` — removed `normalized_money_card` block and two normalization-referencing debug prints; replaced loop condition with direct `.strip()` comparison
- `scripts/verify-m004.sh` — added checks (f) and (g); updated banner
- `.gsd/milestones/M004/slices/S02/tasks/T01-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
