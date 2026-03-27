---
estimated_steps: 5
estimated_files: 5
skills_used:
  - qodo-get-rules
  - swiftui
  - test
---

# T02: Add S03 Home rollback contract suite and phased verifier chaining S02 guards

**Slice:** S03 — Home Rollback + Credit-Card Hero + QR Continuity
**Milestone:** M008-l1ngya

## Description

Create executable S03 closure proof by adding Home rollback source-contract tests and a phased verifier that chains existing S02 rollback/regression guards.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `tests/test_verify_m008_s03_ios_home_rollback_contract.py` | Fail fast with explicit required/forbidden marker messages | N/A (local source test execution) | Assert exact marker context (missing/forbidden marker with file path) |
| `scripts/verify-m008-s02.sh` regression chain | Bubble failing phase and stop S03 closure | Emit explicit Windows Git Bash fallback guidance when `/bin/bash` is unavailable | Treat any non-zero chain exit as regression, never ignore |

## Load Profile

- **Shared resources**: pytest process and serial shell verifier phases.
- **Per-operation cost**: one S03 suite + one targeted continuity-node test + one S02 chain run.
- **10x breakpoint**: runtime duration growth; semantic stability preserved by serial phase boundaries.

## Negative Tests

- **Malformed inputs**: missing source/test/script files fail preflight with guidance.
- **Error paths**: removed continuity marker in Home must fail `home-qr-continuity` phase.
- **Boundary conditions**: S03-local pass + chained S02 fail must still return overall verifier failure.

## Steps

1. Load repo constraints via `qodo-get-rules` and inspect existing verifier style in `scripts/verify-m008-s02.sh`.
2. Add `tests/test_verify_m008_s03_ios_home_rollback_contract.py` asserting R070 Home hero markers plus forbidden heavy-shell markers and required continuity seam markers.
3. Add `scripts/verify-m008-s03.sh` with phases: `preflight`, `s03-home-contract`, `home-qr-continuity`, `s02-regression-chain`.
4. Ensure phase failures emit actionable `guidance=` lines and use Windows-compatible invocation (`C:\Program Files\Git\bin\bash.exe`) in verification guidance.
5. Run full S03 verifier and iterate until all phases pass.

## Must-Haves

- [ ] `tests/test_verify_m008_s03_ios_home_rollback_contract.py` exists and fails on Home rollback marker drift.
- [ ] `scripts/verify-m008-s03.sh` chains S03 contracts with S02 verifier and fails fast per phase.
- [ ] Verifier preflight checks required files and emits actionable guidance.
- [ ] Final closure command proves both R070 and R076 guard continuity.

## Verification

- `rtk proxy python -m py_compile tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s03.sh`

## Observability Impact

- Signals added/changed: S03 phase logs (`phase=<name> status=...`) and phase-scoped guidance output.
- How a future agent inspects this: run `scripts/verify-m008-s03.sh` first, then drill into the failing phase’s direct test command.
- Failure state exposed: Home marker drift, continuity seam drift, and downstream S02 regressions are isolated to explicit phases.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `scripts/verify-m008-s02.sh`

## Expected Output

- `tests/test_verify_m008_s03_ios_home_rollback_contract.py`
- `scripts/verify-m008-s03.sh`
