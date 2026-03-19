---
estimated_steps: 5
estimated_files: 2
---

# T03: Update iOS display strings and write verify-m005-s05.sh

**Slice:** S05 — NFC/HCE Cleanup + Rename
**Milestone:** M005

## Description

Update `TransactionRowView.swift` to consolidate the `"nfc purchase"` and `"nfc"` display-string cases with their `"qr purchase"` / `"qr"` equivalents. This ensures historical NFC transactions still display with correct labels while new QR transactions use the same formatted strings.

Then write `scripts/verify-m005-s05.sh` covering all backend and Android deletions from T01 and T02, plus the iOS display-string update. Run it to confirm exit 0.

## Steps

1. **Read `TransactionRowView.swift`** to find the exact switch/case blocks. The research doc identifies:
   - Around line 30–31: a case matching `"nfc purchase"` returning some label like `"NFC Purchase"`
   - Around line 30–31: a case matching `"nfc"` returning `"NFC Payment"`

2. **Update display-string cases in `TransactionRowView.swift`** — Consolidate the NFC cases with QR equivalents:
   - Change `case "nfc purchase": return "NFC Purchase"` → `case "qr purchase", "nfc purchase": return "QR Purchase"`
   - Change `case "nfc": return "NFC Payment"` → `case "qr", "nfc": return "QR Payment"`
   - Do NOT change `t == "nfc"` debit-type detection logic (line 13) — that is historical type detection for display color/sign, not a display label function.
   - If `ReceiptView.swift` has a similar switch case for `"nfc"` / `"nfc purchase"` display labels, apply the same consolidation there.
   - Verify: `grep -q '"qr purchase", "nfc purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`

3. **Write `scripts/verify-m005-s05.sh`** — Use the same `check()`-accumulator pattern as `verify-m005-s04.sh` (exit 1 only after all checks run, every failure visible in one invocation). Include the following checks:

   ```
   === M005-S05: NFC/HCE Cleanup + Rename ===

   -- Python Backend --
   [ ! -f backend/nfc_payments.py ]                                   "nfc_payments.py deleted"
   python -m py_compile backend/api/api_server.py                     "api_server.py compiles"
   python -m py_compile backend/dashboard/cashier/cashier_routes.py   "cashier_routes.py compiles"
   python -m py_compile backend/dashboard/arduino_bridge.py           "arduino_bridge.py compiles"
   ! grep -q '/api/nfc/' backend/api/api_server.py                    "no /api/nfc/ routes"
   ! grep -q 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py  "complete_sale_nfc gone"
   ! grep -q 'socket.on.*nfc_payment' backend/dashboard/cashier/templates/cashier_index.html  "nfc_payment socket gone"
   ! grep -q '_post_nfc_payment\|_QueuedPayment' backend/dashboard/arduino_bridge.py          "arduino_bridge NFC path gone"

   -- Android --
   [ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt ]    "BankoHceService.kt deleted"
   [ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt ]         "NfcManager.kt deleted"
   [ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt ] "NfcPayOverlayActivity.kt deleted"
   [ ! -f mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml ]             "activity_nfc_pay_overlay.xml deleted"
   [ ! -f mobile/student_app_v2/app/src/main/res/xml/hce_service.xml ]                             "hce_service.xml deleted"
   ! grep -q 'android.permission.NFC' mobile/student_app_v2/app/src/main/AndroidManifest.xml       "NFC permission removed"
   ! grep -q 'BankoHceService' mobile/student_app_v2/app/src/main/AndroidManifest.xml              "BankoHceService removed from manifest"
   ! grep -q 'NfcManager' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt  "NfcManager removed from HomeActivity"
   grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml                  "nfc_cancel string preserved"

   -- iOS --
   grep -q '"qr purchase", "nfc purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift  "iOS QR+NFC purchase label consolidated"
   ```

   That is 19 checks total. Script must be `chmod +x` and run from the repo root.

4. **Run `bash scripts/verify-m005-s05.sh`** from the working directory root and confirm it exits 0. If any check fails, fix the underlying issue (do not modify the script to skip the check).

5. **Confirm exit code:**
   ```bash
   bash scripts/verify-m005-s05.sh
   echo "Exit: $?"
   ```
   Expected: `Results: 19 passed, 0 failed` and `Exit: 0`.

## Must-Haves

- [ ] `TransactionRowView.swift` consolidates `"nfc purchase"` with `"qr purchase"` in the same case expression
- [ ] `TransactionRowView.swift` consolidates `"nfc"` with `"qr"` in the same case expression
- [ ] `scripts/verify-m005-s05.sh` exists and is executable
- [ ] Script covers: Python py_compile (3 files), nfc_payments.py absence, 4 backend grep checks, 5 Android file-absence checks, 4 Android grep checks including `nfc_cancel` preservation, 1 iOS label check
- [ ] `bash scripts/verify-m005-s05.sh` exits 0

## Verification

- `bash scripts/verify-m005-s05.sh` exits 0
- `grep -q '"qr purchase", "nfc purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` exits 0
- `grep -q '"qr", "nfc"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` exits 0

## Inputs

- T01 and T02 completed: all Python deletions done, all Android deletions done — the verify script checks these results
- Research doc: `TransactionRowView.swift` lines 30–31 have the `"nfc purchase"` and `"nfc"` display cases; line 13 `t == "nfc"` debit-type detection must not be changed
- Research doc: `ReceiptView.swift` may have a comment update only (line 55 is a comment); check if it has display-label switch cases for `"nfc"` — if so, apply the same consolidation
- S04 T03 summary: `QRScannerView.swift`, `QRPayView.swift`, and `QRPayViewModel.swift` are confirmed added — iOS QR flow is in place
- Verify script pattern from S03/S04: `check()` function prints `[PASS]`/`[FAIL]`, accumulates counts, exits 1 only if any failed; see `scripts/verify-m005-s04.sh` for the exact shell pattern to copy

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — `"nfc purchase"` and `"nfc"` cases consolidated with QR equivalents
- `scripts/verify-m005-s05.sh` — new; 19-check verification script; exits 0 on clean S05 state; `chmod +x`

## Observability Impact

**What changes are visible at runtime after this task:**
- iOS app: Historical `"nfc purchase"` transactions now render as "QR Purchase" in the transaction list; historical `"nfc"` transactions render as "QR Payment". The debit-type detection (red color, minus sign) is unchanged — `t == "nfc"` on line 13 still triggers debit styling.
- No server-side or backend signals change in this task.

**How a future agent inspects this task:**
- `grep -n 'case "qr purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — should show one line with both `"qr purchase"` and `"nfc purchase"` patterns.
- `grep -n 'case "qr"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — should show one line with both `"qr"` and `"nfc"` patterns.
- `bash scripts/verify-m005-s05.sh` — slice-wide stopping condition; exits 0 when all 18 checks pass.

**Failure state becomes visible as:**
- If the consolidation is reverted or broken, `grep -q '"qr purchase", "nfc purchase"' TransactionRowView.swift` exits non-zero, failing the iOS check in the verify script.
- If `t == "nfc"` on line 13 is accidentally modified, historical NFC transactions lose their red debit styling — detected by visual inspection of the transaction list for a transaction with type `"nfc"`.
- If the verify script itself is missing or non-executable, `bash scripts/verify-m005-s05.sh` returns a shell error immediately.
