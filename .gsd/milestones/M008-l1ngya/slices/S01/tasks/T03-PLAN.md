---
estimated_steps: 4
estimated_files: 4
skills_used:
  - test
  - best-practices
  - build-iphone-apps
  - swiftui
---

# T03: Ship S01 verifier tying backend contract proof to iOS retry-visibility regression checks

**Slice:** S01 — Budget Contract Restoration (Backend + iOS)
**Milestone:** M008-l1ngya

## Description

Provide one-command closure proof for S01 so future agents can quickly detect whether budget contract reliability and iOS-visible retry semantics are still intact.

## Steps

1. Create `scripts/verify-m008-s01.sh` following repo verifier conventions (preflight checks, phased execution, fail-fast guidance lines).
2. Wire the verifier to run backend contract tests (`tests/test_verify_m008_s01_budget_contract.py`) and iOS contract checks (`tests/test_verify_m008_s01_ios_budget_contract.py`).
3. Include regression coverage for existing iOS failure-visibility behavior via `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` to enforce R074 continuity.
4. Add concise static marker assertions in the verifier for high-risk literals (budget endpoint constants and retry controls) only where they improve diagnosis beyond pytest output.

## Must-Haves

- [ ] `scripts/verify-m008-s01.sh` exists and is executable with RTK-prefixed commands.
- [ ] Verifier phases clearly separate backend contract, iOS contract, and failure-visibility regression checks.
- [ ] Verifier emits actionable guidance when any phase fails.
- [ ] A single command can serve as S01 stopping-condition proof.

## Verification

- `rtk proxy bash scripts/verify-m008-s01.sh`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_budget_contract.py tests/test_verify_m008_s01_ios_budget_contract.py tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`

## Observability Impact

- Signals added/changed: phased verifier output (`phase=... status=... guidance=...`) for rapid failure localization.
- How a future agent inspects this: run `scripts/verify-m008-s01.sh` and read phase-specific guidance in terminal output.
- Failure state exposed: backend contract breakage vs iOS contract drift vs retry-visibility regression are disambiguated explicitly.

## Inputs

- `tests/test_verify_m008_s01_budget_contract.py` — backend route contract and failure-path assertions.
- `tests/test_verify_m008_s01_ios_budget_contract.py` — iOS endpoint/payload/retry marker assertions.
- `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py` — existing budget failure-channel regression guard.
- `scripts/verify-m007-s04.sh` — verifier structure/reference pattern for guidance style.

## Expected Output

- `scripts/verify-m008-s01.sh` — one-command S01 verifier with phased diagnostics.
- `tests/test_verify_m008_s01_budget_contract.py` — finalized backend contract suite referenced by verifier.
- `tests/test_verify_m008_s01_ios_budget_contract.py` — finalized iOS contract suite referenced by verifier.
