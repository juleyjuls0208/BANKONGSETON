# S05: Integrated UX Closure + Requirement Validation

**Goal:** Run the integrated UX closure — chained S01-S04 verifiers plus a top-level integration contract test — proving the full login→home→transactions→budget→settings rollback flow is coherent with no QR regressions, then produce the UAT verdict and consolidated requirements validation.
**Demo:** After this: Integrated login→home→transactions→budget→settings flow passes contract and regression suites with no QR regressions.

## Tasks
- [x] **T01: Created scripts/verify-m008-s05.sh — all 4 chained phases (S01→S02→S03→S04) pass** — Create `scripts/verify-m008-s05.sh` that:
1. Preflight-checks all S01-S04 verifier scripts exist
2. Runs S01 verifier (`scripts/verify-m008-s01.sh`) — budget contract
3. Runs S02 verifier (`scripts/verify-m008-s02.sh`) — TabView/regression
4. Runs S03 verifier (`scripts/verify-m008-s03.sh`) — Home/QR continuity
5. Runs S04 verifier (`scripts/verify-m008-s04.sh`) — transactions/settings
6. Reports phase status for each and exits 0 only if all phases pass
Use Windows Git Bash path fallback (`C:/Progra~1/Git/bin/bash.exe`) when `/bin/bash` is unavailable.
  - Estimate: 30min
  - Files: scripts/verify-m008-s05.sh
  - Verify: rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s05.sh → all phases pass with `status=passed`
- [x] **T02: Create S05 integration contract test — 17/17 tests pass** — Create `tests/test_verify_m008_s05_ios_integration_contract.py` with pytest tests that:
1. Assert MainTabView uses native TabView with four Label tab items (from S02)
2. Assert HomeView contains QR entry CTA and credit-card balance presentation (from S03)
3. Assert TransactionsView has filter-only chips (no search bar) and QR Pay/Card Pay/Load taxonomy (from S04)
4. Assert BudgetView references budget endpoints (from S01)
5. Assert SettingsView has theme+accent controls only (from S04)
6. Assert no forbidden markers: no StitchTabShell, no search bar in transactions, no fullscreen-stitch elements
Name the test file correctly so it is picked up by pytest conventions.
  - Estimate: 45min
  - Files: tests/test_verify_m008_s05_ios_integration_contract.py
  - Verify: rtk proxy python -m pytest -q tests/test_verify_m008_s05_ios_integration_contract.py → all tests pass
- [ ] **T03: Run S05 verifier and close slice** — 1. Run `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s05.sh` and confirm all phases pass.
2. Run `rtk proxy python -m pytest -q tests/test_verify_m008_s05_ios_integration_contract.py` and confirm all tests pass.
3. Write S05-SUMMARY.md with oneLiner, narrative, verification evidence.
4. Write S05-UAT.md with test cases and pass/fail verdicts.
5. Use `gsd_slice_complete` to close the slice with `overall_verdict=PASS` and record requirements advanced/validated.
  - Estimate: 30min
  - Files: .gsd/milestones/M008-l1ngya/slices/S05/S05-SUMMARY.md, .gsd/milestones/M008-l1ngya/slices/S05/S05-UAT.md
  - Verify: All phases in verify-m008-s05.sh pass; all integration contract tests pass; slice complete recorded in DB
