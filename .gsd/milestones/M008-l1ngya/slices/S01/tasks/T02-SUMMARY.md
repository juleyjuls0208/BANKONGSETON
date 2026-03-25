---
id: T02
parent: S01
milestone: M008-l1ngya
key_files:
  - tests/conftest.py
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Normalize wrapped pytest `-k` selectors in test config rather than changing contract tests/routes.
  - Treat existing `/api/budget-summary` + iOS contract implementation as source-of-truth after local inspection confirmed T02 scope already delivered.
  - Keep canonical `.sh` verifier flow and document Windows shell fallback as environment behavior, not product regression.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T11:17:42.917Z
blocker_discovered: false
---

# T02: Hardened pytest contract verification against quoted `-k` selectors and revalidated the full M008/S01 budget + iOS contract suite.

**Hardened pytest contract verification against quoted `-k` selectors and revalidated the full M008/S01 budget + iOS contract suite.**

## What Happened

Activated required skills, validated local T02 inputs, and confirmed `/api/budget-summary` + iOS budget contract markers were already implemented and test-covered in this worktree. The gate failure was isolated to pytest receiving a literal quoted selector (`-k '"student_budget"'`), which caused parser failure before collection. Added a narrow `pytest_configure` normalizer in `tests/conftest.py` that strips one matching pair of outer quotes from `config.option.keyword` when present. Re-ran the failing selector and all task/slice verification commands; backend+iOS contracts remained green. Recorded the wrapper-quoting gotcha in `.gsd/KNOWLEDGE.md` for future recovery speed.

## Verification

Confirmed the original failing selector now passes; re-ran task-level backend/iOS contract tests and slice-level checks (subset unauthorized/unavailable/malformed, M007 S04 retry/lost-card regression, and S01 verifier script phases). All Python/pytest checks passed. `rtk proxy bash scripts/verify-m008-s01.sh` still fails on this Windows host because `/bin/bash` is unavailable; equivalent `rtk proxy sh scripts/verify-m008-s01.sh` passed all verifier phases.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k '"student_budget"'` | 0 | ✅ pass | 1670ms |
| 2 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "student_budget"` | 0 | ✅ pass | 1740ms |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py` | 0 | ✅ pass | 1690ms |
| 4 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py -k "unauthorized or unavailable or malformed"` | 0 | ✅ pass | 1610ms |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py` | 0 | ✅ pass | 690ms |
| 6 | `rtk proxy python -m pytest -q tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` | 0 | ✅ pass | 620ms |
| 7 | `rtk proxy bash scripts/verify-m008-s01.sh` | 1 | ❌ fail | 140ms |
| 8 | `rtk proxy sh scripts/verify-m008-s01.sh` | 0 | ✅ pass | 4700ms |


## Deviations

Task plan expected backend/iOS implementation edits; local code already met those requirements, so this execution applied a verifier-compatibility fix (`-k` quoting normalization) and revalidated contracts.

## Known Issues

Environment-only: `/bin/bash` unavailable for `rtk proxy bash`; use `rtk proxy sh scripts/verify-m008-s01.sh` (or explicit Git Bash path) on this host.

## Files Created/Modified

- `tests/conftest.py`
- `.gsd/KNOWLEDGE.md`
