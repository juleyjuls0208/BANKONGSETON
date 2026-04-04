# S04: Transactions/Settings Minimalist Scope Restoration — UAT

**Milestone:** M008-l1ngya
**Written:** 2026-04-02T05:09:16.916Z

## Smoke Test
```
rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s04.sh
```
Expected: all phases pass and final line reports `[verify-m008-s04] status=passed`.

## Test Cases

1. **Transactions filter-only (no search)**: `rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py::test_transactions_is_filter_only_with_no_searchable_surface` → pass
2. **QR continuity seam preserved**: `rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py::test_transactions_qr_continuity_seam_remains_intact_after_rollback` → pass
3. **Receipt+load-more actionable**: `rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py::test_transactions_receipt_and_load_more_remain_actionable` → pass
4. **Settings scoped cards (no personal info)**: `rtk proxy python -m pytest -q tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py::test_settings_appearance_and_account_cards_render_without_personal_info_card` → pass
5. **S07 continuity contract**: `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py` → pass
6. **S05 settings design contract**: `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_design_contract.py` → pass
7. **Full S04 verifier**: `rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s04.sh` → all phases pass, `[verify-m008-s04] status=passed`
