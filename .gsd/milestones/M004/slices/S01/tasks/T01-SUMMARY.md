---
id: T01
parent: S01
milestone: M004
provides:
  - APDU retry loop (3 attempts) in bankongseton_rfid.ino
  - APDU_MAX_RETRIES and APDU_RETRY_DELAY_MS constants at tuning block
  - Per-attempt "APDU attempt N/3 ok=YES/NO rspLen=N" Serial diagnostic
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
key_decisions:
  - delay(150) HCE init delay kept before the loop (not inside it) — it's a one-time RF-field settle, not per-attempt; retrying sooner than 150ms after field-on would still fail
  - responseLength reset to 60 inside loop before each inDataExchange call — library may modify it on failure; fresh reset prevents stale length from prior attempt
patterns_established:
  - for/break-on-success/delay-between-not-before — mirrors existing deliver() retry loop at lines 364–383
observability_surfaces:
  - Serial Monitor at 9600 baud: "APDU attempt N/3 ok=YES/NO rspLen=N" on every attempt — visible retry count, outcome, and response length
  - All-retries-exhausted failure: "APDU: inDataExchange failed — RF error or phone not responding" logged before CARD fallback
duration: ~10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Add APDU retry loop to firmware

**Replaced single-shot `inDataExchange` call with a 3-attempt retry loop guarded by `APDU_MAX_RETRIES` and `APDU_RETRY_DELAY_MS` constants; per-attempt Serial diagnostic shows attempt number, outcome, and response length.**

## What Happened

- Added `#define APDU_MAX_RETRIES 3` and `#define APDU_RETRY_DELAY_MS 150` at the tuning block immediately after `HEARTBEAT_INTERVAL_MS` (lines 72–73).
- Changed `uint8_t responseLength = 60;` → `uint8_t responseLength;` (init now inside loop).
- Added `bool apduOk = false;` before the loop (in scope for `nfcTokenOk` check after it).
- Wrapped `nfc.inDataExchange()` in `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)` with `responseLength = 60` reset, per-attempt diagnostic, `if (apduOk) break`, and guarded inter-attempt delay.
- Removed old one-shot `"APDU ok=... lastBytes=..."` diagnostic block (replaced by per-attempt output).
- `bool nfcTokenOk = false;` block and all downstream code left structurally unchanged.

## Verification

```
grep -c "APDU_MAX_RETRIES"   → 4  (≥ 2 ✓)
grep "<= APDU_MAX_RETRIES"   → for-loop line ✓
grep "apduAttempt"           → loop variable + diagnostic + delay guard ✓
grep -c "APDU attempt "      → 2  (≥ 1 ✓)
grep "lastBytes="            → no output (old diagnostic absent ✓)
```

All 5 must-have checks passed manually; `scripts/verify-m004.sh` is written in T02.

## Diagnostics

- Serial Monitor (9600 baud): each tap emits `APDU attempt 1/3 ok=YES rspLen=50` (success) or up to three `ok=NO` lines followed by `APDU: inDataExchange failed — RF error or phone not responding` before CARD fallback.
- Structural contract: `bash scripts/verify-m004.sh` (written in T02) covers all five checks.

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — added 2 `#define` constants at tuning block; replaced single `inDataExchange` call with 3-attempt retry loop; removed old one-shot diagnostic
