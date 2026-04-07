# S01: Budget Contract Restoration (Backend + iOS) — UAT

**Milestone:** M008-l1ngya
**Written:** 2026-03-25T11:28:59.078Z

## S01 UAT Script — Budget Contract Restoration (Backend + iOS)

### Preconditions
1. Backend API test environment is available in this worktree.
2. Python test dependencies are installed.
3. `scripts/verify-m008-s01.sh` exists and is executable from a shell runtime.
4. For Windows runners without `/bin/bash`, Git Bash is installed at `C:\Program Files\Git\bin\bash.exe`.

---

### Test Case 1 — Student budget limit read/write contract (happy path)
**Objective:** Confirm monthly limit can be created, read back, and updated for current PH month.

1. Run:
   - `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"`
2. Observe test output.

**Expected Results:**
- Test run exits 0.
- Coverage includes create/read/update semantics for `GET/POST /api/student/budget`.
- Response contract includes `monthly_limit` and month-scoped persistence behavior.

---

### Test Case 2 — Monthly spend contract from Transactions Log
**Objective:** Confirm spend segment comes from PH-month transaction rows and remains deterministic.

1. Run:
   - `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py`
2. Inspect pass/fail status for budget summary cases.

**Expected Results:**
- Test run exits 0.
- `/api/budget-summary` contract returns `monthly_spend` using current PH-month window.
- Mixed schema handling (`TransactionType`/`Type`) and malformed row skip behavior are covered.

---

### Test Case 3 — Failure visibility (unauthorized/unavailable/malformed)
**Objective:** Ensure failures are explicit and retry-safe (no silent fallback masking).

1. Run:
   - `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"`
2. Verify status-code/failure envelope assertions pass.

**Expected Results:**
- Test run exits 0.
- Auth failure returns explicit `401` envelope.
- Missing student-card binding returns `404` envelope.
- Sheets/service issues return explicit `503`/`500` envelopes.

---

### Test Case 4 — iOS budget contract compatibility markers
**Objective:** Ensure iOS networking/view-model contracts still align with backend payload and path names.

1. Run:
   - `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`
2. Confirm marker/contract checks pass.

**Expected Results:**
- Test run exits 0.
- iOS constants include `/student/budget` and `/budget-summary`.
- API client decoding and budget-state marker invariants remain aligned to `monthly_limit`/`monthly_spend` contract.

---

### Test Case 5 — Retry visibility regression continuity
**Objective:** Ensure existing budget retry UX channels remain visible and actionable.

1. Run:
   - `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
2. Validate retry-related checks pass.

**Expected Results:**
- Test run exits 0.
- `loadErrorMessage` / `saveErrorMessage` channels and retry actions remain contract-visible.
- No silent masking regressions are introduced.

---

### Test Case 6 — One-command slice verifier gate
**Objective:** Confirm S01 can be validated through a single phased verifier command.

1. Preferred (Windows-compatible in this harness):
   - `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s01.sh`
2. If Linux/WSL `/bin/bash` is available, canonical command may also be used:
   - `rtk proxy bash scripts/verify-m008-s01.sh`

**Expected Results:**
- Verifier prints all phases: `preflight`, `backend-contract`, `ios-contract`, `retry-visibility-regression`, `static-contract`.
- Each phase reports `status=passed`.
- Command exits 0.

---

### Edge Cases Covered by This UAT
- Wrapped pytest keyword selectors (quoted `-k`) remain runnable through test config normalization.
- Shell runtime variance (missing `/bin/bash`) does not block validation when explicit Git Bash path is used.
- Malformed transaction rows do not crash spend computation and are handled as non-fatal diagnostics.

