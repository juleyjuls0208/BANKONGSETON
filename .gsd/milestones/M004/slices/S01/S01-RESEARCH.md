# S01: Firmware APDU Retry — Research

**Date:** 2026-03-16

## Summary

S01 is a surgical firmware edit plus a new verify script. The change is confined to ~15 lines in `arduino/bankongseton_rfid/bankongseton_rfid.ino`: add two constants, convert one `inDataExchange` call into a 3-attempt retry loop, and update the Serial diagnostic to print attempt number. No backend changes are needed — `complete_sale_nfc()` already passes `py_compile` and already uses D032-compliant direct string comparison (D038 alignment is already in place).

The `nfcTokenOk` check block is unchanged — it runs on the final values of `apduOk` and `responseLength` from the last (or successful) loop iteration. The CARD fallback path, the RF-reset on APDU failure, and all downstream delivery code are untouched.

`scripts/verify-m004.sh` doesn't exist yet — it must be created from the patterns in `verify-s01.sh` / `verify-m003-s04.sh`.

## Recommendation

Minimal-footprint edit: add constants at the tuning block, convert the single `inDataExchange` call to a loop with per-attempt `responseLength = 60` reset, replace the old one-shot diagnostic with per-attempt output, defer inter-attempt delay to between-attempts only (existing 150ms pre-delay covers attempt 1). Write verify script with 4 structural checks + `py_compile`.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| HTTP retry pattern | `deliver()` already has `MAX_RETRIES` / `RETRY_DELAY_MS` loop | Follow exact same loop shape for APDU retry — same variable names, same `break on success`, same `delay between, not before first` |
| Constant placement | `HEARTBEAT_INTERVAL_MS` constant at tuning block (~line 78) | `APDU_MAX_RETRIES` and `APDU_RETRY_DELAY_MS` go right after it — identical pattern |
| Verify script shape | `verify-s01.sh` (check/check_absent helpers, INO variable, pass/fail counter) | Copy the scaffold, replace checks |

## Existing Code and Patterns

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` line 78 — `static const int HEARTBEAT_INTERVAL_MS = 30000;` is the constant to add after (`#define APDU_MAX_RETRIES 3` / `#define APDU_RETRY_DELAY_MS 150`)
- `arduino/bankongseton_rfid/bankongseton_rfid.ino` lines 608–650 — the entire APDU block to modify: `uint8_t responseLength = 60;` → declare without init; `delay(150);` → keep as-is (pre-delay for attempt 1); single `bool apduOk = nfc.inDataExchange(...)` + one-shot diagnostic → replace with retry loop; `nfcTokenOk` block → unchanged
- `arduino/bankongseton_rfid/bankongseton_rfid.ino` lines 670–695 — APDU failure path (RF reset, SW_NO_TOKEN diagnosis, CARD fallback) — unchanged; still runs when `nfcTokenOk == false` after the loop
- `scripts/verify-s01.sh` — `check()` / `check_absent()` helper functions, `PASS`/`FAIL` counter, exit code pattern — copy verbatim for `verify-m004.sh`
- `backend/dashboard/cashier/cashier_routes.py` line 616 — `str(record.get('MoneyCardNumber', '')).strip() == money_card_number` — **already D032-compliant**; no change needed in S01
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` — exits 0 today; verify-m004.sh should assert this continues to pass

## Constraints

- `inDataExchange` uses `_inListedTag` state set by `readPassiveTargetID` — the ISO14443-4 session must stay open between retries; no re-call to `readPassiveTargetID` inside the loop (session is held until the loop exits or the phone moves out of range)
- `uint8_t response[60]` is a stack buffer declared once before the loop — correct; only `responseLength` (the in/out parameter) needs resetting to `60` before each call
- Pre-delay `delay(150)` fires once before the loop — decision D037 explicitly says delay fires between attempts only (not before attempt 1); the existing 150ms pre-delay covers HCE wakeup for attempt 1
- APDU_MAX_RETRIES and APDU_RETRY_DELAY_MS must be `#define` (not `static const int`) to match the existing constant style in the tuning block
- `verify-m004.sh` must run from repo root — same as all existing verify scripts

## Common Pitfalls

- **Resetting `responseLength` inside the loop** — if omitted, a failed attempt's leftover `responseLength=60` (or 2 for SW_NO_TOKEN) contaminates the token-validity check on the next attempt; reset to `60` before every `inDataExchange` call
- **Placing the inter-attempt delay before attempt 1** — the existing 150ms delay already runs before the loop; adding another 150ms before attempt 1 wastes time on every phone tap, including fast phones that succeed immediately
- **Changing the `nfcTokenOk` logic** — it's correct as-is; it checks the final `response` buffer and `responseLength` after the loop exits, which holds the last attempt's values; no changes needed
- **verify-m004.sh: grepping for `for.*apduAttempt`** — fragile; grep for `APDU_MAX_RETRIES` used inside the loop body (`<= APDU_MAX_RETRIES`) instead — confirms the constant is actually wired into the loop, not just declared

## Open Risks

- PN532 internal state after a failed `inDataExchange` — the existing code does an RF reset only after ALL retries are exhausted (in the APDU-failed else block). Between retries, no RF reset is done. This is intentional: the phone stays ISO14443-4 SELECTED between retries; an RF reset between attempts would require re-running RATS/ATS which is slower than a retry. If a specific phone model still fails at 3×150ms, the constants can be tuned (D037 marked revisable).
- Total APDU budget: 3 × (inDataExchange timeout + 150ms delay) ≈ 3 × ~300ms = ~900ms worst case. Combined with the 1000ms NFC_TIMEOUT_MS scan, the loop() iteration for a failing phone tap is ~1.9s. This is within the 1500ms SCAN_COOLDOWN_MS + loop overhead — no timing conflict.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Arduino / C++ | none applicable | none found — changes are mechanical loop addition, no library research needed |

## Sources

- APDU retry loop structure: `deliver()` in `bankongseton_rfid.ino` lines 394–420 (same shape — `MAX_RETRIES`, `RETRY_DELAY_MS`, break on success, delay between not before first)
- Constant placement: lines 73–78 in same file (tuning block; `HEARTBEAT_INTERVAL_MS` is the immediate predecessor)
- D037 (APDU retry decision) and D038 (D032 alignment already done) in `.gsd/DECISIONS.md`
- `scripts/verify-s01.sh` — scaffold to copy for `verify-m004.sh`
