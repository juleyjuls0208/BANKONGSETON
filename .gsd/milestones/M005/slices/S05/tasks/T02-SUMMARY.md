---
id: T02
parent: S05
milestone: M005
provides:
  - All 5 Android NFC/HCE files deleted (BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml)
  - Dead NFC code removed from HomeActivity.kt, ApiClient.kt, Models.kt, AndroidManifest.xml, activity_settings.xml, strings.xml, activity_home.xml, ReceiptActivity.kt
  - nfc_cancel string preserved in strings.xml
key_files:
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt
  - mobile/student_app_v2/app/src/main/AndroidManifest.xml
  - mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml
  - mobile/student_app_v2/app/src/main/res/layout/activity_home.xml
  - mobile/student_app_v2/app/src/main/res/values/strings.xml
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt
key_decisions:
  - Deleted activateNfcPayButton block from activity_home.xml (not in plan) — AAPT2 resolves @string references at build time regardless of android:visibility="gone", so leaving it would cause a build error after action_nfc_pay was removed from strings.xml
  - Replaced getString(R.string.nfc_receipt_label) in ReceiptActivity.kt with inline "Payment" — the string was deleted and no suitable existing generic string was available; "Payment" is descriptive and keeps ReceiptActivity functional for all non-itemized transactions
  - Removed dead imports (android.app.Activity, ActivityResultContracts) from HomeActivity.kt after nfcPayLauncher block removal
patterns_established:
  - When removing Android string resources, grep all *.xml and *.kt files for the resource ID before deleting — AAPT2 resolves @string/ references at build time even in hidden (visibility="gone") layout elements
  - After removing a feature block from Kotlin, audit imports for anything exclusively used by the removed code
observability_surfaces:
  - "grep -rn 'NfcManager|BankoHceService|nfc/register|activateNfcPayButton' mobile/student_app_v2/app/src/main/ — must return 0 lines"
  - "grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml — must exit 0 (string preserved for activity_qr_pay.xml)"
duration: ~15 min
verification_result: passed
completed_at: 2026-03-18
blocker_discovered: false
---

# T02: Delete NFC Android files and scrub dead code from Android sources

**Deleted 5 Android NFC/HCE files and removed all dead NFC code from 8 Android source files; nfc_cancel preserved, "nfc" historical-type filter references left intact.**

## What Happened

All five NFC/HCE files were deleted first (BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml).

`HomeActivity.kt` was edited to remove: the `activateNfcPayButton` and `nfcManager` field declarations, the `nfcPayLauncher` block, the `nfcManager = NfcManager.getInstance(this)` init in `onCreate`, the `activateNfcPayButton = findViewById(...)` binding, the `activateNfcPayButton.setOnClickListener` block, both `updateNfcButtonVisibility()` call sites (onCreate and onResume), the four dead NFC functions (`updateNfcButtonVisibility`, `onNfcPayClicked`, `showSetupPinDialog`, `showPinDialog`) and the `// ── NFC ─` section comment. Dead imports (`android.app.Activity`, `ActivityResultContracts`) were also removed since they were only used by the deleted `nfcPayLauncher` block. The `"nfc"` historical-type filter references at lines ~224, ~322, ~336 were left untouched as required.

`ApiClient.kt`: removed `registerNfcDevice` and `unregisterNfcDevice` suspend functions from the `BangkoApiService` interface.

`Models.kt`: removed `NfcDeviceRequest`, `NfcUnregisterRequest`, and `NfcRegisterResponse` data classes.

`AndroidManifest.xml`: removed `android.permission.NFC` permission, both `<uses-feature android:name="android.hardware.nfc*"` lines, the `NfcPayOverlayActivity` activity block, and the `BankoHceService` service block with its intent-filter and meta-data.

`activity_settings.xml`: removed the entire `<!-- ── Section: NFC Payment ── -->` block including the `nfcSection` LinearLayout and its contents.

`strings.xml`: removed `action_nfc_pay`, the 9 NFC strings in the NFC block (`nfc_pay_activate`, `nfc_icon_description`, `nfc_hold_to_terminal`, `nfc_countdown_start`, `nfc_seconds_remaining`, `nfc_payment_section`, `nfc_status_not_set_up`, `nfc_setup_button`, `nfc_remove_button`), the HCE Service section (`hce_service_description`, `hce_aid_description`), and `nfc_receipt_label`. `nfc_cancel` was preserved.

**Deviation 1 — activity_home.xml not in task plan:** A broad NFC grep after edits revealed `activity_home.xml` contained an `activateNfcPayButton` LinearLayout block referencing `@string/action_nfc_pay` (just deleted from strings.xml). Although the block had `android:visibility="gone"`, AAPT2 resolves string references at build time regardless of visibility — leaving it would cause a build error. The entire block was deleted.

**Deviation 2 — ReceiptActivity.kt not in task plan:** The same broad grep found `ReceiptActivity.kt` used `getString(R.string.nfc_receipt_label)` as a synthetic item label for transactions with no line items. The string had been deleted. Replaced with inline `"Payment"` to keep the fallback path functional for any transaction type without line items.

## Verification

Ran the full 10-check verification sweep from the task plan — all pass. Also ran a broad grep sweep (`grep -rn 'NfcManager|BankoHceService|nfc/register|activateNfcPayButton|...' mobile/student_app_v2/app/src/main/`) — returned 0 hits.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `[ ! -f .../BankoHceService.kt ]` | 0 | ✅ pass | <1s |
| 2 | `[ ! -f .../NfcManager.kt ]` | 0 | ✅ pass | <1s |
| 3 | `[ ! -f .../NfcPayOverlayActivity.kt ]` | 0 | ✅ pass | <1s |
| 4 | `[ ! -f .../activity_nfc_pay_overlay.xml ]` | 0 | ✅ pass | <1s |
| 5 | `[ ! -f .../hce_service.xml ]` | 0 | ✅ pass | <1s |
| 6 | `! grep -q 'android.permission.NFC' AndroidManifest.xml` | 0 | ✅ pass | <1s |
| 7 | `! grep -q 'BankoHceService\|NfcPayOverlayActivity' AndroidManifest.xml` | 0 | ✅ pass | <1s |
| 8 | `! grep -q 'nfcManager\|NfcManager' HomeActivity.kt` | 0 | ✅ pass | <1s |
| 9 | `grep -q 'nfc_cancel' strings.xml` | 0 | ✅ pass | <1s |
| 10 | broad NFC grep across all Android sources | 0 hits | ✅ pass | <1s |

## Diagnostics

- `grep -rn 'NfcManager\|BankoHceService\|nfc/register\|activateNfcPayButton\|nfcPayLauncher\|action_nfc_pay\|nfc_receipt_label\|hce_service_description' mobile/student_app_v2/app/src/main/` — must return 0 lines; any hit identifies the exact file/line with remaining dead NFC code.
- `grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml` — must exit 0; this string is still referenced by `activity_qr_pay.xml`.
- `grep -n '"nfc"' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — should show 3 lines (transaction type filter lists); these are live historical-display references and must remain.
- At Android build time: `./gradlew assembleDebug` would fail with AAPT2 unresolved-resource errors if any `@string/` reference was removed from strings.xml without removing all usages in layout/code files.

## Deviations

1. **activity_home.xml deleted NFC block (unplanned):** Task plan did not list this file. The `activateNfcPayButton` LinearLayout block referenced `@string/action_nfc_pay` which was deleted from strings.xml. Removing it was required to prevent an AAPT2 build error.

2. **ReceiptActivity.kt inline string replacement (unplanned):** Task plan did not list this file. `getString(R.string.nfc_receipt_label)` was replaced with `"Payment"` after the string was removed, to keep the fallback receipt rendering path functional.

## Known Issues

None.

## Files Created/Modified

- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — **deleted**
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — **deleted**
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt` — **deleted**
- `mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml` — **deleted**
- `mobile/student_app_v2/app/src/main/res/xml/hce_service.xml` — **deleted**
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — removed NFC fields, nfcPayLauncher, NFC functions, dead imports; preserved "nfc" historical-type refs
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — removed registerNfcDevice and unregisterNfcDevice
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — removed NfcDeviceRequest, NfcUnregisterRequest, NfcRegisterResponse
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — removed NFC permission, features, NfcPayOverlayActivity, BankoHceService
- `mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml` — removed nfcSection block
- `mobile/student_app_v2/app/src/main/res/layout/activity_home.xml` — removed activateNfcPayButton block (unplanned; required for build)
- `mobile/student_app_v2/app/src/main/res/values/strings.xml` — removed NFC strings; nfc_cancel preserved
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ReceiptActivity.kt` — replaced nfc_receipt_label reference with inline "Payment"
- `.gsd/milestones/M005/slices/S05/tasks/T02-PLAN.md` — added Observability Impact section (pre-flight requirement)
- `.gsd/KNOWLEDGE.md` — created with two new knowledge entries
