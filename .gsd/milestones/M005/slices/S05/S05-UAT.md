---
id: S05
parent: M005
milestone: M005
uat_type: artifact-driven
---

# S05: NFC/HCE Cleanup + Rename — UAT

**Milestone:** M005
**Written:** 2026-03-18

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S05's proof level is "contract" — no runtime server required. All checks are file-absence tests, grep-absence tests, and `py_compile` syntax verification. The `scripts/verify-m005-s05.sh` script is the authoritative stopping condition and captures all 18 assertions.

## Preconditions

- Working directory is the M005 worktree root: `C:/Users/admin/Desktop/projects/BANKONGSETON/.gsd/worktrees/M005`
- Python 3 is available at `python` or `python3` in PATH
- `bash` is available (Git Bash or WSL on Windows)
- The S01, S03, and S04 work is present in this worktree (all prior slice files exist)

## Smoke Test

```bash
bash scripts/verify-m005-s05.sh
echo "Exit code: $?"
```

**Expected:** Output ends with `Results: 18 passed, 0 failed` and exit code is `0`.

---

## Test Cases

### 1. verify-m005-s05.sh exits 0 with 18/18 checks

```bash
bash scripts/verify-m005-s05.sh
```

**Expected output (all lines must appear):**
```
  ✓ nfc_payments.py deleted
  ✓ api_server.py compiles
  ✓ cashier_routes.py compiles
  ✓ arduino_bridge.py compiles
  ✓ no /api/nfc/ routes
  ✓ complete_sale_nfc gone
  ✓ nfc_payment socket gone
  ✓ arduino_bridge NFC path gone
  ✓ BankoHceService.kt deleted
  ✓ NfcManager.kt deleted
  ✓ NfcPayOverlayActivity.kt deleted
  ✓ activity_nfc_pay_overlay.xml deleted
  ✓ hce_service.xml deleted
  ✓ NFC permission removed
  ✓ BankoHceService removed from manifest
  ✓ NfcManager removed from HomeActivity
  ✓ nfc_cancel string preserved
  ✓ iOS QR+NFC purchase label consolidated
Results: 18 passed, 0 failed
```

**Exit code: 0**

---

### 2. Python backend files compile clean

```bash
python -m py_compile backend/api/api_server.py && echo "api_server OK"
python -m py_compile backend/dashboard/cashier/cashier_routes.py && echo "cashier_routes OK"
python -m py_compile backend/dashboard/arduino_bridge.py && echo "arduino_bridge OK"
```

**Expected:** All three print their "OK" message; no SyntaxError output; all exit 0.

---

### 3. nfc_payments.py is absent

```bash
[ ! -f backend/nfc_payments.py ] && echo "ABSENT" || echo "STILL PRESENT — FAIL"
```

**Expected:** prints `ABSENT`

---

### 4. No NFC routes remain in api_server.py

```bash
grep -n '/api/nfc/' backend/api/api_server.py && echo "FAIL: NFC route found" || echo "CLEAN"
```

**Expected:** prints `CLEAN` (grep finds nothing, exits 1, `||` branch runs)

---

### 5. complete_sale_nfc is gone from cashier_routes.py

```bash
grep -n 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py && echo "FAIL" || echo "CLEAN"
```

**Expected:** prints `CLEAN`

---

### 6. nfc_payment socket handler gone from cashier_index.html

```bash
grep -n 'nfc_payment' backend/dashboard/cashier/templates/cashier_index.html && echo "FAIL" || echo "CLEAN"
```

**Expected:** prints `CLEAN`

---

### 7. arduino_bridge.py has no NFC queue infrastructure

```bash
grep -n '_QueuedPayment\|_post_nfc_payment\|import queue\|NFC|\|ERROR|' backend/dashboard/arduino_bridge.py && echo "FAIL" || echo "CLEAN"
```

**Expected:** prints `CLEAN`

---

### 8. android.permission.NFC is absent from AndroidManifest.xml

```bash
grep -n 'android.permission.NFC' mobile/student_app_v2/app/src/main/AndroidManifest.xml && echo "FAIL" || echo "CLEAN"
```

**Expected:** prints `CLEAN`

---

### 9. All 5 Android NFC/HCE files are absent

```bash
for f in \
  "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt" \
  "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt" \
  "mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt" \
  "mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml" \
  "mobile/student_app_v2/app/src/main/res/xml/hce_service.xml"; do
  [ ! -f "$f" ] && echo "ABSENT: $f" || echo "FAIL — PRESENT: $f"
done
```

**Expected:** Five `ABSENT:` lines, zero `FAIL` lines.

---

### 10. nfc_cancel string preserved in strings.xml

```bash
grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml && echo "PRESENT (correct)" || echo "FAIL — MISSING"
```

**Expected:** prints `PRESENT (correct)`. This string is referenced by `activity_qr_pay.xml` from S04 and must not be absent.

---

### 11. iOS display-label switch consolidates "nfc purchase" with "qr purchase"

```bash
grep -n 'case "qr purchase", "nfc purchase"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
```

**Expected:** One matching line, e.g.:
```
30:        case "qr purchase", "nfc purchase": return "QR Purchase"
```

---

### 12. iOS display-label switch consolidates "nfc" with "qr"

```bash
grep -n 'case "qr", "nfc"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
```

**Expected:** One matching line, e.g.:
```
31:        case "qr", "nfc":                  return "QR Payment"
```

---

### 13. iOS debit-type detection for historical NFC records preserved

```bash
grep -n 't == "nfc"' mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
```

**Expected:** Exactly one line (around line 13) showing the debit-type check. This must NOT have been removed — it governs amount sign/color for historical NFC records.

---

### 14. Broad backend grep — zero dead NFC identifiers

```bash
grep -rn 'nfc_payments\|complete_sale_nfc\|completeNFCSale\|_QueuedPayment\|_post_nfc_payment' backend/ 2>/dev/null | wc -l
```

**Expected:** `0`

---

### 15. Broad Android grep — zero dead NFC class references

```bash
grep -rn 'NfcManager\|BankoHceService\|NfcPayOverlayActivity\|activateNfcPayButton\|nfcPayLauncher\|action_nfc_pay\|nfc_receipt_label' \
  mobile/student_app_v2/app/src/main/ 2>/dev/null | wc -l
```

**Expected:** `0`

---

## Edge Cases

### "nfc" historical-type references must survive in HomeActivity.kt

```bash
grep -c '"nfc"' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
```

**Expected:** `3` (the three transaction-filter type-list references at lines ~224, ~322, ~336 that handle display of historical NFC transactions). These are NOT dead code.

---

### activity_home.xml must not contain activateNfcPayButton

```bash
grep -q 'activateNfcPayButton' mobile/student_app_v2/app/src/main/res/layout/activity_home.xml && echo "FAIL" || echo "CLEAN"
```

**Expected:** prints `CLEAN`. This block was added as an unplanned deviation — AAPT2 would fail the build if it were still present after `@string/action_nfc_pay` was deleted.

---

### ReceiptActivity.kt uses inline "Payment" not R.string.nfc_receipt_label

```bash
grep -n 'nfc_receipt_label' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt && echo "FAIL" || echo "CLEAN"
grep -n '"Payment"' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt
```

**Expected:** First grep prints `CLEAN`; second grep shows the inline `"Payment"` string on the relevant line.

---

## Failure Signals

- `verify-m005-s05.sh` exits non-zero or reports any `✗` check — indicates a file is present that should be absent, or a string that should be gone is still in place
- `py_compile` prints `SyntaxError: ..., line N` — an edit accidentally removed a closing brace or colon somewhere; the line number pinpoints the location
- `grep -rn 'nfc_payments|...' backend/ | wc -l` returns non-zero — a dead NFC identifier was missed; grep output shows the exact file and line
- `grep -q 'nfc_cancel' strings.xml` exits 1 — the `nfc_cancel` string was accidentally removed; `activity_qr_pay.xml` would fail to compile

## Requirements Proved By This UAT

- R032 — Dead NFC/HCE Code Removed: all 18 checks in the verify script confirm the listed deletions are complete and the Python files remain syntactically valid; both apps would build without NFC/HCE references

## Not Proven By This UAT

- Actual Android build (`./gradlew assembleDebug`) — not run due to environment constraints; the AAPT2-breaking resources were identified and removed via grep, but a real Gradle build is the authoritative Android proof
- Actual iOS build (`xcodebuild`) — not run; Swift file changes are verified by grep and the verify script; a real build would catch any missed symbol references
- Runtime behavior — no server was started; the QR payment flow is proven by S03/S04 UAT, not this slice

## Notes for Tester

- The three `"nfc"` type-string references in `HomeActivity.kt` transaction filter logic are **intentional survivors** — they display historical NFC transactions correctly and must not be deleted. The verify script does not check for them (they are live code, not dead code).
- The `nfc_cancel` string in strings.xml is also an **intentional survivor** — it is referenced by `activity_qr_pay.xml` from S04. The verify script explicitly checks its presence.
- The iOS `t == "nfc"` check on line 13 of `TransactionRowView.swift` is also **intentional** — it governs debit amount display color/sign for historical records and was deliberately not consolidated with the display-label cases.
- If running on Windows, use Git Bash for `bash scripts/verify-m005-s05.sh` — the script uses POSIX constructs that don't work in CMD or PowerShell.
