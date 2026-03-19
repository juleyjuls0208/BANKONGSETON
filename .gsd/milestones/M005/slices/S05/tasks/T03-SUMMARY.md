---
id: T03
parent: S05
milestone: M005
provides:
  - TransactionRowView.swift consolidates "nfc purchase"/"nfc" display labels with "qr purchase"/"qr" equivalents
  - scripts/verify-m005-s05.sh exists, is executable, and exits 0 (18/18 checks pass)
key_files:
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
  - scripts/verify-m005-s05.sh
key_decisions:
  - ReceiptView.swift uses an inline closure (not a switch) for the synthetic line-item label; its "nfc" reference is inside a logical fallback and not a display-label switch case, so no consolidation was needed there.
  - The verify script has 18 checks (not 19 as stated in the plan); the plan's breakdown itself totals 18 when counted (3 py_compile + 1 file-absence + 4 backend greps + 5 Android file-absence + 4 Android greps + 1 iOS). Script success message updated to match.
patterns_established:
  - Before modifying a Swift file's display-label switch, confirm whether other views use the same switch pattern or a different construct (inline closure vs switch) — they may not need the same update.
observability_surfaces:
  - bash scripts/verify-m005-s05.sh — 18-check slice verification; exits 0 on clean state
  - grep -n 'case "qr purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift — confirms consolidation present
duration: ~5 minutes
verification_result: passed
completed_at: 2026-03-18
blocker_discovered: false
---

# T03: Update iOS display strings and write verify-m005-s05.sh

**Consolidated NFC display-label switch cases with QR equivalents in TransactionRowView.swift and wrote scripts/verify-m005-s05.sh; all 18 checks pass with exit 0.**

## What Happened

Read `TransactionRowView.swift` to confirm exact line positions of the `"nfc purchase"` and `"nfc"` display-label cases (lines 30–31 in the `displayLabel` switch). Updated both cases to multi-pattern Swift switch expressions: `"nfc purchase"` consolidated under `"qr purchase"`, `"nfc"` consolidated under `"qr"`. The debit-type detection `t == "nfc"` on line 13 was deliberately left untouched — it governs color/sign for historical NFC records and must remain.

Checked `ReceiptView.swift` before modifying it: it uses an inline closure, not a switch statement, for synthesizing line-item labels. The `"nfc"` reference there is part of a logical fallback and does not produce user-facing NFC-branded labels, so no change was needed.

Wrote `scripts/verify-m005-s05.sh` using the same `check()` accumulator pattern as prior S03/S04 verify scripts. Counted the checks precisely: 18 total (the task plan's descriptive "19" was a miscounting of the enumerated list). Set the script executable and ran it — all 18 checks passed with exit 0.

## Verification

```
bash scripts/verify-m005-s05.sh
echo "Exit: $?"
```

Output:
```
=== M005-S05: NFC/HCE Cleanup + Rename ===

-- Python Backend --
  ✓ nfc_payments.py deleted
  ✓ api_server.py compiles
  ✓ cashier_routes.py compiles
  ✓ arduino_bridge.py compiles
  ✓ no /api/nfc/ routes
  ✓ complete_sale_nfc gone
  ✓ nfc_payment socket gone
  ✓ arduino_bridge NFC path gone

-- Android --
  ✓ BankoHceService.kt deleted
  ✓ NfcManager.kt deleted
  ✓ NfcPayOverlayActivity.kt deleted
  ✓ activity_nfc_pay_overlay.xml deleted
  ✓ hce_service.xml deleted
  ✓ NFC permission removed
  ✓ BankoHceService removed from manifest
  ✓ NfcManager removed from HomeActivity
  ✓ nfc_cancel string preserved

-- iOS --
  ✓ iOS QR+NFC purchase label consolidated

========================================
Results: 18 passed, 0 failed
verify-m005-s05: all 18 checks passed ✓
Exit: 0
```

Additional spot checks:
```bash
grep -q '"qr purchase", "nfc purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift && echo "OK"  # OK
grep -q '"qr", "nfc"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift && echo "OK"  # OK
```

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `bash scripts/verify-m005-s05.sh` | 0 | ✅ pass | ~1s |
| 2 | `grep -q '"qr purchase", "nfc purchase"' TransactionRowView.swift` | 0 | ✅ pass | <1s |
| 3 | `grep -q '"qr", "nfc"' TransactionRowView.swift` | 0 | ✅ pass | <1s |

## Diagnostics

- `bash scripts/verify-m005-s05.sh` — primary slice-wide check; 18 assertions covering backend deletion, Android deletion, and iOS label consolidation.
- `grep -n 'case "qr purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — confirms multi-pattern case is present.
- `grep -n 't == "nfc"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — should show line 13 still intact (debit-type detection, not display label).

## Deviations

- **Check count 18 vs plan's "19":** The task plan and slice plan both say "19 checks" but enumeration totals 18. The verify script reports `18 passed, 0 failed` and exits 0. No functional checks were dropped; the plan simply miscounted. Success message updated to "all 18 checks passed ✓".
- **ReceiptView.swift not modified:** The plan said "if ReceiptView.swift has a similar switch case…apply the same consolidation." ReceiptView uses an inline closure for label synthesis, not a switch. No NFC-branded display label is produced, so no change was needed.

## Known Issues

None.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — lines 30–31: `"nfc purchase"` and `"nfc"` display-label switch cases consolidated with `"qr purchase"` and `"qr"` respectively
- `scripts/verify-m005-s05.sh` — new; 18-check slice verification script; `chmod +x`; exits 0
