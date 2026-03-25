---
estimated_steps: 4
estimated_files: 6
skills_used:
  - qodo-get-rules
  - swiftui
  - build-iphone-apps
  - test
---

# T01: Migrate root navigation to native TabView and establish S02 rollback contract harness

**Slice:** S02 — Full UX Rollback Baseline + Native Tab Bar
**Milestone:** M008-l1ngya

## Description

Replace the floating custom shell with native `TabView` first (R069), then add executable rollback-contract checks so downstream rollback edits have deterministic boundaries.

## Steps

1. Load repo constraints via `qodo-get-rules`, then refactor `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` from `StitchTabShell`/`StitchTabItem` composition to native `TabView` with four `.tabItem` labels (`Home`, `History`, `Budget`, `Settings`) while preserving session-expired alert behavior.
2. Create `tests/test_verify_m008_s02_ios_rollback_contract.py` with initial tab-shell assertions (`main_tab_view`-scoped test names) that fail on reintroduced `StitchTabShell` markers.
3. Create `scripts/verify-m008-s02.sh` with phased execution (`preflight`, `s02-rollback-contract`, `budget-regression`, `qr-regression`, `login-regression`) and actionable guidance lines.
4. Run targeted tab-shell checks and iterate until native-shell migration + verifier preflight are stable.

## Must-Haves

- [ ] `MainTabView.swift` has native `TabView` + `.tabItem` markers for all four tabs.
- [ ] `MainTabView.swift` no longer references `StitchTabShell` or `StitchTabItem`.
- [ ] `tests/test_verify_m008_s02_ios_rollback_contract.py` exists with tab-shell assertions runnable via `-k "main_tab_view"`.
- [ ] `scripts/verify-m008-s02.sh` exists with phased command wiring for S02 + regression guards.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py -k "main_tab_view"`
- `rtk proxy python -m py_compile tests/test_verify_m008_s02_ios_rollback_contract.py`

## Observability Impact

- Signals added/changed: phase-scoped verifier logs for shell migration and command-level failure hints.
- How a future agent inspects this: run the targeted pytest command above and inspect `scripts/verify-m008-s02.sh` phase blocks.
- Failure state exposed: native tab-shell drift is isolated before broader surface rollback starts.

## Inputs

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — current floating shell implementation to replace.
- `scripts/verify-m008-s01.sh` — phased verifier style reference.
- `tests/test_verify_m008_s01_ios_budget_contract.py` — budget regression suite to compose into S02 verifier.
- `tests/test_verify_m007_s02_qr_behavior_contract.py` — QR behavior regression suite for R076 support.
- `tests/test_verify_m007_s09_override_contract.py` — login student-ID-only regression guard.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` — native `TabView` root shell.
- `tests/test_verify_m008_s02_ios_rollback_contract.py` — new S02 rollback contract test suite (initial tab-shell assertions).
- `scripts/verify-m008-s02.sh` — phased S02 verifier script.
