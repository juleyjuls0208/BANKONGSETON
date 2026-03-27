---
sliceId: S02
uatType: artifact-driven
verdict: PASS
date: 2026-03-27T10:21:21.055198+00:00
---

# UAT Result — S02

## Checks

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| Preconditions: required iOS/verifier files exist | artifact | PASS | Ran `rtk proxy python -c ...`; output `preflight=ok` and `missing=none` for `MainTabView.swift`, `test_verify_m008_s02_ios_rollback_contract.py`, and `verify-m008-s02.sh`. |
| Smoke test: phased verifier passes via Git Bash | runtime | PASS | Ran `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`; output included all phases `status=passed` and final `[verify-m008-s02] status=passed`. |
| Native tab shell contract is present | runtime | PASS | Ran `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py::test_main_tab_view_uses_native_tab_view_with_all_four_tab_items`; `1 passed`. |
| Floating stitch shell markers are removed | runtime | PASS | Ran `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py::test_main_tab_view_removes_stitch_shell_markers`; `1 passed`. |
| Session-expired alert behavior is preserved | runtime | PASS | Ran `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py::test_main_tab_view_preserves_session_expired_alert_behavior`; `1 passed`. |
| Regression harness still protects budget/QR/login | runtime | PASS | Re-ran `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`; phases `s02-rollback-contract`, `budget-regression`, `qr-regression`, `login-regression` all `status=passed`; no `status=failed` or `guidance=` failure lines. |
| Edge case: `/bin/bash` path failure is environment-only | runtime | PASS | Ran `rtk proxy bash scripts/verify-m008-s02.sh`; failed with `execvpe(/bin/bash) failed: No such file or directory` (expected Windows shell-availability constraint). |
| Edge case fallback: Git Bash path executes same verifier semantics | runtime | PASS | Ran `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s02.sh`; full phased pass and final `[verify-m008-s02] status=passed`. |

## Overall Verdict

PASS — All automatable S02 artifact-driven checks and edge-case fallback checks passed with expected outputs.

## Notes

- Coverage emitted non-blocking `CoverageWarning: No data was collected` warnings during pytest runs; these did not affect pass/fail outcomes for the contract assertions.
- No human-only subjective checks were defined for this slice; no `NEEDS-HUMAN` items remain.
