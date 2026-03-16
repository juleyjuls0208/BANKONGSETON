---
estimated_steps: 4
estimated_files: 1
---

# T02: Write verify-m004.sh and confirm all checks pass

**Slice:** S01 — Firmware APDU Retry
**Milestone:** M004

## Description

Create `scripts/verify-m004.sh` — the structural contract proof for R025 and the slice's objective stopping condition. Five checks: APDU_MAX_RETRIES defined, `<= APDU_MAX_RETRIES` wired in loop body, APDU_RETRY_DELAY_MS defined, per-attempt diagnostic pattern, and `python -m py_compile` on cashier_routes.py. Scaffold copied verbatim from `verify-s01.sh`.

## Steps

1. Read `scripts/verify-s01.sh` in full to extract the `check()`/`check_absent()` helpers, PASS/FAIL counter pattern, and exit-code logic.
2. Write `scripts/verify-m004.sh`:
   - Shebang + `set -euo pipefail`
   - Header comment and usage line
   - `INO="arduino/bankongseton_rfid/bankongseton_rfid.ino"`
   - `check()` and `check_absent()` helper functions copied verbatim
   - PASS/FAIL counters initialized to 0
   - Section header: `"=== M004 verify: APDU retry firmware + py_compile ==="`
   - Check (a): `APDU_MAX_RETRIES` present in INO (constant defined)
   - Check (b): `<= APDU_MAX_RETRIES` present in INO (constant wired into loop condition — not just declared)
   - Check (c): `APDU_RETRY_DELAY_MS` present in INO (delay constant defined)
   - Check (d): `"APDU attempt "` present in INO (per-attempt diagnostic pattern)
   - Check (e): `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0 — run this as an inline command and add PASS/FAIL to counter based on exit code (not a grep check; use `if python -m py_compile ...; then ...`)
   - Results line: `"=== Results: $PASS passed, $FAIL failed ==="`
   - Exit 1 if `$FAIL -gt 0`, else exit 0
3. `chmod +x scripts/verify-m004.sh`
4. Run `bash scripts/verify-m004.sh` from repo root and confirm exit 0.

## Must-Haves

- [ ] Script runs from repo root without modification to any path
- [ ] `check()` and `check_absent()` helpers copied from `verify-s01.sh` (consistent tooling across verify scripts)
- [ ] Check (b) greps for `<= APDU_MAX_RETRIES` — not `for.*apduAttempt` (fragile) — confirms the constant is actually used as the loop bound
- [ ] Check (e) runs `python -m py_compile` as a live command (not a grep); counts toward PASS/FAIL total
- [ ] Exit code is 0 only when all 5 checks pass; exits 1 on any failure

## Verification

- `bash scripts/verify-m004.sh` from repo root → exits 0, output shows `5 passed, 0 failed`

## Inputs

- `scripts/verify-s01.sh` — scaffold to copy (check helpers, counter pattern, exit logic)
- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — the file all grep checks target; must have T01 edits applied
- `backend/dashboard/cashier/cashier_routes.py` — target of py_compile check (already exits 0 today; assert it continues to)

## Expected Output

- `scripts/verify-m004.sh` — executable verify script; `bash scripts/verify-m004.sh` exits 0 with 5 passed, 0 failed

## Observability Impact

This task produces no runtime signals of its own — it is a structural verification tool, not shipped firmware or backend code.

**Inspection surface:** `bash scripts/verify-m004.sh` from repo root. Each check line is labelled `PASS`/`FAIL` with the pattern and file printed on failure. The final `=== Results: N passed, N failed ===` line and exit code are machine-readable by CI.

**Failure visibility:** If a grep check fails the script prints the failing pattern and file path. If `py_compile` fails it prints the Python traceback to stderr. Exit code 1 on any failure — CI or a future agent can detect regression without reading the output.

**What becomes inspectable:** After T01's retry loop is in place, `bash scripts/verify-m004.sh` is the single command a future agent uses to confirm the structural contract without hardware. Five checks covering constant definition, constant use as loop bound, delay constant, per-attempt diagnostic pattern, and Python syntax integrity.
