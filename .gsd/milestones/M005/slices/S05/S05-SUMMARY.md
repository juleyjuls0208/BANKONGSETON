---
id: S05
parent: M005
milestone: M005
provides:
  - backend/nfc_payments.py deleted — Python NFC module fully gone
  - /api/nfc/register|status|unregister|pay routes removed from api_server.py
  - complete_sale_nfc() and PhoneUID VirtualCards fallback removed from cashier_routes.py
  - socket.on('nfc_payment') handler and completeNFCSale() removed from cashier_index.html
  - NFC delivery infrastructure (_QueuedPayment, queue constants, NFC parse branches, retry thread) removed from arduino_bridge.py
  - backend/tests/test_arduino_bridge_nfc.py deleted (dead test file)
  - 5 Android NFC/HCE files deleted: BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml
  - Dead NFC code removed from HomeActivity.kt, ApiClient.kt, Models.kt, AndroidManifest.xml, activity_settings.xml, strings.xml, activity_home.xml, ReceiptActivity.kt
  - nfc_cancel string preserved in strings.xml (used by activity_qr_pay.xml)
  - iOS TransactionRowView.swift: "nfc purchase"/"nfc" display cases consolidated with "qr purchase"/"qr"
  - scripts/verify-m005-s05.sh written and passing: 18/18 checks
requires:
  - slice: S01
    provides: arduino/bankongseton_r4/ firmware exists; bankongseton_nfc_r3 cleaned of PN532 refs
  - slice: S03
    provides: /api/qr/* routes confirmed replacing /api/nfc/*; complete_sale logic confirmed clean
  - slice: S04
    provides: Android and iOS confirmed not importing NfcManager/BankoHceService; QR payment confirmed working
affects: []
key_files:
  - backend/nfc_payments.py (deleted)
  - backend/api/api_server.py
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/cashier/templates/cashier_index.html
  - backend/dashboard/arduino_bridge.py
  - backend/tests/test_arduino_bridge_nfc.py (deleted)
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt (deleted)
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt (deleted)
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt (deleted)
  - mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml (deleted)
  - mobile/student_app_v2/app/src/main/res/xml/hce_service.xml (deleted)
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt
  - mobile/student_app_v2/app/src/main/AndroidManifest.xml
  - mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml
  - mobile/student_app_v2/app/src/main/res/layout/activity_home.xml
  - mobile/student_app_v2/app/src/main/res/values/strings.xml
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift
  - scripts/verify-m005-s05.sh (new)
key_decisions:
  - Deleted backend/tests/test_arduino_bridge_nfc.py alongside the production NFC code it tested — dead tests that reference deleted methods cause AttributeError on import; removing them keeps the test suite green
  - Deleted activateNfcPayButton block from activity_home.xml (not in plan) — AAPT2 resolves @string/ references at build time regardless of android:visibility="gone"; leaving it would cause a build error after action_nfc_pay was removed
  - Replaced getString(R.string.nfc_receipt_label) in ReceiptActivity.kt with inline "Payment" — string deleted, no suitable generic string existed; "Payment" is correct for any non-itemized transaction type
  - ReceiptView.swift not modified — uses an inline closure for label synthesis, not a switch; the "nfc" reference there is a logical fallback, not a user-facing display label
  - iOS debit-type check (t == "nfc" on line 13 of TransactionRowView.swift) deliberately preserved — governs amount color/sign for historical NFC records; this is not a display-label case
patterns_established:
  - When removing Android string resources, grep all *.xml and *.kt for the resource ID before deleting — AAPT2 resolves @string/ at build time even in visibility="gone" elements
  - After removing a Kotlin feature block, audit imports for anything exclusively used by the removed code
  - Remove dead test files alongside the production code they test — preserves a green test suite and avoids import-time AttributeErrors
observability_surfaces:
  - bash scripts/verify-m005-s05.sh — 18-check slice verification; primary stopping condition
  - python -m py_compile backend/api/api_server.py (and cashier_routes.py, arduino_bridge.py) — immediate syntax proof
  - grep -rn 'nfc_payments|complete_sale_nfc|completeNFCSale|_QueuedPayment|_post_nfc_payment' backend/ — must return 0 lines
  - grep -rn 'NfcManager|BankoHceService|activateNfcPayButton' mobile/student_app_v2/app/src/main/ — must return 0 lines
drill_down_paths:
  - .gsd/milestones/M005/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S05/tasks/T02-SUMMARY.md
  - .gsd/milestones/M005/slices/S05/tasks/T03-SUMMARY.md
duration: ~40m total (T01: 20m, T02: 15m, T03: 5m)
verification_result: passed
completed_at: 2026-03-18
---

# S05: NFC/HCE Cleanup + Rename

**All NFC/HCE dead code deleted from backend, Android, and iOS; scripts/verify-m005-s05.sh exits 0 with 18/18 checks passing.**

## What Happened

S05 was a pure deletion slice — no new code shipped, no new features added. The goal was to remove all traces of the phone NFC/HCE payment system that the QR payment flow (S03/S04) replaced.

**T01 — Python backend:** Deleted `backend/nfc_payments.py` and removed all downstream references: four `/api/nfc/*` route functions from `api_server.py`, `complete_sale_nfc()` and the PhoneUID VirtualCards fallback block from `cashier_routes.py`, the `socket.on('nfc_payment')` handler and `completeNFCSale()` from `cashier_index.html`, and the full NFC delivery infrastructure from `arduino_bridge.py` (`_QueuedPayment` dataclass, queue constants, retry thread, `_post_nfc_payment`, `_enqueue_payment`, `_retry_loop`, `_drain_queue`, `queue_status`, the `NFC|` and `ERROR|` parse branches, and `import queue`). An unplanned deletion: `backend/tests/test_arduino_bridge_nfc.py` — a test file that exclusively tested the deleted NFC methods and would have caused `AttributeError` on import. All three Python files pass `py_compile` at exit 0.

**T02 — Android:** Deleted 5 NFC/HCE files (BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml) and scrubbed dead code from 8 source files. The task plan listed 6 files to edit; execution surfaced 2 more:
- `activity_home.xml` contained an `activateNfcPayButton` LinearLayout with `android:visibility="gone"` referencing `@string/action_nfc_pay` (deleted from strings.xml). AAPT2 resolves all `@string/` references at build time regardless of visibility — the block had to go.
- `ReceiptActivity.kt` used `getString(R.string.nfc_receipt_label)` for fallback receipt rendering. The string was deleted; replaced with inline `"Payment"`.

In `HomeActivity.kt`, the three `"nfc"` type-string references in the transaction-filter logic were deliberately preserved — they handle historical NFC records in the transaction list and are not HCE functionality. Dead imports (`android.app.Activity`, `ActivityResultContracts`) introduced by the `nfcPayLauncher` block removal were cleaned up. The `nfc_cancel` string in strings.xml was preserved — it is referenced by `activity_qr_pay.xml` from S04.

**T03 — iOS + verify script:** In `TransactionRowView.swift`, the `displayLabel` switch's `case "nfc purchase"` and `case "nfc"` were merged into multi-pattern cases with their `"qr"` equivalents, so historical NFC transactions render with the same QR Purchase / QR Payment labels going forward. The debit-type detection on line 13 (`t == "nfc"`) was left intact — it governs amount sign/color for historical records.

`ReceiptView.swift` was inspected but not modified — it uses an inline closure for label synthesis, not a switch statement; the `"nfc"` reference there is a logical fallback, not a display-label case.

`scripts/verify-m005-s05.sh` was written with 18 checks across three sections (Python backend, Android, iOS). The slice plan's stated "19" checks was a counting error in the plan itself; the script correctly has 18. All 18 pass.

## Verification

All verification is contract-level (no runtime required):

```
bash scripts/verify-m005-s05.sh                         → 18/18 passed, exit 0

python -m py_compile backend/api/api_server.py          → exit 0
python -m py_compile backend/dashboard/cashier/cashier_routes.py → exit 0
python -m py_compile backend/dashboard/arduino_bridge.py → exit 0

grep -rn 'nfc_payments|complete_sale_nfc|completeNFCSale|_QueuedPayment|_post_nfc_payment' backend/ | wc -l  → 0
grep -rn 'NfcManager|BankoHceService|activateNfcPayButton' mobile/student_app_v2/app/src/main/ | wc -l       → 0
```

## Requirements Advanced

- R032 — Dead NFC/HCE Code Removed: all listed artifacts deleted and verified absent by verify script

## Requirements Validated

- R032 — `bash scripts/verify-m005-s05.sh` exits 0 with 18/18 checks; `py_compile` exits 0 on all three Python files; all 5 Android NFC files absent; NFC manifest entries gone; `nfc_cancel` preserved; iOS display labels consolidated

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

1. **activity_home.xml (unplanned):** The `activateNfcPayButton` block (visibility="gone") referenced `@string/action_nfc_pay` which was deleted from strings.xml. AAPT2 would have raised a build error. Block deleted.

2. **ReceiptActivity.kt (unplanned):** Used `getString(R.string.nfc_receipt_label)` which was deleted. Replaced with inline `"Payment"` to keep receipt fallback rendering functional.

3. **backend/tests/test_arduino_bridge_nfc.py (unplanned):** Dead test file testing deleted NFC methods. Deleted alongside the production code to keep the test suite importable.

4. **wsgi.py comment (cosmetic):** Comment at line 26 mentioned `nfc_payments`; updated to remove the stale reference.

5. **Verify script check count 18 vs plan's "19":** The plan's enumeration totals 18 when counted; the script correctly reports 18. No check was dropped.

6. **ReceiptView.swift not modified:** Plan said "if ReceiptView.swift has a similar switch case, apply the same consolidation." It does not use a switch — it uses an inline closure. No change needed.

## Known Limitations

None. The slice's proof level was "contract" and all contract checks pass. No runtime verification was scoped.

## Follow-ups

None. All NFC/HCE code is gone. The `"nfc"` historical-type references in `HomeActivity.kt` and `TransactionRowView.swift` are intentional survivors — they allow existing transaction history rows (from before M005) to display correctly without a data migration.

## Files Created/Modified

- `backend/nfc_payments.py` — **deleted**
- `backend/api/api_server.py` — removed NFC import block (NFCService, ensure_virtual_cards_sheet) and four NFC route functions
- `backend/dashboard/cashier/cashier_routes.py` — removed complete_sale_nfc(), PhoneUID VirtualCards fallback, NFC debug print
- `backend/dashboard/cashier/templates/cashier_index.html` — removed socket.on('nfc_payment') and completeNFCSale()
- `backend/dashboard/arduino_bridge.py` — removed NFC delivery infrastructure, _QueuedPayment, queue constants, import queue, NFC/ERROR parse branches
- `backend/tests/test_arduino_bridge_nfc.py` — **deleted** (dead test file)
- `backend/api/wsgi.py` — updated comment to remove nfc_payments reference
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — **deleted**
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — **deleted**
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt` — **deleted**
- `mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml` — **deleted**
- `mobile/student_app_v2/app/src/main/res/xml/hce_service.xml` — **deleted**
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — removed NFC fields/launcher/functions/dead imports; preserved "nfc" historical-type refs
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — removed registerNfcDevice, unregisterNfcDevice
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — removed NfcDeviceRequest, NfcUnregisterRequest, NfcRegisterResponse
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — removed NFC permission, uses-feature, NfcPayOverlayActivity, BankoHceService service block
- `mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml` — removed nfcSection block
- `mobile/student_app_v2/app/src/main/res/layout/activity_home.xml` — removed activateNfcPayButton block (unplanned; required for build)
- `mobile/student_app_v2/app/src/main/res/values/strings.xml` — removed NFC strings; nfc_cancel preserved
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt` — replaced nfc_receipt_label with inline "Payment"
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift` — consolidated "nfc purchase" and "nfc" display-label cases with "qr" equivalents
- `scripts/verify-m005-s05.sh` — **new**; 18-check slice verification; chmod +x; exits 0
- `.gsd/KNOWLEDGE.md` — two new knowledge entries (Android string resource grep rule; dead import cleanup rule)

## Forward Intelligence

### What the next slice should know
- The `"nfc"` transaction type string is preserved in Android and iOS transaction history display code — this is intentional for backward compatibility with historical records. It is not dead code.
- The `nfc_cancel` string in Android strings.xml is also live — it is referenced by `activity_qr_pay.xml` from S04 and must not be deleted in any future cleanup pass.
- M005 is now fully complete: RC522 firmware on both Arduinos, OLED + QR display on R4, QR payment backend, Android + iOS QR pay, and all NFC/HCE dead code removed.

### What's fragile
- `app.pending_qr_token` is in-memory Flask app state (set by S03). Single-worker PythonAnywhere deployment is the only reason this is safe — a multi-worker deployment would cause split-brain where one worker has the token and another doesn't.
- `ReceiptActivity.kt` now uses hardcoded `"Payment"` for the synthetic fallback line item on transactions with no line items. If a more specific label per payment type is ever needed, this will require a refactor.

### Authoritative diagnostics
- `bash scripts/verify-m005-s05.sh` — 18 checks, all documented, fastest way to confirm clean state after any future deletion or refactor touching these files
- `python -m py_compile backend/api/api_server.py` — immediate syntax proof; catches any edit that breaks the import chain

### What assumptions changed
- Task plan assumed 6 Android source files to edit; execution found 8. The extras (`activity_home.xml`, `ReceiptActivity.kt`) were found by a broad post-edit grep. The KNOWLEDGE.md entries document this pattern for future reference.
- ReceiptView.swift was assumed to need the same display-label switch consolidation as TransactionRowView.swift; it actually uses an inline closure, so no edit was needed.
