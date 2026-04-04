# S05: Integrated UX Closure + Requirement Validation — UAT

**Milestone:** M008-l1ngya
**Written:** 2026-04-04T09:47:07.701Z

## Test Cases

### 1. S05 integration contract — 17 cross-surface tests
`rtk proxy python -m pytest -q tests/test_verify_m008_s05_ios_integration_contract.py`

All 17 tests pass:
1. MainTabView native tabs (TabView + 4 Label items + 4 .tag markers) ✅
2. Session-expired alert preserved ✅
3. Home QR entry CTA ✅
4. Home credit-card hero ✅
5. Home M007 scaffolding removed ✅
6. Home QR continuity seam ✅
7. Transactions filter-only, no search ✅
8. Transactions QR Pay/Card Pay/Load taxonomy ✅
9. Transactions QR continuity seam ✅
10. Transactions receipt + load-more ✅
11. BudgetView endpoint wiring ✅
12. Budget progress + limit editor ✅
13. Settings appearance + account cards ✅
14. Settings no personal info card ✅
15. No StitchTabShell in MainTabView (forbidden) ✅
16. No searchable in Transactions (forbidden) ✅
17. No fullscreen-stitch in Home (forbidden) ✅

### 2. Chained S01-S04 verifier — all 4 phases pass
`rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s05.sh`

- s01-budget-contract: ✅ passed
- s02-tabview-rollback: ✅ passed
- s03-home-qr-rollback: ✅ passed
- s04-transactions-settings-rollback: ✅ passed

S04's nested regression chain verified: S03→S02→S01 dependency chain intact.
