---
estimated_steps: 4
estimated_files: 4
skills_used:
  - qodo-get-rules
  - test
  - debug-like-expert
  - best-practices
  - code-review
---

# T01: Build S07 integration contracts and phased closure verifier

**Slice:** S07 — Final Integration + Device Demo Readiness Gate
**Milestone:** M007

## Description

Create the executable closure gate for S07 before runtime fixes begin. This task adds integration/scope contract tests plus a phased verifier script that emits high-signal diagnostics when the final app journey regresses.

## Steps

1. Add `tests/test_verify_m007_s07_integration_behavior_contract.py` with required final-assembly markers spanning QR success handoff, Home refresh continuity, Transactions search/filter/load-more continuity, and settings/lost-card actionability seams.
2. Add `tests/test_verify_m007_s07_scope_guard_contract.py` with forbidden-marker checks to prevent payment-method surfaces and other out-of-scope settings/receipt actions from reappearing.
3. Implement `scripts/verify-m007-s07.sh` with `set -euo pipefail`, structured phase tags, and `fail_with_guidance` diagnostics; include preflight, contract, scope, integration, and diagnostic-surface phases.
4. Keep shell literal assertions safe under `set -u` by single-quoting literals containing `$` (for example `'text: $viewModel.searchQuery'`) and seed `S07-UAT.md` with headings referenced by the verifier artifact phase.

## Must-Haves

- [ ] New S07 contract tests exist and are executable by pytest.
- [ ] Verifier script emits structured `phase=` and `guidance=` output for inspectable failure localization.
- [ ] Script/source checks avoid unbound-variable failures from `$...` literals under `set -u`.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['set -euo pipefail','fail_with_guidance','phase=diagnostic-surface','guidance=']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

## Observability Impact

- Signals added/changed: phase-tagged verifier lifecycle (`phase=<...>`) and explicit failure guidance lines.
- How a future agent inspects this: run `rtk proxy sh scripts/verify-m007-s07.sh` and inspect which phase fails.
- Failure state exposed: missing required markers, forbidden scope regressions, and missing artifacts each return phase-specific diagnostics.

## Inputs

- `scripts/verify-m007-s06.sh` — prior phased verifier structure to reuse for fail-fast diagnostics.
- `tests/test_verify_m007_s06_motion_behavior_contract.py` — existing contract-test style baseline.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — search/filter marker source (includes `$viewModel.searchQuery` literal risk in shell assertions).
- `.gsd/milestones/M007/slices/S07/S07-PLAN.md` — required slice goal/must-have/verifier contract.

## Expected Output

- `tests/test_verify_m007_s07_integration_behavior_contract.py` — required integration behavior contract assertions.
- `tests/test_verify_m007_s07_scope_guard_contract.py` — final scope-guard contract assertions.
- `scripts/verify-m007-s07.sh` — phased S07 verifier with structured diagnostics.
- `.gsd/milestones/M007/slices/S07/S07-UAT.md` — initial UAT artifact scaffold referenced by S07 verifier.
