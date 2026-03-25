# S02: Full UX Rollback Baseline + Native Tab Bar

**Goal:** Restore the iOS app to a pre-M007 structural UX baseline by replacing the floating Stitch shell with native `TabView` and simplifying Home/Transactions/Settings scaffolds while preserving QR and budget continuity guards for downstream slices.
**Demo:** iOS returns to pre-M007 structural UX baseline (`558d8bc`) with native `TabView` chrome replacing the floating custom shell.

## Must-Haves

- Directly satisfy **R069** by migrating `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` from `StitchTabShell` to native `TabView` with `Home`, `History`, `Budget`, `Settings` tab items.
- Directly satisfy **R068** by restoring baseline interaction structure (commit `558d8bc` reference) across `HomeView`, `TransactionsView`, and `SettingsView` without re-introducing the floating custom shell.
- Support **R076** by preserving QR continuity wiring (`qr_payment_success_continuity_tick` and post-success refresh hooks) in Home/Transactions during rollback edits.
- Keep S01 integration output intact by re-running `tests/test_verify_m008_s01_ios_budget_contract.py` after shell/surface rollback changes.
- Provide objective closure evidence via `tests/test_verify_m008_s02_ios_rollback_contract.py` and `scripts/verify-m008-s02.sh`.

## Proof Level

- This slice proves: integration
- Real runtime required: yes (source-contract integration proof on this Windows host)
- Human/UAT required: no (manual device acceptance is deferred to S06)

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m008_s01_ios_budget_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s02_qr_behavior_contract.py`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only`
- `rtk proxy bash scripts/verify-m008-s02.sh`

## Observability / Diagnostics

- Runtime signals: phased verifier output (`phase=... status=... guidance=...`) for rollback-contract vs regression-guard failures.
- Inspection surfaces: `tests/test_verify_m008_s02_ios_rollback_contract.py`, `scripts/verify-m008-s02.sh`, and guard tests under `tests/`.
- Failure visibility: verifier separates tab-shell drift, baseline-surface drift, QR continuity regression, and budget/login contract regressions.
- Redaction constraints: diagnostics stay marker-based and must not log bearer tokens, session secrets, or full student PII.

## Integration Closure

- Upstream surfaces consumed: `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`, `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`, and S01/M007 guard tests.
- New wiring introduced in this slice: native `TabView` root composition plus S02 rollback verifier (`tests/test_verify_m008_s02_ios_rollback_contract.py` + `scripts/verify-m008-s02.sh`).
- What remains before the milestone is truly usable end-to-end: S03/S04/S05 apply the minimalist refresh layers (Home credit-card hero, filter-only transactions, appearance controls), then S06 executes final manual device acceptance.

## Tasks

- [ ] **T01: Migrate root navigation to native TabView and establish S02 rollback contract harness** `est:1h 20m`
  - Why: R069 is the highest-risk boundary change; locking native tab-shell behavior first prevents drift while downstream view rollback proceeds.
  - Files: `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`, `tests/test_verify_m008_s02_ios_rollback_contract.py`, `scripts/verify-m008-s02.sh`, `tests/test_verify_m008_s01_ios_budget_contract.py`, `tests/test_verify_m007_s02_qr_behavior_contract.py`, `tests/test_verify_m007_s09_override_contract.py`
  - Do: Replace `StitchTabShell` with native `TabView` while preserving session-expired alert semantics; add S02 rollback contract tests (tab-shell assertions first); scaffold `verify-m008-s02.sh` with phased checks for S02 contract + S01 budget + M007 QR/login regressions.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m008_s02_ios_rollback_contract.py -k "main_tab_view"`
  - Done when: native `TabView` markers pass, `StitchTabShell` markers are absent, and the S02 verifier script exists with runnable phased command blocks.

- [ ] **T02: Roll back Home/Transactions/Settings to baseline seams while preserving QR and budget continuity** `est:2h 10m`
  - Why: R068 requires structural rollback of the three primary user-facing surfaces; this task closes that requirement while guarding against QR/budget regressions.
  - Files: `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`, `tests/test_verify_m008_s02_ios_rollback_contract.py`, `scripts/verify-m008-s02.sh`
  - Do: Refactor Home/Transactions/Settings toward `558d8bc` baseline interaction structure (native containers, reduced decorative shell), explicitly remove Transactions `.searchable`, preserve QR continuity markers and refresh hooks, and complete S02 contract assertions for all three surfaces.
  - Verify: `rtk proxy bash scripts/verify-m008-s02.sh`
  - Done when: S02 rollback contract tests pass, S01 budget + M007 QR/login guards remain green, and the slice has one-command closure proof.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `tests/test_verify_m008_s02_ios_rollback_contract.py`
- `scripts/verify-m008-s02.sh`
- `tests/test_verify_m008_s01_ios_budget_contract.py`
- `tests/test_verify_m007_s02_qr_behavior_contract.py`
- `tests/test_verify_m007_s09_override_contract.py`
