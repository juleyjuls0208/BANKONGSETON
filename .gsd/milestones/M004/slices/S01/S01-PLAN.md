# S01: Firmware APDU Retry

**Goal:** Add a 3-attempt APDU retry loop to the firmware so Android HCE startup latency variation no longer causes 100% phone NFC payment failure.
**Demo:** `bash scripts/verify-m004.sh` exits 0 — 5 structural checks (APDU_MAX_RETRIES defined, `<= APDU_MAX_RETRIES` wired in loop body, APDU_RETRY_DELAY_MS defined, per-attempt diagnostic pattern, `py_compile` on cashier_routes.py) all pass.

## Must-Haves

- `#define APDU_MAX_RETRIES 3` and `#define APDU_RETRY_DELAY_MS 150` in firmware tuning block, immediately after `HEARTBEAT_INTERVAL_MS`
- `inDataExchange` wrapped in a `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)` loop; `responseLength = 60` reset before each call; `break` on first `apduOk == true`; `delay(APDU_RETRY_DELAY_MS)` only between attempts (not before attempt 1), guarded by `apduAttempt < APDU_MAX_RETRIES`
- `bool apduOk = false;` declared before the loop so it remains in scope for the `nfcTokenOk` check block after the loop
- Serial diagnostic per attempt: `"APDU attempt N/3 ok=YES/NO rspLen=N"`; old one-shot diagnostic block replaced
- `nfcTokenOk` check block, RF reset on failure, SW_NO_TOKEN diagnosis, and CARD fallback path: structurally unchanged
- `scripts/verify-m004.sh` exits 0 with 5 checks

## Proof Level

- This slice proves: contract
- Real runtime required: no — firmware flash + phone tap is S02/UAT
- Human/UAT required: no

## Verification

- `bash scripts/verify-m004.sh` — all 5 checks pass, exits 0
- Failure-path diagnostic: `grep "APDU: inDataExchange failed" arduino/bankongseton_rfid/bankongseton_rfid.ino` → returns the all-retries-exhausted error line (confirms failure state is named and inspectable)

## Observability / Diagnostics

- Runtime signals: `"APDU attempt N/3 ok=YES/NO rspLen=N"` in Serial Monitor on every attempt; existing `"HTTP: delivered — NFC|<token>"` line confirms downstream success path unchanged
- Inspection surfaces: Serial Monitor at 9600 baud; `bash scripts/verify-m004.sh` for structural contract without hardware
- Failure visibility: attempt number in each diagnostic line shows exactly how many retries were consumed and which succeeded or failed; all-failed path still logs `"APDU: inDataExchange failed"` before CARD fallback
- Redaction constraints: none — token is an opaque random string, no PII

## Integration Closure

- Upstream surfaces consumed: `bankongseton_rfid.ino` existing APDU block (lines 600–695), `deliver()` retry loop shape (lines 364–383 — same `for`/`break`/delay-between-not-before pattern), `HEARTBEAT_INTERVAL_MS` constant placement (line 78)
- New wiring introduced: retry loop wraps single `inDataExchange` call; two `#define` constants at tuning block; `scripts/verify-m004.sh`
- What remains before the milestone is truly usable end-to-end: S02 — flash firmware to hardware, tap phone, confirm `APDU ok=YES attempt N/3` in Serial Monitor and `complete_sale_nfc CALLED` in server log

## Tasks

- [x] **T01: Add APDU retry loop to firmware** `est:20m`
  - Why: Single `inDataExchange` call times out when Android HCE service isn't ready; retry loop with per-attempt `responseLength` reset closes R025
  - Files: `arduino/bankongseton_rfid/bankongseton_rfid.ino`
  - Do: (1) Add `#define APDU_MAX_RETRIES 3` and `#define APDU_RETRY_DELAY_MS 150` immediately after the `HEARTBEAT_INTERVAL_MS` line (~line 78). (2) In the APDU block: keep `uint8_t response[60];` declaration unchanged; change `uint8_t responseLength = 60;` to `uint8_t responseLength;` (init moved into loop); add `bool apduOk = false;` before the loop. (3) Wrap the single `nfc.inDataExchange()` call in `for (int apduAttempt = 1; apduAttempt <= APDU_MAX_RETRIES; apduAttempt++)`: inside the loop — `responseLength = 60;` first, then `apduOk = nfc.inDataExchange(apduCmd, 19, response, &responseLength);`, then print `"APDU attempt "`, `apduAttempt`, `"/"`, `APDU_MAX_RETRIES`, `" ok="`, `"YES"/"NO"`, `" rspLen="`, `responseLength`; `if (apduOk) break;`; `if (apduAttempt < APDU_MAX_RETRIES) delay(APDU_RETRY_DELAY_MS);`. (4) Remove the old one-shot `"APDU ok=..."` diagnostic block entirely. (5) Leave everything from `bool nfcTokenOk = false;` onward untouched.
  - Verify: `grep -c "APDU_MAX_RETRIES" arduino/bankongseton_rfid/bankongseton_rfid.ino` returns ≥ 2; `grep "<= APDU_MAX_RETRIES" arduino/bankongseton_rfid/bankongseton_rfid.ino` returns the loop line; `grep "apduAttempt" arduino/bankongseton_rfid/bankongseton_rfid.ino` shows per-attempt output; old one-shot `"APDU ok="` line absent
  - Done when: constants defined at tuning block; retry loop present with break-on-success; per-attempt `"APDU attempt N/3"` diagnostic prints; `nfcTokenOk` block structurally identical to before the edit
- [x] **T02: Write verify-m004.sh and confirm all checks pass** `est:15m`
  - Why: Structural contract proof for R025; CI-verifiable without physical hardware
  - Files: `scripts/verify-m004.sh`
  - Do: Copy `check()`/`check_absent()` scaffold verbatim from `scripts/verify-s01.sh` (helpers, PASS/FAIL counters, exit-code logic). Set `INO="arduino/bankongseton_rfid/bankongseton_rfid.ino"`. Add 5 checks: (a) `APDU_MAX_RETRIES` constant defined in INO; (b) `<= APDU_MAX_RETRIES` in INO (proves constant is wired into the loop condition, not just declared); (c) `APDU_RETRY_DELAY_MS` constant defined in INO; (d) `"APDU attempt "` diagnostic pattern in INO; (e) `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0 (use a shell command check, not a grep — run the command and check its exit code; add PASS/FAIL accordingly). Add header `"=== M004 verify: APDU retry firmware + py_compile ==="`. chmod +x. Run from repo root.
  - Verify: `bash scripts/verify-m004.sh` from repo root exits 0 and prints `5 passed, 0 failed`
  - Done when: script is executable, all 5 checks pass, exits 0 from repo root

## Files Likely Touched

- `arduino/bankongseton_rfid/bankongseton_rfid.ino`
- `scripts/verify-m004.sh`
