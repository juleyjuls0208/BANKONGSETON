# S01: Firmware APDU Retry — UAT

**Milestone:** M004
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S01 proof level is "contract" — the slice adds code structure (constants + loop) whose correctness can be fully verified by structural grep and py_compile without flashing hardware. Runtime confirmation (Serial Monitor showing `ok=YES` on a real phone tap) is an S02 gate by design. This UAT validates everything that can be verified without hardware.

## Preconditions

1. Working directory is repo root (`/c/Users/admin/Desktop/projects/BANKONGSETON`)
2. Python 3.x available on PATH (`python --version` or `python3 --version` returns without error)
3. `backend/dashboard/cashier/cashier_routes.py` is present and unmodified since M003/S02
4. `arduino/bankongseton_rfid/bankongseton_rfid.ino` has the S01 APDU retry changes applied
5. `scripts/verify-m004.sh` exists and is executable

## Smoke Test

```bash
bash scripts/verify-m004.sh
```

Expected: prints `=== Results: 5 passed, 0 failed ===` and exits 0. If this passes, the slice contract is intact.

## Test Cases

### 1. Structural contract script passes all 5 checks

```bash
bash scripts/verify-m004.sh
```

1. Run the command from repo root.
2. Observe per-check output lines.
3. **Expected:** Each of the 5 lines reads `  PASS  (a/b/c/d/e) ...`; final line reads `=== Results: 5 passed, 0 failed ===`; process exits 0.

---

### 2. APDU_MAX_RETRIES constant defined and wired as loop bound

```bash
grep -n "APDU_MAX_RETRIES" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** At least 2 matching lines — one `#define APDU_MAX_RETRIES 3` (at the tuning block near line 72–73) and at least one `<= APDU_MAX_RETRIES` (loop condition in the APDU block). Constant value must be `3`.

---

### 3. APDU_RETRY_DELAY_MS constant defined with correct value

```bash
grep -n "APDU_RETRY_DELAY_MS" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** At least 2 matching lines — `#define APDU_RETRY_DELAY_MS 150` (constant declaration) and `delay(APDU_RETRY_DELAY_MS)` (usage inside loop, guarded by `apduAttempt < APDU_MAX_RETRIES`).

---

### 4. Per-attempt diagnostic pattern present

```bash
grep -n "APDU attempt " arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** At least 1 match containing `"APDU attempt "` — the Serial.print line inside the loop that emits attempt number, total, ok/no, and rspLen. The diagnostic must include `apduAttempt` and `APDU_MAX_RETRIES` to show N/3 format.

---

### 5. Old one-shot diagnostic is absent (no regression to single-shot behavior)

```bash
grep "lastBytes=" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** No output. The old single-shot `"APDU ok=... lastBytes=..."` diagnostic was removed and must not be present — its presence would indicate the old block was not removed.

---

### 6. Failure-path diagnostic is present and named

```bash
grep "APDU: inDataExchange failed" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** Returns the line `Serial.println("APDU: inDataExchange failed — RF error or phone not responding");` — confirms the all-retries-exhausted failure state is named, inspectable, and present in the codebase.

---

### 7. apduOk declared before loop (in scope for nfcTokenOk block)

```bash
grep -n "bool apduOk" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** Exactly 1 match — `bool apduOk = false;` declared before the `for` loop, not inside it. This confirms it remains in scope for the `nfcTokenOk` check block that follows the loop.

---

### 8. responseLength reset inside loop (not just declared once)

```bash
grep -n "responseLength = 60" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. Run from repo root.
2. **Expected:** Match is inside the `for (apduAttempt ...)` loop body — `responseLength = 60;` as the first statement before each `inDataExchange` call. Confirms the defensive reset is in place; library may modify the field on failure, so per-attempt reset is required.

---

### 9. py_compile passes on cashier_routes.py (no syntax regressions)

```bash
python -m py_compile backend/dashboard/cashier/cashier_routes.py && echo "OK"
```

1. Run from repo root.
2. **Expected:** Prints `OK`, exits 0. No output to stderr. S01 does not touch cashier_routes.py, but this confirms the M003/S02 backend is syntactically intact after all S01 file operations.

---

### 10. Constants placed immediately after HEARTBEAT_INTERVAL_MS (tuning block)

```bash
grep -n -A2 "HEARTBEAT_INTERVAL_MS" arduino/bankongseton_rfid/bankongseton_rfid.ino | head -10
```

1. Run from repo root.
2. **Expected:** The 2 lines immediately following `HEARTBEAT_INTERVAL_MS` are `#define APDU_MAX_RETRIES 3` and `#define APDU_RETRY_DELAY_MS 150`. Confirms tuning constants are co-located in the tuning block for easy adjustment.

## Edge Cases

### Verify retry loop exits on first success (break present)

```bash
grep -n "if (apduOk) break" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. **Expected:** 1 match inside the `for (apduAttempt ...)` loop body. Without the `break`, every attempt fires even when attempt 1 succeeds — adding unnecessary latency for fast phones.

---

### Verify inter-attempt delay is guarded (not fired after last attempt)

```bash
grep -n "apduAttempt < APDU_MAX_RETRIES" arduino/bankongseton_rfid/bankongseton_rfid.ino
```

1. **Expected:** 1 match — `if (apduAttempt < APDU_MAX_RETRIES) delay(APDU_RETRY_DELAY_MS);` — confirms the delay does not fire after the last attempt, matching the deliver() retry loop pattern.

---

### Verify script exits 1 on a broken firmware file (negative self-test)

```bash
bash -c '
INO=$(mktemp /tmp/test_XXXX.ino)
echo "// empty" > "$INO"
grep -q "APDU_MAX_RETRIES" "$INO" && echo "PASS" || echo "FAIL (expected)"
rm "$INO"
'
```

1. **Expected:** Prints `FAIL (expected)` — confirms the grep check logic works and would catch a missing constant. (This is a logic sanity check, not an assertion on the real firmware.)

## Failure Signals

- `verify-m004.sh` prints any `FAIL` line → a constant is missing or the loop condition is not wired; check the tuning block and APDU block in the `.ino`
- `grep "lastBytes="` returns output → old one-shot diagnostic block was not removed; remove the block and re-run verify
- `grep "bool apduOk"` returns 0 matches → `apduOk` was not declared before the loop; `nfcTokenOk` check after the loop will fail to compile
- `grep "responseLength = 60"` returns a match outside the loop → init is in the wrong place; library may return stale length on retries 2–3
- `py_compile` errors on stderr → unrelated syntax regression in cashier_routes.py; investigate separately

## Requirements Proved By This UAT

- R025 (partial — contract proof) — `APDU_MAX_RETRIES=3`, `APDU_RETRY_DELAY_MS=150`, retry loop with break-on-success, per-attempt diagnostic, and failure-path log all confirmed present in firmware source; `verify-m004.sh` exits 0

## Not Proven By This UAT

- R025 (runtime proof) — `APDU attempt N/3 ok=YES` in Serial Monitor on a real phone tap; requires hardware flash + Android phone; this is the S02 UAT gate
- Physical RFID card regression — `POST /api/arduino/card-read 200` after firmware flash; requires hardware; S02 UAT gate
- `complete_sale_nfc CALLED` in server log on phone tap — backend path; S02 UAT gate
- Cashier UI success modal on phone tap — end-to-end flow; S02 UAT gate

## Notes for Tester

All tests in this UAT run without hardware — they are grep/py_compile checks against source files. The commands are designed to be copy-pasted verbatim from repo root. Test cases 1–6 are the core contract (mirrors `verify-m004.sh` checks plus failure-path diagnostic). Test cases 7–10 verify structural details that the script does not explicitly check. Edge cases verify loop semantics (break-on-success, delay-not-after-last) that are important for runtime behavior but verifiable from source.

For runtime validation (actual phone tap), see S02-UAT.md after S02 completes.
