# S05: NFC/HCE Cleanup + Rename

**Goal:** Delete all NFC/HCE dead code — `nfc_payments.py`, 4 backend routes, `complete_sale_nfc()`, NFC socket handler, NFC delivery infrastructure in `arduino_bridge.py`, 5 Android NFC files, dead NFC code in Android sources, and NFC manifest entries — leaving the codebase with no active NFC/HCE references.
**Demo:** `bash scripts/verify-m005-s05.sh` exits 0; `python -m py_compile` exits 0 on `api_server.py`, `cashier_routes.py`, and `arduino_bridge.py`; Android and iOS no longer import or declare any NFC/HCE identifiers in active code paths.

## Must-Haves

- `nfc_payments.py` deleted; no `/api/nfc/` routes in `api_server.py`; no `complete_sale_nfc` in `cashier_routes.py`; no `socket.on('nfc_payment')` in `cashier_index.html`; NFC delivery path gone from `arduino_bridge.py`; `python -m py_compile` exits 0 on all three Python files
- `BankoHceService.kt`, `NfcManager.kt`, `NfcPayOverlayActivity.kt`, `activity_nfc_pay_overlay.xml`, `hce_service.xml` deleted; dead NFC code removed from `HomeActivity.kt`, `ApiClient.kt`, `Models.kt`, `AndroidManifest.xml`, `activity_settings.xml`, `strings.xml`; **`nfc_cancel` string preserved** (used by `activity_qr_pay.xml`)
- iOS `TransactionRowView.swift` display-string cases consolidated to include both `"qr"` and `"nfc"` history types
- `bash scripts/verify-m005-s05.sh` exits 0

## Observability / Diagnostics

### Runtime Signals After Cleanup
- `arduino_bridge.py` `_parse_line()` only emits `card_uid_received` and `arduino_pong` log events; any unrecognised prefix triggers a `debug` line — NFC-related log lines are gone by design.
- `api_server.py` 404s any request to `/api/nfc/*` routes (Flask returns 404 automatically after removal).
- `cashier_routes.py` 404s any POST to `/api/complete-sale-nfc` (route deleted).

### Inspection Surfaces
- `python -m py_compile <file>` — immediate syntax proof on any of the three Python files.
- `grep -r 'nfc\|NFC\|HCE' backend/` — should return only allowed strings (e.g., log messages that mention "NFC" in comments/docstrings of kept code); no live route, import, or handler references.
- `bash scripts/verify-m005-s05.sh` — slice-wide stopping condition (written in T03).

### Failure Visibility
- If a deletion accidentally removes a `def`, `:`, or closing bracket, `python -m py_compile` produces `SyntaxError: <file>, line N` pinpointing the exact location.
- If an NFC grep check fails, the grep output shows the exact file and line still containing the identifier.
- If `nfc_payments.py` is still present, `[ ! -f backend/nfc_payments.py ]` exits 1 with no output (check the exit code).

### Redaction Constraints
- No secrets are stored in or emitted by NFC code paths — redaction is not applicable.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `python -m py_compile backend/api/api_server.py && python -m py_compile backend/dashboard/cashier/cashier_routes.py && python -m py_compile backend/dashboard/arduino_bridge.py` — all exit 0 (confirmed in T01)
- `bash scripts/verify-m005-s05.sh` exits 0 (written and run in T03)
- **Failure-path check:** `grep -rn 'nfc_payments\|complete_sale_nfc\|completeNFCSale\|_QueuedPayment\|_post_nfc_payment' backend/ 2>/dev/null | wc -l` — must output `0`; any non-zero result surfaces the exact file and line still containing a dead NFC identifier

## Tasks

- [x] **T01: Delete nfc_payments.py and scrub NFC dead code from Python backend** `est:45m`
  - Why: Removes the server-side NFC surface — Python module, 4 API routes, `complete_sale_nfc()`, PhoneUID fallback block, NFC delivery infrastructure in `arduino_bridge.py`, and the `nfc_payment` socket handler in `cashier_index.html`. Highest line-count deletion in S05; `py_compile` confirms correctness immediately.
  - Files: `backend/nfc_payments.py`, `backend/api/api_server.py`, `backend/dashboard/cashier/cashier_routes.py`, `backend/dashboard/cashier/templates/cashier_index.html`, `backend/dashboard/arduino_bridge.py`
  - Do: See T01-PLAN.md
  - Verify: `python -m py_compile backend/api/api_server.py && python -m py_compile backend/dashboard/cashier/cashier_routes.py && python -m py_compile backend/dashboard/arduino_bridge.py`; `[ ! -f backend/nfc_payments.py ]`; `! grep -q '/api/nfc/' backend/api/api_server.py`; `! grep -q 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py`; `! grep -q "nfc_payment" backend/dashboard/cashier/templates/cashier_index.html`
  - Done when: All `py_compile` calls exit 0; `nfc_payments.py` absent; no NFC route, function, or socket handler identifiers remain in any of the five files

- [x] **T02: Delete NFC Android files and scrub dead code from Android sources** `est:45m`
  - Why: Removes all HCE/NFC Android dead code — 3 Kotlin files, 2 XML resource files, dead NFC members in `HomeActivity.kt`, NFC API declarations in `ApiClient.kt` and `Models.kt`, NFC permission/feature/activity/service entries in `AndroidManifest.xml`, NFC UI section in `activity_settings.xml`, and NFC strings. The `nfc_cancel` string must be preserved.
  - Files: `BankoHceService.kt`, `NfcManager.kt`, `NfcPayOverlayActivity.kt`, `activity_nfc_pay_overlay.xml`, `hce_service.xml` (deleted); `HomeActivity.kt`, `ApiClient.kt`, `Models.kt`, `AndroidManifest.xml`, `activity_settings.xml`, `strings.xml` (edited)
  - Do: See T02-PLAN.md
  - Verify: `[ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt ]`; `! grep -q 'android.permission.NFC' mobile/student_app_v2/app/src/main/AndroidManifest.xml`; `! grep -q 'NfcManager' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt`; `grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml`
  - Done when: All 5 NFC files absent; NFC manifest entries gone; dead NFC identifiers removed from HomeActivity/ApiClient/Models; `nfc_cancel` string still present in strings.xml

- [x] **T03: Update iOS display strings and write verify-m005-s05.sh** `est:20m`
  - Why: iOS `TransactionRowView.swift` has display-string switch cases for `"nfc purchase"` and `"nfc"` types that should be consolidated with their `"qr"` equivalents so both historical NFC transactions and new QR transactions display correctly. The verify script is the slice's objective stopping condition.
  - Files: `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`, `scripts/verify-m005-s05.sh`
  - Do: See T03-PLAN.md
  - Verify: `bash scripts/verify-m005-s05.sh`
  - Done when: `bash scripts/verify-m005-s05.sh` exits 0

## Files Likely Touched

- `backend/nfc_payments.py` — deleted
- `backend/api/api_server.py`
- `backend/dashboard/cashier/cashier_routes.py`
- `backend/dashboard/cashier/templates/cashier_index.html`
- `backend/dashboard/arduino_bridge.py`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — deleted
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — deleted
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt` — deleted
- `mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml` — deleted
- `mobile/student_app_v2/app/src/main/res/xml/hce_service.xml` — deleted
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt`
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt`
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml`
- `mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml`
- `mobile/student_app_v2/app/src/main/res/values/strings.xml`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
- `scripts/verify-m005-s05.sh` — new
