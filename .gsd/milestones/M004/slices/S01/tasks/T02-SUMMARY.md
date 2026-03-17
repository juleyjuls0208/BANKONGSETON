---
id: T02
parent: S01
milestone: M004
provides:
  - scripts/verify-m004.sh — executable 5-check structural contract for M004/S01
key_files:
  - scripts/verify-m004.sh
key_decisions:
  - check(e) uses `python -m py_compile` as a live subprocess rather than a grep — catches actual syntax errors, not just file presence
  - check(b) greps for `<= APDU_MAX_RETRIES` not `for.*apduAttempt` — confirms the constant is used as the loop bound, not merely declared
patterns_established:
  - verify-m00N.sh follows the same check()/check_absent() helper pattern as verify-s01.sh — consistent tooling across all structural verify scripts
observability_surfaces:
  - "bash scripts/verify-m004.sh" — prints PASS/FAIL per check with pattern+file on failure; exits 1 on any failure; machine-readable by CI
duration: <5 min
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Write verify-m004.sh and confirm all checks pass

**Created `scripts/verify-m004.sh`; `bash scripts/verify-m004.sh` exits 0 — 5 passed, 0 failed.**

## What Happened

Read `scripts/verify-s01.sh` for the scaffold, then wrote `scripts/verify-m004.sh` with the same `check()`/`check_absent()` helper pattern and PASS/FAIL counter logic. Five checks:

- **(a)** `APDU_MAX_RETRIES` present in INO — constant defined
- **(b)** `<= APDU_MAX_RETRIES` present in INO — constant wired as loop bound (not just declared)
- **(c)** `APDU_RETRY_DELAY_MS` present in INO — delay constant defined
- **(d)** `"APDU attempt "` present in INO — per-attempt diagnostic pattern
- **(e)** `python -m py_compile backend/dashboard/cashier/cashier_routes.py` — live subprocess, exit 0

Check (b) intentionally greps the loop-condition token (`<= APDU_MAX_RETRIES`) rather than the for-loop structure — this is more resilient to loop variable renames and confirms the constant actually controls the iteration bound.

Check (e) runs `py_compile` inline with `if python -m py_compile ...; then` — output goes to stdout/stderr live so any syntax error is visible in the script run, and the exit code feeds the PASS/FAIL counter directly.

Also patched the pre-flight observability gap: added `## Observability Impact` section to `T02-PLAN.md`.

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

Exit: 0
```

Slice-level secondary check also passes:
```
grep "APDU: inDataExchange failed" arduino/bankongseton_rfid/bankongseton_rfid.ino
→ Serial.println("APDU: inDataExchange failed — RF error or phone not responding");
```

Both slice verification checks pass. S01 is complete.

## Diagnostics

`bash scripts/verify-m004.sh` is the structural contract surface for this slice. On failure, each check line shows the failing pattern and target file. `py_compile` errors appear on stderr. Exit code is machine-readable by CI.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scripts/verify-m004.sh` — executable 5-check structural verify script for M004/S01; exits 0 with 5 passed
- `.gsd/milestones/M004/slices/S01/tasks/T02-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
