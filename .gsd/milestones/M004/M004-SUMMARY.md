---
id: M004
provides:
  - APDU_MAX_RETRIES=3 and APDU_RETRY_DELAY_MS=150 constants at firmware tuning block (lines 72-73)
  - 3-attempt inDataExchange retry loop with break-on-success and guarded inter-attempt delay (lines 624-636)
  - Per-attempt Serial diagnostic "APDU attempt N/3 ok=YES/NO rspLen=N" on every attempt
  - D038-aligned complete_sale_nfc() Money Accounts lookup — direct str().strip() comparison, normalized_money_card removed
  - scripts/verify-m004.sh — 7-check structural contract script (extended S01 5→7 in S02), exits 0
  - Full NFC signal chain verified by static analysis: firmware → /api/nfc/tap → nfc_payment socket → completeNFCSale() JS → /cashier/api/complete-sale-nfc → complete_sale_nfc()
  - S02-UAT.md hardware test checklist ready for human operator
key_decisions:
  - D037 — APDU inDataExchange wrapped in retry loop (3 attempts, 150ms between, responseLength reset before each)
  - D038 — complete_sale_nfc Money Accounts lookup uses direct string comparison (aligning to D032); normalize_card_uid stays in complete_sale() only
  - Pre-delay placement — 150ms field-settle delay kept outside retry loop (one-time RF settle, not per-attempt delay)
patterns_established:
  - for/break-on-success/delay-between-not-before retry loop — mirrors existing deliver() retry loop at lines 364-383
  - NFC lookup path uses no normalization — plain str().strip() equality only; symmetric with api_server.py nfc_pay() reference
  - verify-m00N.sh follows same check()/check_absent() scaffold as verify-s01.sh — consistent structural-contract tooling
observability_surfaces:
  - "APDU attempt N/3 ok=YES/NO rspLen=N — Serial Monitor at 9600 baud; primary hardware APDU diagnostic per attempt"
  - "APDU: inDataExchange failed — RF error or phone not responding — all-retries-exhausted path before CARD fallback"
  - "[NFC DEBUG] >>> complete_sale_nfc CALLED <<< — Flask log on every phone tap; primary route confirmation"
  - "[NFC DEBUG] raw_money_card=<value> — Money Accounts lookup diagnostic; compare against MoneyCardNumber in Sheets on 404"
  - "[NFC DEBUG] money_accounts count=<n> — confirms Sheets read succeeded"
  - "bash scripts/verify-m004.sh — 7/7 structural static checks; re-run after any cashier_routes.py or firmware edit"
requirement_outcomes:
  - id: R025
    from_status: active
    to_status: active
    proof: "Contract verified — bash scripts/verify-m004.sh 7/7 pass; APDU_MAX_RETRIES=3 and APDU_RETRY_DELAY_MS=150 at lines 72-73; retry loop at lines 624-636; per-attempt diagnostic at 627-630; py_compile exit 0. Hardware tap confirming APDU ok=YES attempt N/3 in Serial Monitor advances to validated — pending human operator UAT."
  - id: R021
    from_status: active
    to_status: active
    proof: "Contract verified — py_compile exits 0; verify-m004.sh 7/7 pass including D038 alignment checks (f+g); full signal chain statically verified end-to-end (firmware → Flask → SocketIO → JS → /cashier/api/complete-sale-nfc → complete_sale_nfc()); normalized_money_card removed per D032. Hardware tap advancing to validated — pending human operator UAT."
duration: ~40m (S01 ~15m + S02 ~25m)
verification_result: partial — contract/structural checks passed (7/7); hardware UAT pending human operator
completed_at: 2026-03-16
---

# M004: NFC Phone Payment Fix

**Fixed the APDU retry bug in firmware (3-attempt loop, 150ms between, constants at tuning block) and aligned `complete_sale_nfc()` to D032 (direct string comparison, normalization removed); `bash scripts/verify-m004.sh` 7/7 — hardware UAT ready for human operator.**

## What Happened

M004 addressed a 100% phone NFC payment failure caused by two independent root causes: a firmware timing bug and a backend lookup deviation.

**S01** replaced the single-shot `nfc.inDataExchange()` call with a 3-attempt retry loop. The root cause was confirmed from Serial Monitor: `APDU ok=NO rspLen=60` — Android HCE service initialization takes longer than the single 150ms pre-delay after RF field reconnect. The fix adds `APDU_MAX_RETRIES 3` and `APDU_RETRY_DELAY_MS 150` constants at the firmware tuning block (immediately after `HEARTBEAT_INTERVAL_MS`), then wraps `inDataExchange` in a `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)` loop. `responseLength` is reset to 60 before each call (defensive — library may modify it on failure). Per-attempt `"APDU attempt N/3 ok=YES/NO rspLen=N"` diagnostics replace the old one-shot output. The inter-attempt delay fires between attempts only (not before attempt 1 — the existing 150ms field-settle pre-delay is intentional and was left in place). `verify-m004.sh` was created with 5 structural checks; all 5 passed.

**S02** found and fixed a D032 deviation in `complete_sale_nfc()`. The Money Accounts loop comparison used `normalize_card_uid()` rather than direct string equality — deviating from D032 and the reference implementation in `api_server.py nfc_pay()`. The fix removed the `normalized_money_card` intermediate variable and replaced the loop condition with `str(record.get('MoneyCardNumber', '')).strip() == money_card_number`. The `normalize_card_uid` import was preserved (still used by `complete_sale()` at 5 call sites). `verify-m004.sh` was extended with checks (f) and (g) asserting the direct comparison pattern and the absence of `normalized_money_card`, bringing the script to 7/7. The full NFC signal chain was then verified by static analysis: firmware APDU retry loop confirmed at lines 624–633; Flask routing confirmed (`POST /cashier/api/complete-sale-nfc → complete_sale_nfc() → [NFC DEBUG] >>> complete_sale_nfc CALLED <<<`); cashier JS routing confirmed (`socket.on('nfc_payment', data => completeNFCSale(data.token)) → /cashier/api/complete-sale-nfc → "NFC Payment received!\nNew Balance: ₱X.XX"`); `arduino_bridge.py` routing confirmed (`NFC|<token>` → `nfc_payment` event, `CARD|<uid>` → `card_read` event — mutually exclusive). All code-path preconditions are met.

## Cross-Slice Verification

**Success criteria from M004-ROADMAP.md:**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `APDU_MAX_RETRIES=3`, `APDU_RETRY_DELAY_MS=150` constants in firmware | ✅ VERIFIED | Lines 72-73 in bankongseton_rfid.ino; verify-m004.sh check (a)(c) pass |
| Retry loop wraps `inDataExchange`; `APDU attempt N/3 ok=YES/NO` in Serial Monitor | ✅ VERIFIED (structure) | Loop at lines 624-636; diagnostic at 627-630; verify-m004.sh checks (b)(d) pass |
| `APDU ok=YES attempt N/3` in Serial Monitor on real phone tap | ⏳ PENDING | Hardware UAT — requires human operator to flash Arduino and tap phone |
| `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` in server log (not `complete_sale CALLED`) | ⏳ PENDING | Signal chain statically verified; runtime proof requires live phone tap |
| Cashier sees "NFC Payment received! New Balance: ₱X.XX" | ⏳ PENDING | JS handler + backend response path statically confirmed; runtime proof requires live tap |
| Physical RFID card tap → no regression | ⏳ PENDING | CARD fallback path structurally unchanged; regression test requires live hardware |
| `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0 | ✅ VERIFIED | py_compile exits 0; verify-m004.sh check (e) pass |

```
bash scripts/verify-m004.sh
=== M004 verify: APDU retry firmware + py_compile + D038 alignment ===
  PASS  (a) APDU_MAX_RETRIES constant defined
  PASS  (b) <= APDU_MAX_RETRIES wired in loop condition
  PASS  (c) APDU_RETRY_DELAY_MS constant defined
  PASS  (d) "APDU attempt " per-attempt diagnostic present
  PASS  (e) py_compile backend/dashboard/cashier/cashier_routes.py
  PASS  (f) direct string comparison in complete_sale_nfc Money Accounts loop
  PASS  (g) normalized_money_card variable absent (normalize removed from NFC lookup)
=== Results: 7 passed, 0 failed ===
```

**Definition of done items not yet met (hardware UAT gate):**
- `ok=YES` visible in Serial Monitor on real phone tap (requires flashing + human tap)
- `complete_sale_nfc CALLED` in Flask log on real phone tap
- Cashier UI success modal with correct new balance
- Physical RFID card regression-free on real hardware
- R021 and R025 advancing to validated (contingent on UAT above)

UAT checklist: `.gsd/milestones/M004/slices/S02/S02-UAT.md`

## Requirement Changes

- R025: active → active (contract verified) — `verify-m004.sh` 7/7; APDU_MAX_RETRIES=3, retry loop wired; advances to validated after human operator runs S02-UAT.md
- R021: active → active (contract verified) — D038 alignment applied; full signal chain statically confirmed; advances to validated after human operator runs S02-UAT.md

## Forward Intelligence

### What the next milestone should know
- The firmware is ready to flash and all backend code is correct; the only remaining step is the hardware UAT sequence in S02-UAT.md — no code changes needed before the first tap
- After hardware UAT confirms `ok=YES`, update R021 and R025 status in REQUIREMENTS.md from "active" to "validated" and record the proof (date, phone model, Serial Monitor output, Flask log line)
- `bash scripts/verify-m004.sh` is the fast structural guard after any future cashier_routes.py or firmware edit touching the NFC path — run it before marking any NFC-related task done
- The `[NFC DEBUG]` prints in `complete_sale_nfc()` are intentionally kept for first hardware validation; they can be removed (or gated behind DEBUG_NFC env var) once end-to-end is confirmed on real hardware

### What's fragile
- APDU retry budget (3 × 150ms = 450ms total) — unverified on all Android HCE implementations; a very slow phone model may still exhaust all 3 attempts; watch for `APDU attempt 3/3 ok=NO` in Serial Monitor with no `ok=YES`; fix is to increase `APDU_MAX_RETRIES` or `APDU_RETRY_DELAY_MS` per D037 revision note
- `complete_sale_nfc()` depends on the VirtualCards sheet having a `MoneyCardNumber` column that exactly matches (after strip) the corresponding row in Money Accounts; any mismatch silently returns 404; the `raw_money_card` debug print is the only diagnostic — compare against the Sheets value directly on a 404
- `responseLength` reset inside the retry loop — library documentation does not guarantee the field is unmodified on failure; removing the reset could cause silent payload truncation on attempt 2+

### Authoritative diagnostics
- Serial Monitor at 9600 baud — `APDU attempt N/3 ok=YES rspLen=N` is the ground truth for whether the phone's HCE service responded; three consecutive `ok=NO` lines + the `inDataExchange failed` message = retry exhausted
- Flask server log — `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` confirms the correct route was reached (vs `complete_sale CALLED` which means CARD fallback); `[NFC DEBUG] raw_money_card=<value>` is the first log to check on a 404 "Card not found"
- `bash scripts/verify-m004.sh` — run after any cashier_routes.py or firmware edit; check (g) fails immediately if normalization re-enters the NFC lookup path

### What assumptions changed
- Pre-delay placement: original plan suggested the delay could potentially move inside the loop; confirmed it must remain outside (one-time RF field settle after `startPassiveTargetIDDetection`, not an APDU attempt delay)
- D038 alignment: assumed to be in place from M003/S02; the implementation deviated (used normalize_card_uid); S02 corrected it to match D032

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — added APDU_MAX_RETRIES + APDU_RETRY_DELAY_MS constants (lines 72-73); replaced single inDataExchange call with 3-attempt retry loop (lines 624-636); per-attempt Serial diagnostic (627-630); old one-shot diagnostic removed
- `backend/dashboard/cashier/cashier_routes.py` — removed normalized_money_card block; replaced loop condition with direct str().strip() comparison (line 626); single [NFC DEBUG] raw_money_card diagnostic retained
- `scripts/verify-m004.sh` — 7-check structural contract script (5 from S01 + 2 from S02); exits 0; chmod +x
