---
id: S01
parent: M004
milestone: M004
provides:
  - APDU_MAX_RETRIES=3 and APDU_RETRY_DELAY_MS=150 constants at firmware tuning block
  - 3-attempt inDataExchange retry loop with break-on-success and guarded inter-attempt delay
  - Per-attempt Serial diagnostic "APDU attempt N/3 ok=YES/NO rspLen=N"
  - scripts/verify-m004.sh — 5-check structural contract script, exits 0
requires:
  - slice: none
    provides: root slice
affects:
  - S02
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
  - scripts/verify-m004.sh
key_decisions:
  - D037 — APDU inDataExchange wrapped in retry loop (3 attempts, 150ms between, responseLength reset before each)
  - 150ms pre-delay before the loop is kept outside the retry loop — it is a one-time RF-field settle, not a per-attempt delay
  - verify-m004.sh check(b) greps `<= APDU_MAX_RETRIES` (loop condition token) rather than for-loop structure — resilient to variable renames, confirms constant is actually controlling iteration
  - verify-m004.sh check(e) runs py_compile as a live subprocess rather than a grep — catches real syntax errors
patterns_established:
  - for/break-on-success/delay-between-not-before retry loop — mirrors existing deliver() retry loop at lines 364–383
  - verify-m00N.sh follows same check()/check_absent() scaffold as verify-s01.sh — consistent structural-contract tooling across milestones
observability_surfaces:
  - Serial Monitor at 9600 baud — "APDU attempt N/3 ok=YES/NO rspLen=N" on every attempt; visible retry count, outcome, and response length
  - All-retries-exhausted failure path — "APDU: inDataExchange failed — RF error or phone not responding" before CARD fallback
  - bash scripts/verify-m004.sh — 5 structural checks, PASS/FAIL per line, exits 1 on any failure; machine-readable by CI
drill_down_paths:
  - .gsd/milestones/M004/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004/slices/S01/tasks/T02-SUMMARY.md
duration: ~15m
verification_result: passed
completed_at: 2026-03-16
---

# S01: Firmware APDU Retry

**Added a 3-attempt `inDataExchange` retry loop to the Arduino firmware with per-attempt Serial diagnostics and a structural contract script; `bash scripts/verify-m004.sh` exits 0 — 5 passed, 0 failed.**

## What Happened

**T01** replaced the single-shot `nfc.inDataExchange()` call with a `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)` loop. Two `#define` constants were added at the firmware tuning block immediately after `HEARTBEAT_INTERVAL_MS`: `APDU_MAX_RETRIES 3` and `APDU_RETRY_DELAY_MS 150`. Inside the loop: `responseLength` is reset to 60 before each call (library may modify it on failure), `apduOk = nfc.inDataExchange(...)` is called, per-attempt diagnostic is printed, and `if (apduOk) break` short-circuits on success. Inter-attempt delay fires only between attempts (`if (apduAttempt < APDU_MAX_RETRIES) delay(APDU_RETRY_DELAY_MS)`), not before attempt 1, mirroring the existing `deliver()` retry loop pattern. The pre-existing 150ms field-settle delay before the loop was left in place — it is a one-time RF settle, not an APDU retry delay. The old one-shot `"APDU ok=... lastBytes=..."` diagnostic was removed and replaced by the per-attempt output. Everything from `bool nfcTokenOk = false;` onward was left structurally unchanged.

**T02** created `scripts/verify-m004.sh` using the same `check()`/`check_absent()` scaffold as `scripts/verify-s01.sh`. Five checks: (a) `APDU_MAX_RETRIES` defined, (b) `<= APDU_MAX_RETRIES` wired as loop condition, (c) `APDU_RETRY_DELAY_MS` defined, (d) `"APDU attempt "` per-attempt diagnostic present, (e) `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0. All 5 pass.

## Verification

```
bash scripts/verify-m004.sh

=== M004 verify: APDU retry firmware + py_compile ===

  PASS  (a) APDU_MAX_RETRIES constant defined
  PASS  (b) <= APDU_MAX_RETRIES wired in loop condition
  PASS  (c) APDU_RETRY_DELAY_MS constant defined
  PASS  (d) "APDU attempt " per-attempt diagnostic present
  PASS  (e) py_compile backend/dashboard/cashier/cashier_routes.py

=== Results: 5 passed, 0 failed ===
```

Secondary check:
```
grep "APDU: inDataExchange failed" arduino/bankongseton_rfid/bankongseton_rfid.ino
→ Serial.println("APDU: inDataExchange failed — RF error or phone not responding");
```

## Requirements Advanced

- R025 — Structural contract verified: `APDU_MAX_RETRIES=3`, `APDU_RETRY_DELAY_MS=150`, retry loop present, per-attempt diagnostic wired; `verify-m004.sh` exits 0. Hardware tap confirming `APDU ok=YES attempt N/3` in Serial Monitor advances R025 to validated in S02.

## Requirements Validated

- none — R025 proof level is "contract" for S01; runtime proof requires hardware tap in S02

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

None — implementation matched the plan exactly.

## Known Limitations

- Firmware has not been flashed to hardware yet — Serial Monitor confirmation of `APDU attempt N/3 ok=YES` on a real phone tap is an S02 gate
- APDU_RETRY_DELAY_MS=150 and APDU_MAX_RETRIES=3 are unverified against all phone models; budget is 3×150=450ms which is sufficient for tested devices but may not cover extreme HCE implementations

## Follow-ups

- S02: Flash firmware, tap Android phone at Arduino, confirm `APDU attempt N/3 ok=YES` in Serial Monitor + `POST /api/nfc/tap 200` in Flask log + `complete_sale_nfc CALLED` in server log
- S02: Confirm physical RFID card tap regression-free after firmware change

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — added APDU_MAX_RETRIES + APDU_RETRY_DELAY_MS constants; replaced single inDataExchange call with 3-attempt retry loop; per-attempt Serial diagnostic; old one-shot diagnostic removed
- `scripts/verify-m004.sh` — 5-check structural contract script; exits 0; chmod +x

## Forward Intelligence

### What the next slice should know
- The firmware retry loop is in place; S02 starts from flashing the `.ino` to hardware — no code changes needed before the first tap
- The existing 150ms pre-delay (`delay(150)`) before the APDU block is intentional and correct — it settles the RF field after `nfc.startPassiveTargetIDDetection()` returns; do not move it inside the retry loop
- `bool nfcTokenOk` and the SW_NO_TOKEN diagnosis block after the loop are structurally unchanged from M003 — the token resolution and CARD fallback paths are as they were

### What's fragile
- APDU retry budget (450ms total) — if a specific phone model's HCE service takes longer than 450ms to initialize, all 3 attempts will still fail; watch for `APDU attempt 3/3 ok=NO` in Serial Monitor with no `ok=YES`
- `responseLength` reset: library documentation does not guarantee the field is unmodified on failure — the reset inside the loop is defensive; removing it could cause silent payload truncation on attempt 2+

### Authoritative diagnostics
- Serial Monitor at 9600 baud — primary runtime signal; each attempt emits one line; 3 `ok=NO` lines followed by the inDataExchange failed message is the definitive "retry exhausted" signal
- `bash scripts/verify-m004.sh` — authoritative structural contract check without hardware; run from repo root

### What assumptions changed
- Pre-delay placement: original plan implied the delay could move inside the loop; T01 execution confirmed it must remain outside (one-time RF settle, not a per-attempt APDU delay)
