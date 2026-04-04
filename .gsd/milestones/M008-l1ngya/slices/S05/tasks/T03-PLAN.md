---
estimated_steps: 5
estimated_files: 2
skills_used: []
---

# T03: Run S05 verifier and close slice

1. Run `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s05.sh` and confirm all phases pass.
2. Run `rtk proxy python -m pytest -q tests/test_verify_m008_s05_ios_integration_contract.py` and confirm all tests pass.
3. Write S05-SUMMARY.md with oneLiner, narrative, verification evidence.
4. Write S05-UAT.md with test cases and pass/fail verdicts.
5. Use `gsd_slice_complete` to close the slice with `overall_verdict=PASS` and record requirements advanced/validated.

## Inputs

- `scripts/verify-m008-s05.sh`
- `tests/test_verify_m008_s05_ios_integration_contract.py`
- `tests/test_verify_m008_s01_budget_contract.py`
- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py`

## Expected Output

- `.gsd/milestones/M008-l1ngya/slices/S05/S05-SUMMARY.md`
- `.gsd/milestones/M008-l1ngya/slices/S05/S05-UAT.md`

## Verification

All phases in verify-m008-s05.sh pass; all integration contract tests pass; slice complete recorded in DB
