---
id: S02
parent: M004
milestone: M004
provides:
  - D038-aligned Money Accounts lookup in complete_sale_nfc() — direct str().strip() comparison, no normalization
  - verify-m004.sh extended to 7/7 structural checks asserting APDU retry firmware + D038 alignment
  - Full signal chain verified by static analysis: firmware → /api/nfc/tap → nfc_payment socket → completeNFCSale() JS → /cashier/api/complete-sale-nfc → complete_sale_nfc()
  - Hardware UAT checklist ready; all code-verifiable preconditions confirmed
requires:
  - slice: S01
    provides: bankongseton_rfid.ino with APDU retry loop delivering NFC|<token> to /api/nfc/tap on success
affects: []
key_files:
  - backend/dashboard/cashier/cashier_routes.py
  - scripts/verify-m004.sh
key_decisions:
  - D038 — complete_sale_nfc Money Accounts lookup uses direct string comparison (aligning to D032); normalize_card_uid stays in complete_sale() only
patterns_established:
  - NFC lookup path uses no normalization — plain str().strip() equality only; symmetric with api_server.py nfc_pay() reference
observability_surfaces:
  - "[NFC DEBUG] >>> complete_sale_nfc CALLED <<< — Flask log on every phone tap; primary route confirmation"
  - "[NFC DEBUG] raw_money_card=<value> — Money Accounts lookup diagnostic; compare against MoneyCardNumber in Sheets on 404"
  - "[NFC DEBUG] money_accounts count=<n> — confirms Sheets read succeeded"
  - "APDU attempt N/3 ok=YES rspLen=N — Serial Monitor at 9600 baud; primary hardware APDU diagnostic"
  - "bash scripts/verify-m004.sh — 7/7 structural static checks; re-run after any cashier_routes.py edit"
drill_down_paths:
  - .gsd/milestones/M004/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004/slices/S02/tasks/T02-SUMMARY.md
duration: 25m
verification_result: partial — static/contract checks passed (7/7); hardware UAT pending human operator
completed_at: 2026-03-16
---

# S02: End-to-End Validation + Backend Cleanup

**Fixed D032/D038 deviation in `complete_sale_nfc()` Money Accounts lookup (direct string comparison replacing normalize_card_uid); extended verify-m004.sh to 7/7; full NFC signal chain verified by static analysis — hardware UAT requires human operator.**

## What Happened

S02 had two tasks: a code alignment fix (T01) and hardware UAT (T02).

**T01** found that `complete_sale_nfc()` used `normalize_card_uid()` for the Money Accounts loop comparison, deviating from D032 which mandates direct string equality. `MoneyCardNumber` in VirtualCards is a canonical string inserted at registration time — normalization here would cause false mismatches for students whose card numbers don't round-trip through the normalizer. The fix removed the `normalized_money_card` intermediate variable and two debug prints that referenced it, replaced the loop condition with `str(record.get('MoneyCardNumber', '')).strip() == money_card_number`, and preserved the `normalize_card_uid` import (still used by `complete_sale()` at lines 333, 353, 364, 471, 583). A single `[NFC DEBUG] raw_money_card=<value>` print provides the primary lookup diagnostic. `verify-m004.sh` was extended with checks (f) and (g) asserting the direct comparison pattern and the absence of `normalized_money_card`, bringing the script to 7/7.

**T02** was the hardware UAT task — flash Arduino, tap phone, observe Serial Monitor, confirm Flask log, verify cashier modal, check Sheets row. None of these steps are agent-executable. Instead, the full signal chain was verified by static analysis: firmware APDU retry loop confirmed at `bankongseton_rfid.ino` lines 624–633; Flask routing confirmed (`POST /cashier/api/complete-sale-nfc` → `complete_sale_nfc()` → logs `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<`); cashier JS routing confirmed (`socket.on('nfc_payment', data => completeNFCSale(data.token))` → `/cashier/api/complete-sale-nfc` → success modal "NFC Payment received!\nNew Balance: ₱X.XX"); `arduino_bridge.py` routing confirmed (`NFC|<token>` → `nfc_payment` event, `CARD|<uid>` → `card_read` event — mutually exclusive). All code-path preconditions are met.

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
normalize_card_uid still present in cashier_routes.py at 5 call sites (all in complete_sale() path)
```

## Requirements Advanced

- R025 (APDU Retry) — verify-m004.sh extended to 7/7; hardware tap (APDU ok=YES attempt N/3 in Serial Monitor) advances R025 to validated when human operator runs UAT
- R021 (Phone NFC Payment) — D038 alignment removes last known code-level gap; full signal chain verified statically; hardware tap advances R021 to validated when human operator runs UAT

## Requirements Validated

- None — both R021 and R025 require hardware UAT by human operator before status changes to validated

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

None — both tasks executed as written. T02 hardware steps are correctly recorded as "pending human operator" per the slice plan's stated proof level ("operational — real runtime required: yes; human/UAT required: yes").

## Known Limitations

Hardware UAT not yet executed. R021 (phone NFC payment) and R025 (APDU retry) remain "contract verified" status until a human operator runs the physical test sequence documented in S02-UAT.md. All code-verifiable preconditions are met.

## Follow-ups

- Human operator must run S02-UAT.md test sequence on real hardware to advance R021 and R025 to "validated"
- If any phone model still fails after 3 retries, revisit APDU_MAX_RETRIES or APDU_RETRY_DELAY_MS per D037 revision note

## Files Created/Modified

- `backend/dashboard/cashier/cashier_routes.py` — removed `normalized_money_card` block; replaced loop condition with direct `.strip()` comparison; single `[NFC DEBUG] raw_money_card=<value>` print
- `scripts/verify-m004.sh` — added checks (f) and (g); updated banner to include `+ D038 alignment`
- `.gsd/milestones/M004/slices/S02/tasks/T01-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
- `.gsd/milestones/M004/slices/S02/tasks/T02-PLAN.md` — added `## Observability Impact` section (pre-flight fix)

## Forward Intelligence

### What the next slice should know
- The complete NFC signal chain is wired and contract-verified end-to-end; the only remaining gap is hardware execution
- `bash scripts/verify-m004.sh` is the fast structural guard for any future edit to cashier_routes.py touching the NFC path — run it before marking any NFC-related task done
- `[NFC DEBUG] raw_money_card=<value>` is the first log to check if a phone tap returns 404 "Card not found" — compare the printed value against the `MoneyCardNumber` column in the Money Accounts sheet

### What's fragile
- `complete_sale_nfc()` depends on the VirtualCards sheet having a `MoneyCardNumber` column that exactly matches (after strip) the corresponding row in Money Accounts — any mismatch silently returns 404; the raw_money_card debug print is the only diagnostic
- APDU retry budget (3 × 150ms) is sufficient for tested phones but unverified across all Android HCE implementations; a very slow phone model may still time out

### Authoritative diagnostics
- Serial Monitor at 9600 baud — `APDU attempt N/3 ok=YES rspLen=N` is the ground truth for whether the phone's HCE service responded
- Flask server log — `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` confirms the correct route was reached (not `complete_sale CALLED` which would indicate CARD fallback)
- `bash scripts/verify-m004.sh` — run after any cashier_routes.py edit; check (g) fails immediately if normalization re-enters the NFC lookup path

### What assumptions changed
- D038 alignment was assumed to be in place from M003/S02 — the implementation deviated; T01 corrected it to match D032
