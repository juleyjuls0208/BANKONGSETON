---
estimated_steps: 5
estimated_files: 1
---

# T01: Add APDU retry loop to firmware

**Slice:** S01 — Firmware APDU Retry
**Milestone:** M004

## Description

Replace the single `inDataExchange` call with a 3-attempt retry loop so Android HCE startup latency variation no longer causes 100% phone NFC payment failure. Add two `#define` constants at the tuning block. The loop shape mirrors `deliver()` exactly: `for`/`break-on-success`/`delay-between-not-before`. The `nfcTokenOk` check block and all downstream code are untouched.

## Steps

1. Read `arduino/bankongseton_rfid/bankongseton_rfid.ino` lines 65–82 to confirm the `HEARTBEAT_INTERVAL_MS` line and its surrounding context.
2. Edit: add `#define APDU_MAX_RETRIES 3` and `#define APDU_RETRY_DELAY_MS 150` immediately after the `HEARTBEAT_INTERVAL_MS` line.
3. Read `bankongseton_rfid.ino` lines 607–660 to confirm the exact current APDU block structure before editing.
4. Edit the APDU block:
   - Change `uint8_t responseLength = 60;` → `uint8_t responseLength;` (init moves into loop body)
   - Add `bool apduOk = false;` before the loop (must be in scope for `nfcTokenOk` check after the loop)
   - Wrap the single `nfc.inDataExchange()` call in `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)` with body:
     ```
     responseLength = 60;
     apduOk = nfc.inDataExchange(apduCmd, 19, response, &responseLength);
     Serial.print("APDU attempt "); Serial.print(apduAttempt);
     Serial.print("/"); Serial.print(APDU_MAX_RETRIES);
     Serial.print(" ok="); Serial.print(apduOk ? "YES" : "NO");
     Serial.print(" rspLen="); Serial.println(responseLength);
     if (apduOk) break;
     if (apduAttempt < APDU_MAX_RETRIES) delay(APDU_RETRY_DELAY_MS);
     ```
   - Remove the old one-shot `"APDU ok=..."` diagnostic block (the multi-line `Serial.print` block ending with `Serial.println()`) — it is fully replaced by the per-attempt output above
   - Leave everything from `bool nfcTokenOk = false;` onward unchanged
5. Structural grep verification (see Verification section).

## Must-Haves

- [ ] `#define APDU_MAX_RETRIES 3` present at tuning block (after `HEARTBEAT_INTERVAL_MS`)
- [ ] `#define APDU_RETRY_DELAY_MS 150` present at tuning block
- [ ] `bool apduOk = false;` declared before the loop (not inside it — must be in scope for `nfcTokenOk` after the loop)
- [ ] `responseLength = 60;` reset inside the loop before every `inDataExchange` call
- [ ] Per-attempt `"APDU attempt N/3 ok=YES/NO rspLen=N"` diagnostic in the loop
- [ ] `if (apduOk) break;` — first success exits the loop immediately
- [ ] Inter-attempt `delay(APDU_RETRY_DELAY_MS)` guarded by `apduAttempt < APDU_MAX_RETRIES` — no delay before attempt 1, no delay after the last attempt
- [ ] Old one-shot `"APDU ok=..."` diagnostic block removed
- [ ] `bool nfcTokenOk = false;` check block and everything below structurally unchanged

## Verification

- `grep -c "APDU_MAX_RETRIES" arduino/bankongseton_rfid/bankongseton_rfid.ino` → ≥ 2 (defined + used in loop condition)
- `grep "<= APDU_MAX_RETRIES" arduino/bankongseton_rfid/bankongseton_rfid.ino` → returns the for-loop line
- `grep "apduAttempt" arduino/bankongseton_rfid/bankongseton_rfid.ino` → returns per-attempt diagnostic and loop variable lines
- `grep -c "APDU attempt " arduino/bankongseton_rfid/bankongseton_rfid.ino` → ≥ 1
- Old one-shot diagnostic absent: `grep "lastBytes=" arduino/bankongseton_rfid/bankongseton_rfid.ino` → returns nothing (that line only existed in the old diagnostic)

## Observability Impact

- Signals added/changed: per-attempt `"APDU attempt N/3 ok=YES/NO rspLen=N"` replaces the old single-shot `"APDU ok=YES/NO rspLen=N lastBytes=..."` diagnostic; attempt number now visible in Serial Monitor
- How a future agent inspects this: `bash scripts/verify-m004.sh` for structural contract; Serial Monitor at 9600 baud for runtime confirmation on real hardware
- Failure state exposed: how many retries were consumed and which attempt succeeded or failed is now explicit in the serial log

## Inputs

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — existing APDU block (single `inDataExchange` + one-shot diagnostic) to be replaced; `deliver()` retry loop (lines 364–383) as the structural pattern to follow; `HEARTBEAT_INTERVAL_MS` at ~line 78 as constant placement anchor

## Expected Output

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — two `#define` constants at tuning block; APDU block with retry loop, per-attempt diagnostic, and unchanged `nfcTokenOk` check block below
